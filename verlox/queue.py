import asyncio

_event_queue = None


def get_queue() -> asyncio.Queue:
    global _event_queue
    if _event_queue is None:
        _event_queue = asyncio.Queue(maxsize=1000)
    return _event_queue


def enqueue(event: dict):
    queue = get_queue()
    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        try:
            _ = queue.get_nowait()
            queue.task_done()
            queue.put_nowait(event)
        except Exception:
            pass


async def enqueue_async(event: dict):
    enqueue(event)
