"""
src/output/formatters.py
Convierte un ResumenCiclista en texto plano, Markdown o datos para PDF.
"""

from __future__ import annotations

from src.llm.schemas import ResumenCiclista


def formato_txt(resumen: ResumenCiclista) -> str:
    """
    Genera un libro de ruta en texto plano (imprimible).
    """
    lineas: list[str] = []
    sep = "=" * 60

    lineas.append(sep)
    lineas.append("  🚴 LIBRO DE RUTA")
    lineas.append(sep)
    lineas.append("")
    lineas.append(f"  {resumen.titulo_ruta}")
    lineas.append(f"  Distancia: {resumen.distancia_km:.1f} km | "
                  f"Desnivel +: {resumen.desnivel_positivo_m} m | "
                  f"Dificultad: {resumen.nivel_dificultad}")
    lineas.append("")
    lineas.append(f"  Inicio: {resumen.inicio}")
    lineas.append(f"  Fin:    {resumen.fin}")
    lineas.append("")
    lineas.append("-" * 60)
    lineas.append("  RESUMEN")
    lineas.append("-" * 60)
    lineas.append(f"  {resumen.resumen_narrativo}")

    # ── Puertos ──
    if resumen.puertos:
        lineas.append("")
        lineas.append("-" * 60)
        lineas.append(f"  PUERTOS DE MONTAÑA ({len(resumen.puertos)})")
        lineas.append("-" * 60)
        for i, p in enumerate(resumen.puertos, 1):
            lineas.append("")
            lineas.append(f"  [{i}] {p.nombre}")
            lineas.append(f"      Km {p.km_inicio:.1f} → {p.km_cima:.1f}")
            lineas.append(f"      Desnivel: {p.desnivel_m}m | "
                          f"Pendiente: {p.pendiente_media_pct:.1f}% | "
                          f"Cat: {p.categoria}")
            lineas.append(f"      Consejo: {p.consejo}")

    # ── Localidades ──
    if resumen.localidades:
        lineas.append("")
        lineas.append("-" * 60)
        lineas.append(f"  LOCALIDADES DE PASO ({len(resumen.localidades)})")
        lineas.append("-" * 60)
        for loc in resumen.localidades:
            servicios = ", ".join(loc.servicios) if loc.servicios else "sin datos"
            lineas.append("")
            lineas.append(f"  Km {loc.km:.1f} - {loc.nombre} [{servicios}]")
            lineas.append(f"      → {loc.recomendacion}")

    # ── Abastecimientos ──
    if resumen.abastecimientos_aislados:
        lineas.append("")
        lineas.append("-" * 60)
        lineas.append(f"  PUNTOS DE ABASTECIMIENTO ({len(resumen.abastecimientos_aislados)})")
        lineas.append("-" * 60)
        for ab in resumen.abastecimientos_aislados:
            lineas.append(f"  Km {ab.km:.1f} - {ab.tipo}: {ab.descripcion}")

    # ── Cambios de carretera ──
    if resumen.cambios_carretera:
        lineas.append("")
        lineas.append("-" * 60)
        lineas.append(f"  CAMBIOS DE CARRETERA ({len(resumen.cambios_carretera)})")
        lineas.append("-" * 60)
        for cc in resumen.cambios_carretera:
            precaucion = f" ⚠️ {cc.precaucion}" if cc.precaucion else ""
            lineas.append(f"  Km {cc.km:.1f}: {cc.descripcion} [{cc.carretera}]{precaucion}")

    # ── Consejo general ──
    lineas.append("")
    lineas.append("-" * 60)
    lineas.append("  CONSEJO GENERAL")
    lineas.append("-" * 60)
    lineas.append(f"  {resumen.consejo_general}")
    lineas.append("")
    lineas.append(sep)
    lineas.append("  Generado por bike-route-llm")
    lineas.append(sep)

    return "\n".join(lineas)


def formato_markdown(resumen: ResumenCiclista) -> str:
    """
    Genera un libro de ruta en Markdown (para web o documentación).
    """
    lineas: list[str] = []

    lineas.append(f"# 🚴 {resumen.titulo_ruta}")
    lineas.append("")
    lineas.append("| Dato | Valor |")
    lineas.append("|------|-------|")
    lineas.append(f"| Distancia | {resumen.distancia_km:.1f} km |")
    lineas.append(f"| Desnivel + | {resumen.desnivel_positivo_m} m |")
    lineas.append(f"| Dificultad | {resumen.nivel_dificultad} |")
    lineas.append(f"| Inicio | {resumen.inicio} |")
    lineas.append(f"| Fin | {resumen.fin} |")
    lineas.append("")

    lineas.append("## 📝 Resumen")
    lineas.append("")
    lineas.append(resumen.resumen_narrativo)
    lineas.append("")

    # ── Puertos ──
    if resumen.puertos:
        lineas.append("## ⛰️ Puertos de Montaña")
        lineas.append("")
        for p in resumen.puertos:
            lineas.append(f"### {p.nombre}")
            lineas.append(f"- **Tramo:** Km {p.km_inicio:.1f} → {p.km_cima:.1f}")
            lineas.append(f"- **Desnivel:** {p.desnivel_m} m")
            lineas.append(f"- **Pendiente media:** {p.pendiente_media_pct:.1f}%")
            lineas.append(f"- **Categoría:** {p.categoria}")
            lineas.append(f"- **💡 Consejo:** {p.consejo}")
            lineas.append("")

    # ── Localidades ──
    if resumen.localidades:
        lineas.append("## 🏘️ Localidades de Paso")
        lineas.append("")
        lineas.append("| Km | Localidad | Servicios | Recomendación |")
        lineas.append("|----|-----------|-----------|---------------|")
        for loc in resumen.localidades:
            servicios = ", ".join(loc.servicios) if loc.servicios else "sin datos"
            lineas.append(
                f"| {loc.km:.1f} | {loc.nombre} | {servicios} | {loc.recomendacion} |"
            )
        lineas.append("")

    # ── Abastecimientos ──
    if resumen.abastecimientos_aislados:
        lineas.append("## 🚰 Puntos de Abastecimiento")
        lineas.append("")
        for ab in resumen.abastecimientos_aislados:
            lineas.append(f"- **Km {ab.km:.1f}** — {ab.tipo}: {ab.descripcion}")
        lineas.append("")

    # ── Cambios de carretera ──
    if resumen.cambios_carretera:
        lineas.append("## 🔀 Cambios de Carretera")
        lineas.append("")
        for cc in resumen.cambios_carretera:
            precaucion = f"\n  > ⚠️ {cc.precaucion}" if cc.precaucion else ""
            lineas.append(f"- **Km {cc.km:.1f}:** {cc.descripcion} `{cc.carretera}`{precaucion}")
        lineas.append("")

    # ── Consejo general ──
    lineas.append("## 💬 Consejo General")
    lineas.append("")
    lineas.append(f"> {resumen.consejo_general}")
    lineas.append("")
    lineas.append("---")
    lineas.append("*Generado por bike-route-llm*")

    return "\n".join(lineas)
