"""
Request Context Middleware for FastMVC.

Provides request context management with context variables for async access.
"""

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from datetime import datetime
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


# Context variables for async-safe access to request data
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_request_context_var: ContextVar[dict[str, Any] | None] = ContextVar(
    "request_context", default=None
)


def get_request_id() -> str | None:
    """
    Get the current request ID from context.

    This function can be called from anywhere in your async code
    to access the current request's ID.

    Returns:
        The current request ID, or None if not in a request context.

    Example:
        ```python
        from FastMiddleware import get_request_id

        async def my_function():
            request_id = get_request_id()
            logger.info(f"Processing in request {request_id}")
        ```
    """
    return _request_id_var.get()


def get_request_context() -> dict[str, Any]:
    """
    Get the current request context from context variables.

    Returns a dictionary with request metadata that can be accessed
    from anywhere in your async code.

    Returns:
        Dictionary with request context data.

    Example:
        ```python
        from FastMiddleware import get_request_context

        async def my_function():
            ctx = get_request_context()
            client_ip = ctx.get("client_ip")
            start_time = ctx.get("start_time")
        ```
    """
    ctx = _request_context_var.get()
    if ctx is None:
        ctx = {}
        _request_context_var.set(ctx)
    return ctx


class RequestContextMiddleware(FastMVCMiddleware):
    """
    Middleware that manages request context using context variables.

    This middleware provides a way to access request information
    from anywhere in your async code without passing the request
    object through every function call.

    Features:
        - Unique request ID generation
        - Request timing (start time, process time)
        - Client IP tracking
        - Custom context data
        - Context variable access from any async code

    Context Data Available:
        - request_id: Unique identifier for the request
        - start_time: When the request started (datetime)
        - client_ip: Client IP address
        - method: HTTP method
        - path: Request path

    Response Headers:
        - X-Request-ID: The unique request identifier
        - X-Process-Time: Time taken to process the request

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import RequestContextMiddleware, get_request_id

        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)

        @app.get("/")
        async def root():
            # Access request ID from anywhere
            request_id = get_request_id()
            return {"request_id": request_id}

        # In a service or utility function
        async def log_something():
            from FastMiddleware import get_request_context
            ctx = get_request_context()
            logger.info(f"Request {ctx['request_id']} from {ctx['client_ip']}")
        ```
    """

    def __init__(
        self,
        app,
        id_generator: Callable[[], str] | None = None,
        request_id_header: str = "X-Request-ID",
        process_time_header: str = "X-Process-Time",
        trust_incoming_id: bool = True,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the request context middleware.

        Args:
            app: The ASGI application.
            id_generator: Custom function to generate request IDs.
            request_id_header: Header name for request ID.
            process_time_header: Header name for process time.
            trust_incoming_id: Whether to trust incoming request IDs.
            exclude_paths: Paths to exclude from context tracking.
            exclude_methods: HTTP methods to exclude from context tracking.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)
        self.id_generator = id_generator or (lambda: str(uuid.uuid4()))
        self.request_id_header = request_id_header
        self.process_time_header = process_time_header
        self.trust_incoming_id = trust_incoming_id

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request with context management.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response with context headers.
        """
        # Generate or get request ID
        request_id = None
        if self.trust_incoming_id:
            request_id = request.headers.get(self.request_id_header)

        if not request_id:
            request_id = self.id_generator()

        # Record start time
        start_time = datetime.now()

        # Build context
        context = {
            "request_id": request_id,
            "start_time": start_time,
            "client_ip": self.get_client_ip(request),
            "method": request.method,
            "path": request.url.path,
        }

        # Set context variables
        request_id_token = _request_id_var.set(request_id)
        context_token = _request_context_var.set(context)

        try:
            # Store in request.state for direct access
            request.state.request_id = request_id
            request.state.start_time = start_time
            request.state.context = context

            # Process request
            response = await call_next(request)

            # Calculate process time
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds() * 1000

            # Add response headers
            response.headers[self.request_id_header] = request_id
            response.headers[self.process_time_header] = f"{process_time:.2f}ms"

            return response
        finally:
            # Reset context variables
            _request_id_var.reset(request_id_token)
            _request_context_var.reset(context_token)
