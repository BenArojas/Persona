# Persona AI Project

A multi-persona AI application that simulates cognitive models using RAG and GraphRAG. Built with Ollama (Llama 3), LangChain, ChromaDB, Neo4j, and Streamlit.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Install Ollama and pull Llama 3: `ollama pull llama3`
3. Install Neo4j Desktop from neo4j.com
4. Run the app: `streamlit run ui/app.py`

## Structure
- `personas/`: Stores data for each persona (e.g., vector stores, graphs).
- `src/`: Python scripts for ingestion and logic.
- `config/`: Configuration files.
- `ui/`: Streamlit app.
- `data/`: Temporary file uploads.

## Status
Work in progress (Phase 0: Core Setup).