from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .processor import summarize, clean_headers
from .utils import iso_ts
from .task_manager import spawn
from .queue import enqueue_async
from .config import settings


class VerloxMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            payload = {
                "timestamp": iso_ts(),
                "sdk": {"name": settings.APP_NAME, "version": "0.1.0"},
                "app": {
                    "name": settings.SERVICE_NAME,
                    "environment": settings.ENVIRONMENT,
                },
                "exception": summarize(exc),
                "request": {
                    "path": request.url.path,
                    "method": request.method,
                    "headers": clean_headers(dict(request.headers)),
                },
            }

            spawn(enqueue_async(payload))
            raise
