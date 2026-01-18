"""
Tests for Rate Limiting middleware.
"""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from FastMiddleware import InMemoryRateLimitStore, RateLimitConfig, RateLimitMiddleware


@pytest.fixture
def rate_limit_app(sample_routes) -> FastAPI:
    """Create app with rate limiting middleware."""
    app = sample_routes
    config = RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=100,
    )
    app.add_middleware(RateLimitMiddleware, config=config)
    return app


@pytest.fixture
def rate_limit_client(rate_limit_app: FastAPI) -> TestClient:
    """Create test client for rate limited app."""
    return TestClient(rate_limit_app)


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    def test_rate_limit_headers_added(self, rate_limit_client: TestClient):
        """Test that rate limit headers are added to responses."""
        response = rate_limit_client.get("/")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_decrements(self, rate_limit_client: TestClient):
        """Test that remaining count decrements."""
        response1 = rate_limit_client.get("/")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])

        response2 = rate_limit_client.get("/")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])

        assert remaining2 < remaining1

    def test_excluded_paths_not_limited(self, rate_limit_client: TestClient):
        """Test that excluded paths are not rate limited."""
        # Health endpoint is excluded by default
        for _ in range(10):
            response = rate_limit_client.get("/health")
            assert response.status_code == 200

    def test_rate_limit_exceeded(self, sample_routes):
        """Test 429 response when rate limit is exceeded."""
        app = sample_routes
        config = RateLimitConfig(requests_per_minute=2)
        app.add_middleware(RateLimitMiddleware, config=config)
        client = TestClient(app)

        # Make requests up to the limit
        for _ in range(2):
            response = client.get("/")
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.json()["detail"] == "Rate limit exceeded. Please try again later."


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_limit == 10
        assert config.strategy == "sliding"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=2000,
            burst_limit=20,
        )

        assert config.requests_per_minute == 100
        assert config.requests_per_hour == 2000
        assert config.burst_limit == 20


class TestInMemoryRateLimitStore:
    """Tests for InMemoryRateLimitStore."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_first_request(self):
        """Test that first request is allowed."""
        store = InMemoryRateLimitStore()

        allowed, remaining, _reset = await store.check_rate_limit("test", 10, 60)

        assert allowed is True
        assert remaining == 9

    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_over_limit(self):
        """Test that requests over limit are blocked."""
        store = InMemoryRateLimitStore()

        # Use up the limit
        for _ in range(5):
            await store.check_rate_limit("test", 5, 60)

        # Next should be blocked
        allowed, remaining, _reset = await store.check_rate_limit("test", 5, 60)

        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_cleanup_removes_old_entries(self):
        """Test that cleanup removes old entries."""
        store = InMemoryRateLimitStore()

        await store.check_rate_limit("test", 10, 60)
        assert "test" in store._windows

        # Cleanup should keep recent entries
        await store.cleanup(max_age=3600)
        assert "test" in store._windows
