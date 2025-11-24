import asyncio
import random
import logging
from .queue import get_queue
from .transport import post_event
from .core import is_enabled, get_config
from .task_manager import spawn
from .internal_logger import debug, error
from .constants import MAX_RETRY_ATTEMPTS, MAX_BACKOFF_SECONDS

_logger = logging.getLogger("verlox.sender")


async def _backoff_sleep(attempt: int):
    base = min(MAX_BACKOFF_SECONDS, 2**attempt)
    jitter = random.uniform(0, 1)
    await asyncio.sleep(base + jitter)


async def _sender_loop(stop_event: asyncio.Event | None = None):
    queue = get_queue()
    debug("Verlox sender loop started")

    while not _should_stop(stop_event):
        event = await _get_event(queue)
        if event is None:
            continue

        await _send_event_with_retry(event)
        try:
            queue.task_done()
        except Exception:
            pass


def _should_stop(stop_event: asyncio.Event | None = None) -> bool:
    return bool(stop_event and stop_event.is_set())


async def _get_event(queue: asyncio.Queue) -> dict | None:
    try:
        return await queue.get()
    except Exception as exc:
        error(f"Sender failed to get from queue: {str(exc)}")
        await asyncio.sleep(1)
        return None


async def _send_event_with_retry(event: dict):
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


async def _try_send_event(endpoint, config, event, attempt: int) -> bool:
    try:
        await post_event(
            endpoint=endpoint,
            api_key=config.api_key,
            api_secret=config.api_secret,
            event=event,
        )
        debug("Event posted successfully")
        return True
    except Exception as exc:
        error(f"Verlox sender failed attempt={attempt} error={str(exc)}")
        if attempt >= MAX_RETRY_ATTEMPTS:
            error(f"Verlox giving up after {attempt} attempts")
        return False


def start_sender_loop():
    try:
        loop = asyncio.get_event_loop()
        stop_event = asyncio.Event()
        spawn(_sender_loop(stop_event))
        return stop_event
    except Exception as exc:
        error("start_sender_loop failed: %s", exc)
        return None
