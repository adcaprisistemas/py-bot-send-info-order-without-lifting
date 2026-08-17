from src.alerts.ordenes_sin_levante.config import module_config
from src.core.config import config
from src.core.http_client import build_session


def get_session():
    return build_session(token=module_config.API_TOKEN or None)


def obtener_ordenes(session):
    response = session.get(module_config.API_GET_URL, timeout=config.TIMEOUT_SEGUNDOS)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        return data
    return data.get("data", []) if isinstance(data, dict) else []
