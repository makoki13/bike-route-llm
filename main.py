"""
bike-route-llm — Orquestador principal.
Recibe GPX track, GPX route y CSV cuesheet.
Devuelve resumen estructulado del recorrido.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def main():
    print("🚴 bike-route-llm")
    print(f"   Modelo : {os.getenv('OLLAMA_MODEL')}")
    print(f"   Ollama : {os.getenv('OLLAMA_BASE_URL')}")
    print("   Estado : Proyecto inicializado. Pendiente Fase 2.")


if __name__ == "__main__":
    main()
