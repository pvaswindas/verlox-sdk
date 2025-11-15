import asyncio
import random
import logging
from .queue import get_queue
from .transport import post_event

logger = logging.getLogger(__name__)


async def _backoff_sleep(attempt: int):
    base = min(30, 2**attempt)
    jitter = random.uniform(0, 1)
    await asyncio.sleep(base + jitter)


async def sender_loop(
    endpoint: str,
    api_key: str,
    api_secret: str,
    stop_event: asyncio.Event | None = None,
):
    queue = get_queue()
    logger.info("[Verlox] sender started")
    while True:
        if stop_event and stop_event.is_set():
            break
        event = await queue.get()
        attempt = 0
        max_attempts = 5
        while True:
            try:
                await post_event(endpoint, api_key, api_secret, event)
                break
            except Exception as exc:
                attempt += 1
                logger.warning(f"[Verlox] send failed attempt={attempt} error={exc}")
                if attempt >= max_attempts:
                    logger.error(f"[Verlox] giving up after {attempt} attempts")
                    break
                await _backoff_sleep(attempt)
        queue.task_done()


def start_verlox_sender(endpoint: str, api_key: str, api_secret: str):
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()
    loop.create_task(sender_loop(endpoint, api_key, api_secret, stop_event))
    return stop_event
