"""
src/output/exporter.py
Exporta el ResumenCiclista a TXT, Markdown y PDF.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from src.llm.schemas import ResumenCiclista
from src.output.formatters import formato_markdown, formato_txt

if TYPE_CHECKING:
    from fpdf import FPDF


def exportar_todo(resumen: ResumenCiclista, output_dir: str) -> list[str]:
    """
    Exporta el resumen a todos los formatos disponibles.
    Devuelve la lista de ficheros generados.
    """
    os.makedirs(output_dir, exist_ok=True)
    ficheros: list[str] = []

    # ── TXT ──
    txt_path = os.path.join(output_dir, "libro_ruta.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(formato_txt(resumen))
    ficheros.append(txt_path)

    # ── Markdown ──
    md_path = os.path.join(output_dir, "libro_ruta.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(formato_markdown(resumen))
    ficheros.append(md_path)

    # ── JSON ──
    json_path = os.path.join(output_dir, "resumen_ruta.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resumen.model_dump(), f, ensure_ascii=False, indent=2)
    ficheros.append(json_path)

    # ── PDF ──
    try:
        pdf_path = os.path.join(output_dir, "libro_ruta.pdf")
        _generar_pdf(resumen, pdf_path)
        ficheros.append(pdf_path)
    except ImportError:
        print("  ⚠️  fpdf2 no instalado. PDF omitido. Instala: pip install fpdf2")

    return ficheros


def _generar_pdf(resumen: ResumenCiclista, filepath: str) -> None:
    """
    Genera un PDF con formato de libro de ruta.
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Página de título ──
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "LIBRO DE RUTA", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, resumen.titulo_ruta, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(
        0, 8,
        f"Distancia: {resumen.distancia_km:.1f} km | "
        f"Desnivel +: {resumen.desnivel_positivo_m} m | "
        f"Dificultad: {resumen.nivel_dificultad}",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.ln(3)
    pdf.cell(0, 8, f"Inicio: {resumen.inicio}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, f"Fin: {resumen.fin}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    # ── Resumen ──
    _pdf_section(pdf, "RESUMEN")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, resumen.resumen_narrativo)
    pdf.ln(5)

    # ── Puertos ──
    if resumen.puertos:
        _pdf_section(pdf, f"PUERTOS DE MONTANA ({len(resumen.puertos)})")
        for p in resumen.puertos:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, f"{p.nombre} | Cat: {p.categoria}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(
                0, 6,
                f"Km {p.km_inicio:.1f} - {p.km_cima:.1f} | "
                f"Desnivel: {p.desnivel_m}m | "
                f"Pendiente: {p.pendiente_media_pct:.1f}%",
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.multi_cell(0, 6, f"Consejo: {p.consejo}")
            pdf.ln(3)

    # ── Localidades ──
    if resumen.localidades:
        _pdf_section(pdf, f"LOCALIDADES DE PASO ({len(resumen.localidades)})")
        pdf.set_font("Helvetica", "", 10)
        for loc in resumen.localidades:
            servicios = ", ".join(loc.servicios) if loc.servicios else "sin datos"
            pdf.cell(
                0, 6,
                f"Km {loc.km:.1f} - {loc.nombre} [{servicios}]",
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(0, 5, f"  {loc.recomendacion}")
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(1)

    # ── Abastecimientos ──
    if resumen.abastecimientos_aislados:
        _pdf_section(pdf, "PUNTOS DE ABASTECIMIENTO")
        pdf.set_font("Helvetica", "", 10)
        for ab in resumen.abastecimientos_aislados:
            pdf.cell(
                0, 6,
                f"Km {ab.km:.1f} - {ab.tipo}: {ab.descripcion}",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.ln(3)

    # ── Cambios de carretera ──
    if resumen.cambios_carretera:
        _pdf_section(pdf, "CAMBIOS DE CARRETERA")
        pdf.set_font("Helvetica", "", 10)
        for cc in resumen.cambios_carretera:
            precaucion = f" | Precaucion: {cc.precaucion}" if cc.precaucion else ""
            pdf.cell(
                0, 6,
                f"Km {cc.km:.1f}: {cc.descripcion} [{cc.carretera}]{precaucion}",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.ln(3)

    # ── Consejo general ──
    _pdf_section(pdf, "CONSEJO GENERAL")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, resumen.consejo_general)

    # ── Pie de página ──
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Generado por bike-route-llm", align="C")

    pdf.output(filepath)


def _pdf_section(pdf: FPDF, titulo: str) -> None:
    """Escribe un título de sección en el PDF."""
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 9, f"  {titulo}", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3)
