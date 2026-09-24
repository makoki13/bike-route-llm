"""
src/ui/components.py
Componentes reutilizables de la interfaz Streamlit.
"""

from __future__ import annotations

import json

import plotly.graph_objects as go
import streamlit as st

from src.gis.models import Climb, Localidad, TrackPoint
from src.llm.schemas import ResumenCiclista
from src.output.formatters import formato_markdown, formato_txt


def mostrar_perfil_elevacion(
    puntos: list[TrackPoint],
    puertos: list[Climb],
) -> None:
    """
    Muestra el perfil de elevación con zonas de puerto sombreadas.
    Usa Plotly para interactividad (hover, zoom).
    """
    distancias = [p.dist_km for p in puntos]
    elevaciones = [p.ele for p in puntos]

    fig = go.Figure()

    # Zonas de puerto (sombreado)
    for puerto in puertos:
        fig.add_vrect(
            x0=puerto.km_inicio,
            x1=puerto.km_cima,
            fillcolor="rgba(255, 140, 0, 0.2)",
            line_width=0,
            annotation_text=f"⛰️ {puerto.nombre}",
            annotation_position="top left",
        )

    # Línea de elevación
    fig.add_trace(
        go.Scatter(
            x=distancias,
            y=elevaciones,
            mode="lines",
            name="Elevación",
            line=dict(color="#2196F3", width=2),
            fill="tozeroy",
            fillcolor="rgba(33, 150, 243, 0.1)",
            hovertemplate=(
                "<b>Km %{x:.1f}</b><br>Elevación: %{y:.0f} m<br><extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="📈 Perfil de Elevación",
        xaxis_title="Distancia (km)",
        yaxis_title="Elevación (m)",
        height=400,
        showlegend=False,
        margin=dict(l=40, r=20, t=50, b=40),
    )

    st.plotly_chart(fig, width="stretch")


def mostrar_mapa(
    puntos: list[TrackPoint],
    puertos: list[Climb],
    localidades: list[Localidad],
) -> None:
    """
    Muestra el track sobre un mapa interactivo con Folium.
    """
    try:
        import folium
        from streamlit_folium import folium_static
    except ImportError:
        st.warning("⚠️ Instala folium y streamlit-folium para ver el mapa.")
        return

    if not puntos:
        return

    # Centro del mapa
    lat_centro = sum(p.lat for p in puntos) / len(puntos)
    lon_centro = sum(p.lon for p in puntos) / len(puntos)

    # Crear mapa
    mapa = folium.Map(
        location=[lat_centro, lon_centro],
        zoom_start=11,
        tiles="OpenStreetMap",
    )

    # Capa de terreno
    folium.TileLayer(
        "Stamen Terrain",
        attr="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap.",
    ).add_to(mapa)

    # Track como polilínea
    coordenadas = [[p.lat, p.lon] for p in puntos]
    folium.PolyLine(
        locations=coordenadas,
        color="#2196F3",
        weight=3,
        opacity=0.8,
        tooltip="Track GPX",
    ).add_to(mapa)

    # Marcador de inicio
    folium.Marker(
        location=[puntos[0].lat, puntos[0].lon],
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
        tooltip="🟢 Inicio",
        popup="Inicio de la ruta",
    ).add_to(mapa)

    # Marcador de fin
    folium.Marker(
        location=[puntos[-1].lat, puntos[-1].lon],
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        tooltip="🔴 Fin",
        popup="Fin de la ruta",
    ).add_to(mapa)

    # Puertos (cima)
    for puerto in puertos:
        # Buscar el punto más cercano a la cima
        idx_cima = min(
            range(len(puntos)),
            key=lambda i: abs(puntos[i].dist_km - puerto.km_cima),
        )
        folium.Marker(
            location=[puntos[idx_cima].lat, puntos[idx_cima].lon],
            icon=folium.Icon(color="orange", icon="mountain", prefix="fa"),
            tooltip=f"⛰️ {puerto.nombre} ({puerto.categoria.value})",
            popup=(
                f"<b>{puerto.nombre}</b><br>"
                f"Desnivel: {puerto.desnivel_m:.0f}m<br>"
                f"Pendiente: {puerto.pendiente_media_pct:.1f}%"
            ),
        ).add_to(mapa)

    # Localidades
    for loc in localidades:
        folium.CircleMarker(
            location=[loc.lat, loc.lon],
            radius=8,
            color="#4CAF50",
            fill=True,
            fill_color="#4CAF50",
            fill_opacity=0.7,
            tooltip=f"🏘️ {loc.nombre} (km {loc.km:.1f})",
        ).add_to(mapa)

    st.subheader("🗺️ Mapa de la Ruta")
    folium_static(mapa, width=900, height=500)


def mostrar_resumen(resumen: ResumenCiclista) -> None:
    """
    Muestra el libro de ruta generado por el LLM.
    """
    # Cabecera
    st.markdown(f"## 📌 {resumen.titulo_ruta}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Distancia", f"{resumen.distancia_km:.1f} km")
    col2.metric("Desnivel +", f"{resumen.desnivel_positivo_m} m")
    col3.metric("Dificultad", resumen.nivel_dificultad)

    st.markdown(f"**Inicio:** {resumen.inicio}")
    st.markdown(f"**Fin:** {resumen.fin}")

    st.markdown("---")
    st.markdown("### 📝 Resumen")
    st.write(resumen.resumen_narrativo)

    # Puertos
    if resumen.puertos:
        st.markdown("---")
        st.markdown(f"### ⛰️ Puertos ({len(resumen.puertos)})")
        for p in resumen.puertos:
            with st.container():
                st.markdown(f"**{p.nombre}** — Cat: {p.categoria}")
                st.markdown(
                    f"Km {p.km_inicio:.1f} → {p.km_cima:.1f} | "
                    f"{p.desnivel_m}m+ | {p.pendiente_media_pct:.1f}%"
                )
                st.info(f"💡 {p.consejo}")

    # Localidades
    if resumen.localidades:
        st.markdown("---")
        st.markdown(f"### 🏘️ Localidades ({len(resumen.localidades)})")
        for loc in resumen.localidades:
            servicios = ", ".join(loc.servicios) if loc.servicios else "sin datos"
            st.markdown(
                f"**Km {loc.km:.1f}** — {loc.nombre} [{servicios}]\n\n"
                f"*{loc.recomendacion}*"
            )

    # Abastecimientos
    if resumen.abastecimientos_aislados:
        st.markdown("---")
        st.markdown("### 🚰 Abastecimientos")
        for ab in resumen.abastecimientos_aislados:
            st.markdown(f"- Km {ab.km:.1f}: **{ab.tipo}** — {ab.descripcion}")

    # Cambios de carretera
    if resumen.cambios_carretera:
        st.markdown("---")
        st.markdown("### 🔀 Cambios de Carretera")
        for cc in resumen.cambios_carretera:
            precaucion = f" ⚠️ {cc.precaucion}" if cc.precaucion else ""
            st.markdown(
                f"- Km {cc.km:.1f}: {cc.descripcion} `{cc.carretera}`{precaucion}"
            )

    # Consejo general
    st.markdown("---")
    st.markdown("### 💬 Consejo General")
    st.success(resumen.consejo_general)


def mostrar_descargas(resumen: ResumenCiclista) -> None:
    """
    Muestra botones de descarga para cada formato.
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button(
            label="📄 TXT",
            data=formato_txt(resumen),
            file_name="libro_ruta.txt",
            mime="text/plain",
            width="stretch",
        )

    with col2:
        st.download_button(
            label="📝 Markdown",
            data=formato_markdown(resumen),
            file_name="libro_ruta.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col3:
        st.download_button(
            label="📊 JSON",
            data=json.dumps(resumen.model_dump(), ensure_ascii=False, indent=2),
            file_name="resumen_ruta.json",
            mime="application/json",
            use_container_width=True,
        )

    with col4:
        try:
            import os
            import tempfile

            from src.output.exporter import _generar_pdf

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp_path = tmp.name
            tmp.close()

            _generar_pdf(resumen, tmp_path)

            with open(tmp_path, "rb") as f:
                pdf_data = f.read()
            os.unlink(tmp_path)

            st.download_button(
                label="📕 PDF",
                data=pdf_data,
                file_name="libro_ruta.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            st.button("📕 PDF (no disponible)", disabled=True)
