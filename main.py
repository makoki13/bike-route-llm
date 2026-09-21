"""
main.py — Orquestador principal del pipeline.
Fase 2 + Fase 3: GIS + LLM.
"""


from __future__ import annotations

import json
import os

from dotenv import load_dotenv

from src.gis.csv_parser import parse_csv_cuesheet
from src.gis.elevation import analizar_elevacion, detectar_puertos
from src.gis.geocoder import detectar_localidades
from src.gis.gpx_parser import parse_gpx_route, parse_gpx_track
from src.gis.models import ResumenRuta
from src.gis.poi_finder import buscar_abastecimientos
from src.llm.llm_client import generar_resumen_ciclista

load_dotenv()


INPUT_DIR = os.getenv("DATA_INPUT_DIR", "./data/input")
OUTPUT_DIR = os.getenv("DATA_OUTPUT_DIR", "./data/output")




def main() -> None:  # noqa: C901
    print("=" * 55)
    print("  🚴 bike-route-llm — Pipeline Completo")
    print("=" * 55)


    # ═══════════════════════════════════════════
    #  FASE 2: Pipeline GIS
    # ═══════════════════════════════════════════
    print("\n📂 Leyendo ficheros de entrada...")


    track_file = os.path.join(INPUT_DIR, "ruta_track.gpx")
    route_file = os.path.join(INPUT_DIR, "ruta_route.gpx")
    csv_file = os.path.join(INPUT_DIR, "ruta_cuesheet.csv")


    for f in [track_file, route_file, csv_file]:
        if not os.path.isfile(f):
            print(f"  ❌ No encontrado: {f}")
            print("     → Ejecuta: python -m tests.generate_test_data")
            return


    nombre_track, puntos_track = parse_gpx_track(track_file)
    nombre_route, puntos_route = parse_gpx_route(route_file)
    cuesheet = parse_csv_cuesheet(csv_file)


    print("\n📈 Analizando perfil de elevación...")
    stats = analizar_elevacion(puntos_track)


    print("\n⛰️  Detectando puertos de montaña...")
    puertos = detectar_puertos(puntos_track)


    print("\n🏘️  Detectando localidades...")
    localidades = detectar_localidades(puntos_track, intervalo_km=5.0)


    print("\n🚰 Buscando puntos de abastecimiento...")
    abastecimientos = buscar_abastecimientos(
        puntos_track, localidades, intervalo_km=10.0
    )


    cambios_carretera = [
        f"Km {c.km:.1f}: {c.descripcion} ({c.carretera})"
        for c in cuesheet
        if c.tipo == "cambio_carretera"
    ]


    resumen_ruta = ResumenRuta(
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


    # ═══════════════════════════════════════════
    #  FASE 3: Conexión con el LLM
    # ═══════════════════════════════════════════
    print("\n" + "=" * 55)
    print("  🤖 FASE 3: Generando resumen con LLM")
    print("=" * 55)


    try:
        resumen_ciclista = generar_resumen_ciclista(resumen_ruta)
    except Exception as e:
        print(f"\n  ❌ Error al consultar el LLM: {e}")
        print("     → ¿Está Ollama corriendo? Ejecuta: ollama serve")
        return


    # ═══════════════════════════════════════════
    #  MOSTRAR RESULTADOS
    # ═══════════════════════════════════════════
    print("\n" + "=" * 55)
    print("  📋 LIBRO DE RUTA GENERADO POR EL LLM")
    print("=" * 55)


    print(f"\n📌 {resumen_ciclista.titulo_ruta}")
    print(f"   Distancia: {resumen_ciclista.distancia_km:.1f} km | "
          f"Desnivel +: {resumen_ciclista.desnivel_positivo_m} m | "
          f"Dificultad: {resumen_ciclista.nivel_dificultad}")
    print(f"\n📝 {resumen_ciclista.resumen_narrativo}")


    print(f"\n🏁 Inicio: {resumen_ciclista.inicio}")
    print(f"🏁 Fin:    {resumen_ciclista.fin}")


    if resumen_ciclista.puertos:
        print(f"\n⛰️  PUERTOS ({len(resumen_ciclista.puertos)}):")
        for p in resumen_ciclista.puertos:
            print(f"   → {p.nombre} | km {p.km_inicio:.1f}-{p.km_cima:.1f} | "
                  f"{p.desnivel_m}m+ | {p.pendiente_media_pct:.1f}% | {p.categoria}")
            print(f"     💡 {p.consejo}")


    if resumen_ciclista.localidades:
        print(f"\n🏘️  LOCALIDADES ({len(resumen_ciclista.localidades)}):")
        for loc in resumen_ciclista.localidades:
            servicios = ", ".join(loc.servicios) if loc.servicios else "sin datos"
            print(f"   → {loc.nombre} (km {loc.km:.1f}) [{servicios}]")
            print(f"     💡 {loc.recomendacion}")


    if resumen_ciclista.abastecimientos_aislados:
        print(f"\n🚰 ABASTECIMIENTOS ({len(resumen_ciclista.abastecimientos_aislados)}):")
        for ab in resumen_ciclista.abastecimientos_aislados:
            print(f"   → {ab.tipo} en km {ab.km:.1f}: {ab.descripcion}")


    if resumen_ciclista.cambios_carretera:
        print(f"\n🔀 CAMBIOS DE CARRETERA ({len(resumen_ciclista.cambios_carretera)}):")
        for cc in resumen_ciclista.cambios_carretera:
            print(f"   → Km {cc.km:.1f}: {cc.descripcion} [{cc.carretera}]")
            if cc.precaucion:
                print(f"     ⚠️  {cc.precaucion}")


    print(f"\n💬 Consejo general: {resumen_ciclista.consejo_general}")


    # ═══════════════════════════════════════════
    #  EXPORTAR JSON
    # ═══════════════════════════════════════════
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "resumen_ruta.json")


    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            resumen_ciclista.model_dump(),
            f,
            ensure_ascii=False,
            indent=2,
        )


    print(f"\n💾 JSON exportado: {output_path}")
    print("\n✅ Pipeline completo finalizado.")




def _obtener_inicio(puntos_route: list, cuesheet: list) -> str:
    """Extrae una descripción del punto de inicio."""
    if puntos_route:
        return f"{puntos_route[0].name} - {puntos_route[0].desc}"
    if cuesheet:
        return f"Km {cuesheet[0].km:.1f} - {cuesheet[0].descripcion}"
    return "Inicio de ruta"




def _obtener_fin(puntos_route: list, cuesheet: list) -> str:
    """Extrae una descripción del punto final."""
    if puntos_route:
        return f"{puntos_route[-1].name} - {puntos_route[-1].desc}"
    if cuesheet:
        return f"Km {cuesheet[-1].km:.1f} - {cuesheet[-1].descripcion}"
    return "Fin de ruta"




if __name__ == "__main__":
    main()
