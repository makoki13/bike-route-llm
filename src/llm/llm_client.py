"""
src/llm/llm_client.py
Conexión con el LLM vía Instructor.
Soporta: Groq, Ollama local, cualquier API compatible OpenAI.
Incluye reintentos, manejo de errores y métricas.
"""

from __future__ import annotations

import os
import time

import instructor
from openai import OpenAI

from src.gis.models import ResumenRuta
from src.llm.prompts import SYSTEM_PROMPT, construir_user_prompt
from src.llm.schemas import ResumenCiclista

# ──────────────────────────────────────────────
#  Configuración
# ──────────────────────────────────────────────
TIMEOUT_SEGUNDOS = 120.0
MAX_RETRIES = 3
RETRY_DELAY_S = 3


def obtener_client() -> instructor.Instructor:
    """
    Crea un cliente Instructor conectado a la API configurada.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    api_key = os.getenv("GROQ_API_KEY", "ollama")

    # Construir URL del endpoint /v1
    if "/v1" in base_url:
        api_url = base_url
    else:
        api_url = f"{base_url}/v1"

    openai_client = OpenAI(
        base_url=api_url,
        api_key=api_key,
        timeout=TIMEOUT_SEGUNDOS,
    )

    client = instructor.from_openai(
        openai_client,
        mode=instructor.Mode.JSON,
    )

    return client


def generar_resumen_ciclista(resumen_ruta: ResumenRuta) -> ResumenCiclista:  # noqa: C901
    """
    Envía los datos GIS al LLM y recibe un ResumenCiclista estructurado.
    Incluye reintentos automáticos y manejo de errores.
    """
    client = obtener_client()
    model = os.getenv("OLLAMA_MODEL", "qwen/qwen3.8-27b")

    user_prompt = construir_user_prompt(resumen_ruta)

    print(f"\n🤖 Consultando al LLM ({model})...")

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()

            result: ResumenCiclista = client.chat.completions.create(
                model=model,
                response_model=ResumenCiclista,
                max_retries=1,
                temperature=0.3,
                top_p=0.9,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            elapsed = time.time() - start
            print(f"   ✅ Respuesta recibida en {elapsed:.1f}s")
            return result

        except Exception as e:
            last_error = e
            error_msg = str(e).lower()

            if "model_not_found" in error_msg or "does not exist" in error_msg:
                print(f"   ❌ Modelo '{model}' no encontrado.")
                raise ValueError(f"Modelo '{model}' no disponible") from e

            if "401" in error_msg or "unauthorized" in error_msg:
                print("   ❌ API key inválida.")
                raise PermissionError("API key inválida") from e

            if "connection" in error_msg or "refused" in error_msg:
                print("   ❌ No se puede conectar a la API.")
                raise ConnectionError("No se puede conectar") from e

            if "429" in error_msg or "rate" in error_msg:
                print(f"   ⚠️  Rate limit. Esperando {RETRY_DELAY_S * attempt}s...")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_S * attempt)
                    continue

            if "retry" in error_msg or "validation" in error_msg:
                print(f"   ⚠️  JSON inválido (intento {attempt}/{MAX_RETRIES}).")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_S)
                    continue

            print(f"   ⚠️  Error (intento {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S)
                continue

    raise RuntimeError(
        f"El LLM no produjo un JSON válido tras {MAX_RETRIES} intentos. "
        f"Último error: {last_error}"
    )
