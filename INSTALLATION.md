📦 Download these models before running the application:
```bash
ollama pull qwen3:1.7b
ollama pull nomic-embed-text
```
📦 Installation

   ```bash
   wget https://github.com/ricard1406/Little_MCP/archive/refs/heads/main.zip
   unzip main.zip
   mv Little_MCP-main Little_MCP
   cd Little_MCP
   ```
   ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install requests pydantic langchain langchain-community langchain-core chromadb pypdf fastapi uvicorn requests python-dotenv pytz timezonefinder geopy
   ```
📦 Config your api_key
   ```bash
   [your fav editor] .env
   OPENWEATHER_API_KEY=your_api_key_here
   ```
   your local .data folder contains demo docs

   ```
