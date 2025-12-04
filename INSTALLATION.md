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
    pip install requests pydantic langchain==0.0.354 langchain-community langchain-core chromadb pypdf fastapi uvicorn requests python-dotenv pytz timezonefinder geopy

    BUT if you get little_mcp_2.py version
    pip install langchain-core langchain-community langchain-ollama langchain-text-splitters langgraph fastapi uvicorn requests python-dotenv pytz timezonefinder geopy chromadb pypdf
   ```
📦 Config your api_key
   ```bash
   cd source
   [if you want real time weather, open your fav editor and set your openweather key
   [vi] .env
   OPENWEATHER_API_KEY=your_api_key_here

   Note: your local .data folder contains demo docs

   ```
📦 Start app
   ```bash
   python mcp_server.py

   [leave open this terminal and open a second terminal please]
   [activate your env if not jet] : source ../.venv/bin/activate   ]
   python little_mcp.py
   ```
