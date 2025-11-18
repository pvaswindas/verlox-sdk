from .middleware import VerloxMiddleware
from .handler import VerloxLogHandler
from .sender import start_verlox_sender

try:
    import asyncio

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.call_soon(start_verlox_sender)
except Exception:
    pass

__all__ = [
    "VerloxMiddleware",
    "VerloxLogHandler",
    "start_verlox_sender",
]
