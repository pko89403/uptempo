"""Claim state enum and state-machine transition logic.

Internal claim states (distinct from Linear issue states):
Unclaimed → Claimed → Running | RetryQueued → Released
"""

from __future__ import annotations

from enum import Enum, auto

import structlog

logger = structlog.get_logger(__name__)


class ClaimState(Enum):
    UNCLAIMED = auto()
    CLAIMED = auto()
    RUNNING = auto()
    RETRY_QUEUED = auto()
    RELEASED = auto()


# Allowed source → {destinations} transitions.
TRANSITIONS: dict[ClaimState, frozenset[ClaimState]] = {
    ClaimState.UNCLAIMED: frozenset({ClaimState.CLAIMED}),
    ClaimState.CLAIMED: frozenset({ClaimState.RUNNING, ClaimState.RELEASED}),
    ClaimState.RUNNING: frozenset({ClaimState.RETRY_QUEUED, ClaimState.RELEASED}),
    ClaimState.RETRY_QUEUED: frozenset({ClaimState.RUNNING, ClaimState.RELEASED}),
    ClaimState.RELEASED: frozenset(),
}


class ClaimStateMachine:
    """Guard valid state transitions for an issue claim."""

    _state: ClaimState
    _issue_id: str

    def __init__(self, issue_id: str) -> None:
        self._issue_id = issue_id
        self._state = ClaimState.UNCLAIMED

    @property
    def state(self) -> ClaimState:
        return self._state

    def transition(self, target: ClaimState) -> None:
        """Transition to *target*, raising ``ValueError`` on illegal moves."""
        allowed = TRANSITIONS.get(self._state, frozenset())
        if target not in allowed:
            msg = f"Invalid transition {self._state.name} → {target.name}"
            raise ValueError(msg)
        logger.info(
            "claim_state_transition",
            issue_id=self._issue_id,
            from_state=self._state.name,
            to_state=target.name,
        )
        self._state = target
