"""
src/gis/csv_parser.py
Lectura del fichero CSV Cuesheet (puntos de cambio de ruta).
"""

import pandas as pd

from src.gis.models import CueEntry


def parse_csv_cuesheet(filepath: str) -> list[CueEntry]:
    """
    Lee un CSV de cuesheet.
    Columnas esperadas: km, tipo, descripcion, carretera, notas
    (Se aceptan variaciones de nombres de columna)
    """
    df = pd.read_csv(filepath, encoding="utf-8")


    # Normalizar nombres de columnas a minúsculas sin espacios
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]


    # Mapeo flexible de columnas
    col_map = {
        "km": ["km", "kilometro", "kilometros", "distance", "distancia"],
        "tipo": ["tipo", "type", "accion", "action", "maniobra"],
        "descripcion": ["descripcion", "description", "desc", "instruccion"],
        "carretera": ["carretera", "road", "via", "ruta", "highway"],
        "notas": ["notas", "notes", "observaciones", "comentario"],
    }


    # Renombrar columnas según el mapeo
    rename = {}
    for target, aliases in col_map.items():
        for alias in aliases:
            if alias in df.columns:
                rename[alias] = target
                break
    df.rename(columns=rename, inplace=True)


    # Asegurar columnas mínimas
    if "km" not in df.columns:
        raise ValueError("El CSV debe tener una columna 'km' o 'kilometro'")


    df["km"] = pd.to_numeric(df["km"], errors="coerce").fillna(0.0)


    # Construir lista de CueEntry
    entradas: list[CueEntry] = []
    for _, row in df.iterrows():
        entrada = CueEntry(
            km=float(row.get("km", 0)),
            tipo=str(row.get("tipo", "recto")).strip(),
            descripcion=str(row.get("descripcion", "")).strip(),
            carretera=str(row.get("carretera", "")).strip(),
            notas=str(row.get("notas", "")).strip(),
        )
        entradas.append(entrada)


    # Ordenar por km
    entradas.sort(key=lambda e: e.km)


    print(f"  📍 Cuesheet: {len(entradas)} entradas")
    return entradas
