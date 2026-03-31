"""CLI entrypoint for ``python -m uptempo``."""

from __future__ import annotations

import asyncio
from pathlib import Path

from uptempo.config.settings import Config
from uptempo.orchestrator.loop import run_poll_loop
from uptempo.workflow.loader import WorkflowLoader


async def _run() -> None:
    workflow = WorkflowLoader().load(Path.cwd() / "WORKFLOW.md")
    config = Config.from_frontmatter(workflow.config)
    await run_poll_loop(config)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
