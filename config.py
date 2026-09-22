import os
from pathlib import Path
from dotenv import load_dotenv

try:
    import streamlit as st
except Exception:
    st = None

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_setting(name, default=""):
    # 1. Local / environment variable
    value = os.getenv(name)
    if value:
        return str(value).strip()

    # 2. Streamlit Community Cloud Secrets
    if st is not None:
        try:
            value = st.secrets[name]
            if value:
                return str(value).strip()
        except Exception:
            pass

    return default


LLM_API_URL = get_setting(
    "LLM_API_URL",
    "https://api.openai.com/v1/chat/completions"
)

LLM_API_KEY = get_setting("LLM_API_KEY")
LLM_MODEL = get_setting("LLM_MODEL")
SERPER_API_KEY = get_setting("SERPER_API_KEY")

DEMO_MODE = not (LLM_API_KEY and LLM_MODEL)
