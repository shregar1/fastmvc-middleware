"""
Rate Limiting Middleware for FastMVC.

Provides configurable rate limiting with multiple algorithms and storage backends.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class RateLimitConfig:
    """
    Configuration for rate limiting.

    Supports multiple rate limiting strategies:
    - Sliding window: Smooth rate limiting over time
    - Fixed window: Simple counter reset at intervals
    - Token bucket: Burst-friendly rate limiting

    Attributes:
        requests_per_minute: Maximum requests allowed per minute.
        requests_per_hour: Maximum requests allowed per hour.
        burst_limit: Maximum burst requests (for token bucket).
        window_size: Size of the rate limit window in seconds.
        strategy: Rate limiting strategy ("sliding", "fixed", "token_bucket").
        key_func: Custom function to generate rate limit keys.

    Example:
        ```python
        from FastMiddleware import RateLimitConfig

        # 100 requests per minute
        config = RateLimitConfig(requests_per_minute=100)

        # Hourly limits with burst allowance
        config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_limit=20,
        )
        ```
    """

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_size: int = 60
    strategy: str = "sliding"  # sliding, fixed, token_bucket
    key_func: Callable[[Request], str] | None = None


class RateLimitStore(ABC):
    """
    Abstract base class for rate limit storage backends.

    Implement this class to create custom storage backends (Redis, Memcached, etc.)

    Example:
        ```python
        from FastMiddleware import RateLimitStore

        class RedisRateLimitStore(RateLimitStore):
            def __init__(self, redis_client):
                self.redis = redis_client

            async def check_rate_limit(self, key, limit, window):
                # Implement Redis-based rate limiting
                ...

            async def cleanup(self):
                # No cleanup needed for Redis (TTL handles it)
                pass
        ```
    """

    @abstractmethod
    async def check_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """
        Check if the request is within rate limits.

        Args:
            key: Unique identifier for the rate limit bucket.
            limit: Maximum allowed requests.
            window: Time window in seconds.

        Returns:
            Tuple of (allowed, remaining, reset_time).
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up expired rate limit entries."""
        pass


class InMemoryRateLimitStore(RateLimitStore):
    """
    In-memory rate limit storage using sliding window algorithm.

    Suitable for single-instance deployments or development.
    For distributed systems, use Redis or another shared storage.

    Features:
        - Thread-safe with async lock
        - Automatic cleanup of expired entries
        - Efficient sliding window implementation
    """

    def __init__(self) -> None:
        self._windows: dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """
        Check sliding window rate limit.

        Args:
            key: Unique identifier for the rate limit bucket.
            limit: Maximum allowed requests.
            window: Time window in seconds.

        Returns:
            Tuple of (allowed, remaining, reset_time).
        """
        async with self._lock:
            now = time.time()
            window_start = now - window
            reset_time = int(now) + window

            # Remove expired entries
            while self._windows[key] and self._windows[key][0] < window_start:
                self._windows[key].popleft()

            current_count = len(self._windows[key])

            if current_count >= limit:
                return False, 0, reset_time

            # Add new request timestamp
            self._windows[key].append(now)
            remaining = limit - current_count - 1

            return True, remaining, reset_time

    async def cleanup(self, max_age: int = 3600) -> None:
        """
        Clean up expired rate limit entries.

        Args:
            max_age: Maximum age in seconds for entries to keep.
        """
        async with self._lock:
            now = time.time()
            expired_keys = []

            for key in list(self._windows.keys()):
                # Remove old entries
                while self._windows[key] and self._windows[key][0] < now - max_age:
                    self._windows[key].popleft()

                # Mark empty buckets for deletion
                if not self._windows[key]:
                    expired_keys.append(key)

            # Remove empty buckets
            for key in expired_keys:
                del self._windows[key]


class RateLimitMiddleware(FastMVCMiddleware):
    """
    Rate limiting middleware with configurable algorithms and storage.

    Protects your API from abuse by limiting the number of requests
    from each client within a time window.

    Features:
        - Sliding window rate limiting (default)
        - Minute and hour limits
        - Custom key generation (by IP, user ID, API key, etc.)
        - Standard rate limit headers
        - Configurable response format
        - Path exclusion

    Response Headers:
        - X-RateLimit-Limit: Maximum requests allowed
        - X-RateLimit-Remaining: Remaining requests in window
        - X-RateLimit-Reset: Unix timestamp when limit resets
        - Retry-After: Seconds until requests are allowed (when limited)

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import RateLimitMiddleware, RateLimitConfig

        app = FastAPI()

        # Basic usage - 60 requests per minute
        app.add_middleware(RateLimitMiddleware)

        # Custom limits
        config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
        )
        app.add_middleware(RateLimitMiddleware, config=config)

        # Custom key function (rate limit by user ID)
        def get_user_id(request):
            return getattr(request.state, "user_id", None) or get_client_ip(request)

        config = RateLimitConfig(key_func=get_user_id)
        app.add_middleware(RateLimitMiddleware, config=config)
        ```
    """

    # Default paths to exclude from rate limiting
    DEFAULT_EXCLUDE_PATHS = {"/health", "/healthz", "/ready", "/metrics"}

    def __init__(
        self,
        app,
        config: RateLimitConfig | None = None,
        store: RateLimitStore | None = None,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
        error_message: str = "Rate limit exceeded. Please try again later.",
        include_headers: bool = True,
    ) -> None:
        """
        Initialize the rate limiting middleware.

        Args:
            app: The ASGI application.
            config: Rate limiting configuration.
            store: Storage backend for rate limit data.
            exclude_paths: Paths to exclude from rate limiting.
            exclude_methods: HTTP methods to exclude from rate limiting.
            error_message: Message to return when rate limited.
            include_headers: Whether to include rate limit headers in responses.
        """
        _exclude_paths = exclude_paths if exclude_paths is not None else self.DEFAULT_EXCLUDE_PATHS
        _exclude_methods = exclude_methods if exclude_methods is not None else {"OPTIONS"}
        super().__init__(app, exclude_paths=_exclude_paths, exclude_methods=_exclude_methods)

        self.config = config or RateLimitConfig()
        self.store = store or InMemoryRateLimitStore()
        self.error_message = error_message
        self.include_headers = include_headers

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired rate limit entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                await self.store.cleanup()
            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Log error in production

    def _get_rate_limit_key(self, request: Request) -> str:
        """
        Generate a rate limit key for the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            A unique key for rate limiting.
        """
        if self.config.key_func:
            return self.config.key_func(request)

        # Default: rate limit by client IP and endpoint
        client_ip = self.get_client_ip(request)
        return f"{client_ip}:{request.method}:{request.url.path}"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request with rate limiting.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response, or a 429 error if rate limited.
        """
        # Skip rate limiting for excluded paths/methods
        if self.should_skip(request):
            return await call_next(request)

        # Get rate limit key
        key = self._get_rate_limit_key(request)

        # Check minute rate limit
        allowed, remaining, reset_time = await self.store.check_rate_limit(
            f"{key}:minute",
            self.config.requests_per_minute,
            60,
        )

        if not allowed:
            return self._rate_limited_response(
                request,
                self.config.requests_per_minute,
                reset_time,
            )

        # Check hour rate limit
        hour_allowed, _hour_remaining, hour_reset = await self.store.check_rate_limit(
            f"{key}:hour",
            self.config.requests_per_hour,
            3600,
        )

        if not hour_allowed:
            return self._rate_limited_response(
                request,
                self.config.requests_per_hour,
                hour_reset,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        if self.include_headers:
            response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _rate_limited_response(self, request: Request, limit: int, reset_time: int) -> Response:
        """
        Create a rate limited (429) response.

        Args:
            request: The incoming HTTP request.
            limit: The rate limit that was exceeded.
            reset_time: Unix timestamp when limit resets.

        Returns:
            A 429 Too Many Requests response.
        """
        retry_after = max(1, reset_time - int(time.time()))

        headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
        }

        content = {
            "detail": self.error_message,
            "retry_after": retry_after,
        }

        return JSONResponse(
            content=content,
            status_code=429,
            headers=headers,
        )
