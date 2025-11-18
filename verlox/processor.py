import traceback


SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "x-token"}


def clean_headers(headers: dict) -> dict:
    cleaned = {}
    for key, value in (headers or {}).items():
        if key.lower() in SENSITIVE_HEADERS:
            cleaned[key] = "[REDACTED]"
        else:
            cleaned[key] = value
    return cleaned


def extract_frames(exc: BaseException, max_frames: int = 6) -> list[dict]:
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


def summarize(exc: BaseException) -> dict:
    return {
        "type": type(exc).__name__,
        "message": str(exc)[:500],
        "frames": extract_frames(exc),
        "raw": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[
            :2000
        ],
    }
