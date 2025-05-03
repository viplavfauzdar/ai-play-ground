import requests

host = "http://localhost:11434"  # ← your actual remote IP or localhost
prompt = "Say hello in a friendly tone."

r = requests.post(f"{host}/api/generate", json={
    "model": "mistral",
    "prompt": prompt
}, timeout=20)

print(r)