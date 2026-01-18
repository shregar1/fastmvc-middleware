# FastMVC Middleware

[![PyPI version](https://badge.fury.io/py/fastmvc-middleware.svg)](https://badge.fury.io/py/fastmvc-middleware)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/hyyre/fastmvc-middleware/actions/workflows/ci.yml/badge.svg)](https://github.com/hyyre/fastmvc-middleware/actions)

**Production-ready middleware collection for FastAPI/Starlette applications.**

A comprehensive set of **94+ battle-tested, configurable middleware components** for building robust APIs.

## 📦 Installation

```bash
pip install fastmvc-middleware
```

**Optional dependencies:**
```bash
pip install fastmvc-middleware[jwt]    # JWT authentication
pip install fastmvc-middleware[proxy]  # Proxy middleware (httpx)
pip install fastmvc-middleware[all]    # All optional dependencies
```

## 🚀 Quick Start

```python
from fastapi import FastAPI
from FastMiddleware import (
    CORSMiddleware,
    SecurityHeadersMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    HealthCheckMiddleware,
)

app = FastAPI()

# Add middleware (order matters - first added = last executed)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(HealthCheckMiddleware, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["https://example.com"])

@app.get("/")
async def root():
    return {"message": "Hello, World!"}
```

---

## 📋 Complete Import Reference

All available imports organized by category:

### Core Middlewares

```python
from FastMiddleware import (
    FastMVCMiddleware,       # Base middleware class
    CORSMiddleware,          # Cross-Origin Resource Sharing
    LoggingMiddleware,       # Structured request/response logging
    TimingMiddleware,        # Response timing headers
    RequestIDMiddleware,     # Unique request ID generation
)
```

### Security Middlewares

```python
from FastMiddleware import (
    # Security Headers
    SecurityHeadersMiddleware, SecurityHeadersConfig,
    TrustedHostMiddleware,
    ReferrerPolicyMiddleware, ReferrerPolicyConfig,
    PermissionsPolicyMiddleware, PermissionsPolicyConfig,
    CSPReportMiddleware, CSPReportConfig,
    
    # CSRF & Origin
    CSRFMiddleware, CSRFConfig,
    OriginMiddleware, OriginConfig,
    
    # Network Security
    HTTPSRedirectMiddleware, HTTPSRedirectConfig,
    IPFilterMiddleware, IPFilterConfig,
    XFFTrustMiddleware, XFFTrustConfig,
    RealIPMiddleware, RealIPConfig, get_real_ip,
    
    # Webhook & Signing
    WebhookMiddleware, WebhookConfig,
    RequestSigningMiddleware, RequestSigningConfig,
    ReplayPreventionMiddleware, ReplayPreventionConfig,
    ResponseSignatureMiddleware, ResponseSignatureConfig,
    
    # Protection
    HoneypotMiddleware, HoneypotConfig,
    SanitizationMiddleware, SanitizationConfig,
)
```

### Rate Limiting & Protection

```python
from FastMiddleware import (
    RateLimitMiddleware, RateLimitConfig, RateLimitStore, InMemoryRateLimitStore,
    QuotaMiddleware, QuotaConfig,
    LoadSheddingMiddleware, LoadSheddingConfig,
    BulkheadMiddleware, BulkheadConfig,
    RequestDedupMiddleware, RequestDedupConfig,
    RequestCoalescingMiddleware, CoalescingConfig,
)
```

### Authentication & Authorization

```python
from FastMiddleware import (
    # JWT & API Key
    AuthenticationMiddleware, AuthConfig, AuthBackend,
    JWTAuthBackend, APIKeyAuthBackend,
    
    # Basic & Bearer
    BasicAuthMiddleware, BasicAuthConfig,
    BearerAuthMiddleware, BearerAuthConfig,
    
    # Scopes & Routes
    ScopeMiddleware, ScopeConfig,
    RouteAuthMiddleware, RouteAuthConfig, RouteAuth,
)
```

### Session & Context

```python
from FastMiddleware import (
    # Session
    SessionMiddleware, SessionConfig, SessionStore, InMemorySessionStore, Session,
    
    # Request Context
    RequestContextMiddleware, get_request_id, get_request_context,
    CorrelationMiddleware, CorrelationConfig, get_correlation_id,
    ContextMiddleware, ContextConfig, get_context, get_context_value, set_context_value,
    RequestIDPropagationMiddleware, RequestIDPropagationConfig, get_request_ids, get_trace_header,
    
    # Multi-tenancy
    TenantMiddleware, TenantConfig, get_tenant, get_tenant_id,
)
```

### Response Handling

```python
from FastMiddleware import (
    # Compression & Caching
    CompressionMiddleware, CompressionConfig,
    CacheMiddleware, CacheConfig,
    ETagMiddleware, ETagConfig,
    ResponseCacheMiddleware, ResponseCacheConfig,
    NoCacheMiddleware, NoCacheConfig,
    ConditionalRequestMiddleware, ConditionalRequestConfig,
    
    # Response Formatting
    ResponseFormatMiddleware, ResponseFormatConfig,
    DataMaskingMiddleware, DataMaskingConfig, MaskingRule,
    HATEOASMiddleware, HATEOASConfig, Link,
    
    # Performance
    BandwidthMiddleware, BandwidthConfig,
    EarlyHintsMiddleware, EarlyHintsConfig, EarlyHint,
)
```

### Error Handling

```python
from FastMiddleware import (
    ErrorHandlerMiddleware, ErrorConfig,
    ExceptionHandlerMiddleware, ExceptionHandlerConfig,
    CircuitBreakerMiddleware, CircuitBreakerConfig, CircuitState,
)
```

### Health & Monitoring

```python
from FastMiddleware import (
    # Health Checks
    HealthCheckMiddleware, HealthConfig,
    
    # Metrics & Profiling
    MetricsMiddleware, MetricsConfig, MetricsCollector,
    ProfilingMiddleware, ProfilingConfig,
    
    # Audit & Logging
    AuditMiddleware, AuditConfig, AuditEvent,
    RequestLoggerMiddleware, RequestLoggerConfig,
    
    # Timing & Performance
    ServerTimingMiddleware, ServerTimingConfig, timing, add_timing,
    ResponseTimeMiddleware, ResponseTimeConfig, ResponseTimeSLA,
    
    # Cost & Sampling
    CostTrackingMiddleware, CostTrackingConfig, get_request_cost, add_cost,
    RequestSamplerMiddleware, RequestSamplerConfig, is_sampled,
)
```

### Idempotency

```python
from FastMiddleware import (
    IdempotencyMiddleware, IdempotencyConfig, IdempotencyStore, InMemoryIdempotencyStore,
)
```

### Maintenance & Lifecycle

```python
from FastMiddleware import (
    MaintenanceMiddleware, MaintenanceConfig,
    WarmupMiddleware, WarmupConfig,
    GracefulShutdownMiddleware, GracefulShutdownConfig,
    ChaosMiddleware, ChaosConfig,
    SlowResponseMiddleware, SlowResponseConfig,
)
```

### Request Processing

```python
from FastMiddleware import (
    # Limits & Validation
    TimeoutMiddleware, TimeoutConfig,
    RequestLimitMiddleware, RequestLimitConfig,
    PayloadSizeMiddleware, PayloadSizeConfig,
    ContentTypeMiddleware, ContentTypeConfig,
    RequestValidatorMiddleware, RequestValidatorConfig, ValidationRule,
    JSONSchemaMiddleware, JSONSchemaConfig,
    
    # URL Processing
    TrailingSlashMiddleware, TrailingSlashConfig, SlashAction,
    MethodOverrideMiddleware, MethodOverrideConfig,
    
    # Headers & Fingerprinting
    HeaderTransformMiddleware, HeaderTransformConfig,
    RequestFingerprintMiddleware, FingerprintConfig, get_fingerprint,
    RequestPriorityMiddleware, PriorityConfig, Priority,
)
```

### URL & Routing

```python
from FastMiddleware import (
    RedirectMiddleware, RedirectConfig, RedirectRule,
    PathRewriteMiddleware, PathRewriteConfig, RewriteRule,
    ProxyMiddleware, ProxyConfig, ProxyRoute,  # Requires: pip install fastmvc-middleware[proxy]
)
```

### API Management

```python
from FastMiddleware import (
    VersioningMiddleware, VersioningConfig, VersionLocation, get_api_version,
    DeprecationMiddleware, DeprecationConfig, DeprecationInfo,
    RetryAfterMiddleware, RetryAfterConfig,
    APIVersionHeaderMiddleware, APIVersionHeaderConfig,
    ContentNegotiationMiddleware, ContentNegotiationConfig, get_negotiated_type,
)
```

### Detection & Analytics

```python
from FastMiddleware import (
    BotDetectionMiddleware, BotConfig, BotAction,
    GeoIPMiddleware, GeoIPConfig, get_geo_data,
    UserAgentMiddleware, UserAgentConfig, UserAgentInfo, get_user_agent,
    ClientHintsMiddleware, ClientHintsConfig, get_client_hints,
    RequestFingerprintMiddleware, FingerprintConfig, get_fingerprint,
)
```

### Feature Management & Testing

```python
from FastMiddleware import (
    FeatureFlagMiddleware, FeatureFlagConfig, get_feature_flags, is_feature_enabled,
    ABTestMiddleware, ABTestConfig, Experiment, get_variant,
)
```

### Localization

```python
from FastMiddleware import (
    LocaleMiddleware, LocaleConfig, get_locale,
    AcceptLanguageMiddleware, AcceptLanguageConfig, get_language,
)
```

### Import All (Not Recommended for Production)

```python
from FastMiddleware import *
```

---

## 📊 All Middlewares Quick Reference

| Middleware | Purpose | Basic Usage |
|------------|---------|-------------|
| **Core** |||
| `CORSMiddleware` | Cross-origin requests | `app.add_middleware(CORSMiddleware, allow_origins=["*"])` |
| `LoggingMiddleware` | Request/response logging | `app.add_middleware(LoggingMiddleware)` |
| `TimingMiddleware` | Add X-Process-Time header | `app.add_middleware(TimingMiddleware)` |
| `RequestIDMiddleware` | Generate request IDs | `app.add_middleware(RequestIDMiddleware)` |
| **Security** |||
| `SecurityHeadersMiddleware` | OWASP security headers | `app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)` |
| `CSRFMiddleware` | CSRF protection | `app.add_middleware(CSRFMiddleware, secret_key="...")` |
| `HTTPSRedirectMiddleware` | HTTP → HTTPS redirect | `app.add_middleware(HTTPSRedirectMiddleware)` |
| `IPFilterMiddleware` | IP whitelist/blacklist | `app.add_middleware(IPFilterMiddleware, whitelist={"10.0.0.0/8"})` |
| `TrustedHostMiddleware` | Host header validation | `app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])` |
| `OriginMiddleware` | Origin header validation | `app.add_middleware(OriginMiddleware, allowed_origins={"https://..."})` |
| `WebhookMiddleware` | Webhook signature validation | `app.add_middleware(WebhookMiddleware, secret_key="...")` |
| `ReferrerPolicyMiddleware` | Referrer-Policy header | `app.add_middleware(ReferrerPolicyMiddleware, policy="strict-origin")` |
| `PermissionsPolicyMiddleware` | Browser feature control | `app.add_middleware(PermissionsPolicyMiddleware, policies={...})` |
| `CSPReportMiddleware` | CSP violation reports | `CSPReportMiddleware(app, report_uri="/_csp")` |
| `HoneypotMiddleware` | Trap malicious requests | `app.add_middleware(HoneypotMiddleware, honeypot_paths={"/wp-admin"})` |
| `SanitizationMiddleware` | Input sanitization | `app.add_middleware(SanitizationMiddleware, escape_html=True)` |
| `ReplayPreventionMiddleware` | Prevent replay attacks | `app.add_middleware(ReplayPreventionMiddleware, max_age=300)` |
| `RequestSigningMiddleware` | HMAC signature validation | `app.add_middleware(RequestSigningMiddleware, secret_key="...")` |
| `ResponseSignatureMiddleware` | Sign responses | `app.add_middleware(ResponseSignatureMiddleware, secret_key="...")` |
| **Rate Limiting** |||
| `RateLimitMiddleware` | Request rate limiting | `app.add_middleware(RateLimitMiddleware, requests_per_minute=100)` |
| `QuotaMiddleware` | Usage quotas | `app.add_middleware(QuotaMiddleware, quotas={...})` |
| `LoadSheddingMiddleware` | Shed load under pressure | `app.add_middleware(LoadSheddingMiddleware, max_concurrent=1000)` |
| `BulkheadMiddleware` | Isolation pattern | `app.add_middleware(BulkheadMiddleware, max_concurrent=100)` |
| `RequestDedupMiddleware` | Deduplicate requests | `app.add_middleware(RequestDedupMiddleware, window=1.0)` |
| `RequestCoalescingMiddleware` | Coalesce identical requests | `app.add_middleware(RequestCoalescingMiddleware, window=0.1)` |
| **Authentication** |||
| `AuthenticationMiddleware` | JWT/API key auth | `app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend(...))` |
| `BasicAuthMiddleware` | HTTP Basic auth | `app.add_middleware(BasicAuthMiddleware, users={"admin": "pass"})` |
| `BearerAuthMiddleware` | Bearer token auth | `app.add_middleware(BearerAuthMiddleware, tokens={...})` |
| `ScopeMiddleware` | OAuth scope validation | `app.add_middleware(ScopeMiddleware, route_scopes={...})` |
| `RouteAuthMiddleware` | Per-route auth rules | `app.add_middleware(RouteAuthMiddleware, routes=[...])` |
| **Session & Context** |||
| `SessionMiddleware` | Server-side sessions | `app.add_middleware(SessionMiddleware, secret_key="...")` |
| `RequestContextMiddleware` | Async-safe context | `app.add_middleware(RequestContextMiddleware)` |
| `CorrelationMiddleware` | Correlation IDs | `app.add_middleware(CorrelationMiddleware)` |
| `TenantMiddleware` | Multi-tenancy | `app.add_middleware(TenantMiddleware, header_name="X-Tenant-ID")` |
| `ContextMiddleware` | Shared context values | `app.add_middleware(ContextMiddleware)` |
| `RequestIDPropagationMiddleware` | Propagate request IDs | `app.add_middleware(RequestIDPropagationMiddleware)` |
| `RealIPMiddleware` | Extract real client IP | `app.add_middleware(RealIPMiddleware)` |
| `XFFTrustMiddleware` | X-Forwarded-For handling | `app.add_middleware(XFFTrustMiddleware, trusted_proxies=[...])` |
| **Response Handling** |||
| `CompressionMiddleware` | GZip compression | `app.add_middleware(CompressionMiddleware, minimum_size=500)` |
| `CacheMiddleware` | HTTP caching headers | `app.add_middleware(CacheMiddleware, max_age=3600)` |
| `ETagMiddleware` | ETag generation | `app.add_middleware(ETagMiddleware)` |
| `ResponseCacheMiddleware` | In-memory caching | `ResponseCacheMiddleware(app, default_ttl=60)` |
| `ResponseFormatMiddleware` | Standardize responses | `app.add_middleware(ResponseFormatMiddleware, wrap_responses=True)` |
| `DataMaskingMiddleware` | Mask sensitive data | `app.add_middleware(DataMaskingMiddleware, rules=[...])` |
| `HATEOASMiddleware` | Hypermedia links | `app.add_middleware(HATEOASMiddleware, link_generators={...})` |
| `BandwidthMiddleware` | Throttle bandwidth | `app.add_middleware(BandwidthMiddleware, bytes_per_second=512*1024)` |
| `NoCacheMiddleware` | Disable caching | `app.add_middleware(NoCacheMiddleware, paths={"/api/user"})` |
| `ConditionalRequestMiddleware` | 304 Not Modified | `app.add_middleware(ConditionalRequestMiddleware)` |
| `EarlyHintsMiddleware` | HTTP 103 Early Hints | `app.add_middleware(EarlyHintsMiddleware, global_hints=[...])` |
| **Error Handling** |||
| `ErrorHandlerMiddleware` | Consistent error format | `app.add_middleware(ErrorHandlerMiddleware)` |
| `ExceptionHandlerMiddleware` | Custom exception handlers | `ExceptionHandlerMiddleware(app)` |
| `CircuitBreakerMiddleware` | Circuit breaker pattern | `app.add_middleware(CircuitBreakerMiddleware, failure_threshold=5)` |
| **Health & Monitoring** |||
| `HealthCheckMiddleware` | Health/ready/live endpoints | `app.add_middleware(HealthCheckMiddleware, version="1.0.0")` |
| `MetricsMiddleware` | Prometheus metrics | `app.add_middleware(MetricsMiddleware, endpoint="/metrics")` |
| `ProfilingMiddleware` | Request profiling | `app.add_middleware(ProfilingMiddleware, threshold_ms=100)` |
| `AuditMiddleware` | Audit logging | `app.add_middleware(AuditMiddleware)` |
| `ServerTimingMiddleware` | Server-Timing header | `app.add_middleware(ServerTimingMiddleware)` |
| `RequestLoggerMiddleware` | Access logging | `app.add_middleware(RequestLoggerMiddleware, format="combined")` |
| `ResponseTimeMiddleware` | SLA monitoring | `app.add_middleware(ResponseTimeMiddleware, slas=[...])` |
| `CostTrackingMiddleware` | Request cost tracking | `app.add_middleware(CostTrackingMiddleware, default_cost=1.0)` |
| `RequestSamplerMiddleware` | Request sampling | `app.add_middleware(RequestSamplerMiddleware, rate=0.1)` |
| **Idempotency** |||
| `IdempotencyMiddleware` | Idempotency keys | `app.add_middleware(IdempotencyMiddleware, ttl=3600)` |
| **Maintenance & Lifecycle** |||
| `MaintenanceMiddleware` | Maintenance mode | `MaintenanceMiddleware(app, enabled=False)` |
| `WarmupMiddleware` | Container warmup | `WarmupMiddleware(app, warmup_paths={"/_warmup"})` |
| `GracefulShutdownMiddleware` | Graceful shutdown | `GracefulShutdownMiddleware(app, timeout=30.0)` |
| `ChaosMiddleware` | Chaos engineering ⚠️ | `app.add_middleware(ChaosMiddleware, failure_rate=0.1)` |
| `SlowResponseMiddleware` | Artificial delays ⚠️ | `app.add_middleware(SlowResponseMiddleware, min_delay=1.0)` |
| **Request Processing** |||
| `TimeoutMiddleware` | Request timeouts | `app.add_middleware(TimeoutMiddleware, timeout=30.0)` |
| `RequestLimitMiddleware` | Body size limits | `app.add_middleware(RequestLimitMiddleware, max_size=10*1024*1024)` |
| `PayloadSizeMiddleware` | Request/response limits | `app.add_middleware(PayloadSizeMiddleware, max_request_size=...)` |
| `ContentTypeMiddleware` | Content-Type validation | `app.add_middleware(ContentTypeMiddleware, allowed_types=[...])` |
| `RequestValidatorMiddleware` | Request validation | `app.add_middleware(RequestValidatorMiddleware, rules=[...])` |
| `JSONSchemaMiddleware` | JSON Schema validation | `app.add_middleware(JSONSchemaMiddleware, schemas={...})` |
| `TrailingSlashMiddleware` | Trailing slash handling | `app.add_middleware(TrailingSlashMiddleware, action=SlashAction.STRIP)` |
| `MethodOverrideMiddleware` | HTTP method override | `app.add_middleware(MethodOverrideMiddleware)` |
| `HeaderTransformMiddleware` | Transform headers | `app.add_middleware(HeaderTransformMiddleware, add_response_headers={...})` |
| `RequestFingerprintMiddleware` | Request fingerprints | `app.add_middleware(RequestFingerprintMiddleware)` |
| `RequestPriorityMiddleware` | Request prioritization | `app.add_middleware(RequestPriorityMiddleware, path_priorities={...})` |
| **Routing** |||
| `RedirectMiddleware` | URL redirects | `app.add_middleware(RedirectMiddleware, rules=[...])` |
| `PathRewriteMiddleware` | Path rewriting | `app.add_middleware(PathRewriteMiddleware, rules=[...])` |
| `ProxyMiddleware` | Reverse proxy 🌐 | `app.add_middleware(ProxyMiddleware, routes=[...])` |
| **API Management** |||
| `VersioningMiddleware` | API versioning | `app.add_middleware(VersioningMiddleware, default_version="1.0")` |
| `DeprecationMiddleware` | Deprecation warnings | `app.add_middleware(DeprecationMiddleware, deprecations=[...])` |
| `RetryAfterMiddleware` | Retry-After headers | `app.add_middleware(RetryAfterMiddleware)` |
| `APIVersionHeaderMiddleware` | Version headers | `app.add_middleware(APIVersionHeaderMiddleware, version="2.0")` |
| `ContentNegotiationMiddleware` | Content negotiation | `app.add_middleware(ContentNegotiationMiddleware, supported_types=[...])` |
| **Detection & Analytics** |||
| `BotDetectionMiddleware` | Bot detection | `app.add_middleware(BotDetectionMiddleware, action=BotAction.TAG)` |
| `UserAgentMiddleware` | Parse User-Agent | `app.add_middleware(UserAgentMiddleware)` |
| `GeoIPMiddleware` | GeoIP from CDN headers | `app.add_middleware(GeoIPMiddleware)` |
| `ClientHintsMiddleware` | Client Hints support | `app.add_middleware(ClientHintsMiddleware, request_hints=[...])` |
| **Feature Management** |||
| `FeatureFlagMiddleware` | Feature flags | `app.add_middleware(FeatureFlagMiddleware, flags={...})` |
| `ABTestMiddleware` | A/B testing | `app.add_middleware(ABTestMiddleware, experiments=[...])` |
| **Localization** |||
| `LocaleMiddleware` | Locale detection | `app.add_middleware(LocaleMiddleware, supported_locales=[...])` |
| `AcceptLanguageMiddleware` | Language negotiation | `app.add_middleware(AcceptLanguageMiddleware, supported_languages=[...])` |

---

## 🔧 Helper Functions Reference

| Function | Module | Purpose | Example |
|----------|--------|---------|---------|
| `get_request_id()` | RequestContext | Get current request ID | `request_id = get_request_id()` |
| `get_request_context()` | RequestContext | Get full request context | `ctx = get_request_context()` |
| `get_correlation_id()` | Correlation | Get correlation ID | `corr_id = get_correlation_id()` |
| `get_tenant()` | Tenant | Get tenant object | `tenant = get_tenant()` |
| `get_tenant_id()` | Tenant | Get tenant ID string | `tenant_id = get_tenant_id()` |
| `get_context()` | Context | Get full context dict | `ctx = get_context()` |
| `get_context_value(key)` | Context | Get context value | `user_id = get_context_value("user_id")` |
| `set_context_value(k, v)` | Context | Set context value | `set_context_value("processed", True)` |
| `get_request_ids()` | RequestIDPropagation | Get request ID chain | `ids = get_request_ids()` |
| `get_trace_header()` | RequestIDPropagation | Get trace header | `header = get_trace_header()` |
| `get_real_ip()` | RealIP | Get real client IP | `ip = get_real_ip()` |
| `get_api_version()` | Versioning | Get API version | `version = get_api_version()` |
| `get_negotiated_type()` | ContentNegotiation | Get content type | `type = get_negotiated_type()` |
| `get_geo_data()` | GeoIP | Get geo data dict | `geo = get_geo_data()` |
| `get_user_agent()` | UserAgent | Get parsed UA | `ua = get_user_agent()` |
| `get_client_hints()` | ClientHints | Get client hints | `hints = get_client_hints()` |
| `get_fingerprint()` | RequestFingerprint | Get request fingerprint | `fp = get_fingerprint()` |
| `get_feature_flags()` | FeatureFlag | Get all flags | `flags = get_feature_flags()` |
| `is_feature_enabled(name)` | FeatureFlag | Check if enabled | `if is_feature_enabled("dark_mode"):` |
| `get_variant(name)` | ABTest | Get A/B variant | `variant = get_variant("checkout")` |
| `get_locale()` | Locale | Get current locale | `locale = get_locale()` |
| `get_language()` | AcceptLanguage | Get language code | `lang = get_language()` |
| `timing(name, desc)` | ServerTiming | Time a code block | `with timing("db"): ...` |
| `add_timing(name, dur)` | ServerTiming | Add timing entry | `add_timing("cache", 5.2)` |
| `get_request_cost()` | CostTracking | Get total cost | `cost = get_request_cost()` |
| `add_cost(amount)` | CostTracking | Add to cost | `add_cost(5.0)` |
| `is_sampled()` | RequestSampler | Check if sampled | `if is_sampled(): log_details()` |

---

## 📚 Complete Middleware Reference

### Prerequisites Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | No additional dependencies |
| 🔑 | Requires `pip install fastmvc-middleware[jwt]` |
| 🌐 | Requires `pip install fastmvc-middleware[proxy]` |

---

## 🔒 Security Middlewares

### SecurityHeadersMiddleware ✅

Adds comprehensive security headers (OWASP recommended).

```python
from FastMiddleware import SecurityHeadersMiddleware, SecurityHeadersConfig

app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=True,
    content_security_policy="default-src 'self'",
    x_frame_options="DENY",
)

# Or with config object
config = SecurityHeadersConfig(
    enable_hsts=True,
    hsts_max_age=31536000,
    x_content_type_options="nosniff",
    x_xss_protection="1; mode=block",
)
app.add_middleware(SecurityHeadersMiddleware, config=config)
```

**Headers added:** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`

---

### CORSMiddleware ✅

Cross-Origin Resource Sharing configuration.

```python
from FastMiddleware import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "https://app.example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=3600,
)
```

---

### CSRFMiddleware ✅

Cross-Site Request Forgery protection.

```python
from FastMiddleware import CSRFMiddleware, CSRFConfig

app.add_middleware(
    CSRFMiddleware,
    secret_key="your-secret-key",
    cookie_name="csrf_token",
    header_name="X-CSRF-Token",
)
```

**Usage:** Token is set in cookie, client must include in header for POST/PUT/DELETE.

---

### HTTPSRedirectMiddleware ✅

Redirects HTTP requests to HTTPS.

```python
from FastMiddleware import HTTPSRedirectMiddleware

app.add_middleware(
    HTTPSRedirectMiddleware,
    permanent=True,  # 301 vs 307
    exclude_paths={"/health"},
)
```

---

### IPFilterMiddleware ✅

IP-based access control (whitelist/blacklist).

```python
from FastMiddleware import IPFilterMiddleware, IPFilterConfig

# Whitelist mode
app.add_middleware(
    IPFilterMiddleware,
    whitelist={"192.168.1.0/24", "10.0.0.0/8"},
)

# Blacklist mode
app.add_middleware(
    IPFilterMiddleware,
    blacklist={"192.168.1.100", "10.0.0.50"},
)
```

---

### TrustedHostMiddleware ✅

Validates Host header to prevent host header attacks.

```python
from FastMiddleware import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"],
)
```

---

### OriginMiddleware ✅

Validates Origin header for cross-origin requests.

```python
from FastMiddleware import OriginMiddleware, OriginConfig

app.add_middleware(
    OriginMiddleware,
    allowed_origins={"https://example.com", "https://app.example.com"},
    block_null_origin=True,
)
```

---

### WebhookMiddleware ✅

Validates incoming webhook signatures.

```python
from FastMiddleware import WebhookMiddleware, WebhookConfig

app.add_middleware(
    WebhookMiddleware,
    secret_key="webhook-secret",
    signature_header="X-Webhook-Signature",
    paths={"/webhooks/stripe", "/webhooks/github"},
)
```

---

### ReferrerPolicyMiddleware ✅

Sets Referrer-Policy header.

```python
from FastMiddleware import ReferrerPolicyMiddleware

app.add_middleware(
    ReferrerPolicyMiddleware,
    policy="strict-origin-when-cross-origin",
)
```

**Valid policies:** `no-referrer`, `no-referrer-when-downgrade`, `origin`, `origin-when-cross-origin`, `same-origin`, `strict-origin`, `strict-origin-when-cross-origin`, `unsafe-url`

---

### PermissionsPolicyMiddleware ✅

Controls browser feature permissions.

```python
from FastMiddleware import PermissionsPolicyMiddleware

app.add_middleware(
    PermissionsPolicyMiddleware,
    policies={
        "camera": [],  # Disabled
        "microphone": [],
        "geolocation": ["self"],  # Same origin only
        "fullscreen": ["self", "https://youtube.com"],
    },
)
```

---

### CSPReportMiddleware ✅

Handles CSP violation reports.

```python
from FastMiddleware import CSPReportMiddleware

csp_reporter = CSPReportMiddleware(
    app,
    report_uri="/_csp-report",
    log_reports=True,
    store_reports=True,
)

# Get stored reports
reports = csp_reporter.get_reports()
```

---

### HoneypotMiddleware ✅

Traps malicious requests with fake endpoints.

```python
from FastMiddleware import HoneypotMiddleware, HoneypotConfig

app.add_middleware(
    HoneypotMiddleware,
    honeypot_paths={"/admin.php", "/wp-admin", "/.env", "/.git/config"},
    block_on_access=True,
    block_duration=3600,  # 1 hour
)
```

---

### SanitizationMiddleware ✅

Sanitizes input to prevent XSS and injection.

```python
from FastMiddleware import SanitizationMiddleware, SanitizationConfig

app.add_middleware(
    SanitizationMiddleware,
    escape_html=True,
    strip_tags=True,
    remove_null_bytes=True,
)
```

---

### ReplayPreventionMiddleware ✅

Prevents replay attacks using timestamps and nonces.

```python
from FastMiddleware import ReplayPreventionMiddleware

app.add_middleware(
    ReplayPreventionMiddleware,
    max_age=300,  # 5 minutes
    timestamp_header="X-Timestamp",
    nonce_header="X-Nonce",
)
```

**Client must include:** `X-Timestamp` (Unix timestamp) and `X-Nonce` (unique string)

---

### RequestSigningMiddleware ✅

Validates HMAC request signatures.

```python
from FastMiddleware import RequestSigningMiddleware

app.add_middleware(
    RequestSigningMiddleware,
    secret_key="your-shared-secret",
    signature_header="X-Signature",
    algorithm="sha256",
)
```

**Signature format:** `HMAC-SHA256(secret, "{timestamp}.{method}.{path}.{body}")`

---

## 🔐 Authentication Middlewares

### AuthenticationMiddleware 🔑

Pluggable authentication with JWT and API key support.

```python
from FastMiddleware import AuthenticationMiddleware, JWTAuthBackend, APIKeyAuthBackend

# JWT Authentication
app.add_middleware(
    AuthenticationMiddleware,
    backend=JWTAuthBackend(
        secret_key="your-jwt-secret",
        algorithm="HS256",
    ),
    exclude_paths={"/login", "/register", "/health"},
)

# API Key Authentication
app.add_middleware(
    AuthenticationMiddleware,
    backend=APIKeyAuthBackend(
        api_keys={"key123": {"user_id": 1, "role": "admin"}},
        header_name="X-API-Key",
    ),
)
```

**Prerequisites:** `pip install fastmvc-middleware[jwt]` for JWT support

---

### BasicAuthMiddleware ✅

HTTP Basic Authentication.

```python
from FastMiddleware import BasicAuthMiddleware

app.add_middleware(
    BasicAuthMiddleware,
    users={"admin": "secret123", "user": "password"},
    realm="API",
)
```

---

### BearerAuthMiddleware ✅

Bearer token authentication.

```python
from FastMiddleware import BearerAuthMiddleware

app.add_middleware(
    BearerAuthMiddleware,
    tokens={
        "token123": {"user_id": 1, "role": "admin"},
        "token456": {"user_id": 2, "role": "user"},
    },
)

# Or with custom validation
middleware = BearerAuthMiddleware(app)
middleware.set_validate_func(lambda token: validate_with_db(token))
```

---

### ScopeMiddleware ✅

OAuth scope validation.

```python
from FastMiddleware import ScopeMiddleware

app.add_middleware(
    ScopeMiddleware,
    route_scopes={
        "/api/users": ["users:read"],
        "/api/admin": ["admin:all"],
    },
    require_all=False,  # Any matching scope is sufficient
)
```

---

### RouteAuthMiddleware ✅

Per-route authentication requirements.

```python
from FastMiddleware import RouteAuthMiddleware, RouteAuth

app.add_middleware(
    RouteAuthMiddleware,
    routes=[
        RouteAuth("/api/public", require_auth=False),
        RouteAuth("/api/user", require_auth=True),
        RouteAuth("/api/admin", require_auth=True, required_roles=["admin"]),
    ],
)
```

---

## 📊 Observability Middlewares

### LoggingMiddleware ✅

Structured request/response logging.

```python
from FastMiddleware import LoggingMiddleware

app.add_middleware(
    LoggingMiddleware,
    log_request_body=False,
    log_response_body=False,
    exclude_paths={"/health", "/metrics"},
)
```

---

### TimingMiddleware ✅

Adds processing time to response headers.

```python
from FastMiddleware import TimingMiddleware

app.add_middleware(TimingMiddleware)
# Response includes: X-Process-Time: 0.0234
```

---

### RequestIDMiddleware ✅

Generates unique request IDs.

```python
from FastMiddleware import RequestIDMiddleware

app.add_middleware(
    RequestIDMiddleware,
    header_name="X-Request-ID",
    include_in_response=True,
)
```

---

### RequestContextMiddleware ✅

Async-safe context variables.

```python
from FastMiddleware import RequestContextMiddleware, get_request_id, get_request_context

app.add_middleware(RequestContextMiddleware)

@app.get("/")
async def handler():
    request_id = get_request_id()
    context = get_request_context()
    return {"request_id": request_id}
```

---

### MetricsMiddleware ✅

Prometheus-compatible metrics.

```python
from FastMiddleware import MetricsMiddleware, MetricsConfig

app.add_middleware(
    MetricsMiddleware,
    endpoint="/metrics",
    include_path_labels=True,
)
```

**Metrics exposed:** `http_requests_total`, `http_request_duration_seconds`, `http_requests_in_progress`

---

### ProfilingMiddleware ✅

Request performance profiling.

```python
from FastMiddleware import ProfilingMiddleware

app.add_middleware(
    ProfilingMiddleware,
    enabled=True,
    threshold_ms=100,  # Only profile requests > 100ms
)
```

---

### AuditMiddleware ✅

Audit logging for compliance.

```python
from FastMiddleware import AuditMiddleware, AuditConfig

app.add_middleware(
    AuditMiddleware,
    log_request_body=True,
    log_response_body=False,
    sensitive_headers={"Authorization", "Cookie"},
)
```

---

### ServerTimingMiddleware ✅

Server-Timing header for browser devtools.

```python
from FastMiddleware import ServerTimingMiddleware, timing

app.add_middleware(ServerTimingMiddleware)

@app.get("/")
async def handler():
    with timing("db", "Database query"):
        result = await db.query(...)
    
    with timing("render"):
        output = render(result)
    
    return output
```

---

### RequestLoggerMiddleware ✅

Access logging in various formats.

```python
from FastMiddleware import RequestLoggerMiddleware

app.add_middleware(
    RequestLoggerMiddleware,
    format="combined",  # "combined", "common", "json"
    skip_paths={"/health", "/metrics"},
)
```

---

### CostTrackingMiddleware ✅

Track request costs for billing.

```python
from FastMiddleware import CostTrackingMiddleware, add_cost, get_request_cost

app.add_middleware(
    CostTrackingMiddleware,
    path_costs={"/api/expensive": 10.0, "/api/cheap": 0.5},
    default_cost=1.0,
)

@app.get("/api/custom")
async def handler():
    add_cost(5.0)  # External API call
    return {"cost": get_request_cost()}
```

---

### RequestSamplerMiddleware ✅

Sample requests for analytics.

```python
from FastMiddleware import RequestSamplerMiddleware, is_sampled

app.add_middleware(
    RequestSamplerMiddleware,
    rate=0.1,  # 10% sampling
    path_rates={"/api/high-traffic": 0.01},
)

@app.get("/")
async def handler():
    if is_sampled():
        log_detailed_metrics()
    return {"sampled": is_sampled()}
```

---

## 🛡️ Resilience Middlewares

### RateLimitMiddleware ✅

Sliding window rate limiting.

```python
from FastMiddleware import RateLimitMiddleware, RateLimitConfig

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100,
    burst_size=10,
)

# Custom key function
config = RateLimitConfig(
    requests_per_minute=100,
    key_func=lambda req: req.headers.get("X-API-Key", req.client.host),
)
app.add_middleware(RateLimitMiddleware, config=config)
```

**Response headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

### CircuitBreakerMiddleware ✅

Circuit breaker pattern.

```python
from FastMiddleware import CircuitBreakerMiddleware, CircuitBreakerConfig

app.add_middleware(
    CircuitBreakerMiddleware,
    failure_threshold=5,
    recovery_timeout=30,
    half_open_requests=3,
)
```

**States:** `CLOSED` (normal), `OPEN` (failing), `HALF_OPEN` (testing)

---

### BulkheadMiddleware ✅

Bulkhead pattern for isolation.

```python
from FastMiddleware import BulkheadMiddleware

app.add_middleware(
    BulkheadMiddleware,
    max_concurrent=100,
    max_waiting=50,
    timeout=30.0,
)
```

---

### LoadSheddingMiddleware ✅

Shed load during high traffic.

```python
from FastMiddleware import LoadSheddingMiddleware

app.add_middleware(
    LoadSheddingMiddleware,
    max_concurrent=1000,
    shed_probability=0.5,  # Shed 50% when over limit
)
```

---

### TimeoutMiddleware ✅

Request timeout enforcement.

```python
from FastMiddleware import TimeoutMiddleware

app.add_middleware(
    TimeoutMiddleware,
    timeout=30.0,  # 30 seconds
    exclude_paths={"/upload"},
)
```

---

### ErrorHandlerMiddleware ✅

Consistent error response formatting.

```python
from FastMiddleware import ErrorHandlerMiddleware, ErrorConfig

app.add_middleware(
    ErrorHandlerMiddleware,
    include_traceback=False,  # True for development
    default_message="Internal server error",
)
```

---

### ExceptionHandlerMiddleware ✅

Custom exception handling.

```python
from FastMiddleware import ExceptionHandlerMiddleware

handler = ExceptionHandlerMiddleware(app, debug=False)

@handler.register(ValueError)
def handle_value_error(exc):
    return JSONResponse(status_code=400, content={"error": str(exc)})
```

---

### GracefulShutdownMiddleware ✅

Graceful shutdown with request draining.

```python
from FastMiddleware import GracefulShutdownMiddleware

shutdown_mw = GracefulShutdownMiddleware(app, timeout=30.0)

# When receiving SIGTERM
await shutdown_mw.shutdown()
```

---

### RequestDedupMiddleware ✅

Deduplicate concurrent requests.

```python
from FastMiddleware import RequestDedupMiddleware

app.add_middleware(
    RequestDedupMiddleware,
    window=1.0,  # 1 second window
)
```

---

### RequestCoalescingMiddleware ✅

Coalesce identical requests.

```python
from FastMiddleware import RequestCoalescingMiddleware

app.add_middleware(
    RequestCoalescingMiddleware,
    window=0.1,  # 100ms window
)
```

---

## ⚡ Performance Middlewares

### CompressionMiddleware ✅

GZip response compression.

```python
from FastMiddleware import CompressionMiddleware, CompressionConfig

app.add_middleware(
    CompressionMiddleware,
    minimum_size=500,  # Only compress responses > 500 bytes
    compresslevel=6,
)
```

---

### CacheMiddleware ✅

HTTP caching with ETags.

```python
from FastMiddleware import CacheMiddleware, CacheConfig

app.add_middleware(
    CacheMiddleware,
    max_age=3600,
    stale_while_revalidate=60,
    private=False,
)
```

---

### ETagMiddleware ✅

ETag generation and validation.

```python
from FastMiddleware import ETagMiddleware

app.add_middleware(
    ETagMiddleware,
    weak=True,
)
```

---

### ResponseCacheMiddleware ✅

In-memory response caching.

```python
from FastMiddleware import ResponseCacheMiddleware

cache = ResponseCacheMiddleware(
    app,
    default_ttl=60,
    max_size=1000,
    path_ttls={"/api/static": 3600},
)

# Invalidate cache
cache.invalidate("/api/users")
cache.clear()
```

---

### BandwidthMiddleware ✅

Response bandwidth throttling.

```python
from FastMiddleware import BandwidthMiddleware

app.add_middleware(
    BandwidthMiddleware,
    bytes_per_second=512 * 1024,  # 512 KB/s
)
```

---

### NoCacheMiddleware ✅

Disable caching headers.

```python
from FastMiddleware import NoCacheMiddleware

app.add_middleware(
    NoCacheMiddleware,
    paths={"/api/user", "/api/session"},
)
```

---

### ConditionalRequestMiddleware ✅

If-None-Match / If-Modified-Since handling.

```python
from FastMiddleware import ConditionalRequestMiddleware

app.add_middleware(ConditionalRequestMiddleware)
# Returns 304 Not Modified when appropriate
```

---

### EarlyHintsMiddleware ✅

HTTP 103 Early Hints (via Link header).

```python
from FastMiddleware import EarlyHintsMiddleware, EarlyHint

app.add_middleware(
    EarlyHintsMiddleware,
    global_hints=[
        EarlyHint("/static/css/main.css", as_type="style"),
        EarlyHint("/static/js/app.js", as_type="script"),
    ],
)
```

---

### ResponseSignatureMiddleware ✅

Sign responses for verification.

```python
from FastMiddleware import ResponseSignatureMiddleware

app.add_middleware(
    ResponseSignatureMiddleware,
    secret_key="your-secret",
    signature_header="X-Response-Signature",
)
```

---

### ResponseFormatMiddleware ✅

Standardize response format (wrap all responses).

```python
from FastMiddleware import ResponseFormatMiddleware, ResponseFormatConfig

app.add_middleware(
    ResponseFormatMiddleware,
    wrap_responses=True,
    success_key="data",
    error_key="error",
    include_metadata=True,
)

# Responses become:
# {
#     "data": { ... },
#     "metadata": {
#         "request_id": "...",
#         "timestamp": "...",
#         "duration_ms": 12.5
#     }
# }
```

---

## 🔧 Operations Middlewares

### HealthCheckMiddleware ✅

Health, readiness, and liveness endpoints.

```python
from FastMiddleware import HealthCheckMiddleware, HealthConfig

app.add_middleware(
    HealthCheckMiddleware,
    health_path="/health",
    ready_path="/ready",
    live_path="/live",
    version="1.0.0",
)
```

---

### MaintenanceMiddleware ✅

Maintenance mode with bypass options.

```python
from FastMiddleware import MaintenanceMiddleware

maint = MaintenanceMiddleware(
    app,
    enabled=False,
    bypass_ips={"192.168.1.0/24"},
    bypass_paths={"/health"},
    bypass_token="secret-bypass-token",
)

# Enable maintenance mode
maint.enable()
maint.disable()
```

---

### WarmupMiddleware ✅

Container warmup handling.

```python
from FastMiddleware import WarmupMiddleware

warmup = WarmupMiddleware(
    app,
    warmup_paths={"/_warmup", "/_ah/warmup"},
    min_warmup_time=5.0,
)

# Mark as ready
warmup.set_ready(True)
```

---

### ChaosMiddleware ✅

Chaos engineering (testing only!).

```python
from FastMiddleware import ChaosMiddleware

app.add_middleware(
    ChaosMiddleware,
    enabled=os.getenv("CHAOS_ENABLED") == "true",
    failure_rate=0.1,  # 10% failures
    latency_rate=0.2,  # 20% latency injection
    min_latency=0.5,
    max_latency=5.0,
)
```

⚠️ **Never enable in production!**

---

### SlowResponseMiddleware ✅

Artificial delays (testing only).

```python
from FastMiddleware import SlowResponseMiddleware

app.add_middleware(
    SlowResponseMiddleware,
    enabled=os.getenv("SLOW_MODE") == "true",
    min_delay=1.0,
    max_delay=3.0,
)
```

---

## 🌐 API Management Middlewares

### VersioningMiddleware ✅

API versioning via header, query, or path.

```python
from FastMiddleware import VersioningMiddleware, VersionLocation, get_api_version

app.add_middleware(
    VersioningMiddleware,
    default_version="1.0",
    location=VersionLocation.HEADER,  # HEADER, QUERY, PATH
    header_name="X-API-Version",
)

@app.get("/")
async def handler():
    version = get_api_version()
    return {"version": version}
```

---

### DeprecationMiddleware ✅

API deprecation warnings.

```python
from FastMiddleware import DeprecationMiddleware, DeprecationInfo

app.add_middleware(
    DeprecationMiddleware,
    deprecations=[
        DeprecationInfo(
            path="/api/v1/users",
            sunset_date="2025-12-31",
            replacement="/api/v2/users",
        ),
    ],
)
```

**Response headers:** `Deprecation`, `Sunset`, `Link` (to replacement)

---

### RetryAfterMiddleware ✅

Retry-After headers for rate limits.

```python
from FastMiddleware import RetryAfterMiddleware

app.add_middleware(
    RetryAfterMiddleware,
    default_retry_after=60,
)
```

---

### APIVersionHeaderMiddleware ✅

Add API version to all responses.

```python
from FastMiddleware import APIVersionHeaderMiddleware

app.add_middleware(
    APIVersionHeaderMiddleware,
    version="2.1.0",
    min_version="1.5.0",
    sunset_date="2025-12-31",
)
```

---

### ContentNegotiationMiddleware ✅

Accept header content negotiation.

```python
from FastMiddleware import ContentNegotiationMiddleware, get_negotiated_type

app.add_middleware(
    ContentNegotiationMiddleware,
    supported_types=["application/json", "application/xml"],
    strict=True,  # 406 if no match
)

@app.get("/")
async def handler():
    content_type = get_negotiated_type()
    if content_type == "application/xml":
        return xml_response()
    return json_response()
```

---

### JSONSchemaMiddleware ✅

Validate requests against JSON Schema.

```python
from FastMiddleware import JSONSchemaMiddleware

user_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string"},
    },
    "required": ["name", "email"],
}

app.add_middleware(
    JSONSchemaMiddleware,
    schemas={"/api/users": user_schema},
    strict=True,
)
```

---

### HATEOASMiddleware ✅

Add hypermedia links to responses.

```python
from FastMiddleware import HATEOASMiddleware, Link

app.add_middleware(
    HATEOASMiddleware,
    link_generators={
        "/api/users": [
            Link(rel="create", href="/api/users", method="POST"),
            Link(rel="self", href="/api/users", method="GET"),
        ],
    },
)
```

---

## 👤 Detection Middlewares

### BotDetectionMiddleware ✅

Detect and handle bot traffic.

```python
from FastMiddleware import BotDetectionMiddleware, BotAction

app.add_middleware(
    BotDetectionMiddleware,
    action=BotAction.TAG,  # TAG, BLOCK, CHALLENGE
    block_malicious=True,
)
```

---

### UserAgentMiddleware ✅

Parse User-Agent headers.

```python
from FastMiddleware import UserAgentMiddleware, get_user_agent

app.add_middleware(UserAgentMiddleware)

@app.get("/")
async def handler():
    ua = get_user_agent()
    return {
        "browser": ua["browser"],
        "os": ua["os"],
        "is_mobile": ua["is_mobile"],
        "is_bot": ua["is_bot"],
    }
```

---

### GeoIPMiddleware ✅

Extract GeoIP from CDN headers.

```python
from FastMiddleware import GeoIPMiddleware, get_geo_data

app.add_middleware(GeoIPMiddleware)

@app.get("/")
async def handler():
    geo = get_geo_data()
    return {
        "country": geo.get("country"),
        "city": geo.get("city"),
    }
```

---

### ClientHintsMiddleware ✅

Client Hints support.

```python
from FastMiddleware import ClientHintsMiddleware, get_client_hints

app.add_middleware(
    ClientHintsMiddleware,
    request_hints=["DPR", "Viewport-Width", "Save-Data"],
)

@app.get("/")
async def handler():
    hints = get_client_hints()
    return {
        "dpr": hints.get("dpr"),
        "save_data": hints.get("save_data"),
    }
```

---

### RequestFingerprintMiddleware ✅

Create request fingerprints.

```python
from FastMiddleware import RequestFingerprintMiddleware, get_fingerprint

app.add_middleware(RequestFingerprintMiddleware)

@app.get("/")
async def handler():
    return {"fingerprint": get_fingerprint()}
```

---

## 🧪 Testing Middlewares

### FeatureFlagMiddleware ✅

Feature flag management.

```python
from FastMiddleware import FeatureFlagMiddleware, is_feature_enabled, get_feature_flags

app.add_middleware(
    FeatureFlagMiddleware,
    flags={
        "new_dashboard": True,
        "dark_mode": False,
    },
)

@app.get("/")
async def handler():
    if is_feature_enabled("new_dashboard"):
        return new_dashboard()
    return old_dashboard()
```

---

### ABTestMiddleware ✅

A/B testing support.

```python
from FastMiddleware import ABTestMiddleware, Experiment, get_variant

app.add_middleware(
    ABTestMiddleware,
    experiments=[
        Experiment(
            name="checkout_flow",
            variants=["control", "variant_a", "variant_b"],
            weights=[0.5, 0.25, 0.25],
        ),
    ],
)

@app.get("/")
async def handler():
    variant = get_variant("checkout_flow")
    return {"variant": variant}
```

---

## 🌍 Localization Middlewares

### LocaleMiddleware ✅

Locale detection.

```python
from FastMiddleware import LocaleMiddleware, get_locale

app.add_middleware(
    LocaleMiddleware,
    supported_locales=["en", "es", "fr", "de"],
    default_locale="en",
)

@app.get("/")
async def handler():
    locale = get_locale()
    return get_translations(locale)
```

---

### AcceptLanguageMiddleware ✅

Accept-Language negotiation.

```python
from FastMiddleware import AcceptLanguageMiddleware, get_language

app.add_middleware(
    AcceptLanguageMiddleware,
    supported_languages=["en", "es", "fr"],
    default_language="en",
)

@app.get("/")
async def handler():
    lang = get_language()
    return {"language": lang}
```

---

## 🔀 Routing Middlewares

### RedirectMiddleware ✅

URL redirects.

```python
from FastMiddleware import RedirectMiddleware, RedirectRule

app.add_middleware(
    RedirectMiddleware,
    rules=[
        RedirectRule("/old-path", "/new-path", permanent=True),
        RedirectRule("/legacy/*", "/api/v2/{path}"),
    ],
)
```

---

### PathRewriteMiddleware ✅

Path rewriting.

```python
from FastMiddleware import PathRewriteMiddleware, RewriteRule

app.add_middleware(
    PathRewriteMiddleware,
    rules=[
        RewriteRule("/old-api", "/api/v1"),
        RewriteRule(r"/users/(\d+)", r"/api/users/\1", is_regex=True),
    ],
)
```

---

### ProxyMiddleware 🌐

Reverse proxy to other services.

```python
from FastMiddleware import ProxyMiddleware, ProxyRoute

app.add_middleware(
    ProxyMiddleware,
    routes=[
        ProxyRoute(
            path_prefix="/api/v2",
            target="http://new-api:8000",
            strip_prefix=True,
        ),
    ],
)
```

**Prerequisites:** `pip install fastmvc-middleware[proxy]`

---

### MethodOverrideMiddleware ✅

HTTP method override.

```python
from FastMiddleware import MethodOverrideMiddleware

app.add_middleware(MethodOverrideMiddleware)
# POST /resource?_method=DELETE becomes DELETE /resource
# POST /resource with X-HTTP-Method-Override: DELETE becomes DELETE /resource
```

---

### TrailingSlashMiddleware ✅

Trailing slash handling.

```python
from FastMiddleware import TrailingSlashMiddleware, SlashAction

app.add_middleware(
    TrailingSlashMiddleware,
    action=SlashAction.STRIP,  # STRIP, ADD, REDIRECT
)
```

---

### HeaderTransformMiddleware ✅

Transform request/response headers.

```python
from FastMiddleware import HeaderTransformMiddleware

app.add_middleware(
    HeaderTransformMiddleware,
    add_request_headers={"X-Custom": "value"},
    add_response_headers={"X-Powered-By": "FastMVC"},
    remove_response_headers={"Server"},
)
```

---

## 🆔 Context Middlewares

### SessionMiddleware ✅

Server-side sessions.

```python
from FastMiddleware import SessionMiddleware, SessionConfig

app.add_middleware(
    SessionMiddleware,
    secret_key="session-secret",
    cookie_name="session_id",
    max_age=3600,
)
```

---

### TenantMiddleware ✅

Multi-tenancy support.

```python
from FastMiddleware import TenantMiddleware, get_tenant_id

app.add_middleware(
    TenantMiddleware,
    header_name="X-Tenant-ID",
)

@app.get("/")
async def handler():
    tenant_id = get_tenant_id()
    return {"tenant": tenant_id}
```

---

### CorrelationMiddleware ✅

Correlation ID tracking.

```python
from FastMiddleware import CorrelationMiddleware, get_correlation_id

app.add_middleware(
    CorrelationMiddleware,
    header_name="X-Correlation-ID",
)

@app.get("/")
async def handler():
    return {"correlation_id": get_correlation_id()}
```

---

### RequestIDPropagationMiddleware ✅

Propagate request IDs across services.

```python
from FastMiddleware import RequestIDPropagationMiddleware, get_request_ids

app.add_middleware(RequestIDPropagationMiddleware)

@app.get("/")
async def handler():
    ids = get_request_ids()  # Chain of IDs from upstream services
    return {"request_chain": ids}
```

---

### ContextMiddleware ✅

Shared request context.

```python
from FastMiddleware import ContextMiddleware, get_context_value, set_context_value

app.add_middleware(
    ContextMiddleware,
    extract_headers={"X-User-ID": "user_id"},
)

@app.get("/")
async def handler():
    user_id = get_context_value("user_id")
    set_context_value("processed", True)
    return {"user_id": user_id}
```

---

### RealIPMiddleware ✅

Extract real client IP.

```python
from FastMiddleware import RealIPMiddleware, get_real_ip

app.add_middleware(RealIPMiddleware)

@app.get("/")
async def handler():
    return {"ip": get_real_ip()}
```

---

### XFFTrustMiddleware ✅

X-Forwarded-For trust handling.

```python
from FastMiddleware import XFFTrustMiddleware

app.add_middleware(
    XFFTrustMiddleware,
    trusted_proxies=["10.0.0.0/8", "172.16.0.0/12"],
    depth=2,  # Skip 2 rightmost proxies
)
```

---

## 📄 Additional Middlewares

### DataMaskingMiddleware ✅

Mask sensitive data in logs.

```python
from FastMiddleware import DataMaskingMiddleware, MaskingRule

app.add_middleware(
    DataMaskingMiddleware,
    rules=[
        MaskingRule(field="password", mask="***"),
        MaskingRule(field="ssn", mask="XXX-XX-****"),
    ],
)
```

---

### QuotaMiddleware ✅

Usage quota enforcement.

```python
from FastMiddleware import QuotaMiddleware

app.add_middleware(
    QuotaMiddleware,
    quotas={
        "free": {"requests_per_day": 1000},
        "pro": {"requests_per_day": 100000},
    },
)
```

---

### IdempotencyMiddleware ✅

Idempotency key support.

```python
from FastMiddleware import IdempotencyMiddleware

app.add_middleware(
    IdempotencyMiddleware,
    header_name="Idempotency-Key",
    ttl=3600,
)
```

---

### RequestLimitMiddleware ✅

Request body size limits.

```python
from FastMiddleware import RequestLimitMiddleware

app.add_middleware(
    RequestLimitMiddleware,
    max_size=10 * 1024 * 1024,  # 10 MB
)
```

---

### PayloadSizeMiddleware ✅

Request/response size limits.

```python
from FastMiddleware import PayloadSizeMiddleware

app.add_middleware(
    PayloadSizeMiddleware,
    max_request_size=10 * 1024 * 1024,
    max_response_size=50 * 1024 * 1024,
)
```

---

### ContentTypeMiddleware ✅

Content-Type validation.

```python
from FastMiddleware import ContentTypeMiddleware

app.add_middleware(
    ContentTypeMiddleware,
    allowed_types=["application/json", "application/xml"],
)
```

---

### RequestValidatorMiddleware ✅

Request structure validation.

```python
from FastMiddleware import RequestValidatorMiddleware, ValidationRule

app.add_middleware(
    RequestValidatorMiddleware,
    rules=[
        ValidationRule(
            path="/api/upload",
            method="POST",
            required_headers=["Content-Type"],
            content_types=["multipart/form-data"],
            max_body_size=10 * 1024 * 1024,
        ),
    ],
)
```

---

### ResponseTimeMiddleware ✅

Response time SLA monitoring.

```python
from FastMiddleware import ResponseTimeMiddleware, ResponseTimeSLA

app.add_middleware(
    ResponseTimeMiddleware,
    slas=[
        ResponseTimeSLA("/api/health", target_ms=50, warning_ms=100, critical_ms=200),
        ResponseTimeSLA("/api/search", target_ms=500, warning_ms=1000, critical_ms=2000),
    ],
)
```

---

### RequestPriorityMiddleware ✅

Request prioritization.

```python
from FastMiddleware import RequestPriorityMiddleware, Priority

app.add_middleware(
    RequestPriorityMiddleware,
    path_priorities={
        "/api/health": Priority.CRITICAL,
        "/api/webhooks": Priority.HIGH,
        "/api/reports": Priority.LOW,
    },
)
```

---

## 📖 More Documentation

- [API Reference](docs/API.md)
- [Examples](docs/EXAMPLES.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) file.
