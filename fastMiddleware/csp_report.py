"""
CSP Report Handler Middleware for FastMVC.

Handles Content-Security-Policy violation reports.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class CSPReportConfig:
    """
    Configuration for CSP report middleware.

    Attributes:
        report_uri: URI where reports are sent.
        log_reports: Log CSP violations.
        store_reports: Store reports in memory.
        max_stored: Max reports to store.
        logger_name: Logger name for reports.
    """

    report_uri: str = "/_csp-report"
    log_reports: bool = True
    store_reports: bool = False
    max_stored: int = 100
    logger_name: str = "csp_reports"


class CSPReportMiddleware(FastMVCMiddleware):
    """
    Middleware that handles CSP violation reports.

    Receives and processes Content-Security-Policy
    violation reports sent by browsers.

    Example:
        ```python
        from FastMiddleware import CSPReportMiddleware

        csp_reporter = CSPReportMiddleware(
            app,
            report_uri="/_csp-report",
            log_reports=True,
        )

        # Configure CSP header to send reports:
        # Content-Security-Policy: ...; report-uri /_csp-report
        ```
    """

    def __init__(
        self,
        app,
        config: CSPReportConfig | None = None,
        report_uri: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or CSPReportConfig()

        if report_uri:
            self.config.report_uri = report_uri

        self._logger = logging.getLogger(self.config.logger_name)
        self._reports: list[dict[str, Any]] = []

    def get_reports(self) -> list[dict[str, Any]]:
        """Get stored CSP violation reports."""
        return list(self._reports)

    def clear_reports(self) -> None:
        """Clear stored reports."""
        self._reports.clear()

    async def _handle_report(self, request: Request) -> Response:
        """Handle incoming CSP report."""
        try:
            body = await request.body()
            report = json.loads(body)

            # Handle both wrapped and unwrapped format
            violation = report.get("csp-report", report)

            if self.config.log_reports:
                self._logger.warning(
                    f"CSP Violation: {violation.get('violated-directive')} "
                    f"blocked {violation.get('blocked-uri')} "
                    f"on {violation.get('document-uri')}"
                )

            if self.config.store_reports:
                self._reports.append(
                    {
                        "violation": violation,
                        "client_ip": self.get_client_ip(request),
                        "user_agent": request.headers.get("User-Agent"),
                    }
                )

                if len(self._reports) > self.config.max_stored:
                    self._reports = self._reports[-self.config.max_stored :]

            return Response(status_code=204)

        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "Invalid JSON"},
            )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Handle CSP report endpoint
        if request.url.path == self.config.report_uri and request.method == "POST":
            return await self._handle_report(request)

        if self.should_skip(request):
            return await call_next(request)

        return await call_next(request)
