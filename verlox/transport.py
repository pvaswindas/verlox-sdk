import httpx
import hmac
import hashlib
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

        timeout = httpx.Timeout(DEFAULT_INGEST_TIMEOUT)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(endpoint, content=body, headers=headers)
            resp.raise_for_status()
            debug(f"Transport post_event success: status={resp.status_code}")
            return resp

    except Exception as exc:
        error(f"Transport post_event failed: {exc}")
        raise
