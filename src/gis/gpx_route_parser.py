"""
src/gis/gpx_route_parser.py
Lectura de ficheros GPX de tipo Route (waypoints de navegación).
"""

import gpxpy

from src.gis.models import RoutePoint


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

    # Waypoints dentro de <rte>
    for route in gpx.routes:
        for point in route.points:
            puntos.append(
                RoutePoint(
                    lat=point.latitude,
                    lon=point.longitude,
                    name=point.name or "",
                    desc=point.description or "",
                    ele=point.elevation,
                )
            )

    # Waypoints sueltos (<wpt>)
    for wpt in gpx.waypoints:
        puntos.append(
            RoutePoint(
                lat=wpt.latitude,
                lon=wpt.longitude,
                name=wpt.name or "",
                desc=wpt.description or "",
                ele=wpt.elevation,
            )
        )

    print(f"  📍 Route '{nombre}': {len(puntos)} waypoints")
    return nombre, puntos
