"""
src/llm/schemas.py
Modelos Pydantic que definen la estructura JSON que el LLM debe generar.
Instructor forzará al LLM a cumplir estos esquemas.
"""


from __future__ import annotations

from pydantic import BaseModel, Field


class PuertoMontana(BaseModel):
    """Información de un puerto de montaña."""


    nombre: str = Field(description="Nombre del puerto o 'Puerto sin nombre'")
    km_inicio: float = Field(description="Kilómetro donde empieza la subida")
    km_cima: float = Field(description="Kilómetro donde está la cima")
    desnivel_m: int = Field(description="Desnivel positivo en metros")
    pendiente_media_pct: float = Field(description="Pendiente media en %")
    pendiente_max_pct: float = Field(description="Pendiente máxima en %")
    categoria: str = Field(description="Categoría: HC, Especial, 1ª, 2ª, 3ª, 4ª")
    consejo: str = Field(
        description="Consejo práctico para el ciclista en este puerto"
    )




class LocalidadPaso(BaseModel):
    """Localidad de paso con servicios."""


    nombre: str = Field(description="Nombre de la localidad")
    km: float = Field(description="Kilómetro aproximado de paso")
    servicios: list[str] = Field(
        description="Servicios disponibles: agua, supermercado, bar, farmacia..."
    )
    recomendacion: str = Field(
        description="Recomendación breve para el ciclista"
    )




class PuntoAbastecimientoAislado(BaseModel):
    """Punto de abastecimiento fuera de localidades."""


    tipo: str = Field(description="fuente | tienda | area_descanso | bar")
    km: float = Field(description="Kilómetro donde se encuentra")
    descripcion: str = Field(description="Descripción breve del punto")




class CambioCarretera(BaseModel):
    """Cambio de carretera o cruce relevante."""


    km: float = Field(description="Kilómetro del cambio")
    descripcion: str = Field(description="Instrucción de navegación")
    carretera: str = Field(description="Carretera que se toma")
    precaucion: str = Field(
        default="",
        description="Advertencia de seguridad si aplica",
    )




class ResumenCiclista(BaseModel):
    """Esquema principal que el LLM debe rellenar."""


    titulo_ruta: str = Field(description="Título descriptivo de la ruta")
    distancia_km: float = Field(description="Distancia total en km")
    desnivel_positivo_m: int = Field(description="Desnivel positivo total")
    nivel_dificultad: str = Field(
        description="Fácil | Moderada | Difícil | Muy difícil"
    )
    resumen_narrativo: str = Field(
        description="Resumen en 3-5 frases para el ciclista. "
        "Tono cercano, práctico y motivador."
    )
    inicio: str = Field(description="Descripción del punto de inicio")
    fin: str = Field(description="Descripción del punto final")
    puertos: list[PuertoMontana] = Field(
        description="Lista de puertos de montaña detectados"
    )
    localidades: list[LocalidadPaso] = Field(
        description="Localidades de paso con servicios"
    )
    abastecimientos_aislados: list[PuntoAbastecimientoAislado] = Field(
        description="Puntos de agua/comida fuera de pueblos"
    )
    cambios_carretera: list[CambioCarretera] = Field(
        description="Cambios de carretera relevantes"
    )
    consejo_general: str = Field(
        description="Consejo general para afrontar la ruta "
        "(hidratación, alimentación, equipación)"
    )
