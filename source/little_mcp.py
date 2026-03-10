"""
Little MCP Agent is a simple yet powerful local AI assistant that runs entirely on your machine.
Built for learning and experimentation, it combines the power of open-source LLMs with advanced
retrieval-augmented generation (RAG) to create an intelligent chatbot that can work with your
personal documents and provide real-time information.

Now supports dual provider mode:
  - Local Ollama LLM  (default, no API key needed)
  - Anthropic Claude  (requires --api-key)
"""
VERSION = "0.5.1 dual-provider - text/ graph option"


import requests
import json
import warnings
import os
import sys
import argparse
from typing import Type
from dotenv import load_dotenv

# --- Pydantic ---
from pydantic import BaseModel, Field

# --- LangChain Core & Agent Imports ---
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- LangGraph for Agent ---
from langgraph.prebuilt import create_react_agent

# --- LangChain Community Imports (Loaders & Stores) ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma

# --- Specific Integration Packages ---
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import gradio as gr
import datetime  

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()

# =================================================================
# CONSTANTS
# =================================================================

SERVER_URL = "http://127.0.0.1:8000"
PDF_DOCUMENT_PATH = "./data/Candidates and Scores List - Test Data - compact.pdf"
CHROMA_DB_PATH = "chroma_db_rag"

# Default models
DEFAULT_OLLAMA_MODEL   = "qwen3:4b"
DEFAULT_CLAUDE_MODEL   = "claude-sonnet-4-5"   # great balance of speed & quality


# =================================================================
# LLM FACTORY  
# =================================================================

def get_llm(provider: str, api_key: str = None, model: str = None, temperature: float = 0.1):
    """
    Return a LangChain chat model based on the chosen provider.

    Providers
    ---------
    "ollama"    — local Ollama (no key needed)
    "anthropic" — Anthropic Claude (requires api_key)
    """
    if provider == "anthropic":
        if not api_key:
            raise ValueError(
                "An Anthropic API key is required when using provider='anthropic'.\n"
                "Pass it with --api-key sk-ant-..."
            )
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is not installed.\n"
                "Run:  pip install langchain-anthropic"
            )
        resolved_model = model or DEFAULT_CLAUDE_MODEL
        print(f"[LLM Factory] Using Anthropic Claude — model: {resolved_model}")
        return ChatAnthropic(
            model=resolved_model,
            temperature=temperature,
            api_key=api_key
        )

    else:  # default: ollama
        resolved_model = model or DEFAULT_OLLAMA_MODEL
        print(f"[LLM Factory] Using local Ollama — model: {resolved_model}")
        return ChatOllama(model=resolved_model, temperature=temperature)


# =================================================================
# RAG SYSTEM AND TOOL
# =================================================================

class RAGSystem:
    def __init__(self, pdf_path: str, persist_directory: str, llm):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        self.pdf_path = pdf_path
        self.persist_directory = persist_directory
        self.llm = llm                                      # ← injected, not hardcoded
        self.embedding_function = OllamaEmbeddings(model="nomic-embed-text")
        self.vector_store = self._prepare_vector_store()
        self.rag_chain = self._build_rag_chain()

    def _prepare_vector_store(self):
        if os.path.exists(self.persist_directory):
            print(f"Loading existing vector store from '{self.persist_directory}'...")
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function
            )
        else:
            print(f"Creating new vector store from '{self.pdf_path}'...")
            loader = PyPDFLoader(self.pdf_path)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embedding_function,
                persist_directory=self.persist_directory
            )
            print("Vector store created successfully.")
            return vectorstore

    def _build_rag_chain(self):
        retriever = self.vector_store.as_retriever(search_kwargs={'k': 3})

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
            | self.llm                                      # ← uses injected LLM
            | StrOutputParser()
        )
        return chain

    def query(self, question: str) -> str:
        print(f"\n[RAG System] Querying with: '{question}'")
        return self.rag_chain.invoke(question)


class RAGToolInput(BaseModel):
    query: str = Field(description="The specific question to ask the document retrieval system.")


class RAGTool(BaseTool):
    name: str = "document_qa_system"
    description: str = (
        "Use this tool ONLY when you need to answer questions about the contents of the local document."
    )
    args_schema: Type[BaseModel] = RAGToolInput
    rag_system: RAGSystem

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
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
# Main Client Application
# =================================================================

class FastMCPLangChainClient:
    def __init__(
        self,
        pdf_path: str,
        provider: str = "ollama",
        api_key: str = None,
        model: str = None,
        show_thinking: bool = False,
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.show_thinking = show_thinking
        self.agent_executor = None
        self.chat_history = []

        # Build one shared LLM instance for both RAG and the agent
        self.llm = get_llm(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=0.1
        )

        print(f"\nInitializing RAG System (Thinking Mode: {'ON' if show_thinking else 'OFF'})...")
        self.rag_system = RAGSystem(
            pdf_path=pdf_path,
            persist_directory=CHROMA_DB_PATH,
            llm=self.llm                                    # ← share the same LLM
        )
        print("RAG System ready.")

    def initialize(self):
        """Initialize the LangChain agent with MCP tools + RAG tool."""
        mcp_tools_config = [
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
            },
            {
                "name": "get_SQL_response",
                "description": """Returns the result of SQL statement formatted as String.
    Use this tool whenever the user asks for data from his warehouse.
    Format the required data as SQL statement.
    Allowed tables : FRUITS ; VEGGIE
    Allowed items : ITEM, QUANTITY
    Examples:
    SELECT ITEM, QUANTITY FROM FRUITS
    SELECT ITEM, QUANTITY FROM VEGGIE""",
                "function_name": "get_SQL_response"
            },
            {
                "name": "put_SQL_insert",
                "description": """Update some SQL table.
    Use this tool whenever the user asks to update some data in his warehouse.
    Format the required update as SQL statement.
    Allowed tables : FRUITS ; VEGGIE
    Allowed items : QUANTITY
    Example:
    UPDATE FRUITS SET QUANTITY=4 WHERE ITEM='ORANGE';""",
                "function_name": "put_SQL_insert"
            }
        ]

        langchain_tools = [FastMCPTool(**config) for config in mcp_tools_config]
        langchain_tools.append(RAGTool(rag_system=self.rag_system))

        # Agent uses the same shared LLM
        self.agent_executor = create_react_agent(self.llm, langchain_tools)

        print("\nFastMCP LangChain Client initialized successfully!")
        print("Tools available:", [tool.name for tool in langchain_tools])

    def chat(self, message: str) -> str:
        if not self.agent_executor:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        try:
            messages = list(self.chat_history)
            messages.append({"role": "user", "content": message})

            final_response = ""

            # --- THINKING MODE (stream) ---
            if self.show_thinking:
                print("\n" + "─" * 30 + " 易 THINKING PROCESS " + "─" * 30)

                for event in self.agent_executor.stream({"messages": messages}, stream_mode="values"):
                    current_message = event["messages"][-1]

                    if hasattr(current_message, 'tool_calls') and current_message.tool_calls:
                        for tool in current_message.tool_calls:
                            print(f"\n Thought: I need to use tool '{tool['name']}'")
                            print(f"   Args: {tool['args']}")

                    elif current_message.type == 'tool':
                        preview = current_message.content[:200] + "..." if len(current_message.content) > 200 else current_message.content
                        print(f"\n Observation ({current_message.name}):")
                        print(f"   {preview}")

                    elif current_message.type == 'ai' and not current_message.tool_calls:
                        final_response = current_message.content

                print("─" * 80 + "\n")

            # --- SILENT MODE (invoke) ---
            else:
                result = self.agent_executor.invoke({"messages": messages})
                final_response = result["messages"][-1].content

            # Update history
            self.chat_history.append({"role": "user", "content": message})
            self.chat_history.append({"role": "assistant", "content": final_response})

            return final_response

        except Exception as e:
            return f"Error processing message: {str(e)}"


# =================================================================
# CLI Entry Point
# =================================================================

def parse_args():
    
    parser = argparse.ArgumentParser(
        description="Little MCP Agent — dual provider (Ollama / Claude)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "mode",
        choices=["graph", "text"],
        help="Interface mode:\n  graph — Gradio web UI\n  text  — terminal chat"
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "anthropic"],
        default="ollama",
        help=(
            "LLM provider to use:\n"
            "  ollama    — local Ollama model (default, no key needed)\n"
            "  anthropic — Anthropic Claude   (requires --api-key)\n"
        )
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for the chosen provider (or set ANTHROPIC_API_KEY env var)."
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            f"Model name override.\n"
            f"  Ollama default    : {DEFAULT_OLLAMA_MODEL}\n"
            f"  Anthropic default : {DEFAULT_CLAUDE_MODEL}\n"
        )
    )
    parser.add_argument(
        "--think",
        action="store_true",
        default=False,
        help="Show the agent's thinking / tool-use process (streaming mode)."
    )

    return parser.parse_args()

def clean_agent_response(agent_output_string):
    if "</think>" in agent_output_string:
        clean_output = agent_output_string.split("</think>", 1)[1]
    else:
        clean_output = agent_output_string
    return clean_output.strip()

def main():
    args = parse_args()

    if not os.path.exists(PDF_DOCUMENT_PATH):
        print(f"Error: PDF file not found at '{PDF_DOCUMENT_PATH}'.")
        return

    # API key can also come from environment variable
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")

    # Resolve display model name for the banner
    if args.provider == "anthropic":
        display_model = args.model or DEFAULT_CLAUDE_MODEL
    else:
        display_model = args.model or DEFAULT_OLLAMA_MODEL

    client = FastMCPLangChainClient(
        pdf_path=PDF_DOCUMENT_PATH,
        provider=args.provider,
        api_key=api_key,
        model=args.model,
        show_thinking=args.think,
    )

    try:
        client.initialize()

        print(f"\n{'=' * 55}")
        print(f"  Little MCP Agent  —  v{VERSION}")
        print(f"  Provider : {args.provider.upper()}")
        print(f"  Model    : {display_model}")
        print(f"  Mode     : {'易 THINKING' if args.think else '狼 SILENT'}")
        print(f"{'=' * 55}")
        print("Example questions:")
        print("  What's the weather and time in Sydney now?")
        print("  Is Dianne in our local list of Candidates?")
        print("  Do we have orange in our warehouse?")
        print("Type 'quit' to exit.\n")
        print(" Your Assistant is Ready!\n")

        if args.mode == "graph":
            # callback 
            def chat_with_agent(message, history):
                try:
                    response = client.chat(message)
                    return clean_agent_response(response)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    return "Sorry, I encountered an error while processing your request."

            demo = gr.ChatInterface(
                fn=chat_with_agent,
                title="Little MCP Agent",
                description="Chat with your AI agent. Supports weather, datetime, arithmetic, SQL warehouse queries, and local document search.",
                examples=[
                "What is the current date and time?",
                "What is the weather in London, UK?",
                "Calculate 15 * 3 + 7",
                "Check if you find Dianne Bridgewater in our List of Candidates; if you find her write a document for her convocation in our main office, check the weather in her address if it's good the convocation date is in two days from current date, otherwise the convocation date is Monday of next week from current date",
                "Do we have orange in our warehouse?",
                "Please increase by 2 apples quantity in our warehouse"
                ],
                textbox=gr.Textbox(placeholder="Ask your agent a question...", scale=7),
            )
            demo.launch(share=False, debug=True)

        elif args.mode == "text":
            print("Type your question and press Enter. Type 'quit' or 'exit' to end.")
            print("-" * 50)
            while True:
                try:
                    user_input = input("You: ").strip()
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("Goodbye!")
                        break
                    if not user_input:
                        continue
                    print("\nAssistant: ", end="", flush=True)
                    response = client.chat(user_input)
                    print(clean_agent_response(response))
                    print("-" * 50)
                except (KeyboardInterrupt, EOFError):
                    print("\n\nExiting chat. Goodbye!")
                    break
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
