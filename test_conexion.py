import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b-instruct")
URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

print(f"→ Conectando con Ollama ({URL})...")
print(f"→ Modelo: {MODEL}")

try:
    r = requests.post(
        f"{URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente que solo responde en JSON válido."
                },
                {
                    "role": "user",
                    "content": '¿Cuánto es 5 por 5?'
                }
            ],
            "format": "json",
            "stream": False
        },
        timeout=180  # 3 minutos: la primera carga del modelo en RAM es lenta
    )

    if r.status_code == 200:
        content = r.json()["message"]["content"]
        data = json.loads(content)
        print("✅ Respuesta JSON recibida:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error {r.status_code}: {r.text}")

except requests.exceptions.ConnectionError:
    print("❌ No se puede conectar a Ollama.")
    print("   → ¿Está Ollama ejecutándose? Prueba: ollama serve")
    print("   → ¿La URL es correcta? Prueba en el navegador: http://localhost:11434")

except requests.exceptions.Timeout:
    print("❌ Timeout. El modelo puede estar cargándose en RAM por primera vez.")
    print("   → Espera 1-2 minutos y vuelve a ejecutar.")

except Exception as e:
    print(f"❌ Error inesperado: {e}")
