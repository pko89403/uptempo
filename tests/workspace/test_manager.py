from __future__ import annotations

import shlex
import sys
from pathlib import Path  # noqa: TC003

import pytest

from uptempo.config.settings import Config, TrackerConfig, WorkspaceConfig
from uptempo.workspace.manager import WorkspaceHookError, WorkspaceInfo, WorkspaceManager


def _manager(tmp_path: Path, hooks: dict[str, str] | None = None) -> WorkspaceManager:
    config = Config(
        tracker=TrackerConfig(team_key="UPT"),
        workspace=WorkspaceConfig(root=tmp_path / "workspaces", hooks=hooks or {}),
    )
    return WorkspaceManager(config)


def _python_hook(code: str) -> str:
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


class TestWorkspaceManager:
    async def test_create_remove_lifecycle(self, tmp_path: Path):
        manager = _manager(tmp_path)

        info = await manager.create("issue-5")

        assert info == WorkspaceInfo(issue_id="issue-5", path=tmp_path / "workspaces" / "issue-5")
        assert info.path.is_dir()

        await manager.remove(info)

        assert not info.path.exists()

    async def test_hooks_run_successfully(self, tmp_path: Path):
        manager = _manager(
            tmp_path,
            hooks={
                "after_create": _python_hook(
                    "from pathlib import Path; Path('created.txt').write_text('created')"
                ),
                "before_run": _python_hook(
                    "from pathlib import Path; Path('prepared.txt').write_text('prepared')"
                ),
                "after_run": _python_hook(
                    "from pathlib import Path; Path('finalised.txt').write_text('finalised')"
                ),
                "before_remove": _python_hook(
                    "from pathlib import Path; Path('cleanup.txt').write_text('cleanup')"
                ),
            },
        )

        info = await manager.create("issue-5")
        await manager.prepare(info)
        await manager.finalise(info)

        assert (info.path / "created.txt").read_text() == "created"
        assert (info.path / "prepared.txt").read_text() == "prepared"
        assert (info.path / "finalised.txt").read_text() == "finalised"

        await manager.remove(info)

        assert not info.path.exists()

    async def test_prepare_raises_when_before_run_hook_fails(self, tmp_path: Path):
        manager = _manager(
            tmp_path,
            hooks={
                "before_run": _python_hook(
                    "import sys; print('boom', file=sys.stderr); raise SystemExit(7)"
                )
            },
        )
        info = await manager.create("issue-5")

        with pytest.raises(WorkspaceHookError, match="before_run"):
            await manager.prepare(info)

        assert info.path.exists()

    async def test_finalise_and_remove_ignore_hook_failures(self, tmp_path: Path):
        manager = _manager(
            tmp_path,
            hooks={
                "after_run": _python_hook(
                    "import sys; print('after-run', file=sys.stderr); raise SystemExit(3)"
                ),
                "before_remove": _python_hook(
                    "import sys; print('before-remove', file=sys.stderr); raise SystemExit(4)"
                ),
            },
        )
        info = await manager.create("issue-5")

        await manager.finalise(info)
        await manager.remove(info)

        assert not info.path.exists()

    async def test_create_rejects_path_escape(self, tmp_path: Path):
        manager = _manager(tmp_path)

        with pytest.raises(ValueError, match="escapes root"):
            await manager.create("../escape")

    def test_validate_path_rejects_escape(self, tmp_path: Path):
        manager = _manager(tmp_path)

        with pytest.raises(ValueError, match="escapes root"):
            manager._validate_path((tmp_path / "outside").resolve())
