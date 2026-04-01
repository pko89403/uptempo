from __future__ import annotations

from textwrap import dedent
from unittest.mock import AsyncMock

import pytest

from uptempo import __main__
from uptempo.workflow.runtime import WORKFLOW_OVERRIDE_ENV


@pytest.mark.asyncio()
async def test_run_loads_workflow_from_explicit_override(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workflow_path = tmp_path / "WORKFLOW.md"
    workflow_path.write_text(
        dedent(
            """\
            ---
            tracker:
              project: "UPT"
              active_states: ["In Progress"]
            workspace:
              root: "./workspaces"
            polling:
              interval_ms: 12000
            codex:
              cmd: "codex --profile local"
            ---
            Hello {{ issue.title }}
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(WORKFLOW_OVERRIDE_ENV, str(workflow_path))
    run_poll_loop = AsyncMock()
    monkeypatch.setattr(__main__, "run_poll_loop", run_poll_loop)

    await __main__._run()

    run_poll_loop.assert_awaited_once()
    config = run_poll_loop.await_args.args[0]
    assert config.tracker.team_key == "UPT"
    assert config.tracker.poll_interval_ms == 12_000
    assert config.agent.codex_cmd == "codex --profile local"
