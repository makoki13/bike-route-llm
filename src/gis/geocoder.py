"""
src/gis/geocoder.py
Reverse geocoding: coordenadas → nombre de localidad.
Usa Nominatim (OpenStreetMap) con rate limiting.
"""

from __future__ import annotations

import time
from typing import cast

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from geopy.location import Location

from src.gis.models import Localidad, TrackPoint

# Nominatim exige máx. 1 petición/segundo y un User-Agent identificable
_geolocator = Nominatim(user_agent="bike-route-llm/1.0")
_ultima_peticion: float = 0.0


def detectar_localidades(
    puntos: list[TrackPoint],
    intervalo_km: float = 5.0,
) -> list[Localidad]:
    """
    Recorre el track cada `intervalo_km` y hace reverse geocoding
    para detectar si estamos dentro de una localidad.
    """
    localidades: list[Localidad] = []
    nombres_vistos: set[str] = set()
    ultima_distancia = 0.0

    for p in puntos:
        if p.dist_km - ultima_distancia < intervalo_km:
            continue
        ultima_distancia = p.dist_km

        nombre = _reverse_geocode(p.lat, p.lon)
        if nombre is not None and nombre not in nombres_vistos:
            nombres_vistos.add(nombre)
            localidades.append(
                Localidad(
                    nombre=nombre,
                    km=round(p.dist_km, 2),
                    lat=p.lat,
                    lon=p.lon,
                    servicios=[],
                )
            )
            print(f"  🏘️  Localidad: {nombre} (km {p.dist_km:.1f})")

    print(f"  🏘️  Localidades detectadas: {len(localidades)}")
    return localidades


def _reverse_geocode(lat: float, lon: float) -> str | None:
    """
    Devuelve el nombre de la localidad más cercana, o None.
    Respeta el rate limit de 1 petición/segundo de Nominatim.
    """
    global _ultima_peticion

    # Rate limiting
    elapsed = time.time() - _ultima_peticion
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)

    try:
        query = f"{lat}, {lon}"
        kwargs: dict = {
            "language": "es",
            "addressdetails": True,
            "timeout": 10,
        }
        # Los stubs de geopy tipan mal 'language' y 'timeout'.
        # La llamada es correcta en runtime.
        result = _geolocator.reverse(query, **kwargs)  # type: ignore[arg-type]

        # Forzar tipo Location (elimina confusión con CoroutineType)
        location = cast(Location | None, result)
        _ultima_peticion = time.time()

        if location is not None and location.raw.get("address"):
            addr: dict = location.raw["address"]
            nombre: str | None = (
                addr.get("village")
                or addr.get("town")
                or addr.get("city")
                or addr.get("municipality")
            )
            return nombre

    except (GeocoderTimedOut, GeocoderServiceError):
        pass

    return None
