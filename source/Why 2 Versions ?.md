## 📦 Why 2 little_mcp.py Versions ?
```
little_mcp.py and little_mcp_2.py doing the same BUT 
    little_mcp.py requires langchain==0.0.354. That is an older version based on LangChain website.
    little_mcp_2.py is compatible with LangChain latest release.

note that little_mcp_2.py requires :
    pip install langchain-core langchain-community langchain-ollama langchain-text-splitters langgraph fastapi uvicorn requests python-dotenv pytz timezonefinder geopy
