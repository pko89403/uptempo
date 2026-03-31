"""Async poll loop — main orchestrator entry point.

Continuously polls Linear for eligible issues, dispatches claims,
runs the agent, and handles retry / backoff logic.

Retry strategy:
  - On success: schedule continuous retry after 1 s (multi-turn support).
  - On failure: exponential backoff capped by ``agent.max_retry_backoff_ms``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from uptempo.agent.runner import AgentRunner
    from uptempo.config.settings import Config
    from uptempo.orchestrator.dispatcher import Dispatcher
    from uptempo.tracker.linear import LinearClient
    from uptempo.workflow.loader import WorkflowLoader
    from uptempo.workspace.manager import WorkspaceManager

logger = structlog.get_logger(__name__)


async def run_poll_loop(config: Config) -> None:
    """Top-level entry: initialise components and start the polling loop."""
    raise NotImplementedError


async def _poll_tick(
    *,
    config: Config,
    tracker: LinearClient,
    dispatcher: Dispatcher,
    workspace_mgr: WorkspaceManager,
    agent_runner: AgentRunner,
    workflow_loader: WorkflowLoader,
) -> None:
    """Execute a single poll-dispatch-run cycle."""
    raise NotImplementedError


def _backoff_delay(attempt: int, max_ms: int) -> float:
    """Return exponential backoff delay in seconds, capped at *max_ms*."""
    raise NotImplementedError
