"""
src/gis/elevation_filler.py
Rellena elevaciones faltantes usando la API gratuita de Open-Meteo.
"""

from __future__ import annotations

import requests

from src.gis.gpx_track_parser import calcular_pendientes
from src.gis.models import TrackPoint

URL = "https://api.open-meteo.com/v1/elevation"
BATCH = 100  # coordenadas por petición


def elevaciones_faltan(puntos: list[TrackPoint]) -> bool:
    """True si ningún punto tiene elevación útil."""
    return all(p.ele is None or p.ele == 0 for p in puntos)


def rellenar_elevacion(
    puntos: list[TrackPoint], batch: int = BATCH
) -> list[TrackPoint]:
    """
    Consulta Open-Meteo en lotes y rellena ele donde falta.
    Recalcula pendientes al terminar.
    """
    idx = [i for i, p in enumerate(puntos) if p.ele is None or p.ele == 0]
    if not idx:
        return puntos

    for start in range(0, len(idx), batch):
        chunk = idx[start : start + batch]
        lats = ",".join(f"{puntos[i].lat:.5f}" for i in chunk)
        lons = ",".join(f"{puntos[i].lon:.5f}" for i in chunk)

        r = requests.get(
            URL,
            params={"latitude": lats, "longitude": lons},
            timeout=30,
        )
        r.raise_for_status()
        eles = r.json()["elevation"]

        for i, e in zip(chunk, eles):
            puntos[i].ele = float(e)

    calcular_pendientes(puntos)
    return puntos
