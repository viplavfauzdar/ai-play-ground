import os
import shutil
import gradio as gr
from rag_chain import create_rag_chain

DOCS_DIR = "docs"

# Ensure clean docs folder on file upload
def upload_and_reload(files):
    os.makedirs(DOCS_DIR, exist_ok=True)

    for file in files:
        filename = os.path.basename(file.name)
        dest_path = os.path.join(DOCS_DIR, filename)

        # Only use samefile check if destination file exists
        if os.path.exists(dest_path):
            try:
                if os.path.samefile(file.name, dest_path):
                    continue  # same file, skip copying
            except Exception:
                pass  # fallback: continue to copy below if comparison fails

        shutil.copy(file.name, dest_path)

    global rag_chain
    rag_chain = create_rag_chain()
    return "Documents indexed. You can now ask questions!"

# Handle user queries
def chat(query):
    return rag_chain.run(query)

# Initialize chain
rag_chain = create_rag_chain()

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# 🧠 AI Assistant with RAG")
    with gr.Row():
        file_upload = gr.File(file_types=[".pdf", ".txt"], file_count="multiple")
        upload_btn = gr.Button("Upload & Index")
    status = gr.Textbox(label="Status")
    upload_btn.click(fn=upload_and_reload, inputs=[file_upload], outputs=[status])

    gr.Markdown("### Ask about your uploaded documents:")
    with gr.Row():
        query = gr.Textbox(lines=2, placeholder="e.g., What is section 2 about...", show_label=False)
    send_btn = gr.Button("Send")

    answer = gr.Textbox(label="Assistant Response", interactive=False)

    # When user clicks "Send" button or hits Enter in textbox
    send_btn.click(fn=chat, inputs=query, outputs=answer)
    query.submit(fn=chat, inputs=query, outputs=answer)

demo.launch()