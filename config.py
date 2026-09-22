import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions").strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "").strip()

DEMO_MODE = not (LLM_API_KEY and LLM_MODEL)
