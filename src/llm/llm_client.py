"""
src/llm/llm_client.py
Conexión con Ollama vía Instructor para obtener JSON estructurado.
"""


from __future__ import annotations

import os

import instructor
from openai import OpenAI

from src.gis.models import ResumenRuta
from src.llm.prompts import SYSTEM_PROMPT, construir_user_prompt
from src.llm.schemas import ResumenCiclista


def obtener_client() -> instructor.Instructor:
    """
    Crea un cliente Instructor conectado a Ollama
    vía su endpoint compatible con OpenAI.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")



    # Ollama expone una API compatible con OpenAI en /v1
    openai_client = OpenAI(
        base_url=f"{base_url}/v1",
        api_key="ollama",  # Ollama no requiere API key real
    )


    # Instructor envuelve el cliente para forzar salida JSON válida
    client = instructor.from_openai(
        openai_client,
        mode=instructor.Mode.JSON,
    )


    return client




def generar_resumen_ciclista(resumen_ruta: ResumenRuta) -> ResumenCiclista:
    """
    Envía los datos GIS al LLM y recibe un ResumenCiclista estructurado.


    Args:
        resumen_ruta: Objeto con todos los datos procesados en Fase 2.


    Returns:
        ResumenCiclista: Objeto Pydantic validado con la respuesta del LLM.


    Raises:
        Exception: Si el LLM no responde o el JSON no es válido tras 3 intentos.
    """
    client = obtener_client()
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:14b-instruct")


    user_prompt = construir_user_prompt(resumen_ruta)


    print(f"\n🤖 Consultando al LLM ({model})...")
    print("   Esto puede tardar 30-90 segundos la primera vez...")


    result: ResumenCiclista = client.chat.completions.create(
        model=model,
        response_model=ResumenCiclista,
        max_retries=3,  # Reintenta hasta 3 veces si el JSON no es válido
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )


    print("   ✅ Respuesta del LLM recibida y validada.")
    return result
