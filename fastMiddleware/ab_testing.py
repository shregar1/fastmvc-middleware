"""
A/B Testing Middleware for FastMVC.

Provides A/B test variant assignment and routing.
"""

import hashlib
import random
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


# Context variable for A/B test assignments
_ab_ctx: ContextVar[dict[str, str] | None] = ContextVar("ab_variants", default=None)


def get_variant(experiment: str) -> str | None:
    """
    Get the assigned variant for an experiment.

    Args:
        experiment: Experiment name.

    Returns:
        Variant name or None.

    Example:
        ```python
        from FastMiddleware import get_variant

        @app.get("/checkout")
        async def checkout():
            variant = get_variant("checkout_flow")
            if variant == "new":
                return new_checkout()
            return old_checkout()
        ```
    """
    variants = _ab_ctx.get()
    return variants.get(experiment) if variants else None


@dataclass
class Experiment:
    """An A/B test experiment."""

    name: str
    variants: list[str]
    weights: list[float] | None = None  # Distribution weights
    enabled: bool = True

    def __post_init__(self):
        if self.weights is None:
            # Equal distribution
            self.weights = [1.0 / len(self.variants)] * len(self.variants)


@dataclass
class ABTestConfig:
    """
    Configuration for A/B testing middleware.

    Attributes:
        experiments: List of experiments.
        cookie_name: Cookie for storing assignments.
        cookie_max_age: Cookie max age in seconds.
        id_header: Header for user ID (for consistent assignment).
        sticky: Whether assignments are sticky (consistent per user).

    Example:
        ```python
        from FastMiddleware import ABTestConfig, Experiment

        config = ABTestConfig(
            experiments=[
                Experiment(
                    name="new_homepage",
                    variants=["control", "variant_a", "variant_b"],
                    weights=[0.5, 0.25, 0.25],
                ),
                Experiment(
                    name="pricing_page",
                    variants=["old", "new"],
                ),
            ],
        )
        ```
    """

    experiments: list[Experiment] = field(default_factory=list)
    cookie_name: str = "ab_variants"
    cookie_max_age: int = 30 * 24 * 60 * 60  # 30 days
    id_header: str = "X-User-ID"
    sticky: bool = True


class ABTestMiddleware(FastMVCMiddleware):
    """
    Middleware that provides A/B testing support.

    Assigns users to experiment variants and maintains
    consistent assignments across requests.

    Features:
        - Multiple concurrent experiments
        - Weighted variant distribution
        - Sticky assignments (cookie-based)
        - Deterministic assignment by user ID

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import ABTestMiddleware, Experiment, get_variant

        app = FastAPI()

        app.add_middleware(
            ABTestMiddleware,
            experiments=[
                Experiment("checkout", ["control", "new"]),
                Experiment("pricing", ["low", "high"], weights=[0.7, 0.3]),
            ],
        )

        @app.get("/checkout")
        async def checkout():
            if get_variant("checkout") == "new":
                return new_checkout_flow()
            return standard_checkout_flow()
        ```
    """

    def __init__(
        self,
        app,
        config: ABTestConfig | None = None,
        experiments: list[Experiment] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ABTestConfig()

        if experiments is not None:
            self.config.experiments = experiments

        # Build experiment lookup
        self._experiments = {exp.name: exp for exp in self.config.experiments}

    def _get_user_id(self, request: Request) -> str | None:
        """Get user identifier for consistent assignment."""
        # Try header
        user_id = request.headers.get(self.config.id_header)
        if user_id:
            return user_id

        # Try request state
        user = getattr(request.state, "user", None)
        if user:
            if isinstance(user, dict):
                return user.get("id")
            return getattr(user, "id", None)

        return None

    def _assign_variant(self, experiment: Experiment, user_id: str | None) -> str:
        """Assign a variant for an experiment."""
        if user_id and self.config.sticky:
            # Deterministic assignment based on user ID
            hash_input = f"{experiment.name}:{user_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            value = (hash_value % 10000) / 10000.0
        else:
            # Random assignment
            value = random.random()

        # Select variant based on weights
        cumulative = 0.0
        for variant, weight in zip(experiment.variants, experiment.weights, strict=False):
            cumulative += weight
            if value < cumulative:
                return variant

        return experiment.variants[-1]

    def _parse_cookie(self, cookie: str) -> dict[str, str]:
        """Parse variant assignments from cookie."""
        assignments = {}
        for part in cookie.split("|"):
            if ":" in part:
                name, variant = part.split(":", 1)
                assignments[name] = variant
        return assignments

    def _format_cookie(self, assignments: dict[str, str]) -> str:
        """Format variant assignments for cookie."""
        return "|".join(f"{name}:{variant}" for name, variant in assignments.items())

    def _get_assignments(self, request: Request) -> dict[str, str]:
        """Get all variant assignments for request."""
        assignments = {}
        user_id = self._get_user_id(request)

        # Load existing from cookie
        cookie = request.cookies.get(self.config.cookie_name, "")
        if cookie:
            assignments = self._parse_cookie(cookie)

        # Assign missing experiments
        for name, experiment in self._experiments.items():
            if experiment.enabled and name not in assignments:
                assignments[name] = self._assign_variant(experiment, user_id)

        return assignments

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Get assignments
        assignments = self._get_assignments(request)

        # Set context
        token = _ab_ctx.set(assignments)
        request.state.ab_variants = assignments

        try:
            response = await call_next(request)

            # Set cookie with assignments
            response.set_cookie(
                key=self.config.cookie_name,
                value=self._format_cookie(assignments),
                max_age=self.config.cookie_max_age,
                httponly=True,
                samesite="lax",
            )

            # Add header showing active variants
            response.headers["X-AB-Variants"] = ",".join(f"{k}={v}" for k, v in assignments.items())

            return response
        finally:
            _ab_ctx.reset(token)
