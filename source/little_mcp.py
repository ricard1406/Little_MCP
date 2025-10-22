"""
Little MCP Agent is a simple yet powerful local AI assistant that runs entirely on your machine.
Built for learning and experimentation, it combines the power of open-source LLMs with advanced
retrieval-augmented generation (RAG) to create an intelligent chatbot that can work with your
personal documents and provide real-time information.
"""
VERSION="0.1.01"

import requests
import json
import warnings
import os
from typing import Type

# --- Pydantic and LangChain Imports ---
from pydantic import BaseModel, Field
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory

# --- LangChain Community Imports for RAG ---
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# --- LangChain Core Imports for RAG Chain ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter

warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- Constants ---
# The address of your running MCP server
SERVER_URL = "http://127.0.0.1:8000"
# Define the path to your PDF document
PDF_DOCUMENT_PATH = "./data/Candidates and Scores List - Test Data - compact.pdf"  # <--- IMPORTANT: CHANGE THIS TO YOUR PDF's FILENAME
CHROMA_DB_PATH = "chroma_db_rag"
# set here your LLM
LLM = "qwen3:1.7b"

# =================================================================
# RAG SYSTEM AND TOOL
# =================================================================

class RAGSystem:
    def __init__(self, pdf_path: str, persist_directory: str):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The specified PDF file was not found at: {pdf_path}")

        self.pdf_path = pdf_path
        self.persist_directory = persist_directory
        # Ollama embeddings generate vector representations
        self.embedding_function = OllamaEmbeddings(model="nomic-embed-text")
        self.vector_store = self._prepare_vector_store()
        self.rag_chain = self._build_rag_chain()

    # Chroma vector database store and query vector embeddings
    def _prepare_vector_store(self):
        if os.path.exists(self.persist_directory):
            print(f"Loading existing vector store from '{self.persist_directory}'...")
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function
            )
        else:
            print(f"Creating new vector store from '{self.pdf_path}'...")
            # Load PDF document based on LangChain's PyPDFLoader
            loader = PyPDFLoader(self.pdf_path)
            documents = loader.load()
            # Document splitting into smaller, manageable chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embedding_function,
                persist_directory=self.persist_directory
            )
            print("Vector store created successfully.")
            return vectorstore

    # The RAG (Retrieval-Augmented Generation) chain is a process that combines the capabilities of large language models (LLMs)
    # with external knowledge sources to generate more accurate and contextually relevant responses.
    def _build_rag_chain(self):
        retriever = self.vector_store.as_retriever(search_kwargs={'k': 3})
        llm = ChatOllama(model=LLM, temperature=0.1)

        template = """
        You are an assistant for question-answering tasks.
        Answer the question based ONLY on the following context.
        If you don't know the answer from the context, just say that you don't know.

        Context: {context}
        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)

        chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
        )
        return chain

    def query(self, question: str) -> str:
        """Queries the RAG chain and returns the answer."""
        print(f"\n[RAG System] Querying with: '{question}'")
        return self.rag_chain.invoke(question)


class RAGToolInput(BaseModel):
    query: str = Field(description="The specific question to ask the document retrieval system.")


class RAGTool(BaseTool):
    # A tool to query a local document for specific information.
    ### IMPORTANT: REPLACE WITH YOUR PDF's TOPIC
    name: str = "document_qa_system"
    description: str = (
        "Use this tool ONLY when you need to answer questions about the contents of the local PDF document. "
        "The document contains information about candidate. " ### IMPORTANT: REPLACE 'candidate' WITH YOUR PDF's TOPIC
        "Input should be the user's full and specific question."
    )
    args_schema: Type[BaseModel] = RAGToolInput
    rag_system: RAGSystem

    # This allows Pydantic to handle a custom class like RAGSystem
    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        """Execute the RAG query."""
        return self.rag_system.query(query)


# =================================================================
# FastMCPTool
# =================================================================

class FastMCPTool(BaseTool):
    """A LangChain tool that calls the MCP server API."""
    name: str = Field()
    description: str = Field()
    function_name: str = Field()

    def _run(self, query: str) -> str:
        """Execute the tool by making an HTTP GET request to the MCP server."""
        try:
            endpoint_url = f"{SERVER_URL}/{self.function_name}"
            params = {'myParam': query.strip()}
            response = requests.get(endpoint_url, params=params)
            response.raise_for_status()
            return json.dumps(response.json())
        except requests.exceptions.RequestException as e:
            return f"Network error calling function {self.function_name}: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"


# =================================================================
# ### --- MODIFIED: Main Client Application --- ###
# =================================================================

class FastMCPLangChainClient:
    def __init__(self, pdf_path: str, ollama_model: str = "qwen3:1.7b"):
        self.ollama_model = ollama_model
        self.agent_executor = None
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        # ### --- NEW: Initialize the RAG system upon client creation --- ###
        print("Initializing RAG System...")
        self.rag_system = RAGSystem(pdf_path=pdf_path, persist_directory=CHROMA_DB_PATH)
        print("RAG System ready. ")

    def initialize(self):
        """Initialize the LangChain agent with both MCP tools and the new RAG tool."""
        # --- Existing MCP tools ---
        mcp_tools_config = [
            # list of existing tools
            {
                "name": "get_datetime",
                "description": "Use this tool to find the current date and time for any city. Input should be the city name, like 'Paris' or 'Tokyo, Japan'.",
                "function_name": "get_datetime"
            },
            {
                "name": "get_weather",
                "description": "Use this tool to get the current weather for a city. Input should be the city name, like 'London, UK'.",
                "function_name": "get_weather"
            },
            {
                "name": "get_calc",
                "description": "Use this tool to get the result of arithmetic operations. Input should be OPERATION, NUM-ONE, NUM-TWO.",
                "function_name": "get_calc"
            }
        ]
        langchain_tools = [FastMCPTool(**config) for config in mcp_tools_config]

        # Add the RAG tool to the list of available tools
        rag_tool = RAGTool(rag_system=self.rag_system)
        langchain_tools.append(rag_tool)

        # --- LLM and Agent Initialization
        llm = Ollama(model=self.ollama_model, temperature=0.1)

        system_prompt_prefix = """You are a helpful and knowledgeable assistant. Your goal is to provide the most accurate and relevant response.
Instructions:
1. Analyze the user's request.
2. Check your available tools. You have tools for general tasks (weather, time, math) and a special tool for answering questions from a specific document.
3. If a tool is appropriate, you MUST use it.
4. If NO tool is suitable, answer using your own general knowledge.
5. When answering from general knowledge, NEVER mention the tools.

You have access to the following tools:"""

        agent_kwargs = {"prefix": system_prompt_prefix}

        self.agent_executor = initialize_agent(
            langchain_tools,
            llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            agent_kwargs=agent_kwargs,
        )
        print("\nFastMCP LangChain Client initialized successfully!")
        print("Tools available: ", [tool.name for tool in langchain_tools])

    def chat(self, message: str) -> str:
        """Send a message to the agent and get a response."""
        if not self.agent_executor:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        try:
            response = self.agent_executor.invoke({"input": message})
            return response.get("output", "No output found.")
        except Exception as e:
            return f"Error processing message: {str(e)}"


def main():
    # Pass the PDF path to the client
    if not os.path.exists(PDF_DOCUMENT_PATH):
        print(f"Error: PDF file not found at '{PDF_DOCUMENT_PATH}'.")
        print("Please update the 'PDF_DOCUMENT_PATH' variable in the script.")
        return

    client = FastMCPLangChainClient(pdf_path=PDF_DOCUMENT_PATH, ollama_model="qwen3:1.7b")
    try:
        client.initialize()
        print("\n烙 Your Assistant is Ready!")
        print("You can now ask general questions, ask for the weather, or ask about your PDF document.")
        print("Type 'quit' to exit.\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            if not user_input:
                continue

            print("\nAssistant: ", end="", flush=True)
            response = client.chat(user_input)
            print(response)
            print("-" * 50)
    except Exception as e:
        print(f"An unexpected error occurred during execution: {e}")


if __name__ == "__main__":
    main()
