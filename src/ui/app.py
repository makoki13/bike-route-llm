"""
src/ui/app.py
Interfaz Streamlit para bike-route-llm.

Ejecutar con:
    streamlit run src/ui/app.py
"""

from __future__ import annotations

import os
import sys

import streamlit as st

# Asegurar que el proyecto está en el path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

from dotenv import load_dotenv

from src.gis.csv_parser import parse_csv_cuesheet
from src.gis.elevation import analizar_elevacion, detectar_puertos
from src.gis.elevation_filler import elevaciones_faltan, rellenar_elevacion
from src.gis.geocoder import detectar_localidades
from src.gis.gpx_route_parser import parse_gpx_route
from src.gis.gpx_track_parser import parse_gpx_track
from src.gis.models import ResumenRuta, TrackPoint
from src.gis.poi_finder import buscar_abastecimientos
from src.llm.llm_client import generar_resumen_ciclista
from src.ui.components import (
    mostrar_descargas,
    mostrar_mapa,
    mostrar_perfil_elevacion,
    mostrar_resumen,
)

load_dotenv()


# ──────────────────────────────────────────────
#  Funciones cacheadas
# ──────────────────────────────────────────────
@st.cache_data(show_spinner="Procesando ficheros...")
def _parsear_track(path: str) -> tuple:
    """Parsea el GPX track con caché."""
    return parse_gpx_track(path)


@st.cache_data(show_spinner="Procesando ficheros...")
def _parsear_route(path: str) -> tuple:
    """Parsea el GPX route con caché."""
    return parse_gpx_route(path)


@st.cache_data(show_spinner="Procesando ficheros...")
def _parsear_cuesheet(path: str) -> list:
    """Parsea el CSV cuesheet con caché."""
    return parse_csv_cuesheet(path)


@st.cache_data(show_spinner="Consultando OpenStreetMap...")
def _geocodificar_y_pois(
    coords: tuple,
    intervalo_geo: float,
    intervalo_abas: float,
) -> tuple[list, list]:
    """
    Geocoding + POIs con caché.
    Solo consulta OpenStreetMap si cambian las coordenadas
    o los intervalos. El resto de veces devuelve caché.
    """
    puntos = [
        TrackPoint(lat=c[0], lon=c[1], ele=c[2], dist_km=c[3])
        for c in coords
    ]
    localidades = detectar_localidades(puntos, intervalo_km=intervalo_geo)
    abastecimientos = buscar_abastecimientos(
        puntos, localidades, intervalo_km=intervalo_abas
    )
    return localidades, abastecimientos


@st.cache_data(show_spinner="Rellenando elevación con Open-Meteo...")
def _rellenar_elevacion_cacheado(coords: tuple) -> tuple:
    """
    Rellena elevaciones faltantes con caché.
    Devuelve tupla de (lat, lon, ele, dist_km) ya rellenada.
    """
    puntos = [
        TrackPoint(lat=c[0], lon=c[1], ele=c[2], dist_km=c[3])
        for c in coords
    ]
    puntos = rellenar_elevacion(puntos)
    return tuple((p.lat, p.lon, p.ele, p.dist_km) for p in puntos)


# ──────────────────────────────────────────────
#  Configuración de la página
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="bike-route-llm",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
#  Sidebar: Configuración
# ──────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuración")

    st.subheader("📂 Ficheros de entrada")
    tab = st.radio("Fuente de datos", ["Ficheros locales", "Subir ficheros"])

    intervalo_geocoding = st.slider(
        "Intervalo geocoding (km)", 2.0, 20.0, 5.0, 0.5
    )
    intervalo_abastecimiento = st.slider(
        "Intervalo abastecimiento (km)", 5.0, 30.0, 10.0, 1.0
    )

    st.divider()
    st.subheader("🤖 Modelo LLM")
    modelo = st.text_input(
        "Modelo",
        value=os.getenv("OLLAMA_MODEL", "qwen/qwen3.8-27b"),
    )

# ──────────────────────────────────────────────
#  Cabecera
# ──────────────────────────────────────────────
st.title("🚴 bike-route-llm")
st.markdown(
    "Analiza rutas ciclistas y genera libros de ruta inteligentes "
    "con IA (Qwen + Instructor)."
)

# ──────────────────────────────────────────────
#  Entrada de datos
# ──────────────────────────────────────────────
if tab == "Ficheros locales":
    input_dir = os.getenv("DATA_INPUT_DIR", "./data/input")
    track_file = os.path.join(input_dir, "ruta_track.gpx")
    route_file = os.path.join(input_dir, "ruta_route.gpx")
    csv_file = os.path.join(input_dir, "ruta_cuesheet.csv")

    if not os.path.isfile(track_file):
        st.error(
            f"No se encuentra `{track_file}`. "
            "Ejecuta: `python -m tests.generate_test_data`"
        )
        st.stop()

    st.info(f"📂 Leyendo desde: `{input_dir}`")

    nombre_track, puntos_track = _parsear_track(track_file)
    nombre_route, puntos_route = _parsear_route(route_file)
    cuesheet = _parsear_cuesheet(csv_file)

elif tab == "Subir ficheros":
    st.subheader("📤 Sube tus ficheros")

    col1, col2, col3 = st.columns(3)
    with col1:
        uploaded_track = st.file_uploader("GPX Track", type=["gpx"], key="track")
    with col2:
        uploaded_route = st.file_uploader("GPX Route", type=["gpx"], key="route")
    with col3:
        uploaded_csv = st.file_uploader("CSV Cuesheet", type=["csv"], key="csv")

    if uploaded_track is None:
        st.warning("⚠️ Sube al menos el GPX Track para continuar.")
        st.stop()

    # Guardar ficheros temporales
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as f:
        f.write(uploaded_track.read())
        tmp_track = f.name

    tmp_route = None
    if uploaded_route is not None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as f:
            f.write(uploaded_route.read())
            tmp_route = f.name

    tmp_csv = None
    if uploaded_csv is not None:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            f.write(uploaded_csv.read())
            tmp_csv = f.name

    with st.spinner("Procesando ficheros subidos..."):
        nombre_track, puntos_track = parse_gpx_track(tmp_track)
        if tmp_route:
            nombre_route, puntos_route = parse_gpx_route(tmp_route)
        else:
            nombre_route, puntos_route = "Route", []
        if tmp_csv:
            cuesheet = parse_csv_cuesheet(tmp_csv)
        else:
            cuesheet = []

# ── Guard: el GPX debe tener puntos ──
if not puntos_track:
    st.error("⚠️ El GPX no contiene puntos válidos. Revisa el fichero.")
    st.stop()

# ──────────────────────────────────────────────
#  Relleno de elevación si el GPX no la trae
# ──────────────────────────────────────────────
if elevaciones_faltan(puntos_track):
    st.warning(
        "⚠️ El GPX no incluye elevación. Se consultará Open-Meteo "
        "para rellenar el perfil."
    )
    coords_sin_ele = tuple(
        (p.lat, p.lon, p.ele, p.dist_km) for p in puntos_track
    )
    coords_rellenos = _rellenar_elevacion_cacheado(coords_sin_ele)
    puntos_track = [
        TrackPoint(lat=c[0], lon=c[1], ele=c[2], dist_km=c[3])
        for c in coords_rellenos
    ]

# ──────────────────────────────────────────────
#  Pipeline GIS
# ──────────────────────────────────────────────
st.divider()
st.subheader("📊 Análisis GIS")

with st.spinner("Analizando elevación y detectando puertos..."):
    stats = analizar_elevacion(puntos_track)
    puertos = detectar_puertos(puntos_track)

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
col1.metric("📏 Distancia", f"{puntos_track[-1].dist_km:.1f} km")
col2.metric("⛰️ Desnivel +", f"{stats['desnivel_positivo']:.0f} m")
col3.metric("📉 Desnivel -", f"{stats['desnivel_negativo']:.0f} m")
col4.metric("🏔️ Ele. máx", f"{stats['ele_max']:.0f} m")

# Perfil de elevación
mostrar_perfil_elevacion(puntos_track, puertos)

# ──────────────────────────────────────────────
#  Geocoding y POIs (cacheado)
# ──────────────────────────────────────────────
coords = tuple((p.lat, p.lon, p.ele, p.dist_km) for p in puntos_track)

with st.expander(
    "🏘️ Detectar localidades y abastecimientos (requiere internet)"
):
    localidades, abastecimientos = _geocodificar_y_pois(
        coords, intervalo_geocoding, intervalo_abastecimiento
    )
    st.write(
        f"Localidades: {len(localidades)} | "
        f"Abastecimientos: {len(abastecimientos)}"
    )

# Mapa
mostrar_mapa(puntos_track, puertos, localidades)

# ──────────────────────────────────────────────
#  Construir ResumenRuta
# ──────────────────────────────────────────────
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
    inicio=f"Inicio de {nombre_track}",
    fin=f"Fin de {nombre_track}",
    puntos_track=puntos_track,
    puntos_route=puntos_route,
    cuesheet=cuesheet,
    puertos=puertos,
    localidades=localidades,
    abastecimientos=abastecimientos,
    cambios_carretera=cambios_carretera,
)

# ──────────────────────────────────────────────
#  LLM: Generar libro de ruta
# ──────────────────────────────────────────────
st.divider()
st.subheader("🤖 Libro de Ruta (LLM)")

if st.button(
    "🚀 Generar Libro de Ruta", type="primary", width="stretch"
):
    with st.spinner("Consultando al LLM... (puede tardar 5-30 segundos)"):
        try:
            resumen_ciclista = generar_resumen_ciclista(resumen_ruta)
            st.session_state["resumen_ciclista"] = resumen_ciclista
            st.success("✅ Libro de ruta generado correctamente.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

# Mostrar resultado si existe
if "resumen_ciclista" in st.session_state:
    resumen_ciclista = st.session_state["resumen_ciclista"]

    mostrar_resumen(resumen_ciclista)

    # ── Descargas ──
    st.divider()
    st.subheader("💾 Descargar")
    mostrar_descargas(resumen_ciclista)

# ──────────────────────────────────────────────
#  Pie de página
# ──────────────────────────────────────────────
st.divider()
st.caption("🚴 bike-route-llm | Generado con Qwen + Instructor + Streamlit")
