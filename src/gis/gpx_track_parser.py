"""
src/gis/gpx_track_parser.py
Lectura de ficheros GPX de tipo Track.
Robusto: acepta puntos en <trk>, <rte> o <wpt>.
"""

from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import TYPE_CHECKING

import gpxpy

from src.gis.models import TrackPoint

if TYPE_CHECKING:
    from gpxpy.gpx import GPX


def _haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Distancia horizontal en km entre dos coordenadas."""
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * r * asin(sqrt(a))


def _recoger_puntos_raw(
    gpx: "GPX",
) -> tuple[list[tuple[float, float, float | None, datetime | None]], str]:
    """
    Extrae (lat, lon, ele, time) del GPX.
    Prueba en orden: tracks → routes → waypoints.
    Devuelve también el origen usado.
    """
    raw: list[tuple[float, float, float | None, datetime | None]] = []
    origen = ""

    if gpx.tracks:
        origen = "track"
        for track in gpx.tracks:
            for segment in track.segments:
                for p in segment.points:
                    raw.append((p.latitude, p.longitude, p.elevation, p.time))

    if not raw and gpx.routes:
        origen = "route"
        for route in gpx.routes:
            for p in route.points:
                raw.append((p.latitude, p.longitude, p.elevation, p.time))

    if not raw and gpx.waypoints:
        origen = "waypoints"
        for w in gpx.waypoints:
            raw.append((w.latitude, w.longitude, w.elevation, w.time))

    return raw, origen


def parse_gpx_track(filepath: str) -> tuple[str, list[TrackPoint]]:
    """
    Lee un fichero GPX de tipo Track.
    Devuelve: (nombre_del_track, lista_de_puntos)
    """
    with open(filepath, encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    raw, origen = _recoger_puntos_raw(gpx)

    if not raw:
        raise ValueError(
            f"El GPX '{filepath}' no contiene puntos "
            "(ni tracks, ni routes, ni waypoints)."
        )

    nombre = (
        gpx.tracks[0].name
        if gpx.tracks and gpx.tracks[0].name
        else (
            gpx.routes[0].name
            if gpx.routes and gpx.routes[0].name
            else gpx.name or "Track sin nombre"
        )
    )

    puntos: list[TrackPoint] = []
    dist_acumulada = 0.0

    for i, (lat, lon, ele, time) in enumerate(raw):
        if i > 0:
            prev = raw[i - 1]
            dist_acumulada += _haversine_km(prev[0], prev[1], lat, lon)

        tp = TrackPoint(
            lat=lat,
            lon=lon,
            ele=ele,
            time=time.isoformat() if time else None,
            dist_km=round(dist_acumulada, 4),
        )
        puntos.append(tp)

    calcular_pendientes(puntos)

    print(
        f"  📍 Track '{nombre}': {len(puntos)} puntos, "
        f"{dist_acumulada:.1f} km (origen: {origen})"
    )
    return nombre, puntos


def calcular_pendientes(puntos: list[TrackPoint]) -> None:
    """
    Calcula la pendiente (%) entre cada punto y el anterior.
    pendiente = (desnivel / distancia_horizontal) * 100
    """
    for i in range(1, len(puntos)):
        p_prev = puntos[i - 1]
        p_curr = puntos[i]

        if p_prev.ele is None or p_curr.ele is None:
            p_curr.gradient_pct = 0.0
            continue

        desnivel = p_curr.ele - p_prev.ele
        distancia_m = (p_curr.dist_km - p_prev.dist_km) * 1000.0

        if distancia_m > 0:
            p_curr.gradient_pct = round((desnivel / distancia_m) * 100.0, 2)
        else:
            p_curr.gradient_pct = 0.0
