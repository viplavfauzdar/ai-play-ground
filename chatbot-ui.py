import gradio as gr
from langchain.llms import Ollama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Initialize LangChain LLM and memory
llm = Ollama(model="mistral")
memory = ConversationBufferMemory(return_messages=True)
conversation = ConversationChain(llm=llm, memory=memory)

# Chat handler
import pyttsx3

engine = pyttsx3.init()

def chat(user_input, history):
    response = conversation.run(user_input)
    history.append((user_input, response))
    
    # Speak the assistant's reply
    engine.say(response)
    engine.runAndWait()
    
    return "", history

# Reset history
def clear_chat():
    memory.clear()
    return []

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 Personal AI Assistant")
    
    chatbot = gr.Chatbot(label="Chat History")

    with gr.Row():
        txt = gr.Textbox(placeholder="Type or click mic...", show_label=False, scale=6)
        mic = gr.Audio(sources="microphone", type="filepath", label="🎤", scale=2)
        send_btn = gr.Button("Send", scale=2)

    clear_btn = gr.Button("Clear Chat")

    send_btn.click(chat, inputs=[txt, chatbot], outputs=[txt, chatbot])
    txt.submit(chat, inputs=[txt, chatbot], outputs=[txt, chatbot])

    def handle_input(text_input, audio_input, history):
        if audio_input:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_input) as source:
                audio = recognizer.record(source)
                try:
                    text_input = recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    return "", history + [("🤖", "Sorry, I couldn't understand your voice.")]
        return chat(text_input, history)

    send_btn.click(handle_input, inputs=[txt, mic, chatbot], outputs=[txt, chatbot])
    txt.submit(handle_input, inputs=[txt, mic, chatbot], outputs=[txt, chatbot])
    
    clear_btn.click(clear_chat, outputs=[chatbot])

demo.launch(server_name="0.0.0.0", server_port=7860)