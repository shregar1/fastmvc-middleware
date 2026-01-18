"""
Graceful Shutdown Middleware for FastMVC.

Handles graceful shutdown with in-flight request draining.
"""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class GracefulShutdownConfig:
    """
    Configuration for graceful shutdown middleware.

    Attributes:
        timeout: Max time to wait for requests to complete.
        check_path: Path to check shutdown status.
    """

    timeout: float = 30.0
    check_path: str = "/_shutdown"


class GracefulShutdownMiddleware(FastMVCMiddleware):
    """
    Middleware for graceful shutdown handling.

    Tracks in-flight requests and allows them to complete
    before shutdown, while rejecting new requests.

    Example:
        ```python
        from FastMiddleware import GracefulShutdownMiddleware

        shutdown_mw = GracefulShutdownMiddleware(app, timeout=30.0)

        # When receiving SIGTERM:
        await shutdown_mw.shutdown()
        # Waits for in-flight requests, then returns
        ```
    """

    def __init__(
        self,
        app,
        config: GracefulShutdownConfig | None = None,
        timeout: float | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or GracefulShutdownConfig()

        if timeout:
            self.config.timeout = timeout

        self._shutting_down = False
        self._in_flight = 0
        self._lock = asyncio.Lock()
        self._drain_event = asyncio.Event()

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._shutting_down

    @property
    def in_flight_requests(self) -> int:
        """Get count of in-flight requests."""
        return self._in_flight

    async def shutdown(self) -> None:
        """
        Initiate graceful shutdown.

        Stops accepting new requests and waits for
        in-flight requests to complete.
        """
        self._shutting_down = True

        # Wait for in-flight requests, force shutdown after timeout
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(
                self._wait_for_drain(),
                timeout=self.config.timeout,
            )

    async def _wait_for_drain(self) -> None:
        """Wait for all in-flight requests to complete."""
        while self._in_flight > 0:
            await asyncio.sleep(0.1)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Handle status check
        if request.url.path == self.config.check_path:
            return JSONResponse(
                {
                    "shutting_down": self._shutting_down,
                    "in_flight": self._in_flight,
                }
            )

        # Reject new requests during shutdown
        if self._shutting_down:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "message": "Service is shutting down",
                },
                headers={"Connection": "close"},
            )

        # Track in-flight requests
        async with self._lock:
            self._in_flight += 1

        try:
            return await call_next(request)
        finally:
            async with self._lock:
                self._in_flight -= 1
