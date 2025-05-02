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
import threading
from flask import Flask, request

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
    reviews = [
        {
            "review_id": r.get("review_id"),
            "review": r.get("text")
        }
        for r in result.get("reviews", [])[:limit] if "text" in r and r["text"].strip()
    ]
    return pd.DataFrame(reviews)

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

def post_bulk_responses(account_id, location_id, access_token, file):
    df = pd.read_csv(file.name)
    results = []
    for _, row in df.iterrows():
        if pd.isna(row.get("ai_response")) or pd.isna(row.get("review_id")):
            continue
        status, resp = post_review_reply(
            account_id=account_id,
            location_id=location_id,
            review_id=row["review_id"],
            access_token=access_token,
            comment=row["ai_response"]
        )
        results.append({"review_id": row["review_id"], "status": status, "response": resp})

    result_df = pd.DataFrame(results)
    output_path = "bulk_post_results.csv"
    result_df.to_csv(output_path, index=False)
    return result_df, output_path

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

# Flask server for OAuth callback
oauth_app = Flask(__name__)

@oauth_app.route("/oauth_callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "❌ No code received from Google."

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": "http://localhost:7860/oauth_callback",
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return f"❌ Error fetching token: {response.text}"

    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    return f"""
    ✅ Access Token:<br><code>{access_token}</code><br><br>
    🔁 Refresh Token:<br><code>{refresh_token}</code><br><br>
    Paste the access token into the Gradio UI to post your review response.
    """

def start_oauth_server():
    oauth_app.run(port=7860)

# Gradio UI
def main_interface():
    threading.Thread(target=start_oauth_server, daemon=True).start()

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

        with gr.Tab("📤 Bulk Post Responses"):
            gr.Markdown("### Upload CSV to Post Multiple Review Responses")
            bulk_file = gr.File(label="CSV with review_id and ai_response columns")
            bulk_acc = gr.Textbox(label="Google Account ID")
            bulk_loc = gr.Textbox(label="Location ID")
            bulk_token = gr.Textbox(label="Access Token", type="password")
            bulk_btn = gr.Button("🚀 Post All Responses")
            bulk_result_df = gr.Dataframe(label="Post Status")
            bulk_result_file = gr.File(label="Download Log CSV")

            bulk_btn.click(
                fn=post_bulk_responses,
                inputs=[bulk_acc, bulk_loc, bulk_token, bulk_file],
                outputs=[bulk_result_df, bulk_result_file]
            )

        with gr.Tab("🔐 Google OAuth Login"):
            gr.Markdown("### Connect your Google Account to manage reviews")
            login_btn = gr.Button("🔗 Sign in with Google")
            auth_url = gr.Textbox(label="Google OAuth URL")
            login_btn.click(fn=get_google_oauth_url, inputs=[], outputs=auth_url)

    demo.launch()

if __name__ == "__main__":
    main_interface()
