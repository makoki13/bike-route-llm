"""
src/gis/gpx_parser.py
Lectura de ficheros GPX (Track y Route).
"""

import gpxpy

from src.gis.models import RoutePoint, TrackPoint


def parse_gpx_track(filepath: str) -> tuple[str, list[TrackPoint]]:
    """
    Lee un fichero GPX de tipo Track.
    Devuelve: (nombre_del_track, lista_de_puntos)
    """
    with open(filepath, "r", encoding="utf-8") as f:  # noqa: UP015
        gpx = gpxpy.parse(f)

    nombre = (
        gpx.tracks[0].name
        if gpx.tracks and gpx.tracks[0].name
        else gpx.name or "Track sin nombre"
    )
    puntos: list[TrackPoint] = []
    dist_acumulada = 0.0

    for track in gpx.tracks:
        for segment in track.segments:
            prev = None
            for point in segment.points:
                # Distancia incremental (proteger contra None)
                if prev is not None:
                    d = point.distance_2d(prev)
                    if d is not None:
                        dist_acumulada += d / 1000.0  # km

                tp = TrackPoint(
                    lat=point.latitude,
                    lon=point.longitude,
                    ele=point.elevation,
                    time=point.time.isoformat() if point.time else None,
                    dist_km=round(dist_acumulada, 4),
                )
                puntos.append(tp)
                prev = point

    # Calcular pendientes entre puntos consecutivos
    _calcular_pendientes(puntos)

    print(f"  📍 Track '{nombre}': {len(puntos)} puntos, "
          f"{dist_acumulada:.1f} km")
    return nombre, puntos



def parse_gpx_route(filepath: str) -> tuple[str, list[RoutePoint]]:
    """
    Lee un fichero GPX de tipo Route (waypoints).
    Devuelve: (nombre_de_la_ruta, lista_de_waypoints)
    """
    with open(filepath, encoding="utf-8") as f:
        gpx = gpxpy.parse(f)


    nombre = (
        gpx.routes[0].name
        if gpx.routes and gpx.routes[0].name
        else gpx.name or "Route sin nombre"
    )
    puntos: list[RoutePoint] = []


    for route in gpx.routes:
        for point in route.points:
            rp = RoutePoint(
                lat=point.latitude,
                lon=point.longitude,
                name=point.name or "",
                desc=point.description or "",
                ele=point.elevation,
            )
            puntos.append(rp)


    # También buscar waypoints sueltos (<wpt>)
    for wpt in gpx.waypoints:
        rp = RoutePoint(
            lat=wpt.latitude,
            lon=wpt.longitude,
            name=wpt.name or "",
            desc=wpt.description or "",
            ele=wpt.elevation,
        )
        puntos.append(rp)


    print(f"  📍 Route '{nombre}': {len(puntos)} waypoints")
    return nombre, puntos




def _calcular_pendientes(puntos: list[TrackPoint]) -> None:
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


        desnivel = p_curr.ele - p_prev.ele  # metros
        distancia_m = (p_curr.dist_km - p_prev.dist_km) * 1000.0  # metros


        if distancia_m > 0:
            p_curr.gradient_pct = round((desnivel / distancia_m) * 100.0, 2)
        else:
            p_curr.gradient_pct = 0.0
