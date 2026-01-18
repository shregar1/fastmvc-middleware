"""
FastMVC Middleware - Production-ready middlewares for FastAPI applications.

A comprehensive collection of 90+ battle-tested, configurable middleware components
for building robust FastAPI/Starlette applications.
"""

from fastmiddleware.base import FastMVCMiddleware

# ============================================================================
# Factory & Utilities
# ============================================================================
from fastmiddleware.factory import (
    create_middleware,
    middleware,
    MiddlewareBuilder,
    MiddlewareConfig,
    add_middleware_once,
    quick_middleware,
    is_middleware_registered,
    clear_registry,
)

# ============================================================================
# Core Middlewares
# ============================================================================
from fastmiddleware.cors import CORSMiddleware
from fastmiddleware.logging import LoggingMiddleware
from fastmiddleware.timing import TimingMiddleware
from fastmiddleware.request_id import RequestIDMiddleware

# ============================================================================
# Security Middlewares
# ============================================================================
from fastmiddleware.security import SecurityHeadersMiddleware, SecurityHeadersConfig
from fastmiddleware.trusted_host import TrustedHostMiddleware
from fastmiddleware.csrf import CSRFMiddleware, CSRFConfig
from fastmiddleware.https_redirect import HTTPSRedirectMiddleware, HTTPSRedirectConfig
from fastmiddleware.ip_filter import IPFilterMiddleware, IPFilterConfig
from fastmiddleware.origin import OriginMiddleware, OriginConfig
from fastmiddleware.webhook import WebhookMiddleware, WebhookConfig
from fastmiddleware.referrer_policy import ReferrerPolicyMiddleware, ReferrerPolicyConfig
from fastmiddleware.permissions_policy import PermissionsPolicyMiddleware, PermissionsPolicyConfig
from fastmiddleware.csp_report import CSPReportMiddleware, CSPReportConfig
from fastmiddleware.replay_prevention import ReplayPreventionMiddleware, ReplayPreventionConfig
from fastmiddleware.request_signing import RequestSigningMiddleware, RequestSigningConfig
from fastmiddleware.honeypot import HoneypotMiddleware, HoneypotConfig
from fastmiddleware.sanitization import SanitizationMiddleware, SanitizationConfig

# ============================================================================
# Rate Limiting & Protection
# ============================================================================
from fastmiddleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitConfig,
    RateLimitStore,
    InMemoryRateLimitStore,
)
from fastmiddleware.quota import QuotaMiddleware, QuotaConfig
from fastmiddleware.load_shedding import LoadSheddingMiddleware, LoadSheddingConfig
from fastmiddleware.bulkhead import BulkheadMiddleware, BulkheadConfig
from fastmiddleware.request_dedup import RequestDedupMiddleware, RequestDedupConfig
from fastmiddleware.request_coalescing import RequestCoalescingMiddleware, CoalescingConfig

# ============================================================================
# Authentication & Authorization
# ============================================================================
from fastmiddleware.authentication import (
    AuthenticationMiddleware,
    AuthConfig,
    AuthBackend,
    JWTAuthBackend,
    APIKeyAuthBackend,
)
from fastmiddleware.basic_auth import BasicAuthMiddleware, BasicAuthConfig
from fastmiddleware.bearer_auth import BearerAuthMiddleware, BearerAuthConfig
from fastmiddleware.scope import ScopeMiddleware, ScopeConfig
from fastmiddleware.route_auth import RouteAuthMiddleware, RouteAuthConfig, RouteAuth

# ============================================================================
# Session & Context
# ============================================================================
from fastmiddleware.session import (
    SessionMiddleware,
    SessionConfig,
    SessionStore,
    InMemorySessionStore,
    Session,
)
from fastmiddleware.request_context import (
    RequestContextMiddleware,
    get_request_id,
    get_request_context,
)
from fastmiddleware.correlation import (
    CorrelationMiddleware,
    CorrelationConfig,
    get_correlation_id,
)
from fastmiddleware.tenant import (
    TenantMiddleware,
    TenantConfig,
    get_tenant,
    get_tenant_id,
)
from fastmiddleware.context import (
    ContextMiddleware,
    ContextConfig,
    get_context,
    get_context_value,
    set_context_value,
)
from fastmiddleware.request_id_propagation import (
    RequestIDPropagationMiddleware,
    RequestIDPropagationConfig,
    get_request_ids,
    get_trace_header,
)

# ============================================================================
# Response Handling
# ============================================================================
from fastmiddleware.compression import CompressionMiddleware, CompressionConfig
from fastmiddleware.response_format import ResponseFormatMiddleware, ResponseFormatConfig
from fastmiddleware.cache import CacheMiddleware, CacheConfig
from fastmiddleware.etag import ETagMiddleware, ETagConfig
from fastmiddleware.data_masking import DataMaskingMiddleware, DataMaskingConfig, MaskingRule
from fastmiddleware.response_cache import ResponseCacheMiddleware, ResponseCacheConfig
from fastmiddleware.response_signature import ResponseSignatureMiddleware, ResponseSignatureConfig
from fastmiddleware.hateoas import HATEOASMiddleware, HATEOASConfig, Link
from fastmiddleware.bandwidth import BandwidthMiddleware, BandwidthConfig
from fastmiddleware.no_cache import NoCacheMiddleware, NoCacheConfig
from fastmiddleware.conditional_request import ConditionalRequestMiddleware, ConditionalRequestConfig
from fastmiddleware.early_hints import EarlyHintsMiddleware, EarlyHintsConfig, EarlyHint

# ============================================================================
# Error Handling
# ============================================================================
from fastmiddleware.error_handler import ErrorHandlerMiddleware, ErrorConfig
from fastmiddleware.circuit_breaker import CircuitBreakerMiddleware, CircuitBreakerConfig, CircuitState
from fastmiddleware.exception_handler import ExceptionHandlerMiddleware, ExceptionHandlerConfig

# ============================================================================
# Health & Monitoring
# ============================================================================
from fastmiddleware.health import HealthCheckMiddleware, HealthConfig
from fastmiddleware.metrics import MetricsMiddleware, MetricsConfig, MetricsCollector
from fastmiddleware.profiling import ProfilingMiddleware, ProfilingConfig
from fastmiddleware.audit import AuditMiddleware, AuditConfig, AuditEvent
from fastmiddleware.response_time import ResponseTimeMiddleware, ResponseTimeConfig, ResponseTimeSLA
from fastmiddleware.server_timing import (
    ServerTimingMiddleware,
    ServerTimingConfig,
    timing,
    add_timing,
)
from fastmiddleware.request_logger import RequestLoggerMiddleware, RequestLoggerConfig
from fastmiddleware.cost_tracking import (
    CostTrackingMiddleware,
    CostTrackingConfig,
    get_request_cost,
    add_cost,
)
from fastmiddleware.request_sampler import (
    RequestSamplerMiddleware,
    RequestSamplerConfig,
    is_sampled,
)

# ============================================================================
# Idempotency
# ============================================================================
from fastmiddleware.idempotency import (
    IdempotencyMiddleware,
    IdempotencyConfig,
    IdempotencyStore,
    InMemoryIdempotencyStore,
)

# ============================================================================
# Maintenance & Lifecycle
# ============================================================================
from fastmiddleware.maintenance import MaintenanceMiddleware, MaintenanceConfig
from fastmiddleware.warmup import WarmupMiddleware, WarmupConfig
from fastmiddleware.graceful_shutdown import GracefulShutdownMiddleware, GracefulShutdownConfig
from fastmiddleware.chaos import ChaosMiddleware, ChaosConfig
from fastmiddleware.slow_response import SlowResponseMiddleware, SlowResponseConfig

# ============================================================================
# Request Processing
# ============================================================================
from fastmiddleware.timeout import TimeoutMiddleware, TimeoutConfig
from fastmiddleware.request_limit import RequestLimitMiddleware, RequestLimitConfig
from fastmiddleware.trailing_slash import TrailingSlashMiddleware, TrailingSlashConfig, SlashAction
from fastmiddleware.content_type import ContentTypeMiddleware, ContentTypeConfig
from fastmiddleware.header_transform import HeaderTransformMiddleware, HeaderTransformConfig
from fastmiddleware.request_validator import RequestValidatorMiddleware, RequestValidatorConfig, ValidationRule
from fastmiddleware.json_schema import JSONSchemaMiddleware, JSONSchemaConfig
from fastmiddleware.payload_size import PayloadSizeMiddleware, PayloadSizeConfig
from fastmiddleware.method_override import MethodOverrideMiddleware, MethodOverrideConfig
from fastmiddleware.request_fingerprint import (
    RequestFingerprintMiddleware,
    FingerprintConfig,
    get_fingerprint,
)
from fastmiddleware.request_priority import RequestPriorityMiddleware, PriorityConfig, Priority

# ============================================================================
# URL & Routing
# ============================================================================
from fastmiddleware.redirect import RedirectMiddleware, RedirectConfig, RedirectRule
from fastmiddleware.path_rewrite import PathRewriteMiddleware, PathRewriteConfig, RewriteRule
from fastmiddleware.proxy import ProxyMiddleware, ProxyConfig, ProxyRoute

# ============================================================================
# API Management
# ============================================================================
from fastmiddleware.versioning import (
    VersioningMiddleware,
    VersioningConfig,
    VersionLocation,
    get_api_version,
)
from fastmiddleware.deprecation import DeprecationMiddleware, DeprecationConfig, DeprecationInfo
from fastmiddleware.retry_after import RetryAfterMiddleware, RetryAfterConfig
from fastmiddleware.api_version_header import APIVersionHeaderMiddleware, APIVersionHeaderConfig

# ============================================================================
# Detection & Analytics
# ============================================================================
from fastmiddleware.bot_detection import BotDetectionMiddleware, BotConfig, BotAction
from fastmiddleware.geoip import GeoIPMiddleware, GeoIPConfig, get_geo_data
from fastmiddleware.user_agent import (
    UserAgentMiddleware,
    UserAgentConfig,
    UserAgentInfo,
    get_user_agent,
)

# ============================================================================
# Feature Management & Testing
# ============================================================================
from fastmiddleware.feature_flag import (
    FeatureFlagMiddleware,
    FeatureFlagConfig,
    get_feature_flags,
    is_feature_enabled,
)
from fastmiddleware.ab_testing import (
    ABTestMiddleware,
    ABTestConfig,
    Experiment,
    get_variant,
)

# ============================================================================
# Localization & Content Negotiation
# ============================================================================
from fastmiddleware.locale import LocaleMiddleware, LocaleConfig, get_locale
from fastmiddleware.accept_language import (
    AcceptLanguageMiddleware,
    AcceptLanguageConfig,
    get_language,
)
from fastmiddleware.content_negotiation import (
    ContentNegotiationMiddleware,
    ContentNegotiationConfig,
    get_negotiated_type,
)
from fastmiddleware.client_hints import (
    ClientHintsMiddleware,
    ClientHintsConfig,
    get_client_hints,
)

# ============================================================================
# IP & Proxy Handling
# ============================================================================
from fastmiddleware.real_ip import RealIPMiddleware, RealIPConfig, get_real_ip
from fastmiddleware.xff_trust import XFFTrustMiddleware, XFFTrustConfig

__version__ = "0.6.4"
__author__ = "Shreyansh Sengar"
__email__ = "sengarsinghshivansh@gmail.com, sengarsinghshreyansh@gmail.com"
__license__ = "MIT"
__url__ = "https://github.com/shregar1/fastmvc-middleware"

__all__ = [
    # Base
    "FastMVCMiddleware",

    # Core
    "CORSMiddleware",
    "LoggingMiddleware",
    "TimingMiddleware",
    "RequestIDMiddleware",

    # Security
    "SecurityHeadersMiddleware",
    "SecurityHeadersConfig",
    "TrustedHostMiddleware",
    "CSRFMiddleware",
    "CSRFConfig",
    "HTTPSRedirectMiddleware",
    "HTTPSRedirectConfig",
    "IPFilterMiddleware",
    "IPFilterConfig",
    "OriginMiddleware",
    "OriginConfig",
    "WebhookMiddleware",
    "WebhookConfig",
    "ReferrerPolicyMiddleware",
    "ReferrerPolicyConfig",
    "PermissionsPolicyMiddleware",
    "PermissionsPolicyConfig",
    "CSPReportMiddleware",
    "CSPReportConfig",
    "ReplayPreventionMiddleware",
    "ReplayPreventionConfig",
    "RequestSigningMiddleware",
    "RequestSigningConfig",
    "HoneypotMiddleware",
    "HoneypotConfig",
    "SanitizationMiddleware",
    "SanitizationConfig",

    # Rate Limiting & Protection
    "RateLimitMiddleware",
    "RateLimitConfig",
    "RateLimitStore",
    "InMemoryRateLimitStore",
    "QuotaMiddleware",
    "QuotaConfig",
    "LoadSheddingMiddleware",
    "LoadSheddingConfig",
    "BulkheadMiddleware",
    "BulkheadConfig",
    "RequestDedupMiddleware",
    "RequestDedupConfig",
    "RequestCoalescingMiddleware",
    "CoalescingConfig",

    # Authentication
    "AuthenticationMiddleware",
    "AuthConfig",
    "AuthBackend",
    "JWTAuthBackend",
    "APIKeyAuthBackend",
    "BasicAuthMiddleware",
    "BasicAuthConfig",
    "BearerAuthMiddleware",
    "BearerAuthConfig",
    "ScopeMiddleware",
    "ScopeConfig",
    "RouteAuthMiddleware",
    "RouteAuthConfig",
    "RouteAuth",

    # Session & Context
    "SessionMiddleware",
    "SessionConfig",
    "SessionStore",
    "InMemorySessionStore",
    "Session",
    "RequestContextMiddleware",
    "get_request_id",
    "get_request_context",
    "CorrelationMiddleware",
    "CorrelationConfig",
    "get_correlation_id",
    "TenantMiddleware",
    "TenantConfig",
    "get_tenant",
    "get_tenant_id",
    "ContextMiddleware",
    "ContextConfig",
    "get_context",
    "get_context_value",
    "set_context_value",
    "RequestIDPropagationMiddleware",
    "RequestIDPropagationConfig",
    "get_request_ids",
    "get_trace_header",

    # Response Handling
    "CompressionMiddleware",
    "CompressionConfig",
    "ResponseFormatMiddleware",
    "ResponseFormatConfig",
    "CacheMiddleware",
    "CacheConfig",
    "ETagMiddleware",
    "ETagConfig",
    "DataMaskingMiddleware",
    "DataMaskingConfig",
    "MaskingRule",
    "ResponseCacheMiddleware",
    "ResponseCacheConfig",
    "ResponseSignatureMiddleware",
    "ResponseSignatureConfig",
    "HATEOASMiddleware",
    "HATEOASConfig",
    "Link",
    "BandwidthMiddleware",
    "BandwidthConfig",
    "NoCacheMiddleware",
    "NoCacheConfig",
    "ConditionalRequestMiddleware",
    "ConditionalRequestConfig",
    "EarlyHintsMiddleware",
    "EarlyHintsConfig",
    "EarlyHint",

    # Error Handling
    "ErrorHandlerMiddleware",
    "ErrorConfig",
    "CircuitBreakerMiddleware",
    "CircuitBreakerConfig",
    "CircuitState",
    "ExceptionHandlerMiddleware",
    "ExceptionHandlerConfig",

    # Health & Monitoring
    "HealthCheckMiddleware",
    "HealthConfig",
    "MetricsMiddleware",
    "MetricsConfig",
    "MetricsCollector",
    "ProfilingMiddleware",
    "ProfilingConfig",
    "AuditMiddleware",
    "AuditConfig",
    "AuditEvent",
    "ResponseTimeMiddleware",
    "ResponseTimeConfig",
    "ResponseTimeSLA",
    "ServerTimingMiddleware",
    "ServerTimingConfig",
    "timing",
    "add_timing",
    "RequestLoggerMiddleware",
    "RequestLoggerConfig",
    "CostTrackingMiddleware",
    "CostTrackingConfig",
    "get_request_cost",
    "add_cost",
    "RequestSamplerMiddleware",
    "RequestSamplerConfig",
    "is_sampled",

    # Idempotency
    "IdempotencyMiddleware",
    "IdempotencyConfig",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",

    # Maintenance & Lifecycle
    "MaintenanceMiddleware",
    "MaintenanceConfig",
    "WarmupMiddleware",
    "WarmupConfig",
    "GracefulShutdownMiddleware",
    "GracefulShutdownConfig",
    "ChaosMiddleware",
    "ChaosConfig",
    "SlowResponseMiddleware",
    "SlowResponseConfig",

    # Request Processing
    "TimeoutMiddleware",
    "TimeoutConfig",
    "RequestLimitMiddleware",
    "RequestLimitConfig",
    "TrailingSlashMiddleware",
    "TrailingSlashConfig",
    "SlashAction",
    "ContentTypeMiddleware",
    "ContentTypeConfig",
    "HeaderTransformMiddleware",
    "HeaderTransformConfig",
    "RequestValidatorMiddleware",
    "RequestValidatorConfig",
    "ValidationRule",
    "JSONSchemaMiddleware",
    "JSONSchemaConfig",
    "PayloadSizeMiddleware",
    "PayloadSizeConfig",
    "MethodOverrideMiddleware",
    "MethodOverrideConfig",
    "RequestFingerprintMiddleware",
    "FingerprintConfig",
    "get_fingerprint",
    "RequestPriorityMiddleware",
    "PriorityConfig",
    "Priority",

    # URL & Routing
    "RedirectMiddleware",
    "RedirectConfig",
    "RedirectRule",
    "PathRewriteMiddleware",
    "PathRewriteConfig",
    "RewriteRule",
    "ProxyMiddleware",
    "ProxyConfig",
    "ProxyRoute",

    # API Management
    "VersioningMiddleware",
    "VersioningConfig",
    "VersionLocation",
    "get_api_version",
    "DeprecationMiddleware",
    "DeprecationConfig",
    "DeprecationInfo",
    "RetryAfterMiddleware",
    "RetryAfterConfig",
    "APIVersionHeaderMiddleware",
    "APIVersionHeaderConfig",

    # Detection & Analytics
    "BotDetectionMiddleware",
    "BotConfig",
    "BotAction",
    "GeoIPMiddleware",
    "GeoIPConfig",
    "get_geo_data",
    "UserAgentMiddleware",
    "UserAgentConfig",
    "UserAgentInfo",
    "get_user_agent",

    # Feature Management & Testing
    "FeatureFlagMiddleware",
    "FeatureFlagConfig",
    "get_feature_flags",
    "is_feature_enabled",
    "ABTestMiddleware",
    "ABTestConfig",
    "Experiment",
    "get_variant",

    # Localization & Content Negotiation
    "LocaleMiddleware",
    "LocaleConfig",
    "get_locale",
    "AcceptLanguageMiddleware",
    "AcceptLanguageConfig",
    "get_language",
    "ContentNegotiationMiddleware",
    "ContentNegotiationConfig",
    "get_negotiated_type",
    "ClientHintsMiddleware",
    "ClientHintsConfig",
    "get_client_hints",

    # IP & Proxy Handling
    "RealIPMiddleware",
    "RealIPConfig",
    "get_real_ip",
    "XFFTrustMiddleware",
    "XFFTrustConfig",

    # Factory & Utilities
    "create_middleware",
    "middleware",
    "MiddlewareBuilder",
    "MiddlewareConfig",
    "add_middleware_once",
    "quick_middleware",
    "is_middleware_registered",
    "clear_registry",
]
