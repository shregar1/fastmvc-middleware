"""
Server-Timing Middleware for FastMVC.

Adds Server-Timing headers for performance metrics.
"""

import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


_timings: ContextVar[list[dict] | None] = ContextVar("server_timings", default=None)


def add_timing(name: str, duration: float | None = None, description: str = "") -> None:
    """Add a timing entry."""
    entry = {"name": name}
    if duration is not None:
        entry["dur"] = duration
    if description:
        entry["desc"] = description

    _timings.get().append(entry)


class ServerTimingContext:
    """Context manager for timing code blocks."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.start = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration = (time.perf_counter() - self.start) * 1000  # ms
        add_timing(self.name, duration, self.description)


def timing(name: str, description: str = "") -> ServerTimingContext:
    """Create a timing context."""
    return ServerTimingContext(name, description)


@dataclass
class ServerTimingConfig:
    """
    Configuration for server timing middleware.

    Attributes:
        include_total: Include total time.
        include_app: Include app processing time.
    """

    include_total: bool = True
    include_app: bool = True


class ServerTimingMiddleware(FastMVCMiddleware):
    """
    Middleware that adds Server-Timing headers.

    Implements the Server-Timing HTTP header for exposing
    performance metrics to clients and dev tools.

    Example:
        ```python
        from FastMiddleware import ServerTimingMiddleware, timing

        app.add_middleware(ServerTimingMiddleware)

        @app.get("/")
        async def handler():
            with timing("db", "Database query"):
                result = await db.query(...)

            with timing("render"):
                output = render(result)

            return output
        ```
    """

    def __init__(
        self,
        app,
        config: ServerTimingConfig | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ServerTimingConfig()

    def _build_header(self, timings: list[dict], total_ms: float) -> str:
        """Build Server-Timing header value."""
        parts = []

        for entry in timings:
            timing_str = entry["name"]
            if "dur" in entry:
                timing_str += f";dur={entry['dur']:.2f}"
            if "desc" in entry:
                timing_str += f';desc="{entry["desc"]}"'
            parts.append(timing_str)

        if self.config.include_total:
            parts.append(f"total;dur={total_ms:.2f}")

        return ", ".join(parts)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        timings_list: list[dict] = []
        token = _timings.set(timings_list)

        start = time.perf_counter()

        try:
            response = await call_next(request)
            total_ms = (time.perf_counter() - start) * 1000

            header_value = self._build_header(timings_list, total_ms)
            if header_value:
                response.headers["Server-Timing"] = header_value

            return response
        finally:
            _timings.reset(token)
