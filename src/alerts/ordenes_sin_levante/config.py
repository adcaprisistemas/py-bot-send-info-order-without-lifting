import os

from src.core.config import leer_lista


def _leer(nombre, default=""):
    return os.getenv(nombre, default).strip()


def _leer_lista_bool(nombre, default=""):
    raw = _leer(nombre, default)
    if not raw:
        return []
    return [e.strip().upper() in ("T", "TRUE", "1", "YES") for e in raw.split(",") if e.strip()]


class ModuleConfig:
    PREFIX = "LEVANTE_"

    API_GET_URL = _leer(f"{PREFIX}API_GET_URL", "")
    API_POST_URL = _leer(f"{PREFIX}API_POST_URL", "")
    API_TOKEN = _leer(f"{PREFIX}API_TOKEN", "")

    TITULO_MENSAJE = _leer(
        f"{PREFIX}TITULO_MENSAJE",
        "PRUEBA DE SISTEMAS - ORDENES DE DEPOSITO SIN LEVANTE AUTORIZADO (NO SE ENCUENTRAN LEGAJADAS O EN ABANDONO LEGAL)",
    )

    USER_ID = _leer(f"{PREFIX}USER_ID", "1")
    USUARIOS_ADICIONALES_JEFE = leer_lista(
        f"{PREFIX}USUARIOS_ADICIONALES_JEFE", ""
    )

    HORARIOS_SEMANA = leer_lista(f"{PREFIX}HORARIOS_SEMANA", "10:00,16:00")
    HORARIOS_SABADO = leer_lista(f"{PREFIX}HORARIOS_SABADO", "10:00")
    HORARIOS_DOMINGO = leer_lista(f"{PREFIX}HORARIOS_DOMINGO", "")

    HORARIOS_CORREO = _leer_lista_bool(f"{PREFIX}HORARIOS_CORREO", "")
    HORARIOS_CORREO_SABADO = _leer_lista_bool(f"{PREFIX}HORARIOS_CORREO_SABADO", "")
    HORARIOS_CORREO_DOMINGO = _leer_lista_bool(f"{PREFIX}HORARIOS_CORREO_DOMINGO", "")


module_config = ModuleConfig()
