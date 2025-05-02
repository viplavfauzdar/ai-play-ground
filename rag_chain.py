import os
from langchain.document_loaders import PyMuPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
import shutil

DB_DIR = "db"
DOCS_DIR = "docs"


def load_documents(doc_folder):
    docs = []
    for filename in os.listdir(doc_folder):
        path = os.path.join(doc_folder, filename)
        if filename.endswith(".pdf"):
            docs.extend(PyMuPDFLoader(path).load())
        elif filename.endswith(".txt"):
            docs.extend(TextLoader(path).load())
    return docs

def create_rag_chain():
    documents = load_documents(DOCS_DIR)
    print(f"Loaded {len(documents)} documents")

    if not documents:
        return "No documents found to index."

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    if not chunks:
        return "No chunks generated from documents."

    embeddings = OllamaEmbeddings(model="mistral")
    try:
        vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory=DB_DIR)
        vectorstore.persist()
    except Exception as e:
        return f"Embedding error: {e}"

    llm = Ollama(model="mistral")
    return RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

def upload_and_reload(files):
    os.makedirs("docs", exist_ok=True)
    for file in files:
        dest = os.path.join("docs", os.path.basename(file.name))
        if os.path.abspath(file.name) != os.path.abspath(dest):
            shutil.copy(file.name, dest)
    global rag_chain
    rag_chain = create_rag_chain()
    return "Documents indexed. You can now ask questions!"