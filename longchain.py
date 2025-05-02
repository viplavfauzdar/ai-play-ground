from langchain.llms import Ollama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Set up the Ollama LLM interface
llm = Ollama(model="mistral")  # change to llama2, phi, etc.

# Memory to preserve conversation context
memory = ConversationBufferMemory()

# Build a basic chat assistant
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# Chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() in {"exit", "quit"}:
        break
    response = conversation.run(user_input)
    print("AI:", response)