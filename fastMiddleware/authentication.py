"""
Authentication Middleware for FastMVC.

Provides pluggable authentication with support for JWT, API keys, and custom backends.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class AuthConfig:
    """
    Configuration for authentication middleware.

    Attributes:
        exclude_paths: Paths that don't require authentication.
        exclude_methods: HTTP methods that don't require authentication.
        header_name: Name of the authentication header.
        header_scheme: Expected scheme in the header (e.g., "Bearer").
        error_message: Message to return on authentication failure.
        realm: Realm for WWW-Authenticate header.

    Example:
        ```python
        from FastMiddleware import AuthConfig

        config = AuthConfig(
            exclude_paths={"/health", "/login", "/register"},
            header_name="Authorization",
            header_scheme="Bearer",
        )
        ```
    """

    exclude_paths: set[str] = field(
        default_factory=lambda: {"/health", "/healthz", "/docs", "/openapi.json"}
    )
    exclude_methods: set[str] = field(default_factory=lambda: {"OPTIONS"})
    header_name: str = "Authorization"
    header_scheme: str = "Bearer"
    error_message: str = "Authentication required"
    realm: str = "api"


class AuthBackend(ABC):
    """
    Abstract base class for authentication backends.

    Implement this class to create custom authentication strategies
    (JWT, API keys, OAuth, etc.)

    Example:
        ```python
        from FastMiddleware import AuthBackend

        class CustomAuthBackend(AuthBackend):
            async def authenticate(self, request, credentials):
                # Validate credentials and return user data
                user = await validate_token(credentials)
                if user:
                    return {"user_id": user.id, "email": user.email}
                return None
        ```
    """

    @abstractmethod
    async def authenticate(self, request: Request, credentials: str) -> dict[str, Any] | None:
        """
        Authenticate the request using the provided credentials.

        Args:
            request: The incoming HTTP request.
            credentials: The authentication credentials (token, API key, etc.)

        Returns:
            User/auth data dict if authenticated, None otherwise.
        """
        pass


class JWTAuthBackend(AuthBackend):
    """
    JWT authentication backend.

    Validates JWT tokens and extracts user information.

    Features:
        - Configurable secret and algorithm
        - Custom claims extraction
        - Token expiration validation

    Example:
        ```python
        from FastMiddleware import JWTAuthBackend

        backend = JWTAuthBackend(
            secret="your-secret-key",
            algorithm="HS256",
            verify_exp=True,
        )
        ```

    Note:
        Requires `pyjwt` package: `pip install pyjwt`
    """

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        verify_exp: bool = True,
        audience: str | None = None,
        issuer: str | None = None,
    ) -> None:
        """
        Initialize the JWT backend.

        Args:
            secret: The secret key for token verification.
            algorithm: The signing algorithm (HS256, RS256, etc.)
            verify_exp: Whether to verify token expiration.
            audience: Expected audience claim.
            issuer: Expected issuer claim.
        """
        self.secret = secret
        self.algorithm = algorithm
        self.verify_exp = verify_exp
        self.audience = audience
        self.issuer = issuer

    async def authenticate(self, request: Request, credentials: str) -> dict[str, Any] | None:
        """
        Authenticate using JWT token.

        Args:
            request: The incoming HTTP request.
            credentials: The JWT token.

        Returns:
            Decoded token payload if valid, None otherwise.
        """
        try:
            import jwt
        except ImportError as err:
            raise ImportError(
                "pyjwt is required for JWT authentication. Install it with: pip install pyjwt"
            ) from err

        try:
            options = {"verify_exp": self.verify_exp}
            payload = jwt.decode(
                credentials,
                self.secret,
                algorithms=[self.algorithm],
                options=options,
                audience=self.audience,
                issuer=self.issuer,
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class APIKeyAuthBackend(AuthBackend):
    """
    API key authentication backend.

    Validates API keys against a set of valid keys or a validation function.

    Example:
        ```python
        from FastMiddleware import APIKeyAuthBackend

        # Static keys
        backend = APIKeyAuthBackend(
            valid_keys={"key1", "key2", "key3"}
        )

        # Dynamic validation
        async def validate_key(key):
            user = await db.get_user_by_api_key(key)
            if user:
                return {"user_id": user.id}
            return None

        backend = APIKeyAuthBackend(validator=validate_key)
        ```
    """

    def __init__(
        self,
        valid_keys: set[str] | None = None,
        validator: Callable[[str], Awaitable[dict[str, Any] | None]] | None = None,
    ) -> None:
        """
        Initialize the API key backend.

        Args:
            valid_keys: Set of valid API keys.
            validator: Async function to validate keys dynamically.
        """
        if not valid_keys and not validator:
            raise ValueError("Either valid_keys or validator must be provided")

        self.valid_keys = valid_keys or set()
        self.validator = validator

    async def authenticate(self, request: Request, credentials: str) -> dict[str, Any] | None:
        """
        Authenticate using API key.

        Args:
            request: The incoming HTTP request.
            credentials: The API key.

        Returns:
            Auth data dict if valid, None otherwise.
        """
        if self.validator:
            return await self.validator(credentials)

        if credentials in self.valid_keys:
            return {"api_key": credentials}

        return None


class AuthenticationMiddleware(FastMVCMiddleware):
    """
    Authentication middleware with pluggable backends.

    Extracts credentials from requests and validates them using
    configurable authentication backends.

    Features:
        - Multiple authentication backends
        - Path and method exclusion
        - Stores auth data in request.state
        - Standard WWW-Authenticate header
        - Configurable error responses

    Example:
        ```python
        from fastapi import FastAPI, Request
        from FastMiddleware import (
            AuthenticationMiddleware,
            AuthConfig,
            JWTAuthBackend,
        )

        app = FastAPI()

        backend = JWTAuthBackend(secret="your-secret")
        config = AuthConfig(
            exclude_paths={"/login", "/register", "/health"},
        )

        app.add_middleware(
            AuthenticationMiddleware,
            backend=backend,
            config=config,
        )

        @app.get("/protected")
        async def protected(request: Request):
            user_data = request.state.auth
            return {"user": user_data}
        ```
    """

    def __init__(
        self,
        app,
        backend: AuthBackend,
        config: AuthConfig | None = None,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the authentication middleware.

        Args:
            app: The ASGI application.
            backend: The authentication backend to use.
            config: Authentication configuration.
            exclude_paths: Additional paths to exclude (merged with config).
            exclude_methods: Additional methods to exclude (merged with config).
        """
        self.config = config or AuthConfig()

        # Merge exclude paths/methods
        _exclude_paths = self.config.exclude_paths.copy()
        if exclude_paths:
            _exclude_paths.update(exclude_paths)

        _exclude_methods = self.config.exclude_methods.copy()
        if exclude_methods:
            _exclude_methods.update(exclude_methods)

        super().__init__(app, exclude_paths=_exclude_paths, exclude_methods=_exclude_methods)
        self.backend = backend

    def _extract_credentials(self, request: Request) -> str | None:
        """
        Extract credentials from the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The credentials string, or None if not found.
        """
        auth_header = request.headers.get(self.config.header_name)
        if not auth_header:
            return None

        # Parse scheme and credentials
        parts = auth_header.split(" ", 1)
        if len(parts) != 2:
            return None

        scheme, credentials = parts
        if scheme.lower() != self.config.header_scheme.lower():
            return None

        return credentials

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request with authentication.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response, or a 401 error if authentication fails.
        """
        # Skip authentication for excluded paths/methods
        if self.should_skip(request):
            return await call_next(request)

        # Extract credentials
        credentials = self._extract_credentials(request)
        if not credentials:
            return self._unauthorized_response()

        # Authenticate
        auth_data = await self.backend.authenticate(request, credentials)
        if not auth_data:
            return self._unauthorized_response()

        # Store auth data in request state
        request.state.auth = auth_data

        return await call_next(request)

    def _unauthorized_response(self) -> Response:
        """
        Create an unauthorized (401) response.

        Returns:
            A 401 Unauthorized response.
        """
        headers = {"WWW-Authenticate": f'{self.config.header_scheme} realm="{self.config.realm}"'}

        return JSONResponse(
            content={"detail": self.config.error_message},
            status_code=401,
            headers=headers,
        )
