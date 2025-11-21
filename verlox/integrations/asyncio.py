import asyncio
from ..capture import capture_exception
from ..internal_logger import debug, error


_original_create_task = None
_instrumented = False


def instrument_asyncio_tasks():
    global _original_create_task, _instrumented
    if _instrumented:
        return
    try:
        _original_create_task = asyncio.create_task

        def wrapper(coro, *args, **kwargs):
            task = _original_create_task(coro, *args, **kwargs)

            def done(task):
                try:
                    exc = task.exception()
                    if exc:
                        capture_exception(exc)
                except asyncio.CancelledError:
                    pass
                except Exception as internal_exc:
                    error(f"instrument_asyncio_task done callback: {str(internal_exc)}")

            task.add_done_callback(done)
            return task

        asyncio.create_task = wrapper
        _instrumented = True
        debug("Instrumented asyncio.create_task")
    except Exception as internal_exc:
        error(f"Failed to instrument asyncio task: {str(internal_exc)}")
