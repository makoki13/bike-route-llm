"""
src/gis/poi_finder.py
Búsqueda de puntos de abastecimiento cerca de la ruta.
Usa la API Overpass de OpenStreetMap.
"""

from __future__ import annotations

import requests

from src.gis.models import Localidad, PuntoAbastecimiento, TrackPoint

# Radio de búsqueda en metros alrededor de la ruta
RADIO_BUSQUEDA_M = 2000

# URL de la API Overpass
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Tags OSM que nos interesan
POI_QUERIES: dict[str, str] = {
    "fuente": '["amenity"="drinking_water"]',
    "supermercado": '["shop"="supermarket"]',
    "tienda": '["shop"="convenience"]',
    "bar": '["amenity"="bar"]',
    "cafe": '["amenity"="cafe"]',
    "area_descanso": '["highway"="rest_area"]',
}


def buscar_abastecimientos(
    puntos: list[TrackPoint],
    localidades: list[Localidad],
    intervalo_km: float = 10.0,
) -> list[PuntoAbastecimiento]:
    """
    Busca POIs cerca de la ruta cada `intervalo_km`.
    Usa la API Overpass de OpenStreetMap.
    """
    abastecimientos: list[PuntoAbastecimiento] = []
    coordenadas_vistas: set[tuple[float, float]] = set()
    ultima_distancia = 0.0

    for p in puntos:
        if p.dist_km - ultima_distancia < intervalo_km:
            continue
        ultima_distancia = p.dist_km

        pois = _query_overpass(p.lat, p.lon, RADIO_BUSQUEDA_M)

        for poi in pois:
            # Evitar duplicados por coordenadas cercanas
            key = (round(poi["lat"], 3), round(poi["lon"], 3))
            if key in coordenadas_vistas:
                continue
            coordenadas_vistas.add(key)

            abastecimientos.append(
                PuntoAbastecimiento(
                    tipo=poi["tipo"],
                    km=round(p.dist_km, 2),
                    lat=poi["lat"],
                    lon=poi["lon"],
                    descripcion=poi.get("nombre", ""),
                )
            )

    # Enriquecer localidades con servicios encontrados
    _enriquecer_localidades(localidades, abastecimientos)

    print(f"  🚰 Puntos de abastecimiento: {len(abastecimientos)}")
    return abastecimientos


def _query_overpass(lat: float, lon: float, radio_m: int) -> list[dict]:
    """
    Consulta la API Overpass para buscar POIs alrededor de un punto.
    Devuelve una lista de dicts con claves: tipo, lat, lon, nombre.
    """
    # Construir la query Overpass
    filtros = "\n".join(
        f"  node{tags}(around:{radio_m},{lat},{lon});"
        for tags in POI_QUERIES.values()
    )
    query = f"""
[out:json][timeout:15];
(
{filtros}
);
out body;
"""

    try:
        r = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=20,
        )
        if r.status_code != 200:
            return []

        data: dict = r.json()
        elements: list[dict] = data.get("elements", [])

        results: list[dict] = []
        for element in elements:
            tags: dict = element.get("tags", {})
            tipo = _clasificar_poi(tags)
            results.append({
                "tipo": tipo,
                "lat": float(element.get("lat", 0.0)),
                "lon": float(element.get("lon", 0.0)),
                "nombre": str(tags.get("name", "")),
            })
        return results

    except (requests.exceptions.RequestException, ValueError, KeyError):
        return []


def _clasificar_poi(tags: dict) -> str:
    """Clasifica un POI de OSM en nuestras categorías."""
    if tags.get("amenity") == "drinking_water":
        return "fuente"
    if tags.get("shop") in ("supermarket", "convenience"):
        return "tienda"
    if tags.get("amenity") in ("bar", "cafe"):
        return "bar"
    if tags.get("highway") == "rest_area":
        return "area_descanso"
    return "otro"


def _enriquecer_localidades(
    localidades: list[Localidad],
    abastecimientos: list[PuntoAbastecimiento],
    margen_km: float = 2.0,
) -> None:
    """
    Añade servicios a cada localidad según los POIs cercanos.
    """
    for loc in localidades:
        servicios: set[str] = set()
        for ab in abastecimientos:
            if abs(ab.km - loc.km) <= margen_km:
                servicios.add(ab.tipo)
        loc.servicios = sorted(servicios)
