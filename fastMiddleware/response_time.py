"""
Response Time SLA Middleware for FastMVC.

Monitors and enforces response time SLAs.
"""

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ResponseTimeSLA:
    """Response time SLA definition."""

    path_pattern: str
    target_ms: float
    warning_ms: float
    critical_ms: float


@dataclass
class ResponseTimeConfig:
    """
    Configuration for response time middleware.

    Attributes:
        default_target_ms: Default target response time.
        default_warning_ms: Default warning threshold.
        default_critical_ms: Default critical threshold.
        slas: Path-specific SLAs.
        log_slow: Log slow responses.
        add_header: Add timing header to response.
    """

    default_target_ms: float = 100.0
    default_warning_ms: float = 500.0
    default_critical_ms: float = 1000.0
    slas: list[ResponseTimeSLA] = field(default_factory=list)
    log_slow: bool = True
    add_header: bool = True
    header_name: str = "X-Response-Time"
    logger_name: str = "response_time"


class ResponseTimeMiddleware(FastMVCMiddleware):
    """
    Middleware that monitors response time SLAs.

    Tracks response times and logs warnings when
    SLA thresholds are exceeded.

    Example:
        ```python
        from FastMiddleware import ResponseTimeMiddleware, ResponseTimeSLA

        app.add_middleware(
            ResponseTimeMiddleware,
            slas=[
                ResponseTimeSLA("/api/health", target_ms=50, warning_ms=100, critical_ms=200),
                ResponseTimeSLA("/api/search", target_ms=500, warning_ms=1000, critical_ms=2000),
            ],
        )
        ```
    """

    def __init__(
        self,
        app,
        config: ResponseTimeConfig | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ResponseTimeConfig()
        self._logger = logging.getLogger(self.config.logger_name)

        # Stats tracking
        self._stats: dict[str, dict] = {}

    def _get_sla(self, path: str) -> tuple[float, float, float]:
        """Get SLA thresholds for path."""
        for sla in self.config.slas:
            if path.startswith(sla.path_pattern):
                return sla.target_ms, sla.warning_ms, sla.critical_ms

        return (
            self.config.default_target_ms,
            self.config.default_warning_ms,
            self.config.default_critical_ms,
        )

    def _update_stats(self, path: str, duration_ms: float) -> None:
        """Update stats for path."""
        if path not in self._stats:
            self._stats[path] = {
                "count": 0,
                "total_ms": 0.0,
                "max_ms": 0.0,
                "min_ms": float("inf"),
                "warnings": 0,
                "critical": 0,
            }

        stats = self._stats[path]
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["max_ms"] = max(stats["max_ms"], duration_ms)
        stats["min_ms"] = min(stats["min_ms"], duration_ms)

    def get_stats(self) -> dict[str, dict]:
        """Get response time statistics."""
        result = {}
        for path, stats in self._stats.items():
            result[path] = {
                **stats,
                "avg_ms": stats["total_ms"] / stats["count"] if stats["count"] > 0 else 0,
            }
        return result

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Get SLA thresholds
        _target, warning, critical = self._get_sla(request.url.path)

        # Update stats
        self._update_stats(request.url.path, duration_ms)

        # Check thresholds
        if self.config.log_slow:
            if duration_ms >= critical:
                self._logger.error(
                    f"CRITICAL: {request.method} {request.url.path} took {duration_ms:.2f}ms "
                    f"(critical: {critical}ms)"
                )
                self._stats[request.url.path]["critical"] += 1
            elif duration_ms >= warning:
                self._logger.warning(
                    f"WARNING: {request.method} {request.url.path} took {duration_ms:.2f}ms "
                    f"(warning: {warning}ms)"
                )
                self._stats[request.url.path]["warnings"] += 1

        # Add header
        if self.config.add_header:
            response.headers[self.config.header_name] = f"{duration_ms:.2f}ms"

        return response
