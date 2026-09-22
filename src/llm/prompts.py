"""
src/llm/prompts.py
System Prompt y construcción del contexto para el LLM.
"""

from __future__ import annotations

from src.gis.models import ResumenRuta

SYSTEM_PROMPT = """\
Eres un director deportivo experto en ciclismo de carretera y gravel, \
especializado en diseño y análisis de recorridos ciclistas.

Tu tarea es analizar los datos técnicos de una ruta ciclista y generar \
un libro de ruta claro, práctico y útil para el ciclista que la va a realizar.

REGLAS FUNDAMENTALES:
1. Responde SIEMPRE en español.
2. Genera ÚNICAMENTE el JSON solicitado. Sin texto adicional, sin markdown, \
sin explicaciones fuera del JSON.
3. Sé práctico y directo: el ciclista necesita información accionable.
4. Prioriza la SEGURIDAD: advierte sobre cruces peligrosos, descensos \
técnicos, tramos sin arcén y zonas sin servicios.
5. Para puertos de montaña, da consejos sobre:
   - Desarrollo recomendado (plato/piñón)
   - Cadencia objetivo
   - Alimentación e hidratación durante la subida
   - Ritmo recomendado
6. Si hay tramos largos (>15 km) sin abastecimiento, advierte al ciclista \
de llevar agua y comida extra.
7. NO inventes datos que no estén en el contexto proporcionado.
8. Si un dato no está disponible, indica "sin datos".
9. Usa terminología ciclista correcta: desarrollo, cadencia, desnivel, \
repecho, puerto, collado, alto, grupeta, abanico.
10. Clasifica la dificultad considerando: distancia, desnivel, terreno \
y aislamiento.

ESCALA DE DIFICULTAD:
- Fácil: <30 km, <300m desnivel, sin puertos
- Moderada: 30-80 km, 300-1000m desnivel, puertos de 3ª-4ª
- Difícil: 80-150 km, 1000-2500m desnivel, puertos de 1ª-2ª
- Muy difícil: >150 km, >2500m desnivel, puertos HC/Especial

CONSEJOS DE PUERTO POR CATEGORÍA:
- HC/Especial: desarrollo 34x32, cadencia 70-80 rpm, comer cada 30 min
- 1ª: desarrollo 34x28, cadencia 75-85 rpm, comer cada 40 min
- 2ª: desarrollo 34x25, cadencia 80-90 rpm, gel a mitad de subida
- 3ª-4ª: desarrollo 36x25, cadencia 85-95 rpm, mantener ritmo constante
"""


def construir_contexto(resumen: ResumenRuta) -> str:  # noqa: C901
    """
    Convierte el objeto ResumenRuta (datos GIS procesados)
    en un texto estructurado que el LLM pueda interpretar.
    """
    lineas: list[str] = []

    # ── Datos generales ──
    lineas.append("## DATOS GENERALES DE LA RUTA")
    lineas.append(f"- Nombre: {resumen.nombre}")
    lineas.append(f"- Distancia: {resumen.distancia_km:.1f} km")
    lineas.append(f"- Desnivel positivo: {resumen.desnivel_positivo_m:.0f} m")
    lineas.append(f"- Desnivel negativo: {resumen.desnivel_negativo_m:.0f} m")
    lineas.append(
        f"- Elevación mín/máx: {resumen.ele_min:.0f} / {resumen.ele_max:.0f} m"
    )
    lineas.append(f"- Inicio: {resumen.inicio}")
    lineas.append(f"- Fin: {resumen.fin}")

    # ── Puertos de montaña ──
    lineas.append("\n## PUERTOS DE MONTAÑA DETECTADOS")
    if resumen.puertos:
        for p in resumen.puertos:
            lineas.append(
                f"- {p.nombre}: km {p.km_inicio:.1f} → {p.km_cima:.1f} | "
                f"Desnivel: {p.desnivel_m:.0f}m | "
                f"Longitud: {p.longitud_km:.1f} km | "
                f"Pendiente media: {p.pendiente_media_pct:.1f}% | "
                f"Pendiente máx: {p.pendiente_max_pct:.1f}% | "
                f"Categoría: {p.categoria.value}"
            )
    else:
        lineas.append("- No se han detectado puertos de montaña.")

    # ── Localidades ──
    lineas.append("\n## LOCALIDADES DE PASO")
    if resumen.localidades:
        for loc in resumen.localidades:
            servicios = ", ".join(loc.servicios) if loc.servicios else "sin datos"
            lineas.append(f"- {loc.nombre} (km {loc.km:.1f}) [{servicios}]")
    else:
        lineas.append("- No se han detectado localidades.")

    # ── Abastecimientos aislados ──
    lineas.append("\n## PUNTOS DE ABASTECIMIENTO AISLADOS")
    if resumen.abastecimientos:
        for ab in resumen.abastecimientos:
            lineas.append(f"- {ab.tipo} en km {ab.km:.1f}: {ab.descripcion}")
    else:
        lineas.append("- No se han encontrado puntos de abastecimiento aislados.")

    # ── Cambios de carretera ──
    lineas.append("\n## CAMBIOS DE CARRETERA")
    if resumen.cambios_carretera:
        for cc in resumen.cambios_carretera:
            lineas.append(f"- {cc}")
    else:
        lineas.append("- No hay cambios de carretera registrados.")

    # ── Cuesheet (instrucciones de navegación) ──
    lineas.append("\n## CUESHEET (INSTRUCCIONES DE NAVEGACIÓN)")
    if resumen.cuesheet:
        for c in resumen.cuesheet:
            carretera = f" [{c.carretera}]" if c.carretera else ""
            notas = f" ({c.notas})" if c.notas else ""
            lineas.append(
                f"- Km {c.km:.1f}: {c.tipo} - {c.descripcion}{carretera}{notas}"
            )

    # ── Waypoints del route ──
    lineas.append("\n## WAYPOINTS DE LA RUTA")
    if resumen.puntos_route:
        for wp in resumen.puntos_route:
            desc = f" - {wp.desc}" if wp.desc else ""
            lineas.append(f"- {wp.name}{desc}")

    return "\n".join(lineas)


def construir_user_prompt(resumen: ResumenRuta) -> str:
    """
    Construye el prompt completo del usuario con el contexto GIS.
    """
    contexto = construir_contexto(resumen)

    return f"""\
Analiza los siguientes datos técnicos de una ruta ciclista y genera \
un libro de ruta completo y estructurado.

{contexto}

---

Genera el resumen del recorrido siguiendo exactamente el esquema JSON \
solicitado. Incluye consejos prácticos para el ciclista basándote \
en los datos proporcionados. No inventes información que no esté \
en el contexto anterior.
"""
