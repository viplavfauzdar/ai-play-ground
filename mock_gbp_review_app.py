from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import requests
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ollama_host = "http://127.0.0.1:8080"
llm = Ollama(model="tinyllama:latest", base_url=ollama_host)

prompt = PromptTemplate.from_template("""
Business Type: {business_type}
Customer Review: {review}
Write a friendly and professional response:
""")

chain = LLMChain(llm=llm, prompt=prompt)

@app.get("/api/ollama-status")
def check_ollama_status():
    try:
        r = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if r.status_code == 200:
            return {"status": "ok", "models": r.json()}
        else:
            return {"status": "error", "code": r.status_code, "message": r.text}
    except Exception as e:
        return {"status": "unreachable", "message": str(e)}

@app.get("/api/test-prompt")
def test_prompt():
    try:
        response = llm.invoke("Say hi from llama3")
        return {"reply": response}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/test-prompt-chain")
def test_prompt():
    try:
        response = chain.invoke("Say hi from llama3")
        return {"reply": response}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/direct-test")
def direct_ollama_test():
    print(f"▶️ Using Ollama Host: {ollama_host}")
    try:
        r = requests.post(f"{ollama_host}/api/generate", json={
            "model": "llama3:latest",
            "prompt": "Say hi from direct API",
            "stream": False
        }, timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/raw-test")
def raw_socket_test():
    try:
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=30)
        payload = json.dumps({
            "model": "tinyllama",
            "prompt": "Say hi",
            "stream": False
        })
        headers = { "Content-Type": "application/json" }
        conn.request("POST", "/api/generate", body=payload, headers=headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/reviews")
def get_mock_reviews():
    try:
        with open("mock_gbp_reviews.json", "r") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/reply")
def post_mock_reply(review_id: str = Body(...), review: str = Body(...), business_type: str = Body("restaurant")):
    print(f"🧠 Generating response for review {review_id}")
    try:
        response = chain.invoke({
            "review": review,
            "business_type": business_type
        })
        print(f"✅ AI Response: {response}")
        return {
            "status": "success",
            "reviewId": review_id,
            "reply": response,
            "updateTime": "2024-12-02T15:47:00Z"
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "message": str(e)}