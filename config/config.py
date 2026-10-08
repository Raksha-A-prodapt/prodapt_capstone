from pathlib import Path
import os
from dotenv import load_dotenv


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT
# ============================================================

ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


# ============================================================
# DIRECTORIES
# ============================================================

DATA_DIR = BASE_DIR / "data"
RAG_DIR = BASE_DIR / "rag"
ML_DIR = BASE_DIR / "ml"


# ============================================================
# DATA
# ============================================================

CSV_PATH = DATA_DIR / "telecom_network_incidents_with_id.csv"


# ============================================================
# CHROMADB
# ============================================================

CHROMA_PATH = RAG_DIR / "chroma_db"

CHROMA_COLLECTION_NAME = os.getenv(
    "CHROMA_COLLECTION_NAME",
    "telecom_incidents"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5"
)