import asyncio
import random
import logging
from .queue import get_queue
from .transport import post_event
from .core import is_enabled, get_config
from .task_manager import spawn
from .internal_logger import debug, error

_logger = logging.getLogger("verlox.sender")


async def _backoff_sleep(attempt: int):
    base = min(30, 2**attempt)
    jitter = random.uniform(0, 1)
    await asyncio.sleep(base + jitter)


async def _sender_loop(stop_event: asyncio.Event | None = None):
    queue = get_queue()
    debug("Verlox sender loop started")
    while True:
        if stop_event and stop_event.is_set():
            debug("Verlox sender stop_event set, exiting sender loop")
            break
        try:
            event = await queue.get()
        except Exception as e:
            error("Sender failed to get from queue: %s", e)
            await asyncio.sleep(1)
            continue

        attempt = 0
        max_attempts = 5
        while True:
            try:
                if not is_enabled():
                    debug("Verlox disabled, skipping send")
                    break
                cfg = get_config()
                endpoint = cfg.dsn
                if not endpoint:
                    debug("No endpoint configured, dropping event")
                    break
                await post_event(
                    endpoint=endpoint,
                    api_key=cfg.api_key,
                    api_secret=cfg.api_secret,
                    event=event,
                )
                debug("Event posted successfully")
                break
            except Exception as exc:
                attempt += 1
                error("Verlox sender failed attempt=%s error=%s", attempt, exc)
                if attempt >= max_attempts:
                    error("Verlox giving up after %s attempts", attempt)
                    break
                await _backoff_sleep(attempt)
        try:
            queue.task_done()
        except Exception:
            pass


def start_sender_loop():
    try:
        loop = asyncio.get_event_loop()
        stop_event = asyncio.Event()
        spawn(_sender_loop(stop_event))
        return stop_event
    except Exception as exc:
        error("start_sender_loop failed: %s", exc)
        return None
