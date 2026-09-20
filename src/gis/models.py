"""
src/gis/models.py
Modelos de datos para el pipeline GIS.
"""

from dataclasses import dataclass, field
from enum import Enum


class PuntoTipo(Enum):
    INICIO = "inicio"
    FIN = "fin"
    CAMBIO_CARRETERA = "cambio_carretera"
    LOCALIDAD = "localidad"
    ABASTECIMIENTO = "abastecimiento"
    INICIO_PUERTO = "inicio_puerto"
    CIMA_PUERTO = "cima_puerto"




class CategoriaPuerto(Enum):
    HC = "HC"          # Hors Catégorie
    ESPECIAL = "Especial"
    PRIMERA = "1ª"
    SEGUNDA = "2ª"
    TERCERA = "3ª"
    CUARTA = "4ª"




@dataclass
class TrackPoint:
    """Un punto del GPX Track."""
    lat: float
    lon: float
    ele: float | None = None          # Elevación en metros
    time: str | None = None           # Timestamp ISO
    dist_km: float = 0.0                 # Distancia acumulada desde inicio
    gradient_pct: float = 0.0            # Pendiente en % respecto al punto anterior




@dataclass
class RoutePoint:
    """Un waypoint del GPX Route."""
    lat: float
    lon: float
    name: str = ""
    desc: str = ""
    ele: float | None = None




@dataclass
class CueEntry:
    """Una fila del CSV Cuesheet."""
    km: float
    tipo: str                            # "girar_izq", "recto", "cambio_carretera"...
    descripcion: str = ""
    carretera: str = ""
    notas: str = ""




@dataclass
class Climb:
    """Un puerto de montaña detectado."""
    nombre: str = "Puerto sin nombre"
    km_inicio: float = 0.0
    km_cima: float = 0.0
    ele_inicio: float = 0.0
    ele_cima: float = 0.0
    desnivel_m: float = 0.0
    longitud_km: float = 0.0
    pendiente_media_pct: float = 0.0
    pendiente_max_pct: float = 0.0
    categoria: CategoriaPuerto = CategoriaPuerto.CUARTA




@dataclass
class Localidad:
    """Una localidad de paso."""
    nombre: str
    km: float
    lat: float
    lon: float
    servicios: list = field(default_factory=list)  # ["agua","supermercado","bar"]




@dataclass
class PuntoAbastecimiento:
    """Punto de abastecimiento aislado (fuente, tienda...)."""
    tipo: str                            # "fuente", "tienda", "area_descanso"
    km: float
    lat: float
    lon: float
    descripcion: str = ""




@dataclass
class ResumenRuta:
    """Contenedor final con toda la información enriquecida."""
    nombre: str = ""
    distancia_km: float = 0.0
    desnivel_positivo_m: float = 0.0
    desnivel_negativo_m: float = 0.0
    ele_min: float = 0.0
    ele_max: float = 0.0
    inicio: str = ""
    fin: str = ""
    puntos_track: list = field(default_factory=list)       # List[TrackPoint]
    puntos_route: list = field(default_factory=list)       # List[RoutePoint]
    cuesheet: list = field(default_factory=list)           # List[CueEntry]
    puertos: list = field(default_factory=list)            # List[Climb]
    localidades: list = field(default_factory=list)        # List[Localidad]
    abastecimientos: list = field(default_factory=list)    # List[PuntoAbastecimiento]
    cambios_carretera: list = field(default_factory=list)  # List[str]
