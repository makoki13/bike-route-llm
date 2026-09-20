"""
src/gis/elevation.py
Análisis del perfil de elevación:
  - Suavizado de datos
  - Cálculo de desniveles
  - Detección de puertos de montaña (inicio, cima, categoría)
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from scipy.signal import savgol_filter

from src.gis.models import CategoriaPuerto, Climb, TrackPoint

# ──────────────────────────────────────────────
#  Parámetros de configuración
# ──────────────────────────────────────────────
GRADIENTE_MIN_PCT = 3.0        # Pendiente mínima para considerar "subida"
DISTANCIA_MIN_KM = 1.0         # Longitud mínima del puerto
VENTANA_SUAVIZADO = 15         # Puntos para filtro Savitzky-Golay
POLINOMIO_SUAVIZADO = 3        # Orden del polinomio
GRADIENTE_MAX_DESCANSO = -1.0  # Pendiente bajo la cual se "corta" la subida


def analizar_elevacion(puntos: list[TrackPoint]) -> dict:
    """
    Calcula estadísticas generales del perfil de elevación.
    """
    elevaciones = [p.ele for p in puntos if p.ele is not None]

    if len(elevaciones) < 2:
        return {
            "desnivel_positivo": 0,
            "desnivel_negativo": 0,
            "ele_min": 0,
            "ele_max": 0,
        }

    desnivel_pos = 0.0
    desnivel_neg = 0.0

    for i in range(1, len(elevaciones)):
        diff = elevaciones[i] - elevaciones[i - 1]
        if diff > 0:
            desnivel_pos += diff
        else:
            desnivel_neg += abs(diff)

    return {
        "desnivel_positivo": round(desnivel_pos, 0),
        "desnivel_negativo": round(desnivel_neg, 0),
        "ele_min": round(min(elevaciones), 0),
        "ele_max": round(max(elevaciones), 0),
    }


def detectar_puertos(puntos: list[TrackPoint]) -> list[Climb]:
    """
    Algoritmo principal de detección de puertos de montaña.
    """
    # Filtrar puntos con elevación válida
    validos = [(i, p) for i, p in enumerate(puntos) if p.ele is not None]
    if len(validos) < 10:
        print("  ⚠️  Puntos con elevación insuficientes para detectar puertos")
        return []

    indices = [v[0] for v in validos]
    distancias: npt.NDArray[np.float64] = np.array(
        [puntos[i].dist_km for i in indices], dtype=np.float64
    )
    elevaciones: npt.NDArray[np.float64] = np.array(
        [puntos[i].ele for i in indices], dtype=np.float64
    )

    n_puntos = int(elevaciones.shape[0])

    # ── Paso 1: Suavizar elevación ──
    ventana = min(VENTANA_SUAVIZADO, n_puntos - 1)
    if ventana % 2 == 0:
        ventana -= 1

    elev_suave: npt.NDArray[np.float64]
    if ventana >= 5:
        elev_suave = np.array(
            savgol_filter(elevaciones, ventana, POLINOMIO_SUAVIZADO),
            dtype=np.float64,
        )
    else:
        elev_suave = elevaciones.copy()
    n_suave = int(elev_suave.shape[0])

    # ── Paso 2: Calcular pendiente suavizada ──
    pendientes: npt.NDArray[np.float64] = np.zeros(n_suave, dtype=np.float64)
    for i in range(1, n_suave):
        dx = (distancias[i] - distancias[i - 1]) * 1000.0  # metros
        if dx > 0:
            pendientes[i] = (
                (elev_suave[i] - elev_suave[i - 1]) / dx
            ) * 100.0

    # ── Paso 3: Identificar tramos de subida sostenida ──
    tramos = _identificar_tramos_subida(pendientes)

    # ── Paso 4: Fusionar tramos separados por descansos cortos ──
    tramos = _fusionar_tramos(tramos, distancias, max_gap_km=0.5)

    # ── Paso 5: Filtrar por distancia mínima ──
    tramos = [
        (ini, fin)
        for ini, fin in tramos
        if (distancias[fin] - distancias[ini]) >= DISTANCIA_MIN_KM
    ]

    # ── Paso 6: Construir objetos Climb ──
    puertos: list[Climb] = []
    for ini, fin in tramos:
        climb = _construir_climb(ini, fin, distancias, elev_suave, pendientes)
        if climb is not None:
            puertos.append(climb)

    print(f"  ⛰️  Puertos detectados: {len(puertos)}")
    for p in puertos:
        print(
            f"     → {p.nombre}: km {p.km_inicio:.1f}-{p.km_cima:.1f} | "
            f"{p.desnivel_m:.0f}m+ | {p.pendiente_media_pct:.1f}% | "
            f"{p.categoria.value}"
        )

    return puertos


def _identificar_tramos_subida(
    pendientes: npt.NDArray[np.float64],
) -> list[tuple[int, int]]:
    """
    Encuentra tramos consecutivos donde la pendiente > GRADIENTE_MIN_PCT.
    Devuelve lista de (índice_inicio, índice_fin).
    """
    tramos: list[tuple[int, int]] = []
    en_subida = False
    inicio = 0
    n = int(pendientes.shape[0])

    for i in range(n):
        if pendientes[i] >= GRADIENTE_MIN_PCT and not en_subida:
            en_subida = True
            inicio = i
        elif pendientes[i] < GRADIENTE_MAX_DESCANSO and en_subida:
            en_subida = False
            tramos.append((inicio, i - 1))

    # Cerrar el último tramo si sigue activo
    if en_subida:
        tramos.append((inicio, n - 1))

    return tramos


def _fusionar_tramos(
    tramos: list[tuple[int, int]],
    distancias: npt.NDArray[np.float64],
    max_gap_km: float = 0.5,
) -> list[tuple[int, int]]:
    """
    Fusiona tramos de subida separados por menos de max_gap_km
    (descansos breves dentro del mismo puerto).
    """
    if len(tramos) <= 1:
        return tramos

    fusionados: list[tuple[int, int]] = [tramos[0]]
    for ini, fin in tramos[1:]:
        prev_ini, prev_fin = fusionados[-1]
        gap = float(distancias[ini] - distancias[prev_fin])

        if gap <= max_gap_km:
            fusionados[-1] = (prev_ini, fin)
        else:
            fusionados.append((ini, fin))

    return fusionados


def _construir_climb(
    ini: int,
    fin: int,
    distancias: npt.NDArray[np.float64],
    elevaciones: npt.NDArray[np.float64],
    pendientes: npt.NDArray[np.float64],
) -> Climb | None:
    """
    Construye un objeto Climb a partir de los índices de inicio y fin.
    """
    km_inicio = float(distancias[ini])
    ele_inicio = float(elevaciones[ini])
    ele_max_tramo = float(np.max(elevaciones[ini : fin + 1]))

    # La cima real es el punto de máxima elevación dentro del tramo
    idx_cima = ini + int(np.argmax(elevaciones[ini : fin + 1]))
    km_cima = float(distancias[idx_cima])

    desnivel = ele_max_tramo - ele_inicio
    longitud = km_cima - km_inicio

    if longitud <= 0:
        return None

    pendiente_media = (desnivel / (longitud * 1000.0)) * 100.0
    pendiente_max = float(np.max(pendientes[ini : fin + 1]))

    categoria = _clasificar_puerto(longitud, pendiente_media, desnivel)

    return Climb(
        nombre=f"Puerto km {km_inicio:.0f}",
        km_inicio=round(km_inicio, 2),
        km_cima=round(km_cima, 2),
        ele_inicio=round(ele_inicio, 0),
        ele_cima=round(ele_max_tramo, 0),
        desnivel_m=round(desnivel, 0),
        longitud_km=round(longitud, 2),
        pendiente_media_pct=round(pendiente_media, 1),
        pendiente_max_pct=round(pendiente_max, 1),
        categoria=categoria,
    )


def _clasificar_puerto(
    longitud_km: float,
    pendiente_media: float,
    desnivel_m: float,
) -> CategoriaPuerto:
    """
    Clasificación aproximada según criterios UCI / organizadores de carreras.
    """
    coeficiente = desnivel_m * pendiente_media

    if coeficiente > 8000 or (desnivel_m > 1500 and pendiente_media > 8):
        return CategoriaPuerto.HC
    if coeficiente > 5000 or (desnivel_m > 1000 and pendiente_media > 7):
        return CategoriaPuerto.ESPECIAL
    if coeficiente > 3000 or (desnivel_m > 600 and pendiente_media > 6):
        return CategoriaPuerto.PRIMERA
    if coeficiente > 1500 or (desnivel_m > 400 and pendiente_media > 5):
        return CategoriaPuerto.SEGUNDA
    if coeficiente > 500:
        return CategoriaPuerto.TERCERA
    return CategoriaPuerto.CUARTA
