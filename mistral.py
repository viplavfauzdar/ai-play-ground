import requests
import json

response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "mistral", "prompt": "Tell me a joke"},
    stream=True
)

output = ""
for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8'))
        output += data.get("response", "")

print(output.strip())