import logging
from ..capture import capture_exception
from ..internal_logger import error


class VerloxLogHandler(logging.Handler):
    def __init__(self, level=logging.ERROR):
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.exc_info:
                exc = record.exc_info[1]
                if exc:
                    capture_exception(exc)
                    return

            capture_exception(RuntimeError(record.getMessage()))
        except Exception as internal_exc:
            error(f"VerloxLogHandler internal error: {str(internal_exc)}")
