"""
Client Hints Middleware for FastMVC.

Requests and processes Client Hints for adaptive responses.
"""

import contextlib
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


_hints_ctx: ContextVar[dict[str, Any] | None] = ContextVar("client_hints", default=None)


def get_client_hints() -> dict[str, Any]:
    """Get client hints for current request."""
    return _hints_ctx.get() or {}


@dataclass
class ClientHintsConfig:
    """
    Configuration for client hints middleware.

    Attributes:
        request_hints: Hints to request from clients.
        critical_hints: Critical hints required for response.
    """

    request_hints: list[str] = field(
        default_factory=lambda: [
            "Sec-CH-UA",
            "Sec-CH-UA-Mobile",
            "Sec-CH-UA-Platform",
            "Sec-CH-Prefers-Color-Scheme",
            "Sec-CH-Prefers-Reduced-Motion",
            "Viewport-Width",
            "DPR",
            "Save-Data",
        ]
    )
    critical_hints: list[str] = field(default_factory=list)


class ClientHintsMiddleware(FastMVCMiddleware):
    """
    Middleware for Client Hints.

    Requests Client Hints from browsers and makes
    them available for adaptive responses.

    Example:
        ```python
        from FastMiddleware import ClientHintsMiddleware, get_client_hints

        app.add_middleware(
            ClientHintsMiddleware,
            request_hints=["DPR", "Viewport-Width", "Save-Data"],
        )

        @app.get("/image")
        async def get_image():
            hints = get_client_hints()
            dpr = hints.get("dpr", 1)
            save_data = hints.get("save_data", False)

            return serve_optimized_image(dpr, save_data)
        ```
    """

    def __init__(
        self,
        app,
        config: ClientHintsConfig | None = None,
        request_hints: list[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ClientHintsConfig()

        if request_hints:
            self.config.request_hints = request_hints

    def _parse_hints(self, request: Request) -> dict[str, Any]:
        """Parse client hints from headers."""
        hints: dict[str, Any] = {}

        # Parse numeric hints
        for header in ["DPR", "Viewport-Width", "Device-Memory"]:
            value = request.headers.get(header)
            if value:
                with contextlib.suppress(ValueError):
                    hints[header.lower().replace("-", "_")] = float(value)

        # Parse boolean hints
        save_data = request.headers.get("Save-Data")
        if save_data:
            hints["save_data"] = save_data.lower() == "on"

        # Parse UA hints
        ua = request.headers.get("Sec-CH-UA")
        if ua:
            hints["user_agent"] = ua

        ua_mobile = request.headers.get("Sec-CH-UA-Mobile")
        if ua_mobile:
            hints["is_mobile"] = ua_mobile == "?1"

        ua_platform = request.headers.get("Sec-CH-UA-Platform")
        if ua_platform:
            hints["platform"] = ua_platform.strip('"')

        # Parse preference hints
        color_scheme = request.headers.get("Sec-CH-Prefers-Color-Scheme")
        if color_scheme:
            hints["color_scheme"] = color_scheme.strip('"')

        reduced_motion = request.headers.get("Sec-CH-Prefers-Reduced-Motion")
        if reduced_motion:
            hints["reduced_motion"] = reduced_motion == "reduce"

        return hints

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        hints = self._parse_hints(request)
        token = _hints_ctx.set(hints)
        request.state.client_hints = hints

        try:
            response = await call_next(request)

            # Request hints for future requests
            if self.config.request_hints:
                response.headers["Accept-CH"] = ", ".join(self.config.request_hints)

            if self.config.critical_hints:
                response.headers["Critical-CH"] = ", ".join(self.config.critical_hints)

            return response
        finally:
            _hints_ctx.reset(token)
