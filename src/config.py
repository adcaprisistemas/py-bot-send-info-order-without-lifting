import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")


def _leer_horas(nombre, default):
    horas = os.getenv(nombre, default)
    return [h.strip() for h in horas.split(",") if h.strip()]


def _leer_emails(nombre, default):
    emails = os.getenv(nombre, default)
    return [e.strip() for e in emails.split(",") if e.strip()]


class Config:
    API_GET_URL = os.getenv("API_GET_URL", "").strip()
    API_POST_URL = os.getenv("API_POST_URL", "").strip()
    API_TOKEN = os.getenv("API_TOKEN", "").strip()
    HORARIOS_SEMANA = _leer_horas("HORARIOS_SEMANA", "10:00,16:00")
    HORARIOS_SABADO = _leer_horas("HORARIOS_SABADO", "10:00")
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.gmail.com").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
    EMAIL_ORIGEN = os.getenv("EMAIL_ORIGEN", "").strip()
    EMAIL_DESTINOS = _leer_emails("EMAIL_DESTINO", "desarrollo@gmail.com")
    TIMEOUT_SEGUNDOS = int(os.getenv("TIMEOUT_SEGUNDOS", "30"))
    MAX_REINTENTOS = int(os.getenv("MAX_REINTENTOS", "3"))
    EJECUTAR_AL_INICIAR = os.getenv("EJECUTAR_AL_INICIAR", "false").strip().lower() in ("1", "true", "yes")


config = Config()
