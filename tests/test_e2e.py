"""
tests/test_e2e.py
Test end-to-end del pipeline completo.
Ejecutar con: pytest tests/test_e2e.py -v
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest
from dotenv import load_dotenv

from src.gis.csv_parser import parse_csv_cuesheet
from src.gis.elevation import analizar_elevacion, detectar_puertos
from src.gis.gpx_route_parser import parse_gpx_route
from src.gis.gpx_track_parser import parse_gpx_track
from src.gis.models import ResumenRuta
from src.llm.llm_client import generar_resumen_ciclista
from src.llm.schemas import ResumenCiclista
from src.output.exporter import exportar_todo
from src.output.formatters import formato_markdown, formato_txt

load_dotenv()

INPUT_DIR = os.getenv("DATA_INPUT_DIR", "./data/input")


def _construir_resumen_ruta() -> ResumenRuta:
    """Helper: construye un ResumenRuta desde los ficheros de prueba."""
    track_file = os.path.join(INPUT_DIR, "ruta_track.gpx")
    route_file = os.path.join(INPUT_DIR, "ruta_route.gpx")
    csv_file = os.path.join(INPUT_DIR, "ruta_cuesheet.csv")

    nombre_track, puntos_track = parse_gpx_track(track_file)
    nombre_route, puntos_route = parse_gpx_route(route_file)
    cuesheet = parse_csv_cuesheet(csv_file)
    stats = analizar_elevacion(puntos_track)
    puertos = detectar_puertos(puntos_track)

    return ResumenRuta(
        nombre=nombre_track,
        distancia_km=puntos_track[-1].dist_km,
        desnivel_positivo_m=stats["desnivel_positivo"],
        desnivel_negativo_m=stats["desnivel_negativo"],
        ele_min=stats["ele_min"],
        ele_max=stats["ele_max"],
        inicio="Test inicio",
        fin="Test fin",
        puntos_track=puntos_track,
        puntos_route=puntos_route,
        cuesheet=cuesheet,
        puertos=puertos,
        localidades=[],
        abastecimientos=[],
        cambios_carretera=[],
    )


class TestPipelineGIS:
    """Test del pipeline GIS sin LLM."""

    def test_parseo_gpx_track(self) -> None:
        track_file = os.path.join(INPUT_DIR, "ruta_track.gpx")
        nombre, puntos = parse_gpx_track(track_file)
        assert len(puntos) > 0
        assert nombre != ""
        assert puntos[0].lat != 0
        assert puntos[-1].dist_km > 0

    def test_parseo_gpx_route(self) -> None:
        route_file = os.path.join(INPUT_DIR, "ruta_route.gpx")
        nombre, puntos = parse_gpx_route(route_file)
        assert len(puntos) > 0

    def test_parseo_csv(self) -> None:
        csv_file = os.path.join(INPUT_DIR, "ruta_cuesheet.csv")
        entradas = parse_csv_cuesheet(csv_file)
        assert len(entradas) > 0

    def test_analisis_elevacion(self) -> None:
        track_file = os.path.join(INPUT_DIR, "ruta_track.gpx")
        _, puntos = parse_gpx_track(track_file)
        stats = analizar_elevacion(puntos)
        assert stats["desnivel_positivo"] > 0
        assert stats["ele_max"] > stats["ele_min"]

    def test_deteccion_puertos(self) -> None:
        track_file = os.path.join(INPUT_DIR, "ruta_track.gpx")
        _, puntos = parse_gpx_track(track_file)
        puertos = detectar_puertos(puntos)
        assert len(puertos) >= 1
        assert puertos[0].desnivel_m > 100

    def test_resumen_ruta_completo(self) -> None:
        resumen = _construir_resumen_ruta()
        assert resumen.distancia_km > 40
        assert len(resumen.puertos) >= 1


# ── Fixture a nivel de módulo (evita el warning) ──
@pytest.fixture(scope="module")
def resumen_llm() -> ResumenCiclista:
    """Genera una respuesta del LLM una sola vez para todos los tests."""
    resumen_ruta = _construir_resumen_ruta()
    return generar_resumen_ciclista(resumen_ruta)


class TestPipelineLLM:
    """Test del pipeline con LLM (requiere API activa)."""

    def test_llm_devuelve_json_valido(self, resumen_llm: ResumenCiclista) -> None:
        assert resumen_llm.titulo_ruta != ""
        assert resumen_llm.distancia_km > 0

    def test_llm_exporta_txt(self, resumen_llm: ResumenCiclista) -> None:
        txt = formato_txt(resumen_llm)
        assert len(txt) > 100
        assert "LIBRO DE RUTA" in txt

    def test_llm_exporta_markdown(self, resumen_llm: ResumenCiclista) -> None:
        md = formato_markdown(resumen_llm)
        assert len(md) > 100
        assert "#" in md

    def test_llm_exporta_json(self, resumen_llm: ResumenCiclista) -> None:
        json_str = resumen_llm.model_dump_json()
        data = json.loads(json_str)
        assert "titulo_ruta" in data

    def test_exportar_todo(self, resumen_llm: ResumenCiclista) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ficheros = exportar_todo(resumen_llm, tmpdir)
            assert len(ficheros) >= 3
            for f in ficheros:
                assert os.path.isfile(f)
