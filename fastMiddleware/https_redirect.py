"""
HTTPS Redirect Middleware for FastMVC.

Forces HTTPS connections by redirecting HTTP requests.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class HTTPSRedirectConfig:
    """
    Configuration for HTTPS redirect middleware.

    Attributes:
        redirect_code: HTTP status code for redirect (301 or 308).
        host: Optional host to redirect to.
        exclude_hosts: Hosts to exclude from redirect (e.g., localhost).
        trust_proxy: Trust X-Forwarded-Proto header.

    Example:
        ```python
        from FastMiddleware import HTTPSRedirectConfig

        config = HTTPSRedirectConfig(
            redirect_code=301,
            exclude_hosts={"localhost", "127.0.0.1"},
        )
        ```
    """

    redirect_code: int = 308
    host: str | None = None
    exclude_hosts: set[str] = field(default_factory=lambda: {"localhost", "127.0.0.1"})
    trust_proxy: bool = True


class HTTPSRedirectMiddleware(FastMVCMiddleware):
    """
    Middleware that redirects HTTP requests to HTTPS.

    Essential for production deployments to ensure all traffic
    is encrypted.

    Features:
        - Automatic HTTP to HTTPS redirect
        - Configurable redirect status code
        - Exclude localhost/development hosts
        - Proxy-aware (X-Forwarded-Proto)

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import HTTPSRedirectMiddleware

        app = FastAPI()

        # Basic usage
        app.add_middleware(HTTPSRedirectMiddleware)

        # With configuration
        app.add_middleware(
            HTTPSRedirectMiddleware,
            redirect_code=301,
            exclude_hosts={"localhost"},
        )
        ```

    Note:
        In development, localhost is excluded by default.
        Always enable in production!
    """

    def __init__(
        self,
        app,
        config: HTTPSRedirectConfig | None = None,
        redirect_code: int | None = None,
        exclude_hosts: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the HTTPS redirect middleware.

        Args:
            app: The ASGI application.
            config: HTTPS redirect configuration.
            redirect_code: HTTP status code for redirect.
            exclude_hosts: Hosts to exclude from redirect.
            exclude_paths: Paths to exclude from redirect.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or HTTPSRedirectConfig()

        if redirect_code is not None:
            self.config.redirect_code = redirect_code
        if exclude_hosts is not None:
            self.config.exclude_hosts = exclude_hosts

    def _is_https(self, request: Request) -> bool:
        """Check if request is already HTTPS."""
        # Check direct scheme
        if request.url.scheme == "https":
            return True

        # Check proxy header
        if self.config.trust_proxy:
            proto = request.headers.get("X-Forwarded-Proto", "")
            if proto.lower() == "https":
                return True

        return False

    def _should_redirect(self, request: Request) -> bool:
        """Check if request should be redirected."""
        # Already HTTPS
        if self._is_https(request):
            return False

        # Excluded host
        host = request.url.hostname or ""
        return host not in self.config.exclude_hosts

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and redirect to HTTPS if needed.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            Redirect response or original response.
        """
        if self.should_skip(request):
            return await call_next(request)

        if self._should_redirect(request):
            # Build HTTPS URL
            url = request.url.replace(scheme="https")
            if self.config.host:
                url = url.replace(netloc=self.config.host)

            return RedirectResponse(
                url=str(url),
                status_code=self.config.redirect_code,
            )

        return await call_next(request)
