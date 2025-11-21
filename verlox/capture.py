from .utils import iso_ts
from processor import summarize
from .core import is_enabled, get_config
from .internal_logger import error


def _build_payload_from_exception(exc: BaseException):
    try:
        config = None
        try:
            config = get_config() if is_enabled() else None
        except Exception:
            config = None

        payload = {
            "timestamp": iso_ts(),
            "sdk": {"name": "verlox", "version": "0.1.0"},
            "app": {
                "name": config.service_name if config else None,
                "environment": config.environment.value if config else None,
            },
            "exception": summarize(exc),
        }
        return payload
    except Exception as internal_exc:
        error(f"Failed to build payload: {str(internal_exc)}")
        try:
            return {
                "timestamp": iso_ts(),
                "exception": {"type": type(exc).__name__, "message": str(exc)},
            }
        except Exception:
            return {
                "timestamp": iso_ts(),
                "exception": {
                    "type": "Unknown",
                    "message": "Failed to stringify exception",
                },
            }
