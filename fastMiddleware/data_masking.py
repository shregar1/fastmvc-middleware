"""
Data Masking Middleware for FastMVC.

Masks sensitive data in responses for security and privacy.
"""

import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class MaskingRule:
    """A rule for masking sensitive data."""

    field: str
    pattern: str | None = None  # Regex pattern to match
    mask_char: str = "*"
    show_first: int = 0  # Show first N characters
    show_last: int = 4  # Show last N characters

    def mask_value(self, value: str) -> str:
        """Apply masking to value."""
        if not value or not isinstance(value, str):
            return value

        length = len(value)
        visible_length = self.show_first + self.show_last

        if length <= visible_length:
            return self.mask_char * length

        prefix = value[: self.show_first] if self.show_first > 0 else ""
        suffix = value[-self.show_last :] if self.show_last > 0 else ""
        masked_length = length - visible_length

        return f"{prefix}{self.mask_char * masked_length}{suffix}"


@dataclass
class DataMaskingConfig:
    """
    Configuration for data masking middleware.

    Attributes:
        enabled: Whether masking is enabled.
        fields: Fields to mask (simple field names).
        patterns: Regex patterns to detect and mask.
        custom_rules: Custom masking rules.
        mask_in_logs: Also mask in logs.

    Example:
        ```python
        from FastMiddleware import DataMaskingConfig, MaskingRule

        config = DataMaskingConfig(
            fields={"password", "ssn", "credit_card"},
            custom_rules=[
                MaskingRule("email", show_first=2, show_last=4),
                MaskingRule("phone", show_last=4),
            ],
        )
        ```
    """

    enabled: bool = True
    fields: set[str] = field(
        default_factory=lambda: {
            "password",
            "secret",
            "token",
            "api_key",
            "access_token",
            "refresh_token",
            "authorization",
            "credit_card",
            "cvv",
            "ssn",
            "social_security",
            "bank_account",
        }
    )
    patterns: dict[str, str] = field(
        default_factory=lambda: {
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "ssn": r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        }
    )
    custom_rules: list[MaskingRule] = field(default_factory=list)
    default_mask_char: str = "*"
    default_show_last: int = 4


class DataMaskingMiddleware(FastMVCMiddleware):
    """
    Middleware that masks sensitive data in responses.

    Automatically detects and masks PII and sensitive data
    before sending responses to clients.

    Features:
        - Field-based masking
        - Pattern-based detection
        - Configurable mask format
        - Nested object support

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import DataMaskingMiddleware

        app = FastAPI()

        app.add_middleware(
            DataMaskingMiddleware,
            fields={"ssn", "credit_card", "password"},
        )

        @app.get("/user")
        async def get_user():
            return {
                "name": "John Doe",
                "ssn": "123-45-6789",  # Masked: ***-**-6789
                "credit_card": "4111111111111111",  # Masked: ************1111
            }
        ```
    """

    def __init__(
        self,
        app,
        config: DataMaskingConfig | None = None,
        fields: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or DataMaskingConfig()

        if fields is not None:
            self.config.fields = fields

        # Compile patterns
        self._compiled_patterns = {
            name: re.compile(pattern) for name, pattern in self.config.patterns.items()
        }

    def _should_mask_field(self, key: str) -> bool:
        """Check if field should be masked."""
        key_lower = key.lower()
        return any(field.lower() in key_lower for field in self.config.fields)

    def _mask_string(self, value: str, show_last: int = 4) -> str:
        """Mask a string value."""
        if len(value) <= show_last:
            return self.config.default_mask_char * len(value)

        masked_length = len(value) - show_last
        return self.config.default_mask_char * masked_length + value[-show_last:]

    def _get_custom_rule(self, key: str) -> MaskingRule | None:
        """Get custom masking rule for key."""
        key_lower = key.lower()
        for rule in self.config.custom_rules:
            if rule.field.lower() in key_lower:
                return rule
        return None

    def _mask_value(self, key: str, value: Any) -> Any:
        """Mask a value based on its key."""
        if value is None:
            return None

        # Check custom rules first
        rule = self._get_custom_rule(key)
        if rule and isinstance(value, str):
            return rule.mask_value(value)

        # Check if field should be masked
        if self._should_mask_field(key):
            if isinstance(value, str):
                return self._mask_string(value, self.config.default_show_last)
            elif isinstance(value, (int, float)):
                return self._mask_string(str(value), self.config.default_show_last)

        return value

    def _mask_patterns_in_string(self, text: str) -> str:
        """Mask pattern matches in a string."""
        for pattern in self._compiled_patterns.values():
            text = pattern.sub(
                lambda m: self._mask_string(m.group(), self.config.default_show_last),
                text,
            )
        return text

    def _mask_data(self, data: Any) -> Any:
        """Recursively mask sensitive data."""
        if isinstance(data, dict):
            return {
                key: self._mask_data(self._mask_value(key, value)) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_data(item) for item in data]
        elif isinstance(data, str):
            return self._mask_patterns_in_string(data)
        return data

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request) or not self.config.enabled:
            return await call_next(request)

        response = await call_next(request)

        # Only process JSON responses
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return response

        # Read body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Parse and mask
        try:
            data = json.loads(body)
            masked_data = self._mask_data(data)
            masked_body = json.dumps(masked_data)

            return Response(
                content=masked_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )
        except (json.JSONDecodeError, ValueError):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
