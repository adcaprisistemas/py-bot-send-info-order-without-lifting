import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")


def _leer_horas(nombre, default):
    horas = os.getenv(nombre, default)
    return [h.strip() for h in horas.split(",") if h.strip()]


class Config:
    API_GET_URL = os.getenv("API_GET_URL", "").strip()
    API_POST_URL = os.getenv("API_POST_URL", "").strip()
    API_TOKEN = os.getenv("API_TOKEN", "").strip()
    HORARIOS_SEMANA = _leer_horas("HORARIOS_SEMANA", "10:00,16:00")
    HORARIOS_SABADO = _leer_horas("HORARIOS_SABADO", "10:00")
    TIMEOUT_SEGUNDOS = int(os.getenv("TIMEOUT_SEGUNDOS", "30"))
    MAX_REINTENTOS = int(os.getenv("MAX_REINTENTOS", "3"))
    EJECUTAR_AL_INICIAR = os.getenv("EJECUTAR_AL_INICIAR", "false").strip().lower() in ("1", "true", "yes")


config = Config()
