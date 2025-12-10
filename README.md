# Little MCP Agent 🤖

A simple yet powerful local AI assistant that runs entirely on your machine. Built for learning and experimentation, Little MCP combines the power of open-source LLMs with advanced Retrieval-Augmented Generation (RAG) to create an intelligent chatbot that can work with your personal documents and provide real-time information.

## ✨ Features

- **Local LLM Integration**: Powered by Ollama for complete privacy and offline functionality
- **RAG System**: Query and extract information from your PDF documents using vector embeddings
- **MCP Server/Client Architecture**: Demonstrates Model Context Protocol implementation with FastAPI
- **Multi-Tool Agent**: Access to multiple tools including:
  - Document Q&A system (RAG-based)
  - Real-time weather information (OpenWeather API)
  - Current date and time for any city
  - Arithmetic calculations
- **Conversational Memory**: Maintains context throughout your chat session
- **Vector Store Persistence**: Efficiently stores and reuses document embeddings

## 🔧 Requirements

### System Requirements
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running locally
- OpenWeather API key (free tier available at [openweathermap.org](https://openweathermap.org/api))


### Required Ollama Models
Download these models before running the application:
```bash
ollama pull qwen3:1.7b
ollama pull nomic-embed-text
```

## 📦 Installation
   ## see Installation doc.


## 🚀 Usage

### Step 1: Start the MCP Server

In your first terminal:
```bash
python mcp_server.py
```

You should see:
```
Starting MCP Server ...
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start the MCP Client

In a second terminal:
```bash
[activate your env if not jet] : source ../.venv/bin/activate]
python little_mcp.py
```

### Step 3: Start Chatting!

```
You: What's the weather in Paris?
You: What time is it in Tokyo?
You: What information is in my document about candidates?
You: Calculate ADD, 15, 27
```

### Step 4: Exit

Type `quit`, `exit`, or `bye` to close the client application.

## 🏗️ Architecture

### MCP Server (`mcp_server.py`)

The FastAPI-based server provides RESTful endpoints for various tools:

**DateTime Tool:**
- Uses Nominatim for geocoding city names
- Determines timezone using TimezoneFinder
- Returns current date, time, and day of week

**Weather Tool:**
- Integrates with OpenWeather API
- Returns current weather conditions in metric units
- Includes temperature, humidity, and weather description

**Calculator Tool:**
- Supports basic arithmetic operations (ADD, SUB, MUL, DIV)
- Input format: `"OPERATION, NUM1, NUM2"`
- Example: `"ADD, 5, 3"` returns `8`

### MCP Client (`little_mcp.py`)

The LangChain-based client orchestrates multiple components:

**RAG System:**
1. Loads your PDF document using PyPDFLoader
2. Splits the document into manageable chunks
3. Converts chunks into vector embeddings using Ollama's nomic-embed-text model
4. Stores embeddings in a Chroma vector database
5. Retrieves relevant context when you ask questions
6. Generates answers using the LLM with retrieved context

**Agent Architecture:**
- Analyzes your queries to determine the best tool to use
- Routes questions about your document to the RAG system
- Uses MCP server tools for real-time information
- Falls back to general knowledge when no tool is suitable
- Maintains conversation history for context-aware responses

## 🔄 Customization

### Change the LLM Model
Edit the `LLM` constant in `little_mcp.py`:
```python
LLM = "llama2"  # or mistral, mixtral, phi, etc.
```

### Add More MCP Tools

**Server Side** (`mcp_server.py`):
1. Create your tool function:
```python
def get_my_tool(param: str):
    # Your logic here
    return {"result": "data"}
```

2. Add an API endpoint:
```python
@app.get("/get_my_tool")
def api_get_my_tool(myParam: str = Query(...)):
    result = get_my_tool(myParam)
    return result
```

**Client Side** (`little_mcp.py`):

Add to the `mcp_tools_config` list:
```python
{
    "name": "my_tool",
    "description": "Description for the agent to understand when to use this tool",
    "function_name": "get_my_tool"
}
```

### Adjust RAG Parameters

Modify in `little_mcp.py`:
```python
# Number of document chunks to retrieve
retriever = self.vector_store.as_retriever(search_kwargs={'k': 3})

# Chunk size and overlap
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=200
)
```

## 🗂️ Project Structure

```
Little_MCP/
├── mcp_server.py          # FastAPI MCP server
├── little_mcp.py          # LangChain client application
├── data/                  # PDF documents directory
├── chroma_db_rag/         # Vector store (auto-generated)
├── .env                   # Environment variables (API keys)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🐛 Troubleshooting

**Server won't start:**
- Check if port 8000 is already in use
- Verify your `.env` file contains the API key

**Weather tool fails:**
- Confirm your OpenWeather API key is valid and active
- Check your internet connection

**Vector store issues:**
- Delete the `chroma_db_rag` directory to rebuild from scratch

**Ollama connection errors:**
- Ensure Ollama is running (`ollama serve`)
- Verify models are downloaded (`ollama list`)

**PDF not found:**
- Verify the path in `PDF_DOCUMENT_PATH`
- Ensure the file exists in the `data` directory

**Client can't connect to server:**
- Confirm the server is running on port 8000
- Check the `SERVER_URL` configuration

## 📋 Example Interactions

```
You: What's the weather in London?
Assistant: The current weather in London is 12°C with light rain...

You: What time is it in New York?
Assistant: In New York, it's currently 2024-10-22 14:30:15 (Tuesday)...

You: Calculate ADD, 25, 17
Assistant: 42.0

You: What does my document say about candidate scores?
Assistant: Based on the document, the candidates have the following scores...
```

## 🤝 Contributing

Contributions are welcome! This project is designed for learning and experimentation. Feel free to:
- Add new tools and capabilities
- Improve the RAG system
- Enhance the agent's reasoning
- Add support for more document types
- Implement additional MCP endpoints

## 📄 License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 🙏 Acknowledgments

Built with:
- [LangChain](https://github.com/langchain-ai/langchain) - Agent framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for APIs
- [Ollama](https://ollama.ai) - Local LLM runtime
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [OpenWeatherMap](https://openweathermap.org/) - Weather data API
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io) - Communication standard

---

**Version**: 0.1.01

Made with ❤️ for AI learning and experimentation
