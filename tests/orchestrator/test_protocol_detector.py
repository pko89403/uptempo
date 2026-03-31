"""Tests for protocol detection from Linear issues.

The :class:`ProtocolDetector` is expected at
``uptempo.orchestrator.protocol_detector`` and analyses issue text to
determine which communication protocols an issue requires.
"""

from __future__ import annotations

import pytest

from uptempo.tracker.models import Issue, Label

# Import may fail until the module is created by the sibling agent.
# The ``importorskip`` call causes all tests in this file to be
# skipped with a clear message when the module is not yet available.
pd = pytest.importorskip(
    "uptempo.orchestrator.protocol_detector",
    reason="protocol_detector module not yet created",
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def detector() -> pd.ProtocolDetector:
    return pd.ProtocolDetector()


def _make_issue(
    title: str,
    description: str = "",
    labels: list[Label] | None = None,
) -> Issue:
    return Issue(
        id="issue-1",
        identifier="UP-99",
        title=title,
        description=description,
        labels=labels or [],
    )


# ------------------------------------------------------------------
# Single-protocol detection
# ------------------------------------------------------------------


class TestSingleProtocol:
    def test_rest_from_crud_api_title(self, detector: pd.ProtocolDetector) -> None:
        issue = _make_issue("Build CRUD API for users")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "rest" in protocols

    def test_graphql_from_title(self, detector: pd.ProtocolDetector) -> None:
        issue = _make_issue("Add GraphQL schema for products")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "graphql" in protocols

    def test_grpc_from_title(self, detector: pd.ProtocolDetector) -> None:
        issue = _make_issue("Create gRPC service for payments")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "grpc" in protocols

    def test_websocket_from_title(self, detector: pd.ProtocolDetector) -> None:
        issue = _make_issue("Add WebSocket support for live chat")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "websocket" in protocols

    def test_sse_from_title(self, detector: pd.ProtocolDetector) -> None:
        issue = _make_issue("Stream updates via SSE")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "sse" in protocols

    def test_mqtt_from_title(self, detector: pd.ProtocolDetector) -> None:
        issue = _make_issue("Publish device telemetry over MQTT")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "mqtt" in protocols


# ------------------------------------------------------------------
# Multi-protocol detection
# ------------------------------------------------------------------


class TestMultiProtocol:
    def test_rest_and_kafka_and_websocket(
        self, detector: pd.ProtocolDetector
    ) -> None:
        issue = _make_issue(
            "Order API with Kafka events and WebSocket notifications"
        )
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "rest" in protocols or "kafka" in protocols
        assert "websocket" in protocols

    def test_graphql_and_sse(self, detector: pd.ProtocolDetector) -> None:
        issue = _make_issue(
            "Dashboard with GraphQL queries and SSE live updates"
        )
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "graphql" in protocols
        assert "sse" in protocols


# ------------------------------------------------------------------
# Default / fallback behaviour
# ------------------------------------------------------------------


class TestDefaults:
    def test_no_keywords_falls_back_to_rest(
        self, detector: pd.ProtocolDetector
    ) -> None:
        issue = _make_issue("Implement user management feature")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "rest" in protocols

    def test_results_sorted_by_confidence_descending(
        self, detector: pd.ProtocolDetector
    ) -> None:
        issue = _make_issue(
            "Order API with Kafka events and WebSocket notifications"
        )
        results = detector.detect(issue)
        if len(results) >= 2:
            confidences = [r.confidence for r in results]
            assert confidences == sorted(confidences, reverse=True)


# ------------------------------------------------------------------
# Case insensitivity
# ------------------------------------------------------------------


class TestCaseInsensitivity:
    @pytest.mark.parametrize(
        "keyword",
        ["graphql", "GRAPHQL", "GraphQL", "graphQL"],
    )
    def test_graphql_case_variants(
        self, detector: pd.ProtocolDetector, keyword: str
    ) -> None:
        issue = _make_issue(f"Add {keyword} endpoint")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "graphql" in protocols

    @pytest.mark.parametrize(
        "keyword",
        ["websocket", "WebSocket", "WEBSOCKET"],
    )
    def test_websocket_case_variants(
        self, detector: pd.ProtocolDetector, keyword: str
    ) -> None:
        issue = _make_issue(f"Support {keyword} connections")
        results = detector.detect(issue)
        protocols = [r.protocol for r in results]
        assert "websocket" in protocols


# ------------------------------------------------------------------
# Label-based confidence boost
# ------------------------------------------------------------------


class TestLabelBoost:
    def test_label_boosts_confidence(
        self, detector: pd.ProtocolDetector
    ) -> None:
        issue_no_label = _make_issue("Build API for users")
        issue_with_label = _make_issue(
            "Build API for users",
            labels=[Label(id="lbl-1", name="graphql")],
        )
        results_no = detector.detect(issue_no_label)
        results_yes = detector.detect(issue_with_label)

        def _confidence_for(results: list, protocol: str) -> float:
            for r in results:
                if r.protocol == protocol:
                    return r.confidence
            return 0.0

        # When a label matches, confidence for that protocol should be
        # higher than for the same issue without the label.
        conf_with = _confidence_for(results_yes, "graphql")
        conf_without = _confidence_for(results_no, "graphql")
        assert conf_with > conf_without
