"""Tests for reviewer data models."""

from __future__ import annotations

import pytest

from uptempo.reviewer.models import (
    Category,
    Finding,
    ProtocolCoverage,
    ReviewReport,
    Severity,
    SkippedProtocol,
    Verdict,
)


# ------------------------------------------------------------------
# Enum values
# ------------------------------------------------------------------


class TestVerdict:
    def test_values(self) -> None:
        assert Verdict.PASS.value == "PASS"
        assert Verdict.WARNING.value == "WARNING"
        assert Verdict.FAIL.value == "FAIL"

    def test_member_count(self) -> None:
        assert len(Verdict) == 3


class TestSeverity:
    def test_values(self) -> None:
        assert Severity.critical.value == "critical"
        assert Severity.high.value == "high"
        assert Severity.medium.value == "medium"
        assert Severity.low.value == "low"

    def test_member_count(self) -> None:
        assert len(Severity) == 4


class TestCategory:
    def test_values(self) -> None:
        assert Category.cross_protocol_mapping.value == "cross_protocol_mapping"
        assert Category.naming_convention.value == "naming_convention"
        assert Category.backward_compatibility.value == "backward_compatibility"
        assert Category.security.value == "security"
        assert Category.format_lint.value == "format_lint"

    def test_member_count(self) -> None:
        assert len(Category) == 5


# ------------------------------------------------------------------
# Finding
# ------------------------------------------------------------------


class TestFinding:
    def test_creation_with_all_fields(self) -> None:
        f = Finding(
            verdict=Verdict.FAIL,
            severity=Severity.high,
            category=Category.security,
            protocols=["rest", "grpc"],
            description="Missing auth on gRPC endpoint",
            location="proto/service.proto:12",
            fix="Add auth interceptor",
        )
        assert f.verdict == Verdict.FAIL
        assert f.severity == Severity.high
        assert f.category == Category.security
        assert f.protocols == ["rest", "grpc"]
        assert f.description == "Missing auth on gRPC endpoint"
        assert f.location == "proto/service.proto:12"
        assert f.fix == "Add auth interceptor"

    def test_creation_with_defaults(self) -> None:
        f = Finding(
            verdict=Verdict.WARNING,
            severity=Severity.low,
            category=Category.naming_convention,
            description="Inconsistent casing",
        )
        assert f.protocols == []
        assert f.location == ""
        assert f.fix is None

    def test_serialization_round_trip(self) -> None:
        f = Finding(
            verdict=Verdict.PASS,
            severity=Severity.medium,
            category=Category.format_lint,
            description="All good",
        )
        data = f.model_dump()
        restored = Finding(**data)
        assert restored == f


# ------------------------------------------------------------------
# ProtocolCoverage
# ------------------------------------------------------------------


class TestProtocolCoverage:
    def test_defaults_all_false(self) -> None:
        pc = ProtocolCoverage()
        for field_name in ProtocolCoverage.model_fields:
            assert getattr(pc, field_name) is False

    def test_partial_coverage(self) -> None:
        pc = ProtocolCoverage(rest=True, grpc=True)
        assert pc.rest is True
        assert pc.grpc is True
        assert pc.sse is False

    def test_all_true(self) -> None:
        pc = ProtocolCoverage(**{f: True for f in ProtocolCoverage.model_fields})
        assert all(getattr(pc, f) is True for f in ProtocolCoverage.model_fields)


# ------------------------------------------------------------------
# SkippedProtocol
# ------------------------------------------------------------------


class TestSkippedProtocol:
    def test_creation(self) -> None:
        sp = SkippedProtocol(protocol="mqtt", reason="directory not found")
        assert sp.protocol == "mqtt"
        assert sp.reason == "directory not found"


# ------------------------------------------------------------------
# ReviewReport
# ------------------------------------------------------------------


class TestReviewReport:
    def test_default_state(self) -> None:
        report = ReviewReport()
        assert report.review_status == "passed"
        assert report.review_depth == "full"
        assert report.summary == ""
        assert report.findings == []
        assert isinstance(report.protocol_coverage, ProtocolCoverage)
        assert report.skipped == []

    def test_serialization(self) -> None:
        report = ReviewReport(
            review_status="failed",
            review_depth="standard",
            summary="1 finding(s) across 2 protocol(s)",
            findings=[
                Finding(
                    verdict=Verdict.FAIL,
                    severity=Severity.critical,
                    category=Category.security,
                    description="Auth missing",
                )
            ],
            protocol_coverage=ProtocolCoverage(rest=True, grpc=True),
            skipped=[
                SkippedProtocol(protocol="mqtt", reason="not found"),
            ],
        )
        data = report.model_dump()
        assert data["review_status"] == "failed"
        assert len(data["findings"]) == 1
        assert data["protocol_coverage"]["rest"] is True
        assert data["protocol_coverage"]["mqtt"] is False
        assert len(data["skipped"]) == 1

    def test_reconstruction_from_dump(self) -> None:
        original = ReviewReport(
            review_status="needs_revision",
            findings=[
                Finding(
                    verdict=Verdict.WARNING,
                    severity=Severity.medium,
                    category=Category.naming_convention,
                    description="Inconsistent field casing",
                )
            ],
        )
        restored = ReviewReport(**original.model_dump())
        assert restored == original
