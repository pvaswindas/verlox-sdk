import asyncio
import random
import threading
from concurrent.futures import TimeoutError as FutureTimeoutError
from .queue import get_queue
from .transport import post_event, close_client
from .core import is_enabled, get_config
from .internal_logger import debug, error
from .constants import MAX_RETRY_ATTEMPTS, MAX_BACKOFF_SECONDS

_state_lock = threading.Lock()
_started = False
_sender_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None
_sender_loop_ref: asyncio.AbstractEventLoop | None = None
_sender_thread: threading.Thread | None = None
_owns_sender_loop = False


async def _backoff_sleep(attempt: int):
    base = min(MAX_BACKOFF_SECONDS, 2**attempt)
    jitter = random.uniform(0, 1)
    await asyncio.sleep(base + jitter)


async def _sender_loop(stop_event: asyncio.Event):
    queue = get_queue()
    debug("Verlox sender loop started")

    while not stop_event.is_set():
        event = await _get_event(queue)
        if event is None:
            continue

        await _send_event_with_retry(event)
        try:
            queue.task_done()
        except Exception:
            pass


async def _get_event(queue: asyncio.Queue) -> dict | None:
    try:
        return await asyncio.wait_for(queue.get(), timeout=0.5)
    except asyncio.TimeoutError:
        return None
    except Exception as exc:
        error(f"Sender failed to get from queue: {str(exc)}")
        await asyncio.sleep(1)
        return None


async def _send_event_with_retry(event: dict):
    try:
        if not is_enabled():
            debug("Verlox disabled, skipping send")
            return

        config = get_config()
        endpoint = config.ingest_url
        if not endpoint:
            debug("No endpoint configured, dropping event")
            return

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            if await _try_send_event(endpoint, config, event, attempt):
                return
            await _backoff_sleep(attempt)
    except Exception as exc:
        error(f"Verlox _send_event_with_retry failed: {str(exc)}")


async def _try_send_event(endpoint, config, event, attempt: int) -> bool:
    try:
        result = await post_event(
            endpoint=endpoint,
            api_key=config.api_key,
            api_secret=config.api_secret,
            event=event,
        )
        if result == "success":
            debug("Event posted successfully")
            return True
        if result == "drop":
            debug("Dropping non-retryable event")
            return True
        error(f"Verlox sender retryable failure attempt={attempt}")
        if attempt >= MAX_RETRY_ATTEMPTS:
            error(f"Verlox giving up after {attempt} attempts")
        return False
    except Exception as exc:
        error(f"Verlox sender failed attempt={attempt} error={str(exc)}")
        if attempt >= MAX_RETRY_ATTEMPTS:
            error(f"Verlox giving up after {attempt} attempts")
        return False


async def _flush_queue():
    queue = get_queue()
    while True:
        try:
            event = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        except Exception as exc:
            error(f"Flush failed to read queue: {str(exc)}")
            break

        try:
            await _send_event_with_retry(event)
        except Exception as exc:
            error(f"Flush failed to send event: {str(exc)}")
        finally:
            try:
                queue.task_done()
            except Exception:
                pass


def _thread_loop_main():
    global _sender_loop_ref, _stop_event, _sender_task

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stop_event = asyncio.Event()
        task = loop.create_task(_sender_loop(stop_event))

        with _state_lock:
            _sender_loop_ref = loop
            _stop_event = stop_event
            _sender_task = task

        loop.run_forever()

        try:
            pending = asyncio.all_tasks(loop)
            for pending_task in pending:
                pending_task.cancel()
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
        except Exception as exc:
            error(f"Sender thread cleanup error: {str(exc)}")
        finally:
            loop.close()
    except Exception as exc:
        error(f"Sender thread failed: {str(exc)}")
    finally:
        with _state_lock:
            _reset_state_locked()


def _reset_state_locked():
    global _started, _sender_task, _stop_event, _sender_loop_ref, _sender_thread, _owns_sender_loop
    _started = False
    _sender_task = None
    _stop_event = None
    _sender_loop_ref = None
    _sender_thread = None
    _owns_sender_loop = False


def start_sender_loop():
    global _started, _sender_task, _stop_event, _sender_loop_ref, _sender_thread, _owns_sender_loop

    with _state_lock:
        if _started:
            return _stop_event

    try:
        loop = asyncio.get_running_loop()
    except Exception:
        loop = None

    if loop and loop.is_running():
        try:
            stop_event = asyncio.Event()
            task = loop.create_task(_sender_loop(stop_event))

            with _state_lock:
                if _started:
                    task.cancel()
                    return _stop_event
                _started = True
                _sender_task = task
                _stop_event = stop_event
                _sender_loop_ref = loop
                _sender_thread = None
                _owns_sender_loop = False
            return stop_event
        except Exception as exc:
            error(f"start_sender_loop in running loop failed: {str(exc)}")
            return None

    try:
        thread = threading.Thread(target=_thread_loop_main, name="verlox-sender", daemon=True)
        with _state_lock:
            if _started:
                return _stop_event
            _started = True
            _sender_thread = thread
            _owns_sender_loop = True
        thread.start()
        return _stop_event
    except Exception as exc:
        error(f"start_sender_loop thread mode failed: {str(exc)}")
        with _state_lock:
            _reset_state_locked()
        return None


def flush(timeout: float = 5.0):
    try:
        with _state_lock:
            loop = _sender_loop_ref

        if not loop or not loop.is_running():
            return

        future = asyncio.run_coroutine_threadsafe(_flush_queue(), loop)
        try:
            future.result(timeout=timeout)
        except FutureTimeoutError:
            error("flush timed out")
        except Exception as exc:
            error(f"flush failed: {str(exc)}")
    except Exception as exc:
        error(f"flush internal error: {str(exc)}")


def shutdown(timeout: float = 5.0):
    global _sender_task

    try:
        flush(timeout=timeout)

        with _state_lock:
            loop = _sender_loop_ref
            stop_event = _stop_event
            sender_task = _sender_task
            sender_thread = _sender_thread
            owns_loop = _owns_sender_loop

        if not loop:
            with _state_lock:
                _reset_state_locked()
            return

        try:
            closing_future = asyncio.run_coroutine_threadsafe(close_client(), loop)
            try:
                closing_future.result(timeout=timeout)
            except FutureTimeoutError:
                error("close_client timed out")
            except Exception as exc:
                error(f"close_client failed: {str(exc)}")
        except Exception:
            try:
                running = asyncio.get_running_loop()
            except Exception:
                running = None

            if running and running is loop:
                try:
                    loop.create_task(close_client())
                except Exception as exc:
                    error(f"close_client scheduling failed: {str(exc)}")

        def _request_stop():
            try:
                if stop_event:
                    stop_event.set()
                if sender_task and not sender_task.done():
                    sender_task.cancel()
                if owns_loop:
                    loop.stop()
            except Exception as exc:
                error(f"shutdown stop request failed: {str(exc)}")

        if loop.is_running():
            try:
                loop.call_soon_threadsafe(_request_stop)
            except Exception as exc:
                error(f"shutdown scheduling failed: {str(exc)}")

        if owns_loop and sender_thread:
            try:
                sender_thread.join(timeout=timeout)
            except Exception as exc:
                error(f"shutdown thread join failed: {str(exc)}")

        with _state_lock:
            _reset_state_locked()
    except Exception as exc:
        error(f"shutdown internal error: {str(exc)}")
