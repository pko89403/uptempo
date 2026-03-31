from __future__ import annotations

from textwrap import dedent
from unittest.mock import AsyncMock

import pytest

from uptempo import __main__


@pytest.mark.asyncio()
async def test_run_loads_workflow_from_cwd(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "WORKFLOW.md").write_text(
        dedent(
            """\
            ---
            tracker:
              team_key: "UPT"
            ---
            Hello {{ issue.title }}
            """
        ),
        encoding="utf-8",
    )
    run_poll_loop = AsyncMock()
    monkeypatch.setattr(__main__, "run_poll_loop", run_poll_loop)

    await __main__._run()

    run_poll_loop.assert_awaited_once()
    config = run_poll_loop.await_args.args[0]
    assert config.tracker.team_key == "UPT"
