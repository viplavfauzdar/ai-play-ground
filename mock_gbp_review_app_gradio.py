# mock_gbp_review_app.py (Gradio version)
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import requests
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import gradio as gr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ollama_host = "http://127.0.0.1:8080"
llm = Ollama(model="tinyllama", base_url=ollama_host)

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
        reply_text = response.get("text") if isinstance(response, dict) else response
        return {
            "status": "success",
            "reviewId": review_id,
            "reply": reply_text,
            "updateTime": "2024-12-02T15:47:00Z"
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "message": str(e)}

# Gradio UI to interact with the API
def gradio_generate_reply(review, business_type):
    try:
        response = chain.invoke({
            "review": review,
            "business_type": business_type
        })
        reply_text = response.get("text") if isinstance(response, dict) else response
        return reply_text
    except Exception as e:
        return f"❌ Error: {e}"

with gr.Blocks(title="AI Review Responder") as demo:
    gr.Markdown("# 🧠 Local Business Review Generator")
    business_type = gr.Textbox(label="Business Type", value="restaurant")
    review = gr.Textbox(label="Customer Review")
    output = gr.Textbox(label="AI Reply", lines=6)
    btn = gr.Button("Generate Reply")
    btn.click(gradio_generate_reply, inputs=[review, business_type], outputs=[output])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
