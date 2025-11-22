import httpx
import hmac
import hashlib
from .internal_logger import debug, error
import json


def sign_payload(secret: str | None, payload: dict) -> str:
    try:
        if not secret:
            return ""
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    except Exception as e:
        error("sign_payload error: %s", e)
        return ""


async def post_event(
    endpoint: str, api_key: str | None, api_secret: str | None, event: dict
):
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Verlox-Key"] = api_key
        signature = sign_payload(api_secret, event)
        if signature:
            headers["X-Verlox-Signature"] = f"sha256={signature}"
        body = json.dumps(event, separators=(",", ":"), sort_keys=True)
        timeout = httpx.Timeout(5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(endpoint, content=body, headers=headers)
            resp.raise_for_status()
            debug("Transport post_event success: status=%s", resp.status_code)
            return resp
    except Exception as exc:
        error("Transport post_event failed: %s", exc)
        raise
