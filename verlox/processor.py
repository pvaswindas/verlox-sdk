import traceback


SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "x-token"}
_MAX_FRAMES = 6


def clean_headers(headers: dict) -> dict:
    cleaned = {}
    for key, value in (headers or {}).items():
        try:
            if key.lower() in SENSITIVE_HEADERS:
                cleaned[key] = "[REDACTED]"
            else:
                cleaned[key] = value
        except Exception:
            cleaned[key] = "[UNSAFE]"
    return cleaned


def extract_frames(exc: BaseException, max_frames: int = _MAX_FRAMES) -> list[dict]:
    try:
        tb = exc.__traceback__
        if tb is None:
            return []
        extracted = traceback.extract_tb(tb)
        selected = extracted[-max_frames:]

        frames = []
        for frame in selected:
            frames.append(
                {
                    "file": frame.filename.split("/")[-1],
                    "line": frame.lineno,
                    "function": frame.name,
                }
            )
        return frames
    except Exception:
        return []


def summarize(exc: BaseException) -> dict:
    try:
        raw = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[
            :2000
        ]
        message = str(exc)[:500]
        return {
            "type": type(exc).__name__,
            "message": message,
            "frames": extract_frames(exc),
            "raw": raw,
        }
    except Exception:
        return {
            "type": "Error",
            "message": "Failed to summarize exception",
            "frames": [],
            "raw": "",
        }
