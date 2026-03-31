"""Async poll loop — main orchestrator entry point.

Continuously polls Linear for eligible issues, dispatches claims,
runs the agent, and handles retry / backoff logic.

Retry strategy:
  - On success: schedule continuous retry after 1 s (multi-turn support).
  - On failure: exponential backoff capped by ``agent.max_retry_backoff_ms``.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from uptempo.agent.runner import AgentRunner
from uptempo.orchestrator.dispatcher import Dispatcher
from uptempo.orchestrator.report import (
    ExecutionReport,
    ReportRenderer,
    collect_generated_artifacts,
    collect_metrics,
)
from uptempo.orchestrator.state import ClaimState
from uptempo.tracker.linear import LinearClient
from uptempo.workflow.loader import WorkflowLoader
from uptempo.workflow.renderer import WorkflowRenderer
from uptempo.workspace.manager import WorkspaceManager

if TYPE_CHECKING:
    from uptempo.config.settings import Config

logger = structlog.get_logger(__name__)


async def run_poll_loop(config: Config) -> None:
    """Top-level entry: initialise components and start the polling loop."""
    tracker = LinearClient(config)
    dispatcher = Dispatcher(config)
    workspace_mgr = WorkspaceManager(config)
    agent_runner = AgentRunner(config)
    workflow_loader = WorkflowLoader()
    workflow_renderer = WorkflowRenderer()
    retry_attempt = 0

    logger.info(
        "poll_loop_started",
        team_key=config.tracker.team_key,
        poll_interval_ms=config.tracker.poll_interval_ms,
        eligible_states=config.tracker.eligible_states,
    )

    while True:
        try:
            await _poll_tick(
                config=config,
                tracker=tracker,
                dispatcher=dispatcher,
                workspace_mgr=workspace_mgr,
                agent_runner=agent_runner,
                workflow_loader=workflow_loader,
                workflow_renderer=workflow_renderer,
            )
        except Exception:
            delay = _backoff_delay(retry_attempt, config.agent.max_retry_backoff_ms)
            retry_attempt += 1
            logger.exception("poll_tick_failed", retry_attempt=retry_attempt, delay_seconds=delay)
            await asyncio.sleep(delay)
            continue

        retry_attempt = 0
        await asyncio.sleep(config.tracker.poll_interval_ms / 1000)


async def _poll_tick(
    *,
    config: Config,
    tracker: LinearClient,
    dispatcher: Dispatcher,
    workspace_mgr: WorkspaceManager,
    agent_runner: AgentRunner,
    workflow_loader: WorkflowLoader,
    workflow_renderer: WorkflowRenderer,
) -> None:
    """Execute a single poll-dispatch-run cycle."""
    issues = await tracker.fetch_issues()
    logger.debug("poll_tick_fetched_issues", issue_count=len(issues))
    claims = await dispatcher.dispatch(issues)
    if not claims:
        logger.debug("poll_tick_idle", issue_count=len(issues))
        return

    logger.info("poll_tick_claimed_issues", claim_count=len(claims))

    workflow_definition = workflow_loader.load(_resolve_workflow_path(config))
    issues_by_id = {issue.id: issue for issue in issues}
    report_renderer = ReportRenderer()

    for claim in claims:
        issue = issues_by_id[claim.issue_id]
        workspace = None
        attempted_run = False
        started_at = time.perf_counter()
        failure_reason: str | None = None

        try:
            claim.transition(ClaimState.RUNNING)
            workspace = await workspace_mgr.create(issue.id)
            await workspace_mgr.prepare(workspace)
            prompt = workflow_renderer.render(
                workflow_definition.template,
                {"issue": issue, "attempt": None, "agent": config.agent},
            )

            attempted_run = True
            agent_result = await agent_runner.run(workspace, prompt)
            total_duration_ms = _duration_ms(started_at)
            generated_artifacts = collect_generated_artifacts(
                workspace.path, duration_ms=total_duration_ms
            )
            report = ExecutionReport(
                issue_id=issue.id,
                issue_identifier=issue.identifier,
                title=issue.title,
                total_duration_ms=total_duration_ms,
                agent_turns=1,
                validation_passed=0,
                validation_total=0,
                retry_count=0,
                generated_artifacts=generated_artifacts,
                metrics=collect_metrics(
                    agent_turns=1,
                    retry_count=0,
                    total_duration_ms=total_duration_ms,
                    validation_passed=0,
                    validation_total=0,
                    generated_artifacts=generated_artifacts,
                ),
                failure_reason=agent_result.error if not agent_result.success else None,
            )

            if not agent_result.success:
                failure_reason = agent_result.error or "Agent run failed"
                await tracker.add_comment(issue.id, report_renderer.to_markdown(report))
                continue

            await tracker.update_issue_state(issue.id, config.tracker.done_state)
            await tracker.add_comment(issue.id, report_renderer.to_markdown(report))
        except Exception as exc:
            failure_reason = str(exc)
            total_duration_ms = _duration_ms(started_at)
            generated_artifacts = (
                collect_generated_artifacts(workspace.path, duration_ms=total_duration_ms)
                if workspace is not None
                else []
            )
            report = ExecutionReport(
                issue_id=issue.id,
                issue_identifier=issue.identifier,
                title=issue.title,
                total_duration_ms=total_duration_ms,
                agent_turns=1 if attempted_run else 0,
                validation_passed=0,
                validation_total=0,
                retry_count=0,
                generated_artifacts=generated_artifacts,
                metrics=collect_metrics(
                    agent_turns=1 if attempted_run else 0,
                    retry_count=0,
                    total_duration_ms=total_duration_ms,
                    validation_passed=0,
                    validation_total=0,
                    generated_artifacts=generated_artifacts,
                ),
                failure_reason=failure_reason,
            )
            try:
                await tracker.add_comment(issue.id, report_renderer.to_markdown(report))
            except Exception:
                logger.exception("issue_failure_comment_failed", issue_id=issue.id)
            logger.exception("issue_execution_failed", issue_id=issue.id)
        finally:
            if workspace is not None:
                if attempted_run:
                    try:
                        await workspace_mgr.finalise(workspace)
                    except Exception:
                        logger.exception("workspace_finalise_failed", issue_id=issue.id)
                try:
                    await workspace_mgr.remove(workspace)
                except Exception:
                    logger.exception(
                        "workspace_remove_failed",
                        issue_id=issue.id,
                        failure_reason=failure_reason,
                    )
            dispatcher.release(issue.id)


def _backoff_delay(attempt: int, max_ms: int) -> float:
    """Return exponential backoff delay in seconds, capped at *max_ms*."""
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    return min(float(2**attempt), max_ms / 1000)


def _resolve_workflow_path(config: Config) -> Path:
    """Resolve WORKFLOW.md relative to cwd or the configured workspace root."""
    candidates = [
        Path.cwd() / "WORKFLOW.md",
        config.workspace.root.resolve().parent / "WORKFLOW.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(candidates[0])


def _duration_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)
