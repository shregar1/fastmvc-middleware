"""
GeoIP Middleware for FastMVC.

Provides geolocation information based on client IP.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


# Context variable for geo data
_geo_ctx: ContextVar[dict[str, Any] | None] = ContextVar("geo_data", default=None)


def get_geo_data() -> dict[str, Any] | None:
    """
    Get the current request's geolocation data.

    Returns:
        Geo data dict or None if not available.

    Example:
        ```python
        from FastMiddleware import get_geo_data

        @app.get("/")
        async def root():
            geo = get_geo_data()
            country = geo.get("country") if geo else "Unknown"
        ```
    """
    return _geo_ctx.get()


@dataclass
class GeoIPConfig:
    """
    Configuration for GeoIP middleware.

    Attributes:
        header_prefix: Prefix for geo headers (from CDN/proxy).
        trust_headers: Whether to trust CDN geo headers.
        add_response_headers: Add geo info to response headers.
        country_header: Header name for country.
        city_header: Header name for city.
        region_header: Header name for region.

    Example:
        ```python
        from FastMiddleware import GeoIPConfig

        # Trust Cloudflare headers
        config = GeoIPConfig(
            trust_headers=True,
            country_header="CF-IPCountry",
        )
        ```
    """

    header_prefix: str = "X-Geo-"
    trust_headers: bool = True
    add_response_headers: bool = False

    # Common CDN header mappings
    country_header: str = "CF-IPCountry"  # Cloudflare
    city_header: str = "X-Geo-City"
    region_header: str = "X-Geo-Region"

    # Fallback headers from various CDNs/proxies
    fallback_headers: dict[str, str] = field(
        default_factory=lambda: {
            "country": ["CF-IPCountry", "X-Country-Code", "X-Geo-Country"],
            "city": ["X-Geo-City", "X-City"],
            "region": ["X-Geo-Region", "X-State", "X-Region"],
            "latitude": ["X-Geo-Latitude", "X-Lat"],
            "longitude": ["X-Geo-Longitude", "X-Lon"],
            "timezone": ["X-Geo-Timezone", "X-Timezone"],
        }
    )


class GeoIPMiddleware(FastMVCMiddleware):
    """
    Middleware that extracts geolocation data from request.

    Works with CDN geo headers (Cloudflare, AWS CloudFront, etc.)
    to provide location information.

    Features:
        - Extract geo data from CDN headers
        - Support multiple CDN formats
        - Context variable access
        - Optional response headers

    Example:
        ```python
        from fastapi import FastAPI, Request
        from FastMiddleware import GeoIPMiddleware, get_geo_data

        app = FastAPI()

        app.add_middleware(GeoIPMiddleware)

        @app.get("/")
        async def root(request: Request):
            # Via request state
            country = request.state.geo.get("country")

            # Via context variable
            geo = get_geo_data()
            city = geo.get("city") if geo else None

            return {"country": country, "city": city}
        ```

    Note:
        This middleware does NOT perform GeoIP lookups itself.
        It extracts data from headers set by CDNs/proxies.
        For direct lookups, integrate with MaxMind GeoIP2.
    """

    def __init__(
        self,
        app,
        config: GeoIPConfig | None = None,
        trust_headers: bool | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the GeoIP middleware.

        Args:
            app: The ASGI application.
            config: GeoIP configuration.
            trust_headers: Trust CDN headers (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or GeoIPConfig()

        if trust_headers is not None:
            self.config.trust_headers = trust_headers

    def _extract_geo_data(self, request: Request) -> dict[str, Any]:
        """Extract geo data from request headers."""
        geo = {}

        if not self.config.trust_headers:
            return geo

        # Try fallback headers for each field
        for field_name, headers in self.config.fallback_headers.items():
            for header in headers:
                value = request.headers.get(header)
                if value:
                    geo[field_name] = value
                    break

        return geo

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with geo data extraction.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with geo data handling.
        """
        if self.should_skip(request):
            return await call_next(request)

        # Extract geo data
        geo_data = self._extract_geo_data(request)

        # Set context variable
        token = _geo_ctx.set(geo_data)

        # Store in request state
        request.state.geo = geo_data

        try:
            response = await call_next(request)

            # Optionally add to response headers
            if self.config.add_response_headers and geo_data:
                for key, value in geo_data.items():
                    response.headers[f"{self.config.header_prefix}{key.title()}"] = str(value)

            return response
        finally:
            _geo_ctx.reset(token)
