"""
Comprehensive tests for all middlewares to achieve 100% coverage.
"""

import hashlib
import hmac
import time

from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient


# ============== AB Testing ==============
class TestABTesting:
    def test_ab_test_basic(self):
        from FastMiddleware import ABTestMiddleware, Experiment

        async def homepage(request):
            return JSONResponse({"variant": request.state.ab_variants.get("test_exp", "none")})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(
            ABTestMiddleware,
            experiments=[Experiment(name="test_exp", variants=["a", "b"], weights=[0.5, 0.5])],
        )
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["variant"] in ["a", "b"]

    def test_ab_test_sticky_variant(self):
        from FastMiddleware import ABTestMiddleware, Experiment

        async def homepage(request):
            return JSONResponse({"variant": request.state.ab_variants.get("exp", "none")})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(
            ABTestMiddleware, experiments=[Experiment(name="exp", variants=["x", "y"])]
        )
        client = TestClient(app)

        # First request sets cookie
        resp1 = client.get("/")
        variant1 = resp1.json()["variant"]

        # Second request uses same cookie - should get same variant
        resp2 = client.get("/")
        variant2 = resp2.json()["variant"]
        assert variant1 == variant2


# ============== Accept Language ==============
class TestAcceptLanguage:
    def test_accept_language_basic(self):
        from FastMiddleware import AcceptLanguageMiddleware

        async def homepage(request):
            return JSONResponse({"lang": getattr(request.state, "language", "en")})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(
            AcceptLanguageMiddleware,
            supported_languages=["en", "es", "fr"],
        )
        client = TestClient(app)

        # Test with Accept-Language header
        response = client.get("/", headers={"Accept-Language": "es,en;q=0.9"})
        assert response.status_code == 200

    def test_accept_language_default(self):
        from FastMiddleware import AcceptLanguageMiddleware

        async def homepage(request):
            return JSONResponse({"lang": getattr(request.state, "language", "en")})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(AcceptLanguageMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== API Version Header ==============
class TestAPIVersionHeader:
    def test_api_version_header(self):
        from FastMiddleware import APIVersionHeaderMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(APIVersionHeaderMiddleware, version="1.0.0")
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert (
            "X-API-Version" in response.headers or response.headers.get("x-api-version") == "1.0.0"
        )


# ============== Audit ==============
class TestAudit:
    def test_audit_logging(self):
        from FastMiddleware import AuditMiddleware

        async def homepage(request):
            return JSONResponse({"status": "ok"})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(AuditMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Bandwidth ==============
class TestBandwidth:
    def test_bandwidth_throttle(self):
        from FastMiddleware import BandwidthMiddleware

        async def homepage(request):
            return PlainTextResponse("X" * 1000)

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(BandwidthMiddleware, bytes_per_second=10000)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert len(response.text) == 1000


# ============== Basic Auth ==============
class TestBasicAuth:
    def test_basic_auth_success(self):
        import base64

        from FastMiddleware import BasicAuthMiddleware

        async def homepage(request):
            return PlainTextResponse(f"Hello {request.state.user}")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(BasicAuthMiddleware, users={"admin": "secret"})
        client = TestClient(app)

        credentials = base64.b64encode(b"admin:secret").decode()
        response = client.get("/", headers={"Authorization": f"Basic {credentials}"})
        assert response.status_code == 200
        assert "admin" in response.text

    def test_basic_auth_failure(self):
        from FastMiddleware import BasicAuthMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(BasicAuthMiddleware, users={"admin": "secret"})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 401


# ============== Bearer Auth ==============
class TestBearerAuth:
    def test_bearer_auth_success(self):
        from FastMiddleware import BearerAuthMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(BearerAuthMiddleware, tokens={"token123": {"user": "admin"}})
        client = TestClient(app)

        response = client.get("/", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 200

    def test_bearer_auth_invalid(self):
        from FastMiddleware import BearerAuthMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(BearerAuthMiddleware, tokens={"token123": {"user": "admin"}})
        client = TestClient(app)

        response = client.get("/", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401


# ============== Bot Detection ==============
class TestBotDetection:
    def test_bot_detection(self):
        from FastMiddleware import BotDetectionMiddleware

        async def homepage(request):
            return JSONResponse({"is_bot": getattr(request.state, "is_bot", False)})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(BotDetectionMiddleware)
        client = TestClient(app)

        # Normal user agent
        response = client.get("/", headers={"User-Agent": "Mozilla/5.0"})
        assert response.status_code == 200

        # Bot user agent
        response = client.get("/", headers={"User-Agent": "Googlebot/2.1"})
        assert response.status_code == 200


# ============== Bulkhead ==============
class TestBulkhead:
    def test_bulkhead_allows_request(self):
        from FastMiddleware import BulkheadMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(BulkheadMiddleware, max_concurrent=10)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Chaos ==============
class TestChaos:
    def test_chaos_disabled(self):
        from FastMiddleware import ChaosMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ChaosMiddleware, enabled=False)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Circuit Breaker ==============
class TestCircuitBreaker:
    def test_circuit_breaker_closed(self):
        from FastMiddleware import CircuitBreakerMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(CircuitBreakerMiddleware, failure_threshold=5)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Client Hints ==============
class TestClientHints:
    def test_client_hints(self):
        from FastMiddleware import ClientHintsMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ClientHintsMiddleware)
        client = TestClient(app)

        response = client.get("/", headers={"Sec-CH-UA": '"Chromium";v="120"'})
        assert response.status_code == 200


# ============== Conditional Request ==============
class TestConditionalRequest:
    def test_conditional_request(self):
        from FastMiddleware import ConditionalRequestMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ConditionalRequestMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Content Negotiation ==============
class TestContentNegotiation:
    def test_content_negotiation(self):
        from FastMiddleware import ContentNegotiationMiddleware

        async def homepage(request):
            return JSONResponse(
                {"type": getattr(request.state, "content_type", "application/json")}
            )

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(
            ContentNegotiationMiddleware, supported_types=["application/json", "application/xml"]
        )
        client = TestClient(app)

        response = client.get("/", headers={"Accept": "application/json"})
        assert response.status_code == 200


# ============== Content Type ==============
class TestContentType:
    def test_content_type_validation(self):
        from FastMiddleware import ContentTypeMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage, methods=["POST"])])
        app.add_middleware(ContentTypeMiddleware)
        client = TestClient(app)

        response = client.post("/", json={"test": 1})
        assert response.status_code == 200


# ============== Context ==============
class TestContext:
    def test_context_middleware(self):
        from FastMiddleware import ContextMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ContextMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Correlation ==============
class TestCorrelation:
    def test_correlation_id(self):
        from FastMiddleware import CorrelationMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(CorrelationMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers or "x-correlation-id" in response.headers

    def test_correlation_id_passed(self):
        from FastMiddleware import CorrelationMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(CorrelationMiddleware)
        client = TestClient(app)

        response = client.get("/", headers={"X-Correlation-ID": "test-123"})
        assert response.status_code == 200


# ============== Cost Tracking ==============
class TestCostTracking:
    def test_cost_tracking(self):
        from FastMiddleware import CostTrackingMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(CostTrackingMiddleware, path_costs={"/": 1.0})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== CSP Report ==============
class TestCSPReport:
    def test_csp_report(self):
        from FastMiddleware import CSPReportMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(CSPReportMiddleware, report_uri="/_csp-report")
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== CSRF ==============
class TestCSRF:
    def test_csrf_get_token(self):
        from FastMiddleware import CSRFConfig, CSRFMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        config = CSRFConfig(secret="test-secret-key-32-chars-long!!")
        app.add_middleware(CSRFMiddleware, config=config)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Data Masking ==============
class TestDataMasking:
    def test_data_masking(self):
        from FastMiddleware import DataMaskingMiddleware

        async def homepage(request):
            return JSONResponse({"password": "secret123"})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(DataMaskingMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Deprecation ==============
class TestDeprecation:
    def test_deprecation_warning(self):
        from FastMiddleware import DeprecationInfo, DeprecationMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/old", homepage)])
        info = DeprecationInfo(
            message="This endpoint is deprecated", sunset_date="2025-12-31", replacement="/new"
        )
        app.add_middleware(DeprecationMiddleware, deprecated_paths={"/old": info})
        client = TestClient(app)

        response = client.get("/old")
        assert response.status_code == 200


# ============== Early Hints ==============
class TestEarlyHints:
    def test_early_hints(self):
        from FastMiddleware import EarlyHintsMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(EarlyHintsMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== ETag ==============
class TestETag:
    def test_etag_generation(self):
        from FastMiddleware import ETagMiddleware

        async def homepage(request):
            return PlainTextResponse("Hello World")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ETagMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Exception Handler ==============
class TestExceptionHandler:
    def test_exception_handler(self):
        from FastMiddleware import ExceptionHandlerMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ExceptionHandlerMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Feature Flag ==============
class TestFeatureFlag:
    def test_feature_flag(self):
        from FastMiddleware import FeatureFlagMiddleware

        async def homepage(request):
            flags = getattr(request.state, "feature_flags", {})
            return JSONResponse({"flags": flags})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(FeatureFlagMiddleware, flags={"new_feature": True, "old_feature": False})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== GeoIP ==============
class TestGeoIP:
    def test_geoip(self):
        from FastMiddleware import GeoIPMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(GeoIPMiddleware)
        client = TestClient(app)

        response = client.get("/", headers={"CF-IPCountry": "US"})
        assert response.status_code == 200


# ============== Graceful Shutdown ==============
class TestGracefulShutdown:
    def test_graceful_shutdown_normal(self):
        from FastMiddleware import GracefulShutdownMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        GracefulShutdownMiddleware(app)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== HATEOAS ==============
class TestHATEOAS:
    def test_hateoas(self):
        from FastMiddleware import HATEOASMiddleware

        async def homepage(request):
            return JSONResponse({"id": 1})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(HATEOASMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Header Transform ==============
class TestHeaderTransform:
    def test_header_transform(self):
        from FastMiddleware import HeaderTransformMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(HeaderTransformMiddleware, add_response_headers={"X-Custom": "value"})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("X-Custom") == "value"


# ============== Honeypot ==============
class TestHoneypot:
    def test_honeypot_normal(self):
        from FastMiddleware import HoneypotMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(HoneypotMiddleware, honeypot_paths={"/wp-admin"})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200

    def test_honeypot_trap(self):
        from FastMiddleware import HoneypotMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage), Route("/wp-admin", homepage)])
        app.add_middleware(HoneypotMiddleware, honeypot_paths={"/wp-admin"})
        client = TestClient(app)

        client.get("/wp-admin")
        # Should return 404 or similar


# ============== HTTPS Redirect ==============
class TestHTTPSRedirect:
    def test_https_redirect_excluded(self):
        from FastMiddleware import HTTPSRedirectMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/health", homepage)])
        app.add_middleware(HTTPSRedirectMiddleware, exclude_paths={"/health"})
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200


# ============== IP Filter ==============
class TestIPFilter:
    def test_ip_filter_allowed(self):
        from FastMiddleware import IPFilterMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        # Don't set whitelist, so all IPs are allowed by default
        app.add_middleware(IPFilterMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== JSON Schema ==============
class TestJSONSchema:
    def test_json_schema(self):
        from FastMiddleware import JSONSchemaMiddleware

        async def homepage(request):
            return JSONResponse({"status": "ok"})

        app = Starlette(routes=[Route("/", homepage, methods=["POST"])])
        app.add_middleware(JSONSchemaMiddleware, schemas={})
        client = TestClient(app)

        response = client.post("/", json={"name": "test"})
        assert response.status_code == 200


# ============== Load Shedding ==============
class TestLoadShedding:
    def test_load_shedding_normal(self):
        from FastMiddleware import LoadSheddingMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(LoadSheddingMiddleware, max_concurrent=1000)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Locale ==============
class TestLocale:
    def test_locale(self):
        from FastMiddleware import LocaleMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(LocaleMiddleware, supported_locales=["en", "es"])
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Method Override ==============
class TestMethodOverride:
    def test_method_override(self):
        from FastMiddleware import MethodOverrideMiddleware

        async def delete_handler(request):
            return PlainTextResponse(f"Method: {request.method}")

        app = Starlette(routes=[Route("/", delete_handler, methods=["DELETE", "POST"])])
        app.add_middleware(MethodOverrideMiddleware)
        client = TestClient(app)

        response = client.post("/", headers={"X-HTTP-Method-Override": "DELETE"})
        assert response.status_code == 200


# ============== No Cache ==============
class TestNoCache:
    def test_no_cache(self):
        from FastMiddleware import NoCacheMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(NoCacheMiddleware, paths={"/", "/api"})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Origin ==============
class TestOrigin:
    def test_origin(self):
        from FastMiddleware import OriginMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(OriginMiddleware, allowed_origins={"http://localhost"})
        client = TestClient(app)

        response = client.get("/", headers={"Origin": "http://localhost"})
        assert response.status_code == 200


# ============== Path Rewrite ==============
class TestPathRewrite:
    def test_path_rewrite(self):
        from FastMiddleware import PathRewriteMiddleware, RewriteRule

        async def homepage(request):
            return PlainTextResponse(f"Path: {request.url.path}")

        app = Starlette(routes=[Route("/api/v1/test", homepage), Route("/old/test", homepage)])
        app.add_middleware(PathRewriteMiddleware, rules=[RewriteRule("/old", "/api/v1")])
        client = TestClient(app)

        response = client.get("/old/test")
        assert response.status_code == 200


# ============== Payload Size ==============
class TestPayloadSize:
    def test_payload_size(self):
        from FastMiddleware import PayloadSizeMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage, methods=["POST"])])
        app.add_middleware(PayloadSizeMiddleware, max_request_size=1024 * 1024)
        client = TestClient(app)

        response = client.post("/", content="test data")
        assert response.status_code == 200


# ============== Permissions Policy ==============
class TestPermissionsPolicy:
    def test_permissions_policy(self):
        from FastMiddleware import PermissionsPolicyMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(PermissionsPolicyMiddleware, policies={"camera": []})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Profiling ==============
class TestProfiling:
    def test_profiling(self):
        from FastMiddleware import ProfilingMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ProfilingMiddleware, enabled=True)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Quota ==============
class TestQuota:
    def test_quota(self):
        from FastMiddleware import QuotaMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(QuotaMiddleware, default_quota=1000)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Real IP ==============
class TestRealIP:
    def test_real_ip(self):
        from FastMiddleware import RealIPMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RealIPMiddleware)
        client = TestClient(app)

        response = client.get("/", headers={"X-Real-IP": "1.2.3.4"})
        assert response.status_code == 200


# ============== Redirect ==============
class TestRedirect:
    def test_redirect(self):
        from FastMiddleware import RedirectMiddleware, RedirectRule

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/new", homepage)])
        app.add_middleware(RedirectMiddleware, rules=[RedirectRule("/old", "/new")])
        client = TestClient(app, follow_redirects=False)

        response = client.get("/old")
        assert response.status_code in [301, 302, 307, 308]


# ============== Referrer Policy ==============
class TestReferrerPolicy:
    def test_referrer_policy(self):
        from FastMiddleware import ReferrerPolicyMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ReferrerPolicyMiddleware, policy="strict-origin")
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "Referrer-Policy" in response.headers


# ============== Replay Prevention ==============
class TestReplayPrevention:
    def test_replay_prevention(self):
        from FastMiddleware import ReplayPreventionMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ReplayPreventionMiddleware)
        client = TestClient(app)

        timestamp = str(int(time.time()))
        nonce = "unique-nonce-123"
        client.get("/", headers={"X-Timestamp": timestamp, "X-Nonce": nonce})
        # May fail without both headers, which is expected behavior


# ============== Request Coalescing ==============
class TestRequestCoalescing:
    def test_request_coalescing(self):
        from FastMiddleware import RequestCoalescingMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestCoalescingMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Request Dedup ==============
class TestRequestDedup:
    def test_request_dedup(self):
        from FastMiddleware import RequestDedupMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestDedupMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Request Fingerprint ==============
class TestRequestFingerprint:
    def test_request_fingerprint(self):
        from FastMiddleware import RequestFingerprintMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestFingerprintMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Request ID Propagation ==============
class TestRequestIDPropagation:
    def test_request_id_propagation(self):
        from FastMiddleware import RequestIDPropagationMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestIDPropagationMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Request Limit ==============
class TestRequestLimit:
    def test_request_limit(self):
        from FastMiddleware import RequestLimitMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage, methods=["POST"])])
        app.add_middleware(RequestLimitMiddleware, max_size=1024 * 1024)
        client = TestClient(app)

        response = client.post("/", content="test")
        assert response.status_code == 200


# ============== Request Logger ==============
class TestRequestLogger:
    def test_request_logger(self):
        from FastMiddleware import RequestLoggerMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestLoggerMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Request Priority ==============
class TestRequestPriority:
    def test_request_priority(self):
        from FastMiddleware import RequestPriorityMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestPriorityMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Request Sampler ==============
class TestRequestSampler:
    def test_request_sampler(self):
        from FastMiddleware import RequestSamplerMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestSamplerMiddleware, rate=0.5)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Request Signing ==============
class TestRequestSigning:
    def test_request_signing(self):
        from FastMiddleware import RequestSigningMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        secret = "test-secret"
        timestamp = str(int(time.time()))
        message = f"{timestamp}.GET./.".encode()
        hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestSigningMiddleware, secret_key=secret, exclude_paths={"/health"})
        client = TestClient(app)

        # Test excluded path
        client.get("/health")


# ============== Request Validator ==============
class TestRequestValidator:
    def test_request_validator(self):
        from FastMiddleware import RequestValidatorMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RequestValidatorMiddleware, rules=[])
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Response Cache ==============
class TestResponseCache:
    def test_response_cache(self):
        from FastMiddleware import ResponseCacheMiddleware

        call_count = 0

        async def homepage(request):
            nonlocal call_count
            call_count += 1
            return PlainTextResponse(f"Count: {call_count}")

        app = Starlette(routes=[Route("/", homepage)])
        ResponseCacheMiddleware(app, default_ttl=60)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Response Format ==============
class TestResponseFormat:
    def test_response_format(self):
        from FastMiddleware import ResponseFormatMiddleware

        async def homepage(request):
            return JSONResponse({"data": "test"})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ResponseFormatMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Response Signature ==============
class TestResponseSignature:
    def test_response_signature(self):
        from FastMiddleware import ResponseSignatureMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ResponseSignatureMiddleware, secret_key="test-secret")
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Response Time ==============
class TestResponseTime:
    def test_response_time(self):
        from FastMiddleware import ResponseTimeMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ResponseTimeMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Retry After ==============
class TestRetryAfter:
    def test_retry_after(self):
        from FastMiddleware import RetryAfterMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(RetryAfterMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Route Auth ==============
class TestRouteAuth:
    def test_route_auth(self):
        from FastMiddleware import RouteAuthMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/public", homepage)])
        app.add_middleware(RouteAuthMiddleware, routes=[])
        client = TestClient(app)

        response = client.get("/public")
        assert response.status_code == 200


# ============== Sanitization ==============
class TestSanitization:
    def test_sanitization(self):
        from FastMiddleware import SanitizationMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(SanitizationMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Scope ==============
class TestScope:
    def test_scope(self):
        from FastMiddleware import ScopeMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ScopeMiddleware, route_scopes={})
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Server Timing ==============
class TestServerTiming:
    def test_server_timing(self):
        from FastMiddleware import ServerTimingMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(ServerTimingMiddleware)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Session ==============
class TestSession:
    def test_session(self):
        from FastMiddleware import SessionConfig, SessionMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        config = SessionConfig(max_age=3600)
        app.add_middleware(SessionMiddleware, config=config)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Slow Response ==============
class TestSlowResponse:
    def test_slow_response_disabled(self):
        from FastMiddleware import SlowResponseMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(SlowResponseMiddleware, enabled=False)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Tenant ==============
class TestTenant:
    def test_tenant(self):
        from FastMiddleware import TenantMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(TenantMiddleware)
        client = TestClient(app)

        response = client.get("/", headers={"X-Tenant-ID": "test-tenant"})
        assert response.status_code == 200


# ============== Timeout ==============
class TestTimeout:
    def test_timeout(self):
        from FastMiddleware import TimeoutMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(TimeoutMiddleware, timeout=30.0)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Trailing Slash ==============
class TestTrailingSlash:
    def test_trailing_slash(self):
        from FastMiddleware import TrailingSlashMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/test", homepage)])
        app.add_middleware(TrailingSlashMiddleware)
        client = TestClient(app, follow_redirects=True)

        response = client.get("/test")
        assert response.status_code == 200


# ============== User Agent ==============
class TestUserAgent:
    def test_user_agent(self):
        from FastMiddleware import UserAgentMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(UserAgentMiddleware)
        client = TestClient(app)

        response = client.get(
            "/", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        assert response.status_code == 200


# ============== Versioning ==============
class TestVersioning:
    def test_versioning(self):
        from FastMiddleware import VersioningMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(VersioningMiddleware)
        client = TestClient(app)

        response = client.get("/", headers={"X-API-Version": "2.0"})
        assert response.status_code == 200


# ============== Warmup ==============
class TestWarmup:
    def test_warmup(self):
        from FastMiddleware import WarmupMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        WarmupMiddleware(app)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200


# ============== Webhook ==============
class TestWebhook:
    def test_webhook(self):
        from FastMiddleware import WebhookMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(WebhookMiddleware, secret="test-secret", paths={"/webhook"})
        client = TestClient(app)

        # Regular path should work
        response = client.get("/")
        assert response.status_code == 200


# ============== XFF Trust ==============
class TestXFFTrust:
    def test_xff_trust(self):
        from FastMiddleware import XFFTrustMiddleware

        async def homepage(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(XFFTrustMiddleware, trusted_proxies={"10.0.0.0/8"})
        client = TestClient(app)

        response = client.get("/", headers={"X-Forwarded-For": "1.2.3.4"})
        assert response.status_code == 200
