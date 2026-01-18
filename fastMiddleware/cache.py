"""
Caching Middleware for FastMVC.

Provides HTTP caching with ETags and Cache-Control headers.
"""

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class CacheConfig:
    """
    Configuration for caching middleware.

    Attributes:
        default_max_age: Default Cache-Control max-age in seconds.
        enable_etag: Generate and validate ETags.
        enable_last_modified: Include Last-Modified headers.
        cacheable_methods: HTTP methods that can be cached.
        cacheable_status_codes: Status codes that can be cached.
        vary_headers: Headers to include in Vary response.
        private: Set Cache-Control to private (vs public).
        path_rules: Path-specific cache rules.

    Example:
        ```python
        from FastMiddleware import CacheConfig

        config = CacheConfig(
            default_max_age=3600,
            enable_etag=True,
            path_rules={
                "/api/static": {"max_age": 86400},
                "/api/user": {"private": True, "max_age": 0},
            },
        )
        ```
    """

    default_max_age: int = 0
    enable_etag: bool = True
    enable_last_modified: bool = False
    cacheable_methods: set[str] = field(default_factory=lambda: {"GET", "HEAD"})
    cacheable_status_codes: set[int] = field(default_factory=lambda: {200, 301, 304})
    vary_headers: tuple[str, ...] = ("Accept", "Accept-Encoding")
    private: bool = False
    no_store: bool = False

    # Path-specific rules: {path_prefix: {max_age, private, no_cache, no_store}}
    path_rules: dict[str, dict[str, Any]] = field(default_factory=dict)


class CacheMiddleware(FastMVCMiddleware):
    """
    Middleware that adds HTTP caching headers and ETag support.

    Implements proper HTTP caching semantics including ETags,
    Cache-Control headers, and conditional request handling.

    Features:
        - ETag generation and validation
        - Cache-Control header management
        - Conditional GET (If-None-Match) support
        - Path-specific cache rules
        - Vary header management

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import CacheMiddleware, CacheConfig

        app = FastAPI()

        # Basic usage with ETags
        app.add_middleware(CacheMiddleware)

        # Custom configuration
        config = CacheConfig(
            default_max_age=3600,
            enable_etag=True,
            path_rules={
                "/api/static": {"max_age": 86400, "public": True},
                "/api/private": {"max_age": 0, "no_store": True},
            },
        )
        app.add_middleware(CacheMiddleware, config=config)
        ```

    Response Headers:
        - ETag: "abc123..."
        - Cache-Control: public, max-age=3600
        - Vary: Accept, Accept-Encoding

    Conditional Requests:
        Clients can send If-None-Match header with ETag to receive
        304 Not Modified response if content hasn't changed.
    """

    def __init__(
        self,
        app,
        config: CacheConfig | None = None,
        default_max_age: int | None = None,
        enable_etag: bool | None = None,
        private: bool | None = None,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the cache middleware.

        Args:
            app: The ASGI application.
            config: Cache configuration.
            default_max_age: Default max-age (overrides config).
            enable_etag: Enable ETag generation (overrides config).
            private: Set private caching (overrides config).
            exclude_paths: Paths to exclude from caching.
            exclude_methods: HTTP methods to exclude from caching.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)

        self.config = config or CacheConfig()

        if default_max_age is not None:
            self.config.default_max_age = default_max_age
        if enable_etag is not None:
            self.config.enable_etag = enable_etag
        if private is not None:
            self.config.private = private

    def _generate_etag(self, body: bytes) -> str:
        """Generate ETag from response body."""
        return f'"{hashlib.md5(body).hexdigest()}"'

    def _get_path_rules(self, path: str) -> dict[str, Any]:
        """Get cache rules for a specific path."""
        for prefix, rules in self.config.path_rules.items():
            if path.startswith(prefix):
                return rules
        return {}

    def _build_cache_control(self, path: str) -> str:
        """Build Cache-Control header value."""
        path_rules = self._get_path_rules(path)

        parts = []

        # Private vs public
        if path_rules.get("private", self.config.private):
            parts.append("private")
        else:
            parts.append("public")

        # No-store
        if path_rules.get("no_store", self.config.no_store):
            parts.append("no-store")
            return ", ".join(parts)

        # No-cache
        if path_rules.get("no_cache", False):
            parts.append("no-cache")

        # Max-age
        max_age = path_rules.get("max_age", self.config.default_max_age)
        parts.append(f"max-age={max_age}")

        # Must-revalidate
        if path_rules.get("must_revalidate", False):
            parts.append("must-revalidate")

        return ", ".join(parts)

    def _should_cache(self, request: Request, response: Response) -> bool:
        """Determine if response should be cached."""
        # Check method
        if request.method not in self.config.cacheable_methods:
            return False

        # Check status code
        if response.status_code not in self.config.cacheable_status_codes:
            return False

        # Check for no-store in path rules
        path_rules = self._get_path_rules(request.url.path)
        return not path_rules.get("no_store", self.config.no_store)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with caching support.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response with cache headers.
        """
        # Skip excluded paths/methods
        if self.should_skip(request):
            return await call_next(request)

        # Get If-None-Match header for conditional requests
        if_none_match = request.headers.get("If-None-Match")

        # Process the request
        response = await call_next(request)

        # Skip non-cacheable responses
        if not self._should_cache(request, response):
            return response

        # Read response body for ETag generation
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Generate ETag
        etag = None
        if self.config.enable_etag and body:
            etag = self._generate_etag(body)

            # Check for conditional request (304 Not Modified)
            if if_none_match and if_none_match == etag:
                return Response(
                    status_code=304,
                    headers={
                        "ETag": etag,
                        "Cache-Control": self._build_cache_control(request.url.path),
                    },
                )

        # Build response with cache headers
        headers = dict(response.headers)

        # Add Cache-Control
        headers["Cache-Control"] = self._build_cache_control(request.url.path)

        # Add ETag
        if etag:
            headers["ETag"] = etag

        # Add Vary headers
        if self.config.vary_headers:
            headers["Vary"] = ", ".join(self.config.vary_headers)

        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
