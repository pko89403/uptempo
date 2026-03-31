from __future__ import annotations

import pytest

from uptempo.orchestrator.state import ClaimState, ClaimStateMachine


class TestClaimStateMachine:
    def test_valid_transitions(self) -> None:
        claim = ClaimStateMachine("issue-1")

        claim.transition(ClaimState.CLAIMED)
        claim.transition(ClaimState.RUNNING)
        claim.transition(ClaimState.RETRY_QUEUED)
        claim.transition(ClaimState.RELEASED)

        assert claim.issue_id == "issue-1"
        assert claim.state is ClaimState.RELEASED

    def test_invalid_transition_raises(self) -> None:
        claim = ClaimStateMachine("issue-1")

        with pytest.raises(ValueError, match="UNCLAIMED"):
            claim.transition(ClaimState.RUNNING)
