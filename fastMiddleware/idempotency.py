"""
Idempotency Middleware for FastMVC.

Provides idempotency key support for safe request retries.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class IdempotencyConfig:
    """
    Configuration for idempotency middleware.

    Attributes:
        header_name: Name of the idempotency key header.
        ttl_seconds: Time-to-live for cached responses.
        required_methods: HTTP methods that require idempotency keys.
        require_key: Whether to require idempotency key (vs optional).

    Example:
        ```python
        from FastMiddleware import IdempotencyConfig

        config = IdempotencyConfig(
            header_name="X-Idempotency-Key",
            ttl_seconds=86400,  # 24 hours
            required_methods={"POST", "PUT", "PATCH"},
        )
        ```
    """

    header_name: str = "Idempotency-Key"
    ttl_seconds: int = 86400  # 24 hours
    required_methods: set[str] = None  # type: ignore
    require_key: bool = False

    def __post_init__(self):
        if self.required_methods is None:
            self.required_methods = {"POST", "PUT", "PATCH"}


class IdempotencyStore(ABC):
    """
    Abstract base class for idempotency storage backends.

    Implement this class to create custom storage backends (Redis, etc.)

    Example:
        ```python
        from FastMiddleware import IdempotencyStore

        class RedisIdempotencyStore(IdempotencyStore):
            def __init__(self, redis_client):
                self.redis = redis_client

            async def get(self, key):
                data = await self.redis.get(f"idempotency:{key}")
                return json.loads(data) if data else None

            async def set(self, key, response_data, ttl):
                await self.redis.setex(
                    f"idempotency:{key}",
                    ttl,
                    json.dumps(response_data)
                )
        ```
    """

    @abstractmethod
    async def get(self, key: str) -> dict[str, Any] | None:
        """
        Get cached response for idempotency key.

        Args:
            key: The idempotency key.

        Returns:
            Cached response data or None if not found.
        """
        pass

    @abstractmethod
    async def set(self, key: str, response_data: dict[str, Any], ttl: int) -> None:
        """
        Store response for idempotency key.

        Args:
            key: The idempotency key.
            response_data: Response data to cache.
            ttl: Time-to-live in seconds.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete cached response for idempotency key.

        Args:
            key: The idempotency key to delete.
        """
        pass


class InMemoryIdempotencyStore(IdempotencyStore):
    """
    In-memory idempotency storage.

    Suitable for single-instance deployments or development.
    For distributed systems, use Redis or another shared storage.
    """

    def __init__(self) -> None:
        self._cache: dict[str, tuple[dict[str, Any], float]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get cached response, checking TTL."""
        if key not in self._cache:
            return None

        data, expires_at = self._cache[key]

        if time.time() > expires_at:
            del self._cache[key]
            return None

        return data

    async def set(self, key: str, response_data: dict[str, Any], ttl: int) -> None:
        """Store response with TTL."""
        expires_at = time.time() + ttl
        self._cache[key] = (response_data, expires_at)

    async def delete(self, key: str) -> None:
        """Delete cached response."""
        self._cache.pop(key, None)

    async def cleanup(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired = [k for k, (_, expires) in self._cache.items() if now > expires]
        for key in expired:
            del self._cache[key]


class IdempotencyMiddleware(FastMVCMiddleware):
    """
    Middleware that provides idempotency support for safe request retries.

    Implements the idempotency-key pattern, allowing clients to safely retry
    requests without causing duplicate operations. The middleware caches
    responses and returns the cached response for repeated requests with
    the same idempotency key.

    Features:
        - Configurable idempotency header
        - Pluggable storage backends
        - Automatic response caching
        - TTL for cached responses
        - Request fingerprinting

    Flow:
        1. Client sends request with Idempotency-Key header
        2. Middleware checks if key exists in cache
        3. If cached: return cached response
        4. If not: process request, cache response, return response

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import IdempotencyMiddleware, IdempotencyConfig

        app = FastAPI()

        # Basic usage
        app.add_middleware(IdempotencyMiddleware)

        # Custom configuration
        config = IdempotencyConfig(
            header_name="X-Idempotency-Key",
            ttl_seconds=3600,
            require_key=True,
        )
        app.add_middleware(IdempotencyMiddleware, config=config)
        ```

    Client Usage:
        ```bash
        curl -X POST /api/payments \\
          -H "Idempotency-Key: unique-request-id-123" \\
          -d '{"amount": 100}'
        ```

    Response Headers:
        - X-Idempotent-Replayed: true (if response was cached)
    """

    def __init__(
        self,
        app,
        config: IdempotencyConfig | None = None,
        store: IdempotencyStore | None = None,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the idempotency middleware.

        Args:
            app: The ASGI application.
            config: Idempotency configuration.
            store: Storage backend for cached responses.
            exclude_paths: Paths to exclude from idempotency handling.
            exclude_methods: HTTP methods to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)

        self.config = config or IdempotencyConfig()
        self.store = store or InMemoryIdempotencyStore()

    def _get_idempotency_key(self, request: Request) -> str | None:
        """Extract idempotency key from request."""
        return request.headers.get(self.config.header_name)

    def _should_process(self, request: Request) -> bool:
        """Check if request should be processed for idempotency."""
        return request.method in self.config.required_methods

    async def _cache_response(
        self,
        key: str,
        response: Response,
        body: bytes,
    ) -> None:
        """Cache response for idempotency key."""
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body.decode("utf-8") if body else "",
            "media_type": response.media_type,
        }

        await self.store.set(key, response_data, self.config.ttl_seconds)

    def _build_response(self, cached: dict[str, Any], replayed: bool = True) -> Response:
        """Build response from cached data."""
        headers = dict(cached.get("headers", {}))

        if replayed:
            headers["X-Idempotent-Replayed"] = "true"

        return Response(
            content=cached.get("body", ""),
            status_code=cached.get("status_code", 200),
            headers=headers,
            media_type=cached.get("media_type"),
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with idempotency handling.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response (cached or fresh).
        """
        # Skip if not a method that needs idempotency
        if not self._should_process(request):
            return await call_next(request)

        # Skip excluded paths
        if self.should_skip(request):
            return await call_next(request)

        # Get idempotency key
        idempotency_key = self._get_idempotency_key(request)

        # If no key and key is required, return error
        if not idempotency_key:
            if self.config.require_key:
                return JSONResponse(
                    content={
                        "error": True,
                        "message": f"Missing {self.config.header_name} header",
                    },
                    status_code=400,
                )
            # If key not required, just process normally
            return await call_next(request)

        # Check for cached response
        cached = await self.store.get(idempotency_key)
        if cached:
            return self._build_response(cached, replayed=True)

        # Process the request
        response = await call_next(request)

        # Cache successful responses
        if 200 <= response.status_code < 300:
            # Read body for caching
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            await self._cache_response(idempotency_key, response, body)

            # Return new response with body
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response
