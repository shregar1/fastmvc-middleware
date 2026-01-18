"""
Pytest configuration and fixtures for FastMVC Middleware tests.

This file contains shared fixtures used across all test modules.
"""

import asyncio
from collections.abc import Generator

import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


# ============================================================================
# Basic Application Fixtures
# ============================================================================


@pytest.fixture
def app() -> FastAPI:
    """Create a minimal test FastAPI application."""
    return FastAPI()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def app_with_routes() -> FastAPI:
    """Create a FastAPI application with common test routes."""
    app = FastAPI()

    @app.get("/")
    async def root():
        return {"message": "Hello, World!"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/ready")
    async def ready():
        return {"ready": True}

    @app.get("/live")
    async def live():
        return {"alive": True}

    @app.get("/protected")
    async def protected(request: Request):
        auth = getattr(request.state, "auth", None)
        return {"auth": auth}

    @app.get("/context")
    async def context(request: Request):
        return {
            "request_id": getattr(request.state, "request_id", None),
            "start_time": str(getattr(request.state, "start_time", None)),
        }

    @app.get("/data")
    async def get_data():
        return {"items": list(range(10)), "status": "success"}

    @app.get("/large-data")
    async def get_large_data():
        return {"items": list(range(1000)), "data": "x" * 1000}

    @app.post("/data")
    async def post_data(request: Request):
        try:
            body = await request.json()
            return {"received": body}
        except Exception:
            return {"received": None}

    @app.put("/data/{item_id}")
    async def put_data(item_id: int, request: Request):
        try:
            body = await request.json()
            return {"id": item_id, "updated": body}
        except Exception:
            return {"id": item_id, "updated": None}

    @app.delete("/data/{item_id}")
    async def delete_data(item_id: int):
        return {"id": item_id, "deleted": True}

    @app.get("/error")
    async def raise_error():
        raise ValueError("Test error message")

    @app.get("/slow")
    async def slow():
        import asyncio

        await asyncio.sleep(0.1)
        return {"slow": True}

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        return {"user_id": user_id}

    return app


@pytest.fixture
def client_with_routes(app_with_routes: FastAPI) -> TestClient:
    """Create a test client for the app with routes."""
    return TestClient(app_with_routes, raise_server_exceptions=False)


# ============================================================================
# Legacy Fixtures (for backward compatibility)
# ============================================================================


@pytest.fixture
def sample_routes(app: FastAPI):
    """Add sample routes to the test application."""

    @app.get("/")
    async def root():
        return {"message": "Hello, World!"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/protected")
    async def protected(request: Request):
        auth = getattr(request.state, "auth", None)
        return {"auth": auth}

    @app.get("/context")
    async def context(request: Request):
        return {
            "request_id": getattr(request.state, "request_id", None),
            "start_time": str(getattr(request.state, "start_time", None)),
        }

    @app.post("/data")
    async def post_data(request: Request):
        body = await request.json()
        return {"received": body}

    return app


# ============================================================================
# Async Event Loop Fixture
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock External Dependencies
# ============================================================================


@pytest.fixture
def mock_database():
    """Mock database connection for health checks."""

    class MockDatabase:
        def __init__(self):
            self.connected = True

        async def is_connected(self) -> bool:
            return self.connected

        async def ping(self) -> bool:
            return self.connected

    return MockDatabase()


@pytest.fixture
def mock_redis():
    """Mock Redis connection for health checks."""

    class MockRedis:
        def __init__(self):
            self.connected = True

        async def ping(self) -> bool:
            return self.connected

        async def get(self, key: str) -> str | None:
            return None

        async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
            return True

        async def delete(self, key: str) -> bool:
            return True

    return MockRedis()


# ============================================================================
# JWT Test Fixtures
# ============================================================================


@pytest.fixture
def jwt_secret() -> str:
    """Return a test JWT secret."""
    return "test-secret-key-for-testing-only"


@pytest.fixture
def valid_jwt_token(jwt_secret: str) -> str:
    """Generate a valid JWT token for testing."""
    try:
        from datetime import datetime, timedelta

        import jwt

        payload = {
            "sub": "user123",
            "name": "Test User",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, jwt_secret, algorithm="HS256")
    except ImportError:
        return "test-token"


@pytest.fixture
def expired_jwt_token(jwt_secret: str) -> str:
    """Generate an expired JWT token for testing."""
    try:
        from datetime import datetime, timedelta

        import jwt

        payload = {
            "sub": "user123",
            "name": "Test User",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2),
        }
        return jwt.encode(payload, jwt_secret, algorithm="HS256")
    except ImportError:
        return "expired-token"


# ============================================================================
# Request ID Fixtures
# ============================================================================


@pytest.fixture
def sample_request_id() -> str:
    """Return a sample request ID."""
    return "test-request-id-12345"


# ============================================================================
# HTTP Headers Fixtures
# ============================================================================


@pytest.fixture
def standard_headers() -> dict:
    """Return standard HTTP headers for testing."""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }


@pytest.fixture
def cors_headers() -> dict:
    """Return CORS-related headers for testing."""
    return {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization",
    }


# ============================================================================
# Rate Limiting Fixtures
# ============================================================================


@pytest.fixture
def rate_limit_config():
    """Return a rate limit configuration for testing."""
    from FastMiddleware import RateLimitConfig

    return RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def make_request(client: TestClient, method: str, path: str, **kwargs) -> dict:
    """Helper function to make HTTP requests and return JSON response."""
    response = getattr(client, method.lower())(path, **kwargs)
    try:
        return response.json()
    except Exception:
        return {"status_code": response.status_code, "text": response.text}


def assert_security_headers(response, hsts: bool = False):
    """Helper to assert common security headers are present."""
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers

    if hsts:
        assert "Strict-Transport-Security" in response.headers


def assert_cors_headers(response, expected_origin: str | None = None):
    """Helper to assert CORS headers are present."""
    assert "Access-Control-Allow-Origin" in response.headers
    if expected_origin:
        assert response.headers["Access-Control-Allow-Origin"] == expected_origin
