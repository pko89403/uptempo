"""Pydantic models for schema-review findings and reports."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    """Outcome of a single review check."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class Severity(str, Enum):
    """How serious a finding is."""

    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Category(str, Enum):
    """Classification bucket for a finding."""

    cross_protocol_mapping = "cross_protocol_mapping"
    naming_convention = "naming_convention"
    backward_compatibility = "backward_compatibility"
    security = "security"
    format_lint = "format_lint"


class Finding(BaseModel):
    """A single review finding produced by a checker."""

    verdict: Verdict
    severity: Severity
    category: Category
    protocols: list[str] = Field(default_factory=list)
    description: str
    location: str = ""
    fix: str | None = None


class ProtocolCoverage(BaseModel):
    """Boolean flags indicating which protocol directories were found."""

    rest: bool = False
    sse: bool = False
    websocket: bool = False
    grpc: bool = False
    graphql: bool = False
    kafka: bool = False
    webhook: bool = False
    mqtt: bool = False
    trpc: bool = False


class SkippedProtocol(BaseModel):
    """A protocol that was skipped during review, with the reason."""

    protocol: str
    reason: str


class ReviewReport(BaseModel):
    """Full output of a schema-review run."""

    review_status: str = "passed"
    review_depth: str = "full"
    summary: str = ""
    findings: list[Finding] = Field(default_factory=list)
    protocol_coverage: ProtocolCoverage = Field(default_factory=ProtocolCoverage)
    skipped: list[SkippedProtocol] = Field(default_factory=list)
