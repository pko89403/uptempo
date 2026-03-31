"""Execution reporting helpers for orchestrator runs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pathlib import Path


class ExecutionMetric(BaseModel):
    name: str
    count: int
    total_ms: int


class GeneratedArtifact(BaseModel):
    protocol: str
    path: str
    duration_ms: int


class ExecutionReport(BaseModel):
    issue_id: str
    issue_identifier: str
    title: str
    total_duration_ms: int
    agent_turns: int
    validation_passed: int
    validation_total: int
    retry_count: int
    generated_artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    metrics: list[ExecutionMetric] = Field(default_factory=list)
    failure_reason: str | None = None


def collect_generated_artifacts(
    workspace_path: Path, *, duration_ms: int
) -> list[GeneratedArtifact]:
    """Return a pragmatic list of generated files under *workspace_path*."""
    if not workspace_path.exists():
        return []

    artifacts: list[GeneratedArtifact] = []
    for file_path in sorted(path for path in workspace_path.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(workspace_path)
        if any(part.startswith(".") for part in relative_path.parts):
            continue

        protocol = relative_path.parts[0] if len(relative_path.parts) > 1 else "workspace"
        artifacts.append(
            GeneratedArtifact(
                protocol=protocol,
                path=relative_path.as_posix(),
                duration_ms=duration_ms,
            )
        )
    return artifacts


def collect_metrics(
    *,
    agent_turns: int,
    retry_count: int,
    total_duration_ms: int,
    validation_passed: int,
    validation_total: int,
    generated_artifacts: list[GeneratedArtifact],
) -> list[ExecutionMetric]:
    """Build a small set of execution metrics for comment/report output."""
    return [
        ExecutionMetric(name="agent_turns", count=agent_turns, total_ms=total_duration_ms),
        ExecutionMetric(name="retries", count=retry_count, total_ms=0),
        ExecutionMetric(name="validations", count=validation_total, total_ms=0),
        ExecutionMetric(
            name="artifacts_generated",
            count=len(generated_artifacts),
            total_ms=sum(artifact.duration_ms for artifact in generated_artifacts),
        ),
    ]


class ReportRenderer:
    """Render execution reports to Markdown or JSON."""

    @staticmethod
    def to_markdown(report: ExecutionReport) -> str:
        lines = [
            f"# Execution report for {report.issue_identifier}",
            "",
            f"- Title: {report.title}",
            f"- Issue ID: {report.issue_id}",
            f"- Total duration: {report.total_duration_ms} ms",
            f"- Agent turns: {report.agent_turns}",
            f"- Validation: {report.validation_passed}/{report.validation_total}",
            f"- Retries: {report.retry_count}",
        ]

        if report.failure_reason:
            lines.extend(["", f"**Failure reason:** {report.failure_reason}"])

        lines.extend(["", "## Generated artifacts"])
        if report.generated_artifacts:
            lines.extend(
                f"- `{artifact.path}` ({artifact.protocol}, {artifact.duration_ms} ms)"
                for artifact in report.generated_artifacts
            )
        else:
            lines.append("- None")

        lines.extend(["", "## Metrics"])
        for metric in report.metrics:
            lines.append(f"- {metric.name}: count={metric.count}, total_ms={metric.total_ms}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def to_json(report: ExecutionReport) -> str:
        return json.dumps(report.model_dump(mode="json"), indent=2)
