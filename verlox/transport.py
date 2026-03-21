import httpx
import hmac
import hashlib
import threading
from .internal_logger import debug, error
import json
from .constants import (
    HEADER_VERLOX_KEY,
    HEADER_VERLOX_SIGNATURE,
    SIGNATURE_ALGO,
    DEFAULT_INGEST_TIMEOUT,
    JSON_SEPARATORS,
    JSON_SORT_KEYS,
)

_client: httpx.AsyncClient | None = None
_client_lock = threading.Lock()


def sign_payload(secret: str | None, payload: dict) -> str:
    try:
        if not secret:
            return ""
        body = json.dumps(
            payload, separators=JSON_SEPARATORS, sort_keys=JSON_SORT_KEYS
        ).encode()
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    except Exception as exc:
        error(f"sign_payload error: {exc}")
        return ""


def _get_client() -> httpx.AsyncClient:
    global _client

    if _client is not None:
        return _client

    with _client_lock:
        if _client is None:
            timeout = httpx.Timeout(
                connect=DEFAULT_INGEST_TIMEOUT,
                read=DEFAULT_INGEST_TIMEOUT,
                write=DEFAULT_INGEST_TIMEOUT,
                pool=DEFAULT_INGEST_TIMEOUT,
            )
            limits = httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            )
            _client = httpx.AsyncClient(timeout=timeout, limits=limits)
    return _client


async def close_client():
    global _client

    client = None
    with _client_lock:
        client = _client
        _client = None

    if client is None:
        return

    try:
        await client.aclose()
    except Exception as exc:
        error(f"Transport close_client failed: {exc}")


async def post_event(
    endpoint: str, api_key: str | None, api_secret: str | None, event: dict
):
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers[HEADER_VERLOX_KEY] = api_key

        signature = sign_payload(api_secret, event)
        if signature:
            headers[HEADER_VERLOX_SIGNATURE] = f"{SIGNATURE_ALGO}={signature}"

        body = json.dumps(event, separators=JSON_SEPARATORS, sort_keys=JSON_SORT_KEYS)
        client = _get_client()
        resp = await client.post(endpoint, content=body, headers=headers)
        status = resp.status_code

        if 200 <= status < 300:
            debug(f"Transport post_event success: status={status}")
            return "success"

        if status == 429 or 500 <= status < 600:
            error(f"Transport retryable status={status}")
            return "retry"

        if 400 <= status < 500:
            error(f"Transport dropped event status={status}")
            return "drop"

        error(f"Transport unexpected status={status}")
        return "retry"
    except httpx.TimeoutException as exc:
        error(f"Transport timeout retryable error: {exc}")
        return "retry"
    except httpx.RequestError as exc:
        error(f"Transport request retryable error: {exc}")
        return "retry"
    except Exception as exc:
        error(f"Transport post_event internal error: {exc}")
        return "retry"
