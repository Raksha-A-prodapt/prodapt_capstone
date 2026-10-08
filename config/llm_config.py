import os
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


# ============================================================
# OPENROUTER LLM CONFIGURATION
# ============================================================

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-nano-30b-a3b:free"
)


# ============================================================
# OPENROUTER API KEYS
# ============================================================

OPENROUTER_API_KEYS = [
    os.getenv("OPENROUTER_API_KEY1"),
    os.getenv("OPENROUTER_API_KEY"),
    os.getenv("openrouter_api_key_k"),
    os.getenv("openrouter_api_key_s"),
    os.getenv("openrouter_api_key_r2k"),
]


# ============================================================
# REMOVE EMPTY / MISSING KEYS
# ============================================================

OPENROUTER_API_KEYS = [
    key
    for key in OPENROUTER_API_KEYS
    if key
]


# ============================================================
# LLM SETTINGS
# ============================================================

LLM_TEMPERATURE = float(
    os.getenv("LLM_TEMPERATURE", "0.0")
)

LLM_MAX_TOKENS = int(
    os.getenv("LLM_MAX_TOKENS", "1000")
)

LLM_TIMEOUT = int(
    os.getenv("LLM_TIMEOUT", "30")
)