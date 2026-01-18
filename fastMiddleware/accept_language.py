"""
Accept-Language Middleware for FastMVC.

Parses and handles Accept-Language headers.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


_language_ctx: ContextVar[str | None] = ContextVar("language", default=None)


def get_language() -> str | None:
    """Get negotiated language."""
    return _language_ctx.get()


@dataclass
class AcceptLanguageConfig:
    """
    Configuration for accept language middleware.

    Attributes:
        supported_languages: List of supported languages.
        default_language: Default language if none match.
        add_header: Add Content-Language header.
    """

    supported_languages: list[str] = field(default_factory=lambda: ["en"])
    default_language: str = "en"
    add_header: bool = True


class AcceptLanguageMiddleware(FastMVCMiddleware):
    """
    Middleware that handles Accept-Language negotiation.

    Parses Accept-Language headers and selects the best
    matching language from supported options.

    Example:
        ```python
        from FastMiddleware import AcceptLanguageMiddleware, get_language

        app.add_middleware(
            AcceptLanguageMiddleware,
            supported_languages=["en", "es", "fr", "de"],
            default_language="en",
        )

        @app.get("/")
        async def handler():
            lang = get_language()
            return get_translations(lang)
        ```
    """

    def __init__(
        self,
        app,
        config: AcceptLanguageConfig | None = None,
        supported_languages: list[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or AcceptLanguageConfig()

        if supported_languages:
            self.config.supported_languages = supported_languages

    def _parse_header(self, accept_language: str) -> list[tuple[str, float]]:
        """Parse Accept-Language header."""
        if not accept_language:
            return []

        languages = []
        for raw_part in accept_language.split(","):
            part = raw_part.strip()
            if not part:
                continue

            if ";q=" in part:
                lang, q = part.split(";q=", 1)
                try:
                    quality = float(q)
                except ValueError:
                    quality = 1.0
            else:
                lang = part
                quality = 1.0

            languages.append((lang.strip().lower(), quality))

        return sorted(languages, key=lambda x: x[1], reverse=True)

    def _negotiate(self, requested: list[tuple[str, float]]) -> str:
        """Negotiate best language match."""
        supported_lower = [lang.lower() for lang in self.config.supported_languages]

        for lang, _ in requested:
            # Exact match
            if lang in supported_lower:
                idx = supported_lower.index(lang)
                return self.config.supported_languages[idx]

            # Prefix match (e.g., en-US matches en)
            lang_prefix = lang.split("-")[0]
            for i, supported in enumerate(supported_lower):
                if supported.startswith(lang_prefix) or lang_prefix == supported.split("-")[0]:
                    return self.config.supported_languages[i]

        return self.config.default_language

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        accept_language = request.headers.get("Accept-Language", "")
        requested = self._parse_header(accept_language)
        language = self._negotiate(requested)

        token = _language_ctx.set(language)
        request.state.language = language

        try:
            response = await call_next(request)

            if self.config.add_header:
                response.headers["Content-Language"] = language
                response.headers["Vary"] = "Accept-Language"

            return response
        finally:
            _language_ctx.reset(token)
