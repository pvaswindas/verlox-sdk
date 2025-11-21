import sys
import asyncio
from .task_manager import spawn
from .queue import enqueue
from .utils import iso_ts
from processor import summarize
from .core import is_enabled, get_config
from .internal_logger import debug, error


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


def capture_exception(exc: Exception):
    try:
        if not is_enabled():
            debug("Verlox disabled, skipping capture.")
            return
        payload = _build_payload_from_exception(exc)
        try:
            spawn(enqueue(payload))
        except Exception as internal_exc:
            error(f"Verlox failed to enqueue: {str(internal_exc)}")
    except Exception as internal_exc:
        error(f"Verlox capture_exception internal error: {str(internal_exc)}")


def _handle_uncaught_exception(exc_type, exc, tb):
    try:
        capture_exception(exc if exc is not None else exc_type("Unknown"))
    except Exception:
        pass


def _handle_asyncio_exception(loop, context):
    try:
        exc = context.get("exception")
        if exc:
            capture_exception(exc)
        else:
            msg = context.get("message", "Unknown asyncio error")
            capture_exception(RuntimeError(msg))
    except Exception:
        pass


def setup_global_exception_hooks():
    try:
        sys.excepthook = _handle_uncaught_exception
    except Exception:
        pass

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(_handle_asyncio_exception)
    except Exception:
        pass
