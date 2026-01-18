"""
Request Context Middleware for FastMVC.

Provides shared context for requests.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


_context: ContextVar[dict[str, Any] | None] = ContextVar("request_context", default=None)


def get_context() -> dict[str, Any]:
    """Get current request context."""
    return _context.get() or {}


def set_context_value(key: str, value: Any) -> None:
    """Set a value in the current request context."""
    ctx = _context.get()
    ctx[key] = value


def get_context_value(key: str, default: Any = None) -> Any:
    """Get a value from the current request context."""
    return _context.get().get(key, default)


@dataclass
class ContextConfig:
    """
    Configuration for context middleware.

    Attributes:
        extract_headers: Headers to extract into context.
        extract_query: Query params to extract.
        header_prefix: Strip this prefix from header names.
    """

    extract_headers: dict[str, str] = field(default_factory=dict)
    extract_query: dict[str, str] = field(default_factory=dict)
    header_prefix: str = "X-"


class ContextMiddleware(FastMVCMiddleware):
    """
    Middleware that provides shared request context.

    Extracts values from request and makes them available
    throughout the request lifecycle.

    Example:
        ```python
        from FastMiddleware import ContextMiddleware, get_context_value

        app.add_middleware(
            ContextMiddleware,
            extract_headers={"X-User-ID": "user_id"},
        )

        @app.get("/")
        async def handler():
            user_id = get_context_value("user_id")
            return {"user_id": user_id}
        ```
    """

    def __init__(
        self,
        app,
        config: ContextConfig | None = None,
        extract_headers: dict[str, str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ContextConfig()

        if extract_headers:
            self.config.extract_headers = extract_headers

    def _extract_context(self, request: Request) -> dict[str, Any]:
        """Extract context from request."""
        ctx: dict[str, Any] = {}

        # Extract from headers
        for header, key in self.config.extract_headers.items():
            value = request.headers.get(header)
            if value:
                ctx[key] = value

        # Extract from query
        for param, key in self.config.extract_query.items():
            value = request.query_params.get(param)
            if value:
                ctx[key] = value

        # Add request info
        ctx["path"] = request.url.path
        ctx["method"] = request.method
        ctx["client_ip"] = self.get_client_ip(request)

        return ctx

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        ctx = self._extract_context(request)
        token = _context.set(ctx)
        request.state.context = ctx

        try:
            return await call_next(request)
        finally:
            _context.reset(token)
