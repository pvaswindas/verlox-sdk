import asyncio

_running_tasks: set[asyncio.Task] = set()


def spawn(coro):
    task = asyncio.create_task(coro)
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)
    return task
