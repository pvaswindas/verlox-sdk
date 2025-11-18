import logging
import asyncio
from logging import LogRecord
from .processor import summarize
from .utils import iso_ts
from .queue import enqueue
from .task_manager import spawn


class VerloxLogHandler(logging.Handler):
    def emit(self, record: LogRecord) -> None:
        try:
            exc = record.exc_info[1] if record.exc_info else None

            payload = {
                "timestamp": iso_ts(),
                "sdk": {"name": "verlox", "version": "0.1.0"},
                "exception": summarize(exc)
                if exc
                else {
                    "type": record.levelname,
                    "message": record.getMessage(),
                    "frames": [],
                    "raw": "",
                },
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
