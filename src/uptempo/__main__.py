"""CLI entrypoint for ``python -m uptempo``."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from uptempo.config.settings import Config
from uptempo.orchestrator.loop import run_poll_loop
from uptempo.workflow.loader import WorkflowLoader
from uptempo.workflow.runtime import WORKFLOW_OVERRIDE_ENV, load_active_workflow


def _workflow_project_root() -> Path:
    """Return the repo/project root used for resolving repo-relative hooks."""
    workflow_override = os.getenv(WORKFLOW_OVERRIDE_ENV)
    if workflow_override:
        return Path(workflow_override).resolve().parent
    return Path.cwd()


async def _run() -> None:
    workflow = load_active_workflow(WorkflowLoader())
    config = Config.from_frontmatter(workflow.config, project_root=_workflow_project_root())
    await run_poll_loop(config)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
