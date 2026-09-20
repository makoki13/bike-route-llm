"""
main.py — Orquestador principal del pipeline.
Fase 2: Lectura de ficheros + análisis GIS.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from src.gis.csv_parser import parse_csv_cuesheet
from src.gis.elevation import analizar_elevacion, detectar_puertos
from src.gis.geocoder import detectar_localidades
from src.gis.gpx_parser import parse_gpx_route, parse_gpx_track
from src.gis.models import ResumenRuta
from src.gis.poi_finder import buscar_abastecimientos

load_dotenv()

INPUT_DIR = os.getenv("DATA_INPUT_DIR", "./data/input")


def main() -> None:
    print("=" * 55)
    print("  🚴 bike-route-llm — Pipeline GIS (Fase 2)")
    print("=" * 55)

    # ── 1. Leer ficheros de entrada ──
    print("\n📂 Leyendo ficheros de entrada...")

    track_file = os.path.join(INPUT_DIR, "ruta_track.gpx")
    route_file = os.path.join(INPUT_DIR, "ruta_route.gpx")
    csv_file = os.path.join(INPUT_DIR, "ruta_cuesheet.csv")

    # Verificar que existen
    for f in [track_file, route_file, csv_file]:
        if not os.path.isfile(f):
            print(f"  ❌ No encontrado: {f}")
            print("     → Ejecuta: python -m tests.generate_test_data")
            return

    nombre_track, puntos_track = parse_gpx_track(track_file)
    nombre_route, puntos_route = parse_gpx_route(route_file)
    cuesheet = parse_csv_cuesheet(csv_file)

    # ── 2. Análisis de elevación ──
    print("\n📈 Analizando perfil de elevación...")
    stats = analizar_elevacion(puntos_track)
    print(f"  Desnivel +: {stats['desnivel_positivo']:.0f} m")
    print(f"  Desnivel -: {stats['desnivel_negativo']:.0f} m")
    print(f"  Elevación:  {stats['ele_min']:.0f} - {stats['ele_max']:.0f} m")

    # ── 3. Detección de puertos ──
    print("\n⛰️  Detectando puertos de montaña...")
    puertos = detectar_puertos(puntos_track)

    # ── 4. Geocodificación (localidades) ──
    print("\n🏘️  Detectando localidades...")
    localidades = detectar_localidades(puntos_track, intervalo_km=5.0)

    # ── 5. Puntos de abastecimiento ──
    print("\n🚰 Buscando puntos de abastecimiento...")
    abastecimientos = buscar_abastecimientos(
        puntos_track, localidades, intervalo_km=10.0
    )

    # ── 6. Extraer cambios de carretera del cuesheet ──
    cambios_carretera = [
        f"Km {c.km:.1f}: {c.descripcion} ({c.carretera})"
        for c in cuesheet
        if c.tipo == "cambio_carretera"
    ]

    # ── 7. Construir resumen ──
    resumen = ResumenRuta(
        nombre=nombre_track,
        distancia_km=puntos_track[-1].dist_km if puntos_track else 0.0,
        desnivel_positivo_m=stats["desnivel_positivo"],
        desnivel_negativo_m=stats["desnivel_negativo"],
        ele_min=stats["ele_min"],
        ele_max=stats["ele_max"],
        inicio=_obtener_inicio(puntos_route, cuesheet),
        fin=_obtener_fin(puntos_route, cuesheet),
        puntos_track=puntos_track,
        puntos_route=puntos_route,
        cuesheet=cuesheet,
        puertos=puertos,
        localidades=localidades,
        abastecimientos=abastecimientos,
        cambios_carretera=cambios_carretera,
    )

    # ── 8. Resumen por pantalla ──
    print("\n" + "=" * 55)
    print("  📋 RESUMEN DEL RECORRIDO")
    print("=" * 55)
    print(f"  Nombre:            {resumen.nombre}")
    print(f"  Distancia:         {resumen.distancia_km:.1f} km")
    print(f"  Desnivel +:        {resumen.desnivel_positivo_m:.0f} m")
    print(f"  Elevación:         {resumen.ele_min:.0f} - {resumen.ele_max:.0f} m")
    print(f"  Waypoints route:   {len(resumen.puntos_route)}")
    print(f"  Entradas cuesheet: {len(resumen.cuesheet)}")

    print(f"\n  ⛰️  PUERTOS ({len(resumen.puertos)}):")
    for p in resumen.puertos:
        print(
            f"     → {p.nombre}: km {p.km_inicio:.1f} → {p.km_cima:.1f} | "
            f"{p.desnivel_m:.0f}m+ | {p.pendiente_media_pct:.1f}% | "
            f"Cat: {p.categoria.value}"
        )

    print(f"\n  🏘️  LOCALIDADES ({len(resumen.localidades)}):")
    for loc in resumen.localidades:
        servicios = ", ".join(loc.servicios) if loc.servicios else "sin datos"
        print(f"     → {loc.nombre} (km {loc.km:.1f}) [{servicios}]")

    print(f"\n  🚰 ABASTECIMIENTOS ({len(resumen.abastecimientos)}):")
    for ab in resumen.abastecimientos:
        print(f"     → {ab.tipo} en km {ab.km:.1f}")

    print(f"\n  🔀 CAMBIOS DE CARRETERA ({len(resumen.cambios_carretera)}):")
    for cc in resumen.cambios_carretera:
        print(f"     → {cc}")

    print("\n✅ Fase 2 completada.")

def _obtener_inicio(
    puntos_route: list,
    cuesheet: list,
) -> str:
    """Extrae una descripción del punto de inicio."""
    # Prioridad 1: primer waypoint del route
    if puntos_route:
        return f"{puntos_route[0].name} - {puntos_route[0].desc}"

    # Prioridad 2: primera entrada del cuesheet
    if cuesheet:
        return f"Km {cuesheet[0].km:.1f} - {cuesheet[0].descripcion}"

    return "Inicio de ruta"


def _obtener_fin(
    puntos_route: list,
    cuesheet: list,
) -> str:
    """Extrae una descripción del punto final."""
    # Prioridad 1: último waypoint del route
    if puntos_route:
        return f"{puntos_route[-1].name} - {puntos_route[-1].desc}"

    # Prioridad 2: última entrada del cuesheet
    if cuesheet:
        return f"Km {cuesheet[-1].km:.1f} - {cuesheet[-1].descripcion}"

    return "Fin de ruta"

if __name__ == "__main__":
    main()
