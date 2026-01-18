"""
Content Negotiation Middleware for FastMVC.

Handles Accept header parsing and content type negotiation.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


_content_type_ctx: ContextVar[str | None] = ContextVar("negotiated_type", default=None)


def get_negotiated_type() -> str | None:
    """Get the negotiated content type."""
    return _content_type_ctx.get()


@dataclass
class ContentNegotiationConfig:
    """
    Configuration for content negotiation middleware.

    Attributes:
        supported_types: List of supported content types in preference order.
        default_type: Default type if negotiation fails.
        strict: Return 406 if no acceptable type found.
    """

    supported_types: list[str] = field(
        default_factory=lambda: [
            "application/json",
            "application/xml",
            "text/html",
            "text/plain",
        ]
    )
    default_type: str = "application/json"
    strict: bool = False


class ContentNegotiationMiddleware(FastMVCMiddleware):
    """
    Middleware that handles content type negotiation.

    Parses Accept headers and determines the best content type
    to return based on client preferences and server capabilities.

    Example:
        ```python
        from FastMiddleware import ContentNegotiationMiddleware, get_negotiated_type

        app.add_middleware(
            ContentNegotiationMiddleware,
            supported_types=["application/json", "application/xml"],
        )

        @app.get("/data")
        async def get_data():
            content_type = get_negotiated_type()
            if content_type == "application/xml":
                return xml_response()
            return json_response()
        ```
    """

    def __init__(
        self,
        app,
        config: ContentNegotiationConfig | None = None,
        supported_types: list[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ContentNegotiationConfig()

        if supported_types:
            self.config.supported_types = supported_types

    def _parse_accept(self, accept: str) -> list[tuple[str, float]]:
        """Parse Accept header into list of (type, quality) tuples."""
        if not accept:
            return []

        types = []
        for raw_part in accept.split(","):
            part = raw_part.strip()
            if not part:
                continue

            if ";q=" in part:
                mime, q = part.split(";q=")
                try:
                    quality = float(q.strip())
                except ValueError:
                    quality = 1.0
            else:
                mime = part
                quality = 1.0

            types.append((mime.strip(), quality))

        return sorted(types, key=lambda x: x[1], reverse=True)

    def _matches(self, requested: str, supported: str) -> bool:
        """Check if requested type matches supported type."""
        if requested == "*/*":
            return True

        if requested == supported:
            return True

        # Handle wildcards like text/*
        if requested.endswith("/*"):
            prefix = requested[:-1]
            return supported.startswith(prefix)

        return False

    def _negotiate(self, accept: str) -> str | None:
        """Negotiate best content type."""
        requested_types = self._parse_accept(accept)

        if not requested_types:
            return self.config.default_type

        for requested, _ in requested_types:
            for supported in self.config.supported_types:
                if self._matches(requested, supported):
                    return supported

        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        accept = request.headers.get("Accept", "*/*")
        negotiated = self._negotiate(accept)

        if negotiated is None:
            if self.config.strict:
                return JSONResponse(
                    status_code=406,
                    content={
                        "error": True,
                        "message": "Not Acceptable",
                        "supported_types": self.config.supported_types,
                    },
                )
            negotiated = self.config.default_type

        token = _content_type_ctx.set(negotiated)
        request.state.negotiated_type = negotiated

        try:
            response = await call_next(request)
            response.headers["Vary"] = "Accept"
            return response
        finally:
            _content_type_ctx.reset(token)
