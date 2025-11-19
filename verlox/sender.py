import asyncio
import logging
from .queue import get_queue
from .transport import post_event
from .config import settings

logger = logging.getLogger(__name__)


async def _backoff_sleep(attempt: int):
    import random

    await asyncio.sleep(min(30, 2**attempt) + random.random())


async def sender_loop():
    queue = get_queue()
    logger.info("[Verlox] sender started")

    while True:
        event = await queue.get()
        attempt = 0

        while True:
            try:
                await post_event(
                    settings.ENDPOINT, settings.API_KEY, settings.API_SECRET, event
                )
                break
            except Exception as exc:
                logger.error(f"[VerloxSender] error in sending: {str(exc)}")
                attempt += 1
                if attempt >= 5:
                    logger.exception("[VerloxSender] giving up after 5 attempts")
                    break
                await _backoff_sleep(attempt)

        queue.task_done()


def start_verlox_sender():
    loop = asyncio.get_event_loop()
    loop.create_task(sender_loop())
