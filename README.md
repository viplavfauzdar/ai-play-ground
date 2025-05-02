# 🧠 Local AI Personal Assistant with Ollama + LangChain + Gradio

This project is a simple yet powerful AI assistant that runs entirely **locally** using open-source models (like **Mistral**, **LLaMA2**, etc.) via [Ollama](https://ollama.com), orchestrated with [LangChain](https://www.langchain.com/), and accessible via a clean [Gradio](https://gradio.app/) web interface.

## 🚀 Features

- ✅ Runs open-source LLMs locally (no API key needed)
- ✅ Supports multiple models including:
  - Mistral (default)
  - LLaMA2
  - Phi
  - Gemma
  - And other Ollama-supported models
- ✅ Clean and intuitive Gradio web interface
- ✅ Persistent conversation memory using LangChain
- ✅ 100% private — all processing happens locally
- ✅ Multiple interface options:
  - Web UI (via Gradio)
  - Command-line interface

## 📦 Requirements

- Python 3.8+
- [Ollama](https://ollama.com) installed and running
- Python packages:
  - `langchain`
  - `gradio`
  - `requests`

## 🔧 Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ai-play-ground.git
cd ai-play-ground
```

### 2. Install dependencies

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install langchain gradio requests

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

### 3. Download a model

```bash
# Download the default Mistral model
ollama pull mistral
```

## 💡 Usage

### Web Interface

1. Start the Gradio web interface:
```bash
python gradio_ui.py
```
2. Open your browser and navigate to `http://localhost:7860`
3. Start chatting with your local AI assistant!

### Command Line Interface

For a simple command-line experience:
```bash
python longchain.py
```

## 🔄 Switching Models

You can easily switch between different models by modifying the model name in either `gradio_ui.py` or `longchain.py`:

```python
llm = Ollama(model="mistral")  # Change to "llama2", "phi", etc.
```

## 🛠️ Project Structure

- `gradio_ui.py` - Web interface implementation using Gradio
- `longchain.py` - Command-line interface and core LangChain implementation
- `mistral.py` - Additional Mistral-specific configurations

## 🔒 Privacy

All processing happens locally on your machine. No data is sent to external servers, making this perfect for privacy-conscious users or working with sensitive information.

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## 📝 License

This project is open source and available under the MIT License.

