import httpx
from .constants import DSN_ENDPOINT, DSN_TIMEOUT


def fetch_ingest_url() -> str | None:
    try:
        response = httpx.get(DSN_ENDPOINT, timeout=DSN_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("ingest_url")
    except Exception:
        return None
