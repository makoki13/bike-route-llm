import os

import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('GROQ_API_KEY')
model = os.getenv('OLLAMA_MODEL')

r = requests.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    },
    json={
        'model': model,
        'messages': [{'role': 'user', 'content': 'Responde solo OK'}],
        'max_tokens': 10,
    },
    timeout=30,
)

print(f'Estado: {r.status_code}')
if r.status_code == 200:
    print(f'Respuesta: {r.json()["choices"][0]["message"]["content"]}')
else:
    print(f'Error: {r.text}')
