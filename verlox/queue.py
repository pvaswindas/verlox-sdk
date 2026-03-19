import asyncio
from .internal_logger import debug, error
from .constants import QUEUE_MAX_SIZE

_event_queue: asyncio.Queue | None = None
_event_loop: asyncio.AbstractEventLoop | None = None


def get_queue() -> asyncio.Queue:
    global _event_queue, _event_loop
    if _event_queue is None:
        _event_queue = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
    try:
        _event_loop = asyncio.get_running_loop()
    except Exception:
        pass
    return _event_queue


def _put_event_nowait(queue: asyncio.Queue, event: dict):
    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
            queue.task_done()
            queue.put_nowait(event)
            debug("Queue full: dropped oldest event")
        except Exception as exc:
            error(f"Failed to manage full queue: {str(exc)}")
    except Exception as exc:
        error(f"Failed to enqueue event: {str(exc)}")


def enqueue(event: dict):
    global _event_loop

    try:
        queue = get_queue()
    except Exception as exc:
        error(f"Failed to get queue: {str(exc)}")
        return

    try:
        running_loop = asyncio.get_running_loop()
        _event_loop = running_loop
    except Exception:
        running_loop = None

    target_loop = running_loop or _event_loop
    if target_loop and target_loop.is_running():
        try:
            target_loop.call_soon_threadsafe(_put_event_nowait, queue, event)
            return
        except Exception as exc:
            error(f"Failed to schedule queue put: {str(exc)}")

    try:
        _put_event_nowait(queue, event)
    except Exception as exc:
        error(f"Fallback enqueue failed: {str(exc)}")
