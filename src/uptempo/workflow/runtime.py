"""Runtime helpers for loading Uptempo workflow assets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uptempo.workflow.loader import WorkflowDefinition, WorkflowLoader

WORKFLOW_OVERRIDE_ENV = "UPTEMPO_WORKFLOW_PATH"


def load_active_workflow(loader: WorkflowLoader) -> WorkflowDefinition:
    """Load the explicit override workflow when configured, else the built-in one."""
    from uptempo.workflow.loader import WorkflowLoader

    if not isinstance(loader, WorkflowLoader):
        msg = "loader must be a WorkflowLoader"
        raise TypeError(msg)
    override = os.getenv(WORKFLOW_OVERRIDE_ENV)
    if override:
        return loader.load(Path(override))
    return loader.load_default()
