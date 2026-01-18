"""
Request ID Propagation Middleware for FastMVC.

Propagates request IDs across service boundaries.
"""

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


_request_ids_ctx: ContextVar[list[str] | None] = ContextVar("request_ids", default=None)


def get_request_ids() -> list[str]:
    """Get propagated request IDs."""
    return _request_ids_ctx.get() or []


def get_trace_header() -> str:
    """Get trace header value for outgoing requests."""
    ids = _request_ids_ctx.get()
    return ",".join(ids) if ids else ""


@dataclass
class RequestIDPropagationConfig:
    """
    Configuration for request ID propagation middleware.

    Attributes:
        headers: Headers to check for request IDs.
        response_header: Header for response.
        generate_if_missing: Generate ID if none found.
        max_chain: Maximum chain length to preserve.
    """

    headers: list[str] = field(
        default_factory=lambda: [
            "X-Request-ID",
            "X-Correlation-ID",
            "X-Trace-ID",
        ]
    )
    response_header: str = "X-Request-ID"
    generate_if_missing: bool = True
    max_chain: int = 10


class RequestIDPropagationMiddleware(FastMVCMiddleware):
    """
    Middleware that propagates request IDs across services.

    Collects request IDs from multiple sources and maintains
    the chain for distributed tracing.

    Example:
        ```python
        from FastMiddleware import RequestIDPropagationMiddleware, get_request_ids

        app.add_middleware(RequestIDPropagationMiddleware)

        @app.get("/")
        async def handler():
            ids = get_request_ids()
            # Forward ids to downstream services
            return {"request_ids": ids}
        ```
    """

    def __init__(
        self,
        app,
        config: RequestIDPropagationConfig | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RequestIDPropagationConfig()

    def _extract_ids(self, request: Request) -> list[str]:
        """Extract request IDs from headers."""
        ids = []

        for header in self.config.headers:
            value = request.headers.get(header)
            if value:
                # Handle comma-separated IDs
                for raw_id_val in value.split(","):
                    id_val = raw_id_val.strip()
                    if id_val and id_val not in ids:
                        ids.append(id_val)

        return ids[: self.config.max_chain]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        ids = self._extract_ids(request)

        # Generate new ID for this service
        if self.config.generate_if_missing or ids:
            new_id = str(uuid.uuid4())
            ids.append(new_id)
            ids = ids[-self.config.max_chain :]  # Limit chain length

        token = _request_ids_ctx.set(ids)
        request.state.request_ids = ids

        try:
            response = await call_next(request)

            # Add current request ID to response
            if ids:
                response.headers[self.config.response_header] = ids[-1]
                if len(ids) > 1:
                    response.headers["X-Request-Chain"] = ",".join(ids)

            return response
        finally:
            _request_ids_ctx.reset(token)
