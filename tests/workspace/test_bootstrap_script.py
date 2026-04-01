from __future__ import annotations

import os
import shutil
import stat
import subprocess
from typing import TYPE_CHECKING

from tests.conftest import PROJECT_ROOT

if TYPE_CHECKING:
    from pathlib import Path


def _init_git_repo(path: Path, marker_name: str, marker_value: str) -> None:
    (path / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        PROJECT_ROOT / "scripts" / "bootstrap-workspace.sh",
        path / "scripts" / "bootstrap-workspace.sh",
    )
    (path / marker_name).write_text(marker_value, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "init",
        ],
        cwd=path,
        check=True,
    )
    script_path = path / "scripts" / "bootstrap-workspace.sh"
    script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)


def test_bootstrap_script_clones_current_checkout_by_default(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root, "README.md", "from repo root\n")

    workspace = repo_root / "workspaces" / "issue-1"
    workspace.mkdir(parents=True)

    subprocess.run(
        [str(repo_root / "scripts" / "bootstrap-workspace.sh")],
        cwd=workspace,
        check=True,
    )

    assert (workspace / "README.md").read_text(encoding="utf-8") == "from repo root\n"
    assert (workspace / ".git").is_dir()


def test_bootstrap_script_honors_explicit_workspace_source(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root, "README.md", "from repo root\n")

    source_root = tmp_path / "source"
    source_root.mkdir()
    _init_git_repo(source_root, "SOURCE.txt", "from override\n")

    workspace = repo_root / "workspaces" / "issue-1"
    workspace.mkdir(parents=True)

    env = os.environ.copy()
    env["UPTEMPO_WORKSPACE_SOURCE"] = str(source_root)
    subprocess.run(
        [str(repo_root / "scripts" / "bootstrap-workspace.sh")],
        cwd=workspace,
        check=True,
        env=env,
    )

    assert (workspace / "SOURCE.txt").read_text(encoding="utf-8") == "from override\n"
    assert not (workspace / "README.md").exists()
