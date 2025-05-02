# local_seo_agent.py

import gradio as gr
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import Ollama
import pandas as pd
import os
from serpapi import GoogleSearch
import requests
from urllib.parse import urlencode

# Set up prompt and model
prompt = PromptTemplate.from_template("""
You are a helpful assistant that writes professional and friendly responses to Google reviews.

Business Type: {business_type}
Customer Review: {review}

Write a polite and friendly response below:
""")

llm = Ollama(model="llama3")
chain = LLMChain(llm=llm, prompt=prompt)

# Function to fetch reviews from SerpAPI using data_id
def fetch_reviews_from_google(place_id, limit=10):
    search = GoogleSearch({
        "engine": "google_maps_reviews",
        "data_id": place_id,
        "api_key": os.environ.get("SERPAPI_API_KEY")
    })
    result = search.get_dict()
    reviews = [r["text"] for r in result.get("reviews", [])[:limit] if "text" in r and r["text"].strip()]
    return pd.DataFrame({"review": reviews})

# Lookup function
def lookup_place_id(business_name, location):
    search = GoogleSearch({
        "engine": "google_maps",
        "q": business_name,
        "location": location,
        "type": "search",
        "gl": "us",
        "hl": "en",
        "no_cache": True,
        "api_key": os.environ.get("SERPAPI_API_KEY")
    })
    results = search.get_dict()

    if "error" in results:
        return f"❌ SerpAPI error: {results['error']}"

    local_results = results.get("local_results")
    if not local_results or not isinstance(local_results, list):
        return f"❌ No business found in 'local_results'."

    top = local_results[0]
    return f"{top.get('title')} — data_id: {top.get('data_id')}"

# Google My Business API integration
def post_review_reply(account_id, location_id, review_id, access_token, comment):
    url = f"https://mybusiness.googleapis.com/v4/accounts/{account_id}/locations/{location_id}/reviews/{review_id}/reply"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"comment": comment}
    response = requests.put(url, json=payload, headers=headers)
    return response.status_code, response.json()

# OAuth URL generator
def get_google_oauth_url():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = "http://localhost:7860/oauth_callback"
    scope = "https://www.googleapis.com/auth/business.manage"
    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent"
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

# Async generator with progress
def generate_responses_with_progress(file, business_type, place_id):
    import time
    if place_id:
        df = fetch_reviews_from_google(place_id)
    elif file:
        df = pd.read_csv(file.name)
    else:
        yield None, "❌ No file or Place ID provided."
        return

    if df.empty or 'review' not in df.columns:
        df = pd.DataFrame({
            "review": [
                "Great food, loved the service!",
                "The place was nice but very crowded.",
                "Excellent experience overall!"
            ]
        })

    df = df.dropna(subset=['review'])
    df['review'] = df['review'].astype(str).str.strip()

    responses = []
    total = len(df['review'])

    for i, review in enumerate(df['review']):
        if not review:
            responses.append("⚠️ No review text.")
        else:
            try:
                response = chain.run({"review": review, "business_type": business_type})
                responses.append(response)
            except Exception:
                responses.append("⚠️ Error generating response.")

        yield None, f"🟢 {i+1}/{total} reviews processed..."
        time.sleep(0.1)

    df['ai_response'] = responses
    output_path = "review_responses.csv"
    df.to_csv(output_path, index=False)

    yield output_path, "✅ Done generating responses."

# Gradio UI with post to Google API (manual ID entry)
def main_interface():
    with gr.Blocks() as demo:
        gr.Markdown("## 🧠 Local SEO Review Response Generator")

        with gr.Tab("Generate Responses"):
            file = gr.File(label="Upload CSV with 'review' column (optional)")
            business_type = gr.Textbox(label="Business Type (e.g. coffee shop, dentist)")
            place_id = gr.Textbox(label="Google Place ID (optional – overrides CSV)")
            generate_btn = gr.Button("⚡ Generate AI Responses")
            output = gr.File(label="📥 Download CSV with AI Responses")
            status = gr.Textbox(label="Status", interactive=False)

            generate_btn.click(
                fn=generate_responses_with_progress,
                inputs=[file, business_type, place_id],
                outputs=[output, status],
                show_progress=True,
                api_name="generate_responses_with_progress"
            )

        with gr.Tab("🔍 Lookup Google Place ID"):
            name_input = gr.Textbox(label="Business Name")
            location_input = gr.Textbox(label="Location (e.g., Decatur, Georgia, USA)")
            lookup_btn = gr.Button("Find Place ID")
            place_result = gr.Textbox(label="Result")

            lookup_btn.click(
                lookup_place_id,
                inputs=[name_input, location_input],
                outputs=place_result
            )

        with gr.Tab("Post Response to Google"):
            gr.Markdown("### Post AI Response to Google Review")
            acc = gr.Textbox(label="Google Account ID")
            loc = gr.Textbox(label="Location ID")
            rev = gr.Textbox(label="Review ID")
            token = gr.Textbox(label="Access Token", type="password")
            reply = gr.Textbox(label="Response Text")
            submit = gr.Button("📤 Post to Google")
            result = gr.Textbox(label="Post Result")

            def wrapped_post(acc, loc, rev, token, reply):
                status, response = post_review_reply(acc, loc, rev, token, reply)
                return f"Status: {status}\n{response}"

            submit.click(wrapped_post, inputs=[acc, loc, rev, token, reply], outputs=result)

        with gr.Tab("🔐 Google OAuth Login"):
            gr.Markdown("### Connect your Google Account to manage reviews")
            login_btn = gr.Button("🔗 Sign in with Google")
            auth_url = gr.Textbox(label="Google OAuth URL")
            login_btn.click(fn=get_google_oauth_url, inputs=[], outputs=auth_url)

    demo.launch()

if __name__ == "__main__":
    main_interface()
