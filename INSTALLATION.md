📦 Download Ollama local model : (not required when using Calude)
```bash
ollama pull qwen3:4b
```
📦 Download Ollama embeddings:
```bash
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
   pip install langchain-core langchain-community langchain-ollama langchain-text-splitters langgraph fastapi uvicorn requests python-dotenv pytz timezonefinder geopy chromadb pypdf gradio langchain-anthropic
   ```
📦 Config your api_key
   ```bash
   [open your fav editor and set your openweather key, DB user and password, claude api_key]
   cd source
   [vi] .env
   OPENWEATHER_API_KEY=your_api_key_here
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   ANTHROPIC_API_KEY=your_api_key_here

   Note a): your local .data folder contains demo docs
   Note b): key required just if you use it. otherwise not required

   ```
📦 Start app
   ```bash
   python mcp_server.py

   [leave open this terminal and open a second terminal please]
   [activate your env if not jet] : source ../.venv/bin/activate   ]

   python little_mcp.py [text/graph]              (Ollama LLM)
   python little_mcp.py [text/graph] --think       (Ollama LLM thinking mode)
   python little_mcp.py [text/graph] --provider anthropic               (Claude LLM)
   python little_mcp.py [text/graph] --provider anthropic --think       (Claude LLM thinking mode)

   note: add graph parameter for graphical interface
   When use graph interface open your browser and run local URL:
   http://127.0.0.1:7860             
   ```
