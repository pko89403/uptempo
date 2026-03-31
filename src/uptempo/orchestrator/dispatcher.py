"""Eligibility checking and claim dispatch.

Determines which polled issues are eligible for processing and dispatches
them through the claim state machine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.orchestrator.state import ClaimState, ClaimStateMachine

if TYPE_CHECKING:
    from collections.abc import Sequence

    from uptempo.config.settings import Config
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
        tracker_config = self._config.tracker
        label_names = {label.name for label in issue.labels}

        if issue.state not in tracker_config.eligible_states:
            return False
        if tracker_config.labels_include and not (
            label_names & set(tracker_config.labels_include)
        ):
            return False
        if label_names & set(tracker_config.labels_exclude):
            return False

        claim = self._claims.get(issue.id)
        return claim is None or claim.state is ClaimState.RELEASED

    def claim(self, issue: Issue) -> ClaimStateMachine:
        """Create or retrieve a claim for *issue* and advance to CLAIMED."""
        claim = self._claims.get(issue.id)
        if claim is None:
            claim = ClaimStateMachine(issue.id)
            self._claims[issue.id] = claim

        claim.transition(ClaimState.CLAIMED)
        logger.info("issue_claimed", issue_id=issue.id, identifier=issue.identifier)
        return claim

    async def dispatch(self, issues: Sequence[Issue]) -> list[ClaimStateMachine]:
        """Filter eligible issues and dispatch claims for each."""
        claims: list[ClaimStateMachine] = []
        for issue in issues:
            if self.is_eligible(issue):
                claims.append(self.claim(issue))
        return claims

    def release(self, issue_id: str) -> None:
        """Transition the claim for *issue_id* to RELEASED."""
        claim = self._claims.get(issue_id)
        if claim is None:
            return
        if claim.state is not ClaimState.RELEASED:
            claim.transition(ClaimState.RELEASED)
        self._claims.pop(issue_id, None)
