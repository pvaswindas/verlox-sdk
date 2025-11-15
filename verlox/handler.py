import logging
import asyncio
from logging import LogRecord
from .processor import summarize
from .utils import iso_ts
from .queue import enqueue
from .task_manager import spawn


class VerloxLogHandler(logging.Handler):
    def __init__(self, level=logging.ERROR):
        super().__init__(level=level)

    def emit(self, record: LogRecord) -> None:
        try:
            exc = None
            if record.exc_info:
                exc = record.exc_info[1]
            payload = {
                "event_id": None,
                "timestamp": iso_ts(),
                "sdk": {"name": "verlox", "version": "0.1.0"},
                "app": {"name": "unknown", "environment": "production"},
                "exception": summarize(exc)
                if exc
                else {
                    "type": record.levelname,
                    "message": record.getMessage(),
                    "frames": [],
                    "raw": "",
                },
                "request": {},
                "context": {},
            }
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    spawn(enqueue(payload))
                else:
                    asyncio.run(enqueue(payload))
            except RuntimeError:
                asyncio.run(enqueue(payload))

        except Exception:
            self.handleError(record)
