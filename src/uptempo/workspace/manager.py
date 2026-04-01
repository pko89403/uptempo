"""WorkspaceManager — per-issue directory creation and hook lifecycle.

Hook execution order:
  after_create  — once after initial directory creation (e.g. git clone)
  before_run    — before each agent attempt; failure aborts the attempt
  after_run     — after each agent attempt; failure is logged and ignored
  before_remove — before workspace teardown; failure is logged and ignored

All workspace paths are validated to reside under the configured root.
"""

from __future__ import annotations

import asyncio
import shlex
import shutil
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import structlog
from pydantic import BaseModel

if TYPE_CHECKING:
    from uptempo.config.settings import Config

logger = structlog.get_logger(__name__)


class HookStage(Enum):
    AFTER_CREATE = auto()
    BEFORE_RUN = auto()
    AFTER_RUN = auto()
    BEFORE_REMOVE = auto()


class WorkspaceHookError(RuntimeError):
    """Raised when a workspace hook exits unsuccessfully."""


class WorkspaceInfo(BaseModel):
    issue_id: str
    path: Path


class WorkspaceManager:
    """Manage isolated per-issue workspace directories."""

    _HOOK_STAGE_MAP: ClassVar[dict[str, HookStage]] = {
        "after_create": HookStage.AFTER_CREATE,
        "before_run": HookStage.BEFORE_RUN,
        "after_run": HookStage.AFTER_RUN,
        "before_remove": HookStage.BEFORE_REMOVE,
    }

    _root: Path
    _project_root: Path
    _hooks: dict[HookStage, str]

    def __init__(self, config: Config) -> None:
        self._root = config.workspace.root.resolve()
        self._project_root = (
            config.workspace.project_root.resolve()
            if config.workspace.project_root is not None
            else self._root.parent
        )
        self._hooks = {}
        for name, command in config.workspace.hooks.items():
            stage = self._HOOK_STAGE_MAP.get(name)
            if stage is None:
                logger.warning("ignoring_unknown_workspace_hook", hook=name)
                continue
            self._hooks[stage] = command

    async def create(self, issue_id: str) -> WorkspaceInfo:
        """Create or reopen a workspace for *issue_id*.

        ``after_create`` runs only on first creation so persistent workspaces can
        be reused across poll ticks without repeating bootstrap work.
        """
        workspace_path = (self._root / issue_id).resolve()
        self._validate_path(workspace_path)
        created = not workspace_path.exists()
        await asyncio.to_thread(workspace_path.mkdir, parents=True, exist_ok=True)
        if created:
            await self._run_hook(HookStage.AFTER_CREATE, workspace_path)
        return WorkspaceInfo(issue_id=issue_id, path=workspace_path)

    async def prepare(self, info: WorkspaceInfo) -> None:
        """Run ``before_run`` hook. Raises on failure to abort the attempt."""
        self._validate_path(info.path)
        await self._run_hook(HookStage.BEFORE_RUN, info.path)

    async def finalise(self, info: WorkspaceInfo) -> None:
        """Run ``after_run`` hook. Failures are logged and ignored."""
        self._validate_path(info.path)
        try:
            await self._run_hook(HookStage.AFTER_RUN, info.path)
        except WorkspaceHookError:
            logger.warning(
                "workspace_hook_failed_ignored",
                stage=HookStage.AFTER_RUN.name.lower(),
                issue_id=info.issue_id,
                workspace=str(info.path),
            )

    async def remove(self, info: WorkspaceInfo) -> None:
        """Run ``before_remove`` hook then delete the workspace directory."""
        self._validate_path(info.path)
        try:
            await self._run_hook(HookStage.BEFORE_REMOVE, info.path)
        except WorkspaceHookError:
            logger.warning(
                "workspace_hook_failed_ignored",
                stage=HookStage.BEFORE_REMOVE.name.lower(),
                issue_id=info.issue_id,
                workspace=str(info.path),
            )

        if info.path.exists():
            await asyncio.to_thread(shutil.rmtree, info.path)

    async def _run_hook(self, stage: HookStage, workspace: Path) -> None:
        """Execute the shell command registered for *stage*, if any."""
        self._validate_path(workspace)
        command = self._hooks.get(stage)
        if command is None:
            return
        resolved_command = self._resolve_hook_command(command)

        logger.debug(
            "running_workspace_hook",
            stage=stage.name.lower(),
            workspace=str(workspace),
            command=resolved_command,
        )
        process = await asyncio.create_subprocess_shell(
            resolved_command,
            cwd=str(workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()
        if process.returncode == 0:
            logger.debug(
                "workspace_hook_succeeded",
                stage=stage.name.lower(),
                workspace=str(workspace),
                stdout=stdout_text,
                stderr=stderr_text,
            )
            return

        logger.error(
            "workspace_hook_failed",
            stage=stage.name.lower(),
            workspace=str(workspace),
            returncode=process.returncode,
            stdout=stdout_text,
            stderr=stderr_text,
        )
        msg = (
            f"Workspace hook '{stage.name.lower()}' failed with exit code " f"{process.returncode}"
        )
        raise WorkspaceHookError(msg)

    def _resolve_hook_command(self, command: str) -> str:
        """Resolve script-like hook commands against the project root.

        Hooks still run with ``cwd`` set to the workspace so relative file writes
        land inside the workspace. Only the executable path is rewritten when the
        first token points at a repo-relative script.
        """
        if "\n" in command:
            return command

        try:
            tokens = shlex.split(command)
        except ValueError:
            return command
        if not tokens:
            return command

        candidate = Path(tokens[0])
        if candidate.is_absolute() or candidate.parts == ():
            return command

        resolved = (self._project_root / candidate).resolve()
        if not resolved.exists():
            return command

        tokens[0] = str(resolved)
        return shlex.join(tokens)

    def _validate_path(self, path: Path) -> None:
        """Ensure *path* is under the configured workspace root."""
        resolved = path.resolve()
        if not resolved.is_relative_to(self._root):
            msg = f"Workspace path {resolved} escapes root {self._root}"
            raise ValueError(msg)
