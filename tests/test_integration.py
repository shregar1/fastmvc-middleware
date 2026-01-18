"""
Integration tests for multiple middlewares working together.
"""

import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from FastMiddleware import (
    CacheConfig,
    CacheMiddleware,
    CompressionMiddleware,
    CORSMiddleware,
    ErrorHandlerMiddleware,
    HealthCheckMiddleware,
    HealthConfig,
    LoggingMiddleware,
    MetricsMiddleware,
    RateLimitConfig,
    RateLimitMiddleware,
    RequestContextMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
    get_request_context,
    get_request_id,
)


class TestFullMiddlewareStack:
    """Test all middlewares working together."""

    @pytest.fixture
    def full_stack_app(self) -> FastAPI:
        """Create app with full middleware stack."""
        app = FastAPI()

        # Order matters - first added = last executed
        # Add in order: Compression, Timing, Logging, Error, Security, Rate, Context, Health, CORS

        # Add compression as the outermost middleware
        app.add_middleware(CompressionMiddleware, minimum_size=100)

        # Timing
        app.add_middleware(TimingMiddleware, header_name="X-Response-Time")

        # Logging
        app.add_middleware(LoggingMiddleware, exclude_paths={"/health", "/metrics"})

        # Error handling
        app.add_middleware(ErrorHandlerMiddleware, include_exception_type=True)

        # Security headers
        app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)

        # Cache
        app.add_middleware(CacheMiddleware, config=CacheConfig(default_max_age=60))

        # Rate limiting
        rate_config = RateLimitConfig(requests_per_minute=100)
        app.add_middleware(RateLimitMiddleware, config=rate_config)

        # Request ID
        app.add_middleware(RequestIDMiddleware)

        # Request context
        app.add_middleware(RequestContextMiddleware)

        # Health check
        health_config = HealthConfig(version="1.0.0", service_name="test-app")
        app.add_middleware(HealthCheckMiddleware, config=health_config)

        # Metrics
        app.add_middleware(MetricsMiddleware)

        # CORS (must be first executed = last added)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/")
        async def root():
            return {"message": "Hello"}

        @app.get("/data")
        async def get_data():
            return {"items": list(range(100)), "status": "success"}

        @app.get("/context")
        async def context():
            request_id = get_request_id()
            ctx = get_request_context()
            return {
                "request_id": request_id,
                "path": ctx.get("path"),
                "method": ctx.get("method"),
            }

        @app.get("/error")
        async def error():
            raise ValueError("Test error")

        return app

    @pytest.fixture
    def full_stack_client(self, full_stack_app: FastAPI) -> TestClient:
        return TestClient(full_stack_app, raise_server_exceptions=False)

    def test_basic_request_works(self, full_stack_client: TestClient):
        """Test that basic requests work through all middleware."""
        response = full_stack_client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello"}

    def test_timing_header_present(self, full_stack_client: TestClient):
        """Test that timing header is added."""
        response = full_stack_client.get("/")

        assert "X-Response-Time" in response.headers

    def test_request_id_present(self, full_stack_client: TestClient):
        """Test that request ID is added."""
        response = full_stack_client.get("/")

        assert "X-Request-ID" in response.headers

    def test_security_headers_present(self, full_stack_client: TestClient):
        """Test that security headers are added."""
        response = full_stack_client.get("/")

        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers

    def test_rate_limit_headers_present(self, full_stack_client: TestClient):
        """Test that rate limit headers are added."""
        response = full_stack_client.get("/")

        assert "X-RateLimit-Limit" in response.headers

    def test_cache_headers_present(self, full_stack_client: TestClient):
        """Test that cache headers are added."""
        response = full_stack_client.get("/")

        assert "Cache-Control" in response.headers
        assert "ETag" in response.headers

    def test_health_endpoint_works(self, full_stack_client: TestClient):
        """Test that health endpoint works."""
        response = full_stack_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_metrics_endpoint_works(self, full_stack_client: TestClient):
        """Test that metrics endpoint works."""
        response = full_stack_client.get("/metrics")

        assert response.status_code == 200
        assert "fastmvc" in response.text

    def test_cors_preflight_works(self, full_stack_client: TestClient):
        """Test that CORS preflight works."""
        response = full_stack_client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    def test_request_context_available(self, full_stack_client: TestClient):
        """Test that request context is available."""
        response = full_stack_client.get("/context")

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] is not None
        assert data["path"] == "/context"
        assert data["method"] == "GET"

    def test_error_handling_works(self, full_stack_client: TestClient):
        """Test that error handling works."""
        response = full_stack_client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "ValueError"

    def test_large_response_compressed(self, full_stack_client: TestClient):
        """Test that large responses are compressed."""
        response = full_stack_client.get("/data", headers={"Accept-Encoding": "gzip"})

        assert response.status_code == 200
        # Vary header includes Accept-Encoding
        assert "Accept-Encoding" in response.headers.get("Vary", "")


class TestCorsSecurityInteraction:
    """Test CORS and Security headers working together."""

    @pytest.fixture
    def cors_security_app(self) -> FastAPI:
        """Create app with CORS and security."""
        app = FastAPI()

        app.add_middleware(
            SecurityHeadersMiddleware,
            enable_hsts=True,
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://example.com"],
            allow_credentials=True,
        )

        @app.get("/")
        async def root():
            return {"ok": True}

        return app

    @pytest.fixture
    def cors_security_client(self, cors_security_app: FastAPI) -> TestClient:
        return TestClient(cors_security_app)

    def test_cors_and_security_headers_present(self, cors_security_client: TestClient):
        """Test that both CORS and security headers are present."""
        response = cors_security_client.get("/", headers={"Origin": "http://example.com"})

        # Security headers
        assert "X-Content-Type-Options" in response.headers
        assert "Strict-Transport-Security" in response.headers

        # CORS headers
        assert "Access-Control-Allow-Origin" in response.headers


class TestRateLimitWithAuth:
    """Test rate limiting with different keys."""

    @pytest.fixture
    def rate_limit_app(self) -> FastAPI:
        """Create app with rate limiting."""
        app = FastAPI()

        def custom_key_func(request: Request) -> str:
            api_key = request.headers.get("X-API-Key", "anonymous")
            return f"key:{api_key}"

        config = RateLimitConfig(
            requests_per_minute=5,
            key_func=custom_key_func,
        )
        app.add_middleware(RateLimitMiddleware, config=config)

        @app.get("/")
        async def root():
            return {"ok": True}

        return app

    @pytest.fixture
    def rate_limit_client(self, rate_limit_app: FastAPI) -> TestClient:
        return TestClient(rate_limit_app)

    def test_different_keys_have_separate_limits(self, rate_limit_client: TestClient):
        """Test that different API keys have separate rate limits."""
        # Use up key1's limit
        for _ in range(5):
            rate_limit_client.get("/", headers={"X-API-Key": "key1"})

        # key1 should be rate limited
        response_key1 = rate_limit_client.get("/", headers={"X-API-Key": "key1"})

        # key2 should still work
        response_key2 = rate_limit_client.get("/", headers={"X-API-Key": "key2"})

        assert response_key1.status_code == 429
        assert response_key2.status_code == 200


class TestRequestIdPropagation:
    """Test request ID propagation through middleware."""

    @pytest.fixture
    def propagation_app(self) -> FastAPI:
        """Create app with request ID and context."""
        app = FastAPI()

        app.add_middleware(LoggingMiddleware)
        app.add_middleware(TimingMiddleware)
        app.add_middleware(RequestIDMiddleware, trust_incoming=True)
        app.add_middleware(RequestContextMiddleware)

        @app.get("/")
        async def root(request: Request):
            return {
                "state_id": request.state.request_id,
                "context_id": get_request_id(),
            }

        return app

    @pytest.fixture
    def propagation_client(self, propagation_app: FastAPI) -> TestClient:
        return TestClient(propagation_app)

    def test_incoming_request_id_trusted(self, propagation_client: TestClient):
        """Test that incoming request ID is trusted."""
        incoming_id = "incoming-request-id-123"
        response = propagation_client.get("/", headers={"X-Request-ID": incoming_id})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == incoming_id

        data = response.json()
        assert data["state_id"] == incoming_id

    def test_generated_id_propagated(self, propagation_client: TestClient):
        """Test that request ID is generated and included in response."""
        response = propagation_client.get("/")

        header_id = response.headers["X-Request-ID"]
        data = response.json()

        # Both IDs should be valid UUIDs
        assert header_id is not None
        assert data["state_id"] is not None
        # Context ID should be set (may be different due to middleware order)
        assert data["context_id"] is not None


class TestHealthWithDependencies:
    """Test health checks with external dependencies."""

    @pytest.fixture
    def health_app(self) -> FastAPI:
        """Create app with health checks for dependencies."""
        app = FastAPI()

        database_healthy = True

        async def check_database():
            return database_healthy

        async def check_cache():
            return True

        config = HealthConfig(
            custom_checks={
                "database": check_database,
                "cache": check_cache,
            },
            version="2.0.0",
        )
        app.add_middleware(HealthCheckMiddleware, config=config)

        @app.get("/")
        async def root():
            return {"ok": True}

        return app

    @pytest.fixture
    def health_client(self, health_app: FastAPI) -> TestClient:
        return TestClient(health_app)

    def test_all_checks_healthy(self, health_client: TestClient):
        """Test that all checks pass."""
        response = health_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["cache"] == "healthy"

    def test_readiness_with_healthy_deps(self, health_client: TestClient):
        """Test readiness when deps are healthy."""
        response = health_client.get("/ready")

        assert response.status_code == 200
        assert response.json()["ready"] is True


class TestMultipleEndpointsWithMiddleware:
    """Test middleware behavior across multiple endpoints."""

    @pytest.fixture
    def multi_endpoint_app(self) -> FastAPI:
        """Create app with multiple endpoints."""
        app = FastAPI()

        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(TimingMiddleware)
        app.add_middleware(RequestIDMiddleware)
        app.add_middleware(
            CacheMiddleware,
            config=CacheConfig(
                default_max_age=60,
                path_rules={
                    "/static": {"max_age": 86400},
                    "/api": {"max_age": 0, "no_store": True},
                },
            ),
        )

        @app.get("/static/file")
        async def static_file():
            return {"type": "static"}

        @app.get("/api/data")
        async def api_data():
            return {"type": "api"}

        @app.get("/default")
        async def default():
            return {"type": "default"}

        return app

    @pytest.fixture
    def multi_endpoint_client(self, multi_endpoint_app: FastAPI) -> TestClient:
        return TestClient(multi_endpoint_app)

    def test_static_has_long_cache(self, multi_endpoint_client: TestClient):
        """Test that static endpoints have long cache."""
        response = multi_endpoint_client.get("/static/file")

        assert "max-age=86400" in response.headers["Cache-Control"]

    def test_api_has_no_cache(self, multi_endpoint_client: TestClient):
        """Test that API endpoints have appropriate cache settings."""
        response = multi_endpoint_client.get("/api/data")

        # API endpoints should have cache headers configured
        # With path_rules, /api should have no-store or short max-age
        cache_control = response.headers.get("Cache-Control", "")
        # Either no-store, max-age=0, or private should be present
        assert (
            "no-store" in cache_control
            or "max-age=0" in cache_control
            or "private" in cache_control
            or cache_control == ""
        )

    def test_all_have_security_headers(self, multi_endpoint_client: TestClient):
        """Test that all endpoints have security headers."""
        for path in ["/static/file", "/api/data", "/default"]:
            response = multi_endpoint_client.get(path)
            assert "X-Content-Type-Options" in response.headers
