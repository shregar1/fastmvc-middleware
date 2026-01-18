"""
Trailing Slash Middleware for FastMVC.

Normalizes URL paths by adding or removing trailing slashes.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from FastMiddleware.base import FastMVCMiddleware


class SlashAction(Enum):
    """Action to take with trailing slashes."""

    ADD = "add"
    REMOVE = "remove"
    NONE = "none"


@dataclass
class TrailingSlashConfig:
    """
    Configuration for trailing slash middleware.

    Attributes:
        action: What to do with trailing slashes (add/remove/none).
        redirect: Whether to redirect or rewrite silently.
        redirect_code: HTTP status code for redirect.
        exclude_extensions: File extensions to exclude.

    Example:
        ```python
        from FastMiddleware import TrailingSlashConfig, SlashAction

        # Remove trailing slashes
        config = TrailingSlashConfig(action=SlashAction.REMOVE)

        # Add trailing slashes
        config = TrailingSlashConfig(action=SlashAction.ADD)
        ```
    """

    action: SlashAction = SlashAction.REMOVE
    redirect: bool = True
    redirect_code: int = 308
    exclude_extensions: set[str] = None  # type: ignore

    def __post_init__(self):
        if self.exclude_extensions is None:
            self.exclude_extensions = {
                ".html",
                ".htm",
                ".json",
                ".xml",
                ".txt",
                ".css",
                ".js",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".svg",
                ".ico",
                ".webp",
                ".pdf",
                ".zip",
                ".tar",
                ".gz",
            }


class TrailingSlashMiddleware(FastMVCMiddleware):
    """
    Middleware that normalizes trailing slashes in URLs.

    Ensures consistent URL structure by either adding or removing
    trailing slashes from all paths.

    Features:
        - Add or remove trailing slashes
        - Redirect or silent rewrite
        - Exclude file extensions
        - Configurable redirect codes

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import TrailingSlashMiddleware, SlashAction

        app = FastAPI()

        # Remove trailing slashes (recommended)
        app.add_middleware(TrailingSlashMiddleware)

        # Add trailing slashes
        app.add_middleware(
            TrailingSlashMiddleware,
            action=SlashAction.ADD,
        )
        ```

    SEO Note:
        Consistent trailing slashes help avoid duplicate content issues
        in search engine indexing.
    """

    def __init__(
        self,
        app,
        config: TrailingSlashConfig | None = None,
        action: SlashAction | None = None,
        redirect: bool | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the trailing slash middleware.

        Args:
            app: The ASGI application.
            config: Trailing slash configuration.
            action: Slash action (overrides config).
            redirect: Whether to redirect (overrides config).
            exclude_paths: Paths to exclude from normalization.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or TrailingSlashConfig()

        if action is not None:
            self.config.action = action
        if redirect is not None:
            self.config.redirect = redirect

    def _has_file_extension(self, path: str) -> bool:
        """Check if path ends with a file extension."""
        return any(path.endswith(ext) for ext in self.config.exclude_extensions)

    def _normalize_path(self, path: str) -> str | None:
        """Normalize path and return new path if changed."""
        # Skip root path
        if path == "/":
            return None

        # Skip file extensions
        if self._has_file_extension(path):
            return None

        if self.config.action == SlashAction.REMOVE:
            if path.endswith("/"):
                return path.rstrip("/")
        elif self.config.action == SlashAction.ADD and not path.endswith("/"):
            return path + "/"

        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and normalize trailing slashes.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            Response with normalized URL.
        """
        if self.should_skip(request):
            return await call_next(request)

        if self.config.action == SlashAction.NONE:
            return await call_next(request)

        path = request.url.path
        new_path = self._normalize_path(path)

        if new_path is not None:
            if self.config.redirect:
                # Redirect to normalized URL
                url = request.url.replace(path=new_path)
                return RedirectResponse(
                    url=str(url),
                    status_code=self.config.redirect_code,
                )
            else:
                # Silently rewrite (modify scope)
                request.scope["path"] = new_path

        return await call_next(request)
