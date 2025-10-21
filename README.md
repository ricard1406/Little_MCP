# Little MCP Agent 🤖

A simple yet powerful local AI assistant that runs entirely on your machine. Built for learning and experimentation, Little MCP combines the power of open-source LLMs with advanced Retrieval-Augmented Generation (RAG) to create an intelligent chatbot that can work with your personal documents and provide real-time information.

## ✨ Features

- **Local LLM Integration**: Powered by Ollama for complete privacy and offline functionality
- **RAG System**: Query and extract information from your PDF documents using vector embeddings
- **MCP Server/Client Architecture**: Demonstrates Model Context Protocol implementation
- **Multi-Tool Agent**: Access to multiple tools including:
  - Document Q&A system (RAG-based)
  - Real-time weather information
  - Current date and time for any city
  - Arithmetic calculations
- **Conversational Memory**: Maintains context throughout your chat session
- **Vector Store Persistence**: Efficiently stores and reuses document embeddings

## 🔧 Requirements

### System Requirements
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running locally

### Python Dependencies
```
requests
pydantic
langchain
langchain-community
langchain-core
chromadb
pypdf
```

### Required Ollama Models
Download these models before running the application:
```bash
ollama pull qwen3:1.7b
ollama pull nomic-embed-text
```

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Little_MCP.git
   cd Little_MCP
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your MCP server**
   
   Make sure your MCP server is running at `http://127.0.0.1:8000` with the following endpoints:
   - `/get_datetime` - Returns current date/time for a city
   - `/get_weather` - Returns weather information for a city
   - `/get_calc` - Performs arithmetic operations

4. **Prepare your PDF document**
   
   Create a `data` directory and place your PDF file:
   ```bash
   mkdir data
   # Copy your PDF to ./data/
   ```

5. **Configure the application**
   
   Edit the constants in the script:
   ```python
   SERVER_URL = "http://127.0.0.1:8000"
   PDF_DOCUMENT_PATH = "./data/your-document.pdf"
   LLM = "qwen3:1.7b"  # or any other Ollama model
   ```

## 🚀 Usage

1. **Start your MCP server** (on port 8000)

2. **Run the application**
   ```bash
   python little_mcp.py
   ```

3. **Start chatting!**
   ```
   You: What's the weather in Paris?
   You: What time is it in Tokyo?
   You: What information is in my document about candidates?
   You: Calculate 15 + 27
   ```

4. **Exit**
   Type `quit`, `exit`, or `bye` to close the application.

## 📚 How It Works

### RAG System
The application uses a Retrieval-Augmented Generation system that:
1. Loads your PDF document using PyPDFLoader
2. Splits the document into manageable chunks
3. Converts chunks into vector embeddings using Ollama's nomic-embed-text model
4. Stores embeddings in a Chroma vector database
5. Retrieves relevant context when you ask questions
6. Generates answers using the LLM with retrieved context

### Agent Architecture
The LangChain agent:
- Analyzes your queries to determine the best tool to use
- Routes questions about your document to the RAG system
- Uses MCP server tools for real-time information
- Falls back to general knowledge when no tool is suitable
- Maintains conversation history for context-aware responses

## 🔄 Customization

### Change the LLM Model
Edit the `LLM` constant to use any Ollama model:
```python
LLM = "llama2"  # or mistral, mixtral, etc.
```

### Add More MCP Tools
Extend the `mcp_tools_config` list in the `initialize()` method:
```python
{
    "name": "your_tool_name",
    "description": "Tool description for the agent",
    "function_name": "endpoint_name"
}
```

### Adjust RAG Parameters
Modify the RAG chain configuration:
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
├── little_mcp.py          # Main application
├── data/                  # PDF documents directory
├── chroma_db_rag/         # Vector store (auto-generated)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🐛 Troubleshooting

**Vector store issues**: Delete the `chroma_db_rag` directory to rebuild from scratch

**Ollama connection errors**: Ensure Ollama is running (`ollama serve`)

**PDF not found**: Verify the path in `PDF_DOCUMENT_PATH`

**MCP server errors**: Confirm your server is running and accessible at the configured URL

## 🤝 Contributing

Contributions are welcome! This project is designed for learning and experimentation. Feel free to:
- Add new tools and capabilities
- Improve the RAG system
- Enhance the agent's reasoning
- Add support for more document types

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
- [Ollama](https://ollama.ai) - Local LLM runtime
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io) - Communication standard

---

**Version**: 0.1.01

Made with ❤️ for AI learning and experimentation