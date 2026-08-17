from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.config import config


def build_session(token=None):
    import requests

    session = requests.Session()

    retry = Retry(
        total=config.MAX_REINTENTOS,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"Content-Type": "application/json"})

    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})

    return session
