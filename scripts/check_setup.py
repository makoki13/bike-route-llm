"""
scripts/check_setup.py
Diagnóstico completo del entorno antes de ejecutar el pipeline.

Uso:
    python scripts/check_setup.py
"""

from __future__ import annotations

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


def check_python() -> bool:
    v = sys.version_info
    ok = v >= (3, 10)
    simbolo = "✅" if ok else "❌"
    estado = "(OK)" if ok else "(necesario >= 3.10)"
    print(f"  {simbolo} Python {v.major}.{v.minor}.{v.micro} {estado}")
    return ok


def check_env() -> bool:
    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")
    api_key = os.getenv("GROQ_API_KEY")

    ok_url = base_url is not None and len(base_url) > 0
    ok_model = model is not None and len(model) > 0
    ok_key = api_key is not None and api_key.startswith("gsk_")

    print(f"  {'✅' if ok_url else '❌'} OLLAMA_BASE_URL: {base_url}")
    print(f"  {'✅' if ok_model else '❌'} OLLAMA_MODEL: {model}")

    if ok_key and api_key is not None:
        print(f"  ✅ GROQ_API_KEY: {api_key[:12]}...")
    else:
        print("  ❌ GROQ_API_KEY: no definida o inválida")

    return ok_url and ok_model and ok_key


def check_api_connectivity() -> bool:
    base_url = os.getenv("OLLAMA_BASE_URL", "")
    api_key = os.getenv("GROQ_API_KEY", "")

    if not base_url or not api_key:
        print("  ❌ No se puede verificar (faltan variables en .env)")
        return False

    try:
        r = requests.get(
            f"{base_url}/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if r.status_code == 200:
            models = [m["id"] for m in r.json().get("data", [])]
            model_env = os.getenv("OLLAMA_MODEL", "")
            found = model_env in models
            simbolo = "✅" if found else "❌"
            estado = "encontrado" if found else "NO encontrado"
            print(f"  {simbolo} API accesible. Modelo '{model_env}': {estado}")
            if not found:
                qwen_models = [m for m in models if "qwen" in m.lower()]
                print(f"     Modelos Qwen disponibles: {qwen_models}")
            return found
        else:
            print(f"  ❌ API responde con código {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ❌ No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_data_files() -> bool:
    input_dir = os.getenv("DATA_INPUT_DIR", "./data/input")
    files = ["ruta_track.gpx", "ruta_route.gpx", "ruta_cuesheet.csv"]
    all_ok = True
    for f in files:
        path = os.path.join(input_dir, f)
        exists = os.path.isfile(path)
        print(f"  {'✅' if exists else '❌'} {path}")
        if not exists:
            all_ok = False
    return all_ok


def check_dependencies() -> bool:
    modules = [
        "gpxpy", "pandas", "numpy", "scipy", "geopy",
        "instructor", "pydantic", "openai", "requests",
        "dotenv",
    ]
    all_ok = True
    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
        except ImportError:
            print(f"  ❌ {mod} NO instalado")
            all_ok = False
    return all_ok


def check_output_dir() -> bool:
    output_dir = os.getenv("DATA_OUTPUT_DIR", "./data/output")
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"  ✅ {output_dir} (creado)")
    else:
        print(f"  ✅ {output_dir}")
    return True


def main() -> None:
    print("=" * 55)
    print("  🔍 DIAGNÓSTICO bike-route-llm")
    print("=" * 55)

    print("\n[1/6] Python:")
    ok1 = check_python()

    print("\n[2/6] Variables de entorno (.env):")
    ok2 = check_env()

    print("\n[3/6] Conectividad API:")
    ok3 = check_api_connectivity()

    print("\n[4/6] Ficheros de datos:")
    ok4 = check_data_files()

    print("\n[5/6] Dependencias Python:")
    ok5 = check_dependencies()

    print("\n[6/6] Directorio de salida:")
    ok6 = check_output_dir()

    print("\n" + "=" * 55)
    if all([ok1, ok2, ok3, ok4, ok5, ok6]):
        print("  ✅ Todo listo. Ejecuta: python main.py")
    else:
        print("  ❌ Hay problemas. Revisa los puntos ❌ arriba.")
    print("=" * 55)


if __name__ == "__main__":
    main()
