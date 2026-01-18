"""
Locale/i18n Middleware for FastMVC.

Provides language detection and localization support.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


# Context variable for locale
_locale_ctx: ContextVar[str | None] = ContextVar("locale", default=None)


def get_locale() -> str | None:
    """
    Get the current request's locale.

    Returns:
        Locale string (e.g., 'en-US') or None.

    Example:
        ```python
        from FastMiddleware import get_locale

        @app.get("/")
        async def root():
            locale = get_locale()
            return {"message": translate("hello", locale)}
        ```
    """
    return _locale_ctx.get()


@dataclass
class LocaleConfig:
    """
    Configuration for locale middleware.

    Attributes:
        default_locale: Default locale if none detected.
        supported_locales: List of supported locales.
        locale_header: Header to check for locale.
        locale_query_param: Query param to check for locale.
        locale_cookie: Cookie name for locale preference.
        fallback_chain: Whether to try language without region.

    Example:
        ```python
        from FastMiddleware import LocaleConfig

        config = LocaleConfig(
            default_locale="en-US",
            supported_locales=["en-US", "en-GB", "es", "fr", "de"],
        )
        ```
    """

    default_locale: str = "en"
    supported_locales: list[str] = field(default_factory=lambda: ["en"])
    locale_header: str = "Accept-Language"
    locale_query_param: str = "lang"
    locale_cookie: str = "locale"
    fallback_chain: bool = True
    set_cookie: bool = True


class LocaleMiddleware(FastMVCMiddleware):
    """
    Middleware that detects and manages request locale.

    Determines the user's preferred language from various sources
    and makes it available throughout the request.

    Detection Order:
        1. Query parameter (?lang=es)
        2. Cookie (locale=es)
        3. Accept-Language header
        4. Default locale

    Features:
        - Multiple locale sources
        - Accept-Language parsing
        - Locale fallback (en-US -> en)
        - Cookie persistence

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import LocaleMiddleware, get_locale

        app = FastAPI()

        app.add_middleware(
            LocaleMiddleware,
            supported_locales=["en", "es", "fr", "de"],
            default_locale="en",
        )

        @app.get("/greeting")
        async def greeting():
            locale = get_locale()
            greetings = {
                "en": "Hello",
                "es": "Hola",
                "fr": "Bonjour",
                "de": "Hallo",
            }
            return {"greeting": greetings.get(locale, "Hello")}
        ```
    """

    def __init__(
        self,
        app,
        config: LocaleConfig | None = None,
        supported_locales: list[str] | None = None,
        default_locale: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or LocaleConfig()

        if supported_locales is not None:
            self.config.supported_locales = supported_locales
        if default_locale is not None:
            self.config.default_locale = default_locale

    def _parse_accept_language(self, header: str) -> list[str]:
        """Parse Accept-Language header into sorted list of locales."""
        if not header:
            return []

        locales = []
        for raw_part in header.split(","):
            part = raw_part.strip()
            if not part:
                continue

            # Parse quality factor
            if ";q=" in part:
                locale, q = part.split(";q=")
                try:
                    quality = float(q)
                except ValueError:
                    quality = 1.0
            else:
                locale = part
                quality = 1.0

            locales.append((locale.strip(), quality))

        # Sort by quality descending
        locales.sort(key=lambda x: x[1], reverse=True)
        return [loc for loc, _ in locales]

    def _normalize_locale(self, locale: str) -> str:
        """Normalize locale format (en_US -> en-US)."""
        return locale.replace("_", "-")

    def _find_best_match(self, requested: list[str]) -> str:
        """Find best matching supported locale."""
        supported_lower = {loc.lower(): loc for loc in self.config.supported_locales}

        for raw_locale in requested:
            locale = self._normalize_locale(raw_locale)
            locale_lower = locale.lower()

            # Exact match
            if locale_lower in supported_lower:
                return supported_lower[locale_lower]

            # Try without region (en-US -> en)
            if self.config.fallback_chain and "-" in locale:
                base = locale.split("-")[0].lower()
                if base in supported_lower:
                    return supported_lower[base]

        return self.config.default_locale

    def _detect_locale(self, request: Request) -> str:
        """Detect locale from request."""
        # 1. Check query parameter
        query_locale = request.query_params.get(self.config.locale_query_param)
        if query_locale:
            return self._find_best_match([query_locale])

        # 2. Check cookie
        cookie_locale = request.cookies.get(self.config.locale_cookie)
        if cookie_locale:
            return self._find_best_match([cookie_locale])

        # 3. Parse Accept-Language
        accept_lang = request.headers.get(self.config.locale_header, "")
        locales = self._parse_accept_language(accept_lang)
        if locales:
            return self._find_best_match(locales)

        # 4. Default
        return self.config.default_locale

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Detect locale
        locale = self._detect_locale(request)

        # Set context
        token = _locale_ctx.set(locale)
        request.state.locale = locale

        try:
            response = await call_next(request)

            # Set cookie if configured
            if self.config.set_cookie:
                response.set_cookie(
                    key=self.config.locale_cookie,
                    value=locale,
                    max_age=365 * 24 * 60 * 60,  # 1 year
                    httponly=False,
                    samesite="lax",
                )

            # Add Content-Language header
            response.headers["Content-Language"] = locale

            return response
        finally:
            _locale_ctx.reset(token)
