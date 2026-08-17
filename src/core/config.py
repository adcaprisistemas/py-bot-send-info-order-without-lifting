import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


def leer_lista(nombre, default):
    valor = os.getenv(nombre, default)
    return [e.strip() for e in valor.split(",") if e.strip()]


class Config:
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    # SMTP (compartido por todos los módulos)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.gmail.com").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
    EMAIL_ORIGEN = os.getenv("EMAIL_ORIGEN", "").strip()
    EMAIL_DESTINOS = leer_lista("EMAIL_DESTINO", "desarrollo@gmail.com")

    # HTTP genérico
    TIMEOUT_SEGUNDOS = int(os.getenv("TIMEOUT_SEGUNDOS", "30"))
    MAX_REINTENTOS = int(os.getenv("MAX_REINTENTOS", "3"))

    # Comportamiento
    EJECUTAR_AL_INICIAR = (
        os.getenv("EJECUTAR_AL_INICIAR", "false").strip().lower() in ("1", "true", "yes")
    )


config = Config()
