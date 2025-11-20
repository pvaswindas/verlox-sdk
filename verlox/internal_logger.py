from logging import Formatter, NullHandler, FileHandler
import logging

_logger = logging.getLogger("verlox.sdk")
_logger.propagate = False
_logger.addHandler(NullHandler())


def enable_file_debug(path: str = "verlox-debug.log"):
    for handler in _logger.handlers:
        _logger.removeHandler(handler)

    file_handler = FileHandler(path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(file_handler)
    _logger.setLevel(logging.DEBUG)


def disable_debug():
    for handler in _logger.handlers:
        _logger.removeHandler(handler)

    _logger.addHandler(NullHandler())


def debug(msg: str, *args, **kwargs):
    try:
        _logger.debug(msg, *args, **kwargs)
    except Exception:
        pass


def info(msg: str, *args, **kwargs):
    try:
        _logger.info(msg, *args, **kwargs)
    except Exception:
        pass


def error(msg: str, *args, **kwargs):
    try:
        _logger.error(msg, *args, **kwargs)
    except Exception:
        pass
