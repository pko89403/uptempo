"""Eligibility checking and claim dispatch.

Determines which polled issues are eligible for processing and dispatches
them through the claim state machine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from uptempo.config.settings import Config
    from uptempo.orchestrator.state import ClaimStateMachine
    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class Dispatcher:
    """Evaluates issue eligibility and manages claim lifecycles."""

    _config: Config
    _claims: dict[str, ClaimStateMachine]

    def __init__(self, config: Config) -> None:
        self._config = config
        self._claims = {}

    def is_eligible(self, issue: Issue) -> bool:
        """Return ``True`` if *issue* should be claimed for processing."""
        raise NotImplementedError

    def claim(self, issue: Issue) -> ClaimStateMachine:
        """Create or retrieve a claim for *issue* and advance to CLAIMED."""
        raise NotImplementedError

    async def dispatch(self, issues: Sequence[Issue]) -> list[ClaimStateMachine]:
        """Filter eligible issues and dispatch claims for each."""
        raise NotImplementedError

    def release(self, issue_id: str) -> None:
        """Transition the claim for *issue_id* to RELEASED."""
        raise NotImplementedError
