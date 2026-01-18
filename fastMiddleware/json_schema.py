"""
JSON Schema Validation Middleware for FastMVC.

Validates request bodies against JSON schemas.
"""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class JSONSchemaConfig:
    """
    Configuration for JSON schema middleware.

    Attributes:
        schemas: Dict of path patterns to JSON schemas.
        strict: Return error on validation failure.
    """

    schemas: dict[str, dict[str, Any]] = field(default_factory=dict)
    strict: bool = True


class JSONSchemaMiddleware(FastMVCMiddleware):
    """
    Middleware that validates requests against JSON schemas.

    Example:
        ```python
        from FastMiddleware import JSONSchemaMiddleware

        user_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["name", "email"],
        }

        app.add_middleware(
            JSONSchemaMiddleware,
            schemas={"/api/users": user_schema},
        )
        ```
    """

    def __init__(
        self,
        app,
        config: JSONSchemaConfig | None = None,
        schemas: dict[str, dict[str, Any]] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or JSONSchemaConfig()

        if schemas:
            self.config.schemas = schemas

    def _validate_type(self, value: Any, schema_type: str) -> bool:
        """Basic type validation."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected = type_map.get(schema_type)
        if expected is None:
            return True
        return isinstance(value, expected)

    def _validate(self, data: Any, schema: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Simple JSON schema validation.

        For production, use a proper library like jsonschema.
        """
        errors = []

        if not isinstance(schema, dict):
            return True, errors

        schema_type = schema.get("type")

        # Type check
        if schema_type:
            if isinstance(schema_type, list):
                if not any(self._validate_type(data, t) for t in schema_type):
                    errors.append(f"Expected one of {schema_type}, got {type(data).__name__}")
            elif not self._validate_type(data, schema_type):
                errors.append(f"Expected {schema_type}, got {type(data).__name__}")
                return False, errors

        # Object validation
        if schema_type == "object" and isinstance(data, dict):
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Check required fields
            for field in required:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            # Validate properties
            for key, value in data.items():
                if key in properties:
                    _valid, prop_errors = self._validate(value, properties[key])
                    errors.extend([f"{key}: {e}" for e in prop_errors])

        # Array validation
        if schema_type == "array" and isinstance(data, list):
            items_schema = schema.get("items", {})
            for i, item in enumerate(data):
                _valid, item_errors = self._validate(item, items_schema)
                errors.extend([f"[{i}]: {e}" for e in item_errors])

        # Enum validation
        if "enum" in schema and data not in schema["enum"]:
            errors.append(f"Value must be one of {schema['enum']}")

        # Min/max for numbers
        if isinstance(data, (int, float)):
            if "minimum" in schema and data < schema["minimum"]:
                errors.append(f"Value must be >= {schema['minimum']}")
            if "maximum" in schema and data > schema["maximum"]:
                errors.append(f"Value must be <= {schema['maximum']}")

        # Min/max length for strings
        if isinstance(data, str):
            if "minLength" in schema and len(data) < schema["minLength"]:
                errors.append(f"String length must be >= {schema['minLength']}")
            if "maxLength" in schema and len(data) > schema["maxLength"]:
                errors.append(f"String length must be <= {schema['maxLength']}")

        return len(errors) == 0, errors

    def _get_schema(self, path: str, method: str) -> dict[str, Any] | None:
        """Get schema for path."""
        # Try exact match with method
        key = f"{method}:{path}"
        if key in self.config.schemas:
            return self.config.schemas[key]

        # Try path only
        if path in self.config.schemas:
            return self.config.schemas[path]

        # Try prefix match
        for pattern in self.config.schemas:
            if path.startswith(pattern.rstrip("*")):
                return self.config.schemas[pattern]

        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Only validate methods with body
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        schema = self._get_schema(request.url.path, request.method)
        if not schema:
            return await call_next(request)

        # Parse body
        try:
            body = await request.body()
            if not body:
                if self.config.strict:
                    return JSONResponse(
                        status_code=400,
                        content={"error": True, "message": "Request body required"},
                    )
                return await call_next(request)

            data = json.loads(body)
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "Invalid JSON",
                    "detail": str(e),
                },
            )

        # Validate
        valid, errors = self._validate(data, schema)

        if not valid and self.config.strict:
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "Validation failed",
                    "errors": errors,
                },
            )

        request.state.validated_body = data
        request.state.validation_errors = errors

        return await call_next(request)
