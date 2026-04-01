"""CLI entrypoint for ``python -m uptempo``."""

from __future__ import annotations

import asyncio

from uptempo.config.settings import Config
from uptempo.orchestrator.loop import run_poll_loop
from uptempo.workflow.loader import WorkflowLoader
from uptempo.workflow.runtime import load_active_workflow


async def _run() -> None:
    workflow = load_active_workflow(WorkflowLoader())
    config = Config.from_frontmatter(workflow.config)
    await run_poll_loop(config)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
