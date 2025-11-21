import asyncio
from .internal_logger import debug, error

_event_queue: asyncio.Queue | None = None
_MAXSIZE = 1000


def get_queue() -> asyncio.Queue:
    global _event_queue
    if _event_queue is None:
        _event_queue = asyncio.Queue(maxsize=_MAXSIZE)
    return _event_queue


def enqueue(event: dict):
    try:
        queue = get_queue()
        queue.put_nowait(event)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
            queue.task_done()
            queue.put_nowait(event)
            debug("Queue full: dropped oldest event")
        except Exception as exc:
            error(f"Failed to manage full queue: {str(exc)}")
