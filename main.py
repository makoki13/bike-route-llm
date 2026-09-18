import os

from dotenv import load_dotenv

load_dotenv()

def main():
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:14b-instruct")
    url   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    print("🚴 bike-route-llm")
    print(f"   Modelo : {model}")
    print(f"   Ollama : {url}")
    print("   Estado : Proyecto inicializado. Pendiente Fase 2.")

if __name__ == "__main__":
    main()
