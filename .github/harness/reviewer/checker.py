"""Cross-protocol consistency checker.

The :class:`SchemaReviewer` scans a workspace for protocol-specific schema
directories and runs a configurable set of consistency checks, producing a
:class:`~uptempo.reviewer.models.ReviewReport`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.reviewer.models import (
    Finding,
    ProtocolCoverage,
    ReviewReport,
    SkippedProtocol,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger(__name__)

# Maps each protocol flag to the directory name expected in the workspace.
_PROTOCOL_DIRS: dict[str, str] = {
    "rest": "openapi",
    "sse": "sse",
    "websocket": "websocket",
    "grpc": "proto",
    "graphql": "graphql",
    "kafka": "events",
    "webhook": "webhook",
    "mqtt": "mqtt",
    "trpc": "trpc",
}


class SchemaReviewer:
    """Validates consistency across protocol schemas in *workspace*."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self._protocol_dirs: dict[str, Path] = {}
        self._discover_dirs()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_dirs(self) -> None:
        """Populate ``_protocol_dirs`` with paths that actually exist."""
        for protocol, dirname in _PROTOCOL_DIRS.items():
            candidate = self.workspace / dirname
            if candidate.is_dir():
                self._protocol_dirs[protocol] = candidate

    def discover_protocols(self) -> ProtocolCoverage:
        """Return a :class:`ProtocolCoverage` reflecting which protocol directories exist."""
        coverage = ProtocolCoverage(
            **{proto: proto in self._protocol_dirs for proto in _PROTOCOL_DIRS}
        )
        logger.info("protocol_discovery", coverage=coverage.model_dump())
        return coverage

    # ------------------------------------------------------------------
    # Individual checks (stubs)
    # ------------------------------------------------------------------

    def check_naming_conventions(self, findings: list[Finding]) -> None:
        """Check naming rules per protocol.

        Validates camelCase for JSON-based schemas (REST, SSE, GraphQL),
        snake_case for Proto definitions, and PascalCase for TypeScript
        types (tRPC).
        """
        pass

    def check_cross_protocol_mapping(self, findings: list[Finding]) -> None:
        """Compare entity and field names across protocols.

        Ensures that the same domain concept uses consistent naming and
        typing in every protocol where it appears.
        """
        pass

    def check_security_coverage(self, findings: list[Finding]) -> None:
        """Verify that auth schemes are applied across all protocols.

        Checks that every endpoint or operation that requires
        authentication in one protocol has equivalent protection in the
        others.
        """
        pass

    def check_error_code_mapping(self, findings: list[Finding]) -> None:
        """Verify HTTP ↔ gRPC ↔ GraphQL ↔ tRPC error-code consistency.

        Ensures error codes are correctly mapped between protocol-specific
        representations (e.g. HTTP 404 ↔ gRPC NOT_FOUND).
        """
        pass

    def check_backward_compatibility(self, findings: list[Finding]) -> None:
        """Detect breaking changes relative to previously reviewed schemas.

        Identifies removed fields, changed types, or tightened validation
        rules that could break existing consumers.
        """
        pass

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    def run(self, depth: str = "full") -> ReviewReport:
        """Execute review checks and return a :class:`ReviewReport`.

        Parameters
        ----------
        depth:
            Review depth — ``"full"`` runs every checker, ``"standard"``
            runs security and cross-protocol checks, ``"lightweight"``
            runs format/lint checks only.
        """
        logger.info("review_start", workspace=str(self.workspace), depth=depth)

        coverage = self.discover_protocols()

        # Build the skipped-protocol list.
        skipped: list[SkippedProtocol] = [
            SkippedProtocol(
                protocol=proto,
                reason=f"directory '{dirname}' not found in workspace",
            )
            for proto, dirname in _PROTOCOL_DIRS.items()
            if proto not in self._protocol_dirs
        ]

        findings: list[Finding] = []

        if depth == "full":
            self.check_naming_conventions(findings)
            self.check_cross_protocol_mapping(findings)
            self.check_security_coverage(findings)
            self.check_error_code_mapping(findings)
            self.check_backward_compatibility(findings)
        elif depth == "standard":
            self.check_security_coverage(findings)
            self.check_cross_protocol_mapping(findings)
        elif depth == "lightweight":
            self.check_naming_conventions(findings)
        else:
            logger.warning("unknown_depth", depth=depth)

        # Determine overall status from findings.
        if any(f.verdict.value == "FAIL" for f in findings):
            status = "failed"
        elif any(f.verdict.value == "WARNING" for f in findings):
            status = "needs_revision"
        else:
            status = "passed"

        report = ReviewReport(
            review_status=status,
            review_depth=depth,
            summary=f"{len(findings)} finding(s) across {sum(coverage.model_dump().values())} protocol(s)",
            findings=findings,
            protocol_coverage=coverage,
            skipped=skipped,
        )

        logger.info("review_complete", status=status, findings=len(findings))
        return report
