import asyncio
from .internal_logger import error


_running_tasks: set[asyncio.Task] = set()


def spawn(coro):
    try:
        task = asyncio.create_task(coro)
        _running_tasks.add(task)
        task.add_done_callback(_running_tasks.discard)
        return task
    except RuntimeError as exc:
        error(f"Spawn failed: {str(exc)}")
        return None
