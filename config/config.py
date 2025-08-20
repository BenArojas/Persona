import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Project root directory (where config.py is located)
BASE_DIR = Path(__file__).resolve().parent.parent

# Directory for persona data
PERSONAS_DIR = os.path.join(BASE_DIR, "personas")

# Subdirectory name for ChromaDB vector stores within each persona folder
CHROMA_DIR = "vectordb"

# Ollama model configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")  # Default to llama3 if not set

# Neo4j connection settings (update password if different)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")  # Replace with your Neo4j password

# Ensure personas directory exists
os.makedirs(PERSONAS_DIR, exist_ok=True)

# Function to get path for a persona's vector store
def get_persona_chroma_path(persona_name):
    return os.path.join(PERSONAS_DIR, persona_name, CHROMA_DIR)