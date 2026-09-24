"""
src/gis/csv_parser.py
Parser flexible de cuesheets CSV.

Soporta:
  - Formato propio:      km, tipo, descripcion, carretera, notas
  - Formato RideWithGPS: Type, Notes, Distance (km) From Start,
                         Elevation (m), Description, Edited
"""

from __future__ import annotations

import csv
import re

from src.gis.models import CuesheetEntry

# ── Nombres de columna aceptados (normalizados, sin espacios ni símbolos) ──
KM_COLUMNS = [
    "km", "kilometro", "kilometros", "distancia",
    "distance", "distancekmfromstart",
]
TIPO_COLUMNS = ["tipo", "type"]
DESC_COLUMNS = [
    "descripcion", "description", "notes",
    "instruccion", "instruction",
]
CARRETERA_COLUMNS = ["carretera", "road", "street"]
NOTAS_COLUMNS = ["notas", "note", "comments"]

# ── Traducción de tipos RideWithGPS (inglés) → tipos internos ──
TIPO_MAP = {
    "start": "salida",
    "finish": "meta",
    "end": "meta",
    "straight": "recto",
    "continue": "recto",
    "left": "giro_izquierda",
    "slightleft": "giro_izquierda",
    "sharpleft": "giro_izquierda",
    "bearleft": "giro_izquierda",
    "right": "giro_derecha",
    "slightright": "giro_derecha",
    "sharpright": "giro_derecha",
    "bearright": "giro_derecha",
    "roundabout": "rotonda",
    "uturn": "cambio_sentido",
}

# ── Regex para códigos de carretera (A-1, CV-605, M-611, N-330, AP-7...) ──
ROAD_REGEX = re.compile(r"\b([A-Z]{1,3}-\d{1,4}(?:\.\d)?)\b")


def _normalizar(cadena: str) -> str:
    """Quita espacios, tildes y símbolos; pasa a minúsculas."""
    return re.sub(r"[^a-z0-9]", "", cadena.lower())


def _columnas_presentes(
    fieldnames: list[str], candidatos_ordenados: list[str]
) -> list[str]:
    """Devuelve las columnas reales presentes, en orden de prioridad."""
    norm_map = {_normalizar(f): f for f in fieldnames if f}
    return [norm_map[c] for c in candidatos_ordenados if c in norm_map]


def parse_csv_cuesheet(filepath: str) -> list[CuesheetEntry]:  # noqa: C901
    """
    Parsea un cuesheet CSV en formato propio o RideWithGPS.
    Detecta columnas automáticamente y traduce tipos.
    """
    entradas: list[CuesheetEntry] = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # ✅ CORREGIDO: conversión explícita a list
        fieldnames = list(reader.fieldnames or [])

        cols_km = _columnas_presentes(fieldnames, KM_COLUMNS)
        cols_tipo = _columnas_presentes(fieldnames, TIPO_COLUMNS)
        cols_desc = _columnas_presentes(fieldnames, DESC_COLUMNS)
        cols_carretera = _columnas_presentes(fieldnames, CARRETERA_COLUMNS)
        cols_notas = _columnas_presentes(fieldnames, NOTAS_COLUMNS)

        if not cols_km:
            raise ValueError(
                f"El CSV no tiene columna de kilómetros. "
                f"Columnas detectadas: {fieldnames}"
            )

        col_km = cols_km[0]
        col_tipo = cols_tipo[0] if cols_tipo else None

        carretera_previa = ""

        for row in reader:
            # ── km ─
            try:
                km = float(
                    str(row.get(col_km, "")).replace(",", ".").strip()
                )
            except (ValueError, TypeError):
                continue

            # ── tipo (traducido si viene de RideWithGPS) ──
            tipo_raw = (row.get(col_tipo) or "").strip() if col_tipo else ""
            tipo = TIPO_MAP.get(
                _normalizar(tipo_raw), tipo_raw.lower() or "paso"
            )

            # ── descripción: primera no vacía entre las columnas candidatas ──
            desc = ""
            for c in cols_desc:
                valor = (row.get(c) or "").strip()
                if valor:
                    desc = valor
                    break

            # ── notas ─
            notas = ""
            for c in cols_notas:
                valor = (row.get(c) or "").strip()
                if valor:
                    notas = valor
                    break

            # ── carretera: columna propia o extraída de la descripción ──
            carretera = ""
            for c in cols_carretera:
                valor = (row.get(c) or "").strip()
                if valor:
                    carretera = valor
                    break
            if not carretera:
                m = ROAD_REGEX.search(desc)
                carretera = m.group(1) if m else ""

            # ── detectar cambio de carretera ──
            if (
                carretera
                and carretera_previa
                and carretera != carretera_previa
                and tipo not in ("salida", "meta")
            ):
                tipo = "cambio_carretera"
            if carretera:
                carretera_previa = carretera

            entradas.append(
                CuesheetEntry(
                    km=km,
                    tipo=tipo,
                    descripcion=desc,
                    carretera=carretera,
                    notas=notas,
                )
            )

    return entradas
