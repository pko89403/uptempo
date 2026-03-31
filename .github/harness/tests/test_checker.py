"""Tests for cross-protocol schema reviewer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from uptempo.reviewer.checker import SchemaReviewer, _PROTOCOL_DIRS
from uptempo.reviewer.models import ProtocolCoverage, ReviewReport


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def empty_workspace(tmp_path: Path) -> Path:
    """Workspace with no protocol directories."""
    return tmp_path


@pytest.fixture()
def partial_workspace(tmp_path: Path) -> Path:
    """Workspace with a subset of protocol directories."""
    (tmp_path / "openapi").mkdir()
    (tmp_path / "proto").mkdir()
    (tmp_path / "graphql").mkdir()
    return tmp_path


@pytest.fixture()
def full_workspace(tmp_path: Path) -> Path:
    """Workspace with every known protocol directory."""
    for dirname in _PROTOCOL_DIRS.values():
        (tmp_path / dirname).mkdir()
    return tmp_path


# ------------------------------------------------------------------
# discover_protocols
# ------------------------------------------------------------------


class TestDiscoverProtocols:
    def test_empty_workspace(self, empty_workspace: Path) -> None:
        reviewer = SchemaReviewer(empty_workspace)
        coverage = reviewer.discover_protocols()
        assert isinstance(coverage, ProtocolCoverage)
        for field_name in ProtocolCoverage.model_fields:
            assert getattr(coverage, field_name) is False

    def test_partial_workspace(self, partial_workspace: Path) -> None:
        reviewer = SchemaReviewer(partial_workspace)
        coverage = reviewer.discover_protocols()
        assert coverage.rest is True
        assert coverage.grpc is True
        assert coverage.graphql is True
        assert coverage.sse is False
        assert coverage.websocket is False
        assert coverage.kafka is False
        assert coverage.webhook is False
        assert coverage.mqtt is False
        assert coverage.trpc is False

    def test_full_workspace(self, full_workspace: Path) -> None:
        reviewer = SchemaReviewer(full_workspace)
        coverage = reviewer.discover_protocols()
        for field_name in ProtocolCoverage.model_fields:
            assert getattr(coverage, field_name) is True


# ------------------------------------------------------------------
# run() — review depths
# ------------------------------------------------------------------


class TestRunDepths:
    def test_empty_workspace_passes(self, empty_workspace: Path) -> None:
        reviewer = SchemaReviewer(empty_workspace)
        report = reviewer.run()
        assert isinstance(report, ReviewReport)
        assert report.review_status == "passed"
        assert report.findings == []
        # All protocols should be skipped when workspace is empty.
        assert len(report.skipped) == len(_PROTOCOL_DIRS)

    def test_full_depth_calls_all_checks(self, partial_workspace: Path) -> None:
        reviewer = SchemaReviewer(partial_workspace)
        with (
            patch.object(reviewer, "check_naming_conventions") as naming,
            patch.object(reviewer, "check_cross_protocol_mapping") as cross,
            patch.object(reviewer, "check_security_coverage") as security,
            patch.object(reviewer, "check_error_code_mapping") as error,
            patch.object(reviewer, "check_backward_compatibility") as compat,
        ):
            reviewer.run(depth="full")
            naming.assert_called_once()
            cross.assert_called_once()
            security.assert_called_once()
            error.assert_called_once()
            compat.assert_called_once()

    def test_standard_depth_calls_security_and_cross(
        self, partial_workspace: Path
    ) -> None:
        reviewer = SchemaReviewer(partial_workspace)
        with (
            patch.object(reviewer, "check_naming_conventions") as naming,
            patch.object(reviewer, "check_cross_protocol_mapping") as cross,
            patch.object(reviewer, "check_security_coverage") as security,
            patch.object(reviewer, "check_error_code_mapping") as error,
            patch.object(reviewer, "check_backward_compatibility") as compat,
        ):
            reviewer.run(depth="standard")
            security.assert_called_once()
            cross.assert_called_once()
            naming.assert_not_called()
            error.assert_not_called()
            compat.assert_not_called()

    def test_lightweight_depth_calls_naming_only(
        self, partial_workspace: Path
    ) -> None:
        reviewer = SchemaReviewer(partial_workspace)
        with (
            patch.object(reviewer, "check_naming_conventions") as naming,
            patch.object(reviewer, "check_cross_protocol_mapping") as cross,
            patch.object(reviewer, "check_security_coverage") as security,
            patch.object(reviewer, "check_error_code_mapping") as error,
            patch.object(reviewer, "check_backward_compatibility") as compat,
        ):
            reviewer.run(depth="lightweight")
            naming.assert_called_once()
            cross.assert_not_called()
            security.assert_not_called()
            error.assert_not_called()
            compat.assert_not_called()


# ------------------------------------------------------------------
# run() — report status logic
# ------------------------------------------------------------------


class TestRunStatus:
    def test_no_findings_means_passed(self, empty_workspace: Path) -> None:
        reviewer = SchemaReviewer(empty_workspace)
        report = reviewer.run()
        assert report.review_status == "passed"

    def test_skipped_protocols_listed(self, partial_workspace: Path) -> None:
        reviewer = SchemaReviewer(partial_workspace)
        report = reviewer.run()
        skipped_protocols = {s.protocol for s in report.skipped}
        # rest, grpc, graphql are present → should NOT be skipped
        assert "rest" not in skipped_protocols
        assert "grpc" not in skipped_protocols
        assert "graphql" not in skipped_protocols
        # Others should be skipped
        assert "sse" in skipped_protocols
        assert "websocket" in skipped_protocols

    def test_report_depth_reflects_input(self, empty_workspace: Path) -> None:
        reviewer = SchemaReviewer(empty_workspace)
        assert reviewer.run(depth="full").review_depth == "full"
        assert reviewer.run(depth="standard").review_depth == "standard"
        assert reviewer.run(depth="lightweight").review_depth == "lightweight"

    def test_summary_contains_finding_count(self, empty_workspace: Path) -> None:
        reviewer = SchemaReviewer(empty_workspace)
        report = reviewer.run()
        assert "0 finding(s)" in report.summary
