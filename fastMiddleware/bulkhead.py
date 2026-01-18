"""
Bulkhead Middleware for FastMVC.

Implements bulkhead pattern for isolation.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class BulkheadConfig:
    """
    Configuration for bulkhead middleware.

    Attributes:
        max_concurrent: Max concurrent requests.
        max_waiting: Max waiting requests.
        timeout: Max wait time in seconds.
        per_path: Enable per-path bulkheads.
        path_limits: Path-specific limits.
    """

    max_concurrent: int = 100
    max_waiting: int = 50
    timeout: float = 30.0
    per_path: bool = False
    path_limits: dict[str, int] = None

    def __post_init__(self):
        if self.path_limits is None:
            self.path_limits = {}


class BulkheadMiddleware(FastMVCMiddleware):
    """
    Middleware implementing bulkhead pattern.

    Limits concurrent request processing to prevent
    resource exhaustion and cascade failures.

    Example:
        ```python
        from FastMiddleware import BulkheadMiddleware

        app.add_middleware(
            BulkheadMiddleware,
            max_concurrent=100,
            max_waiting=50,
        )

        # Only 100 requests processed at once
        # 50 more can wait in queue
        # Others get 503 immediately
        ```
    """

    def __init__(
        self,
        app,
        config: BulkheadConfig | None = None,
        max_concurrent: int | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or BulkheadConfig()

        if max_concurrent:
            self.config.max_concurrent = max_concurrent

        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._waiting = 0
        self._path_semaphores: dict[str, asyncio.Semaphore] = {}

    def _get_semaphore(self, path: str) -> asyncio.Semaphore:
        """Get semaphore for path."""
        if not self.config.per_path:
            return self._semaphore

        if path not in self._path_semaphores:
            limit = self.config.path_limits.get(path, self.config.max_concurrent)
            self._path_semaphores[path] = asyncio.Semaphore(limit)

        return self._path_semaphores[path]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        semaphore = self._get_semaphore(request.url.path)

        # Check waiting queue
        if self._waiting >= self.config.max_waiting:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "message": "Service overloaded",
                    "retry_after": 5,
                },
                headers={"Retry-After": "5"},
            )

        self._waiting += 1
        try:
            await asyncio.wait_for(
                semaphore.acquire(),
                timeout=self.config.timeout,
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "message": "Request timeout waiting for resources",
                },
            )
        finally:
            self._waiting -= 1

        try:
            return await call_next(request)
        finally:
            semaphore.release()
