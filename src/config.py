import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")


class Config:
    API_GET_URL = os.getenv("API_GET_URL", "").strip()
    API_POST_URL = os.getenv("API_POST_URL", "").strip()
    API_TOKEN = os.getenv("API_TOKEN", "").strip()
    HORA_EJECUCION = os.getenv("HORA_EJECUCION", "06:00").strip()
    TIMEOUT_SEGUNDOS = int(os.getenv("TIMEOUT_SEGUNDOS", "30"))
    MAX_REINTENTOS = int(os.getenv("MAX_REINTENTOS", "3"))
    EJECUTAR_AL_INICIAR = os.getenv("EJECUTAR_AL_INICIAR", "false").strip().lower() in ("1", "true", "yes")


config = Config()
