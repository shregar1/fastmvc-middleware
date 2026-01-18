"""
Base middleware class for FastMVC middlewares.

Provides a consistent interface and utilities for all middleware implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class FastMVCMiddleware(BaseHTTPMiddleware, ABC):
    """
    Abstract base class for FastMVC middlewares.

    Provides a consistent interface for all middleware implementations
    with support for path exclusion and common utilities.

    Attributes:
        exclude_paths: Set of paths to exclude from middleware processing.
        exclude_methods: Set of HTTP methods to exclude from middleware processing.

    Example:
        ```python
        from FastMiddleware import FastMVCMiddleware

        class MyMiddleware(FastMVCMiddleware):
            async def dispatch(self, request, call_next):
                if self.should_skip(request):
                    return await call_next(request)
                # Your middleware logic here
                return await call_next(request)
        ```
    """

    def __init__(
        self,
        app,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the middleware.

        Args:
            app: The ASGI application.
            exclude_paths: Set of URL paths to skip middleware processing.
            exclude_methods: Set of HTTP methods to skip middleware processing.
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or set()
        self.exclude_methods = exclude_methods or set()

    def should_skip(self, request: Request) -> bool:
        """
        Check if the request should skip middleware processing.

        Args:
            request: The incoming HTTP request.

        Returns:
            True if the request should skip processing, False otherwise.
        """
        if request.url.path in self.exclude_paths:
            return True
        return request.method in self.exclude_methods

    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request, handling proxies.

        Args:
            request: The incoming HTTP request.

        Returns:
            The client IP address as a string.
        """
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client connection
        return request.client.host if request.client else "unknown"

    @abstractmethod
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and return a response.

        This method must be implemented by all middleware subclasses.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response.
        """
        pass
