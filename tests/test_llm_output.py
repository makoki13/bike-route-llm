"""
tests/test_llm_output.py
Evalúa la calidad de las respuestas del LLM.
Ejecutar con: pytest tests/test_llm_output.py -v
"""

from __future__ import annotations

import json

import pytest
from dotenv import load_dotenv

from src.gis.models import Climb, Localidad, ResumenRuta, TrackPoint
from src.llm.llm_client import generar_resumen_ciclista
from src.llm.schemas import ResumenCiclista

load_dotenv()


""" def _crear_resumen_mock() -> ResumenRuta:
    puntos = [
        TrackPoint(lat=40.0, lon=-3.0, ele=600, dist_km=0.0),
        TrackPoint(lat=40.1, lon=-3.0, ele=700, dist_km=5.0),
        TrackPoint(lat=40.2, lon=-3.0, ele=900, dist_km=10.0),
        TrackPoint(lat=40.3, lon=-3.0, ele=1200, dist_km=15.0),
        TrackPoint(lat=40.4, lon=-3.0, ele=800, dist_km=20.0),
        TrackPoint(lat=40.5, lon=-3.0, ele=700, dist_km=25.0),
    ]

    return ResumenRuta(
        nombre="Ruta Test Evaluación",
        distancia_km=25.0,
        desnivel_positivo_m=600,
        desnivel_negativo_m=500,
        ele_min=600,
        ele_max=1200,
        inicio="Plaza del pueblo",
        fin="Ermita del monte",
        puntos_track=puntos,
        puertos=[
            Climb(
                nombre="Puerto Test",
                km_inicio=5.0,
                km_cima=15.0,
                ele_inicio=700,
                ele_cima=1200,
                desnivel_m=500,
                longitud_km=10.0,
                pendiente_media_pct=5.0,
                pendiente_max_pct=8.2,
            )
        ],
        localidades=[
            Localidad(
                nombre="Pueblo A",
                km=5.0,
                lat=40.1,
                lon=-3.0,
                servicios=["agua", "supermercado"],
            ),
        ],
        abastecimientos=[],
        cambios_carretera=["Km 5.0: Girar derecha hacia M-600 (M-600)"],
    )
 """
def _crear_resumen_mock() -> ResumenRuta:
    """Crea un ResumenRuta sintético para testing."""
    puntos = [
        TrackPoint(lat=40.0, lon=-3.0, ele=600, dist_km=0.0),
        TrackPoint(lat=40.1, lon=-3.0, ele=700, dist_km=5.0),
        TrackPoint(lat=40.2, lon=-3.0, ele=900, dist_km=10.0),
        TrackPoint(lat=40.3, lon=-3.0, ele=1200, dist_km=15.0),
        TrackPoint(lat=40.4, lon=-3.0, ele=800, dist_km=20.0),
        TrackPoint(lat=40.5, lon=-3.0, ele=700, dist_km=25.0),
    ]

    # Construir Climb paso a paso (evita el warning de Pylance)
    puerto = Climb()
    puerto.nombre = "Puerto Test"
    puerto.km_inicio = 5.0
    puerto.km_cima = 15.0
    puerto.ele_inicio = 700.0
    puerto.ele_cima = 1200.0
    puerto.desnivel_m = 500.0
    puerto.longitud_km = 10.0
    puerto.pendiente_media_pct = 5.0
    puerto.pendiente_max_pct = 8.2

    # Construir Localidad paso a paso
    localidad = Localidad(
        nombre="Pueblo A",
        km=5.0,
        lat=40.1,
        lon=-3.0,
    )
    localidad.servicios = ["agua", "supermercado"]

    return ResumenRuta(
        nombre="Ruta Test Evaluación",
        distancia_km=25.0,
        desnivel_positivo_m=600.0,
        desnivel_negativo_m=500.0,
        ele_min=600.0,
        ele_max=1200.0,
        inicio="Plaza del pueblo",
        fin="Ermita del monte",
        puntos_track=puntos,
        puertos=[puerto],
        localidades=[localidad],
        abastecimientos=[],
        cambios_carretera=["Km 5.0: Girar derecha hacia M-600 (M-600)"],
    )


@pytest.fixture(scope="module")
def resumen_llm() -> ResumenCiclista:
    """Genera una respuesta del LLM una sola vez para todos los tests."""
    resumen_mock = _crear_resumen_mock()
    return generar_resumen_ciclista(resumen_mock)


class TestEstructuraJSON:
    """Verifica que el JSON tiene la estructura correcta."""

    def test_tiene_titulo(self, resumen_llm: ResumenCiclista) -> None:
        assert len(resumen_llm.titulo_ruta) > 0

    def test_tiene_resumen_narrativo(self, resumen_llm: ResumenCiclista) -> None:
        assert len(resumen_llm.resumen_narrativo) > 50

    def test_tiene_puertos(self, resumen_llm: ResumenCiclista) -> None:
        assert len(resumen_llm.puertos) >= 1

    def test_tiene_localidades(self, resumen_llm: ResumenCiclista) -> None:
        assert len(resumen_llm.localidades) >= 1

    def test_tiene_consejo_general(self, resumen_llm: ResumenCiclista) -> None:
        assert len(resumen_llm.consejo_general) > 20

    def test_dificultad_valida(self, resumen_llm: ResumenCiclista) -> None:
        niveles = ["Fácil", "Moderada", "Difícil", "Muy difícil"]
        assert resumen_llm.nivel_dificultad in niveles


class TestContenidoCiclista:
    """Verifica que el contenido tiene sentido ciclista."""

    def test_puerto_tiene_consejo(self, resumen_llm: ResumenCiclista) -> None:
        for puerto in resumen_llm.puertos:
            assert len(puerto.consejo) > 10, (
                f"El puerto '{puerto.nombre}' no tiene consejo"
            )

    def test_localidad_tiene_recomendacion(
        self, resumen_llm: ResumenCiclista
    ) -> None:
        for loc in resumen_llm.localidades:
            assert len(loc.recomendacion) > 5, (
                f"La localidad '{loc.nombre}' no tiene recomendación"
            )

    def test_no_hay_puertos_inventados(
        self, resumen_llm: ResumenCiclista
    ) -> None:
        """El LLM no debería inventar más puertos de los del contexto."""
        assert len(resumen_llm.puertos) <= 3, "Demasiados puertos inventados"

    def test_distancia_coherente(self, resumen_llm: ResumenCiclista) -> None:
        """La distancia no debería variar más de un 20% respecto al input."""
        assert 20.0 <= resumen_llm.distancia_km <= 30.0


class TestSerializacion:
    """Verifica que el JSON se puede exportar correctamente."""

    def test_json_serializable(self, resumen_llm: ResumenCiclista) -> None:
        json_str = resumen_llm.model_dump_json()
        data = json.loads(json_str)
        assert "titulo_ruta" in data
        assert "puertos" in data

    def test_json_roundtrip(self, resumen_llm: ResumenCiclista) -> None:
        """Serializa y deserializa sin perder datos."""
        json_str = resumen_llm.model_dump_json()
        data = json.loads(json_str)
        reconstructed = ResumenCiclista(**data)
        assert reconstructed.titulo_ruta == resumen_llm.titulo_ruta
