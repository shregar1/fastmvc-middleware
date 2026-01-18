"""
API Versioning Middleware for FastMVC.

Provides API version detection and routing.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


# Context variable for API version
_api_version_ctx: ContextVar[str | None] = ContextVar("api_version", default=None)


def get_api_version() -> str | None:
    """
    Get the current API version.

    Returns:
        The API version string or None if not set.

    Example:
        ```python
        from FastMiddleware import get_api_version

        @app.get("/users")
        async def get_users():
            version = get_api_version()
            if version == "v2":
                return {"users": [...], "meta": {...}}
            return {"users": [...]}
        ```
    """
    return _api_version_ctx.get()


class VersionLocation(Enum):
    """Where to look for API version."""

    HEADER = "header"
    PATH = "path"
    QUERY = "query"
    ACCEPT = "accept"


@dataclass
class VersioningConfig:
    """
    Configuration for API versioning middleware.

    Attributes:
        location: Where to extract version from.
        header_name: Header name for version.
        query_param: Query parameter name for version.
        path_prefix: Path prefix pattern (e.g., "/v{version}").
        default_version: Default version if not specified.
        supported_versions: Set of supported versions.
        deprecated_versions: Versions that are deprecated.

    Example:
        ```python
        from FastMiddleware import VersioningConfig, VersionLocation

        config = VersioningConfig(
            location=VersionLocation.HEADER,
            header_name="X-API-Version",
            supported_versions={"v1", "v2", "v3"},
            deprecated_versions={"v1"},
            default_version="v3",
        )
        ```
    """

    location: VersionLocation = VersionLocation.HEADER
    header_name: str = "X-API-Version"
    query_param: str = "version"
    path_prefix: str = "/v"
    default_version: str = "v1"
    supported_versions: set[str] = field(default_factory=lambda: {"v1"})
    deprecated_versions: set[str] = field(default_factory=set)
    strict: bool = False  # Reject unsupported versions


class VersioningMiddleware(FastMVCMiddleware):
    """
    Middleware that detects and manages API versions.

    Extracts API version from headers, path, query params, or Accept header
    and makes it available throughout the request lifecycle.

    Features:
        - Multiple version sources (header, path, query, Accept)
        - Version validation
        - Deprecation warnings
        - Context variable access

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import VersioningMiddleware, VersionLocation, get_api_version

        app = FastAPI()

        # Header-based versioning
        app.add_middleware(
            VersioningMiddleware,
            location=VersionLocation.HEADER,
            supported_versions={"v1", "v2"},
        )

        # Path-based versioning (e.g., /v1/users)
        app.add_middleware(
            VersioningMiddleware,
            location=VersionLocation.PATH,
        )

        @app.get("/users")
        async def get_users():
            version = get_api_version()
            # Return version-specific response
        ```
    """

    def __init__(
        self,
        app,
        config: VersioningConfig | None = None,
        location: VersionLocation | None = None,
        supported_versions: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the versioning middleware.

        Args:
            app: The ASGI application.
            config: Versioning configuration.
            location: Version location (overrides config).
            supported_versions: Supported versions (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or VersioningConfig()

        if location is not None:
            self.config.location = location
        if supported_versions is not None:
            self.config.supported_versions = supported_versions

    def _extract_from_header(self, request: Request) -> str | None:
        """Extract version from header."""
        return request.headers.get(self.config.header_name)

    def _extract_from_query(self, request: Request) -> str | None:
        """Extract version from query parameter."""
        return request.query_params.get(self.config.query_param)

    def _extract_from_path(self, request: Request) -> str | None:
        """Extract version from path prefix."""
        path = request.url.path
        prefix = self.config.path_prefix

        if path.startswith(prefix):
            # Extract version segment
            rest = path[len(prefix) :]
            version_end = rest.find("/")
            version = rest if version_end == -1 else rest[:version_end]

            if version:
                return f"v{version}" if not version.startswith("v") else version

        return None

    def _extract_from_accept(self, request: Request) -> str | None:
        """Extract version from Accept header (media type versioning)."""
        accept = request.headers.get("Accept", "")
        # Look for version in accept header: application/vnd.api.v1+json
        if "vnd." in accept:
            for raw_part in accept.split(";"):
                part = raw_part.strip()
                if ".v" in part:
                    # Extract version
                    import re

                    match = re.search(r"\.v(\d+)", part)
                    if match:
                        return f"v{match.group(1)}"
        return None

    def _extract_version(self, request: Request) -> str | None:
        """Extract version based on configured location."""
        if self.config.location == VersionLocation.HEADER:
            return self._extract_from_header(request)
        elif self.config.location == VersionLocation.QUERY:
            return self._extract_from_query(request)
        elif self.config.location == VersionLocation.PATH:
            return self._extract_from_path(request)
        elif self.config.location == VersionLocation.ACCEPT:
            return self._extract_from_accept(request)
        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with version detection.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with version handling.
        """
        if self.should_skip(request):
            return await call_next(request)

        # Extract version
        version = self._extract_version(request) or self.config.default_version

        # Validate version
        if self.config.strict and version not in self.config.supported_versions:
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": f"Unsupported API version: {version}",
                    "supported_versions": list(self.config.supported_versions),
                },
            )

        # Set context variable
        token = _api_version_ctx.set(version)

        # Store in request state
        request.state.api_version = version

        try:
            response = await call_next(request)

            # Add version headers
            response.headers["X-API-Version"] = version

            # Add deprecation warning
            if version in self.config.deprecated_versions:
                response.headers["X-API-Deprecated"] = "true"
                response.headers["Warning"] = f'299 - "API version {version} is deprecated"'

            return response
        finally:
            _api_version_ctx.reset(token)
