from __future__ import annotations

import json

from uptempo.orchestrator.report import (
    ExecutionMetric,
    ExecutionReport,
    GeneratedArtifact,
    ReportRenderer,
    collect_generated_artifacts,
    collect_metrics,
)


class TestReportRenderer:
    def test_to_markdown_renders_summary(self, tmp_path) -> None:
        workspace = tmp_path / "workspace"
        artifact_path = workspace / "proto" / "service.proto"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text('syntax = "proto3";', encoding="utf-8")
        artifacts = collect_generated_artifacts(workspace, duration_ms=25)
        report = ExecutionReport(
            issue_id="issue-1",
            issue_identifier="UPT-1",
            title="Generate schema",
            total_duration_ms=25,
            agent_turns=1,
            validation_passed=1,
            validation_total=1,
            retry_count=0,
            generated_artifacts=artifacts,
            metrics=collect_metrics(
                agent_turns=1,
                retry_count=0,
                total_duration_ms=25,
                validation_passed=1,
                validation_total=1,
                generated_artifacts=artifacts,
            ),
        )

        rendered = ReportRenderer.to_markdown(report)

        assert "# Execution report for UPT-1" in rendered
        assert "`proto/service.proto`" in rendered
        assert "Validation: 1/1" in rendered

    def test_to_json_serializes_report(self) -> None:
        report = ExecutionReport(
            issue_id="issue-2",
            issue_identifier="UPT-2",
            title="Handle failure",
            total_duration_ms=10,
            agent_turns=0,
            validation_passed=0,
            validation_total=0,
            retry_count=1,
            generated_artifacts=[
                GeneratedArtifact(protocol="proto", path="proto/service.proto", duration_ms=10)
            ],
            metrics=[ExecutionMetric(name="agent_turns", count=0, total_ms=10)],
            failure_reason="boom",
        )

        rendered = ReportRenderer.to_json(report)
        payload = json.loads(rendered)

        assert payload["issue_identifier"] == "UPT-2"
        assert payload["failure_reason"] == "boom"
        assert payload["generated_artifacts"][0]["path"] == "proto/service.proto"
