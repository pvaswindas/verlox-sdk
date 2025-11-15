from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .processor import summarize, clean_headers
from .utils import iso_ts
from .queue import enqueue
from .task_manager import spawn


class VerloxMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        endpoint: str,
        api_key: str,
        api_secret: str,
        service_name: str = "app",
        environment: str = "production",
    ):
        super().__init__(app)
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        self.service_name = service_name
        self.environment = environment

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            payload = {
                "event_id": None,
                "timestamp": iso_ts(),
                "sdk": {"name": "verlox", "version": "0.1.0"},
                "app": {"name": self.service_name, "environment": self.environment},
                "exception": summarize(exc),
                "request": {
                    "path": str(request.url.path),
                    "method": request.method,
                    "headers": clean_headers(dict(request.headers)),
                },
                "context": {},
            }
            spawn(enqueue(payload))
            raise
