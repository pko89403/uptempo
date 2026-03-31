"""WorkspaceManager — per-issue directory creation and hook lifecycle.

Hook execution order:
  after_create  — once after initial directory creation (e.g. git clone)
  before_run    — before each agent attempt; failure aborts the attempt
  after_run     — after each agent attempt; failure is logged and ignored
  before_remove — before workspace teardown; failure is logged and ignored

All workspace paths are validated to reside under the configured root.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.config.settings import Config

logger = structlog.get_logger(__name__)


class HookStage(Enum):
    AFTER_CREATE = auto()
    BEFORE_RUN = auto()
    AFTER_RUN = auto()
    BEFORE_REMOVE = auto()


class WorkspaceInfo(BaseModel):
    issue_id: str
    path: Path


class WorkspaceManager:
    """Manage isolated per-issue workspace directories."""

    _root: Path
    _hooks: dict[HookStage, str]

    def __init__(self, config: Config) -> None:
        self._root = config.workspace.root.resolve()
        self._hooks = {}

    async def create(self, issue_id: str) -> WorkspaceInfo:
        """Create a workspace directory for *issue_id* and run ``after_create``."""
        raise NotImplementedError

    async def prepare(self, info: WorkspaceInfo) -> None:
        """Run ``before_run`` hook. Raises on failure to abort the attempt."""
        raise NotImplementedError

    async def finalise(self, info: WorkspaceInfo) -> None:
        """Run ``after_run`` hook. Failures are logged and ignored."""
        raise NotImplementedError

    async def remove(self, info: WorkspaceInfo) -> None:
        """Run ``before_remove`` hook then delete the workspace directory."""
        raise NotImplementedError

    async def _run_hook(self, stage: HookStage, workspace: Path) -> None:
        """Execute the shell command registered for *stage*, if any."""
        raise NotImplementedError

    def _validate_path(self, path: Path) -> None:
        """Ensure *path* is under the configured workspace root."""
        resolved = path.resolve()
        if not resolved.is_relative_to(self._root):
            msg = f"Workspace path {resolved} escapes root {self._root}"
            raise ValueError(msg)
