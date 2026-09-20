"""
tests/generate_test_data.py
Genera ficheros GPX y CSV de prueba para testing sin datos reales.

Uso:
    python -m tests.generate_test_data
"""

from __future__ import annotations

import math
import os

OUTPUT_DIR = "data/input"


def generar_gpx_track() -> None:
    """
    Genera un GPX Track sintético de 50 km:
      - Km 0-15:   Llano a ~600 m
      - Km 15-25:  Subida (puerto) de 600 m a 1200 m  → pendiente ~6%
      - Km 25-30:  Bajada de 1200 m a 700 m
      - Km 30-50:  Llano a ~700 m con ondulaciones suaves
    """
    puntos: list[tuple[float, float, float]] = []
    lat_base, lon_base = 40.5000, -3.7000  # Zona cercana a Madrid

    # ── Tramo 1: Llano (0-15 km) ──
    for i in range(150):
        km = i * 0.1
        lat = lat_base + km * 0.009
        lon = lon_base + km * 0.003
        ele = 600.0 + i * 0.2  # Ligera subida progresiva
        puntos.append((lat, lon, ele))

    # ── Tramo 2: Puerto de montaña (15-25 km) ──
    for i in range(100):
        km = 15.0 + i * 0.1
        lat = lat_base + km * 0.009
        lon = lon_base + km * 0.003
        progreso = i / 100.0
        # Subida de 600→1200 m con ondulaciones realistas
        ele = 630.0 + 570.0 * progreso + 15.0 * math.sin(progreso * math.pi * 4)
        puntos.append((lat, lon, ele))

    # ── Tramo 3: Bajada (25-30 km) ──
    for i in range(50):
        km = 25.0 + i * 0.1
        lat = lat_base + km * 0.009
        lon = lon_base + km * 0.003
        progreso = i / 50.0
        ele = 1200.0 - 500.0 * progreso
        puntos.append((lat, lon, ele))

    # ── Tramo 4: Llano final con ondulaciones (30-50 km) ──
    for i in range(200):
        km = 30.0 + i * 0.1
        lat = lat_base + km * 0.009
        lon = lon_base + km * 0.003
        ele = 700.0 + 10.0 * math.sin(i * 0.05)
        puntos.append((lat, lon, ele))

    # ── Escribir GPX ──
    gpx_lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="bike-route-llm-test">',
        "  <trk>",
        "    <name>Ruta de Prueba - Puerto de la Morcuera</name>",
        "    <trkseg>",
    ]

    for lat, lon, ele in puntos:
        gpx_lines.append(
            f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}">'
            f"<ele>{ele:.1f}</ele></trkpt>"
        )

    gpx_lines.extend(["    </trkseg>", "  </trk>", "</gpx>"])

    filepath = os.path.join(OUTPUT_DIR, "ruta_track.gpx")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(gpx_lines))

    print(f"  ✅ GPX Track: {filepath} ({len(puntos)} puntos, 50.0 km)")


def generar_gpx_route() -> None:
    """Genera un GPX Route con waypoints clave."""
    waypoints: list[tuple[float, float, str, str]] = [
        (40.5000, -3.7000, "SALIDA", "Inicio de ruta - Plaza del pueblo"),
        (40.5450, -3.6850, "CRUCE_M40", "Cruce: tomar M-608 direccion norte"),
        (40.6350, -3.6550, "INICIO_PUERTO", "Inicio Puerto de la Morcuera"),
        (40.7250, -3.6250, "CIMA", "Cima Puerto de la Morcuera (1200m)"),
        (40.7700, -3.6100, "CRUCE_BAJADA", "Cruce: continuar descenso"),
        (40.9500, -3.5500, "META", "Fin de ruta - Plaza mayor"),
    ]

    gpx_lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="bike-route-llm-test">',
        "  <rte>",
        "    <name>Waypoints Ruta de Prueba</name>",
    ]

    for lat, lon, name, desc in waypoints:
        gpx_lines.append(
            f'    <rtept lat="{lat:.6f}" lon="{lon:.6f}">'
            f"<name>{name}</name><desc>{desc}</desc></rtept>"
        )

    gpx_lines.extend(["  </rte>", "</gpx>"])

    filepath = os.path.join(OUTPUT_DIR, "ruta_route.gpx")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(gpx_lines))

    print(f"  ✅ GPX Route: {filepath} ({len(waypoints)} waypoints)")


def generar_csv_cuesheet() -> None:
    """Genera un CSV Cuesheet de prueba."""
    filas: list[str] = [
        "km,tipo,descripcion,carretera,notas",
        "0.0,salida,Inicio de ruta en la plaza del pueblo,M-608,Confirmar presencia",
        "5.2,recto,Continuar recto por la M-608,M-608,",
        "12.8,cambio_carretera,Girar a la derecha hacia M-611,M-611,Precaucion cruce",
        "15.0,inicio_puerto,Inicio del Puerto de la Morcuera,M-611,Pendiente media 6%",
        "25.0,cima,Cima del Puerto de la Morcuera,M-611,Vistas panoramicas",
        "25.5,descenso,Inicio del descenso,M-611,Precaucion curvas",
        "30.0,cambio_carretera,Enlazar con M-604,M-604,",
        "35.0,localidad,Paso por Miraflores de la Sierra,M-604,Fuente en la plaza",
        "42.3,cambio_carretera,Girar izquierda hacia A-1,A-1,Tramo con arcen",
        "50.0,meta,Fin de ruta - Plaza mayor,,",
    ]

    filepath = os.path.join(OUTPUT_DIR, "ruta_cuesheet.csv")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(filas))

    print(f"  ✅ CSV Cuesheet: {filepath} ({len(filas) - 1} entradas)")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("🔧 Generando datos de prueba...")
    generar_gpx_track()
    generar_gpx_route()
    generar_csv_cuesheet()
    print("✅ Datos de prueba listos en data/input/")
