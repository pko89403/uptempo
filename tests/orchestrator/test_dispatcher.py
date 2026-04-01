from __future__ import annotations

from uptempo.config.settings import Config
from uptempo.orchestrator.dispatcher import Dispatcher
from uptempo.orchestrator.state import ClaimState
from uptempo.tracker.models import Issue, Label


def make_config() -> Config:
    return Config.from_frontmatter(
        {
            "tracker": {
                "team_key": "UPT",
                "eligible_states": ["In Progress"],
                "labels_include": ["backend", "api"],
                "labels_exclude": ["blocked"],
            },
            "workspace": {"root": "./workspaces"},
        }
    )


def make_issue(
    *,
    issue_id: str = "issue-1",
    state: str = "In Progress",
    labels: list[str] | None = None,
) -> Issue:
    return Issue(
        id=issue_id,
        identifier="UPT-1",
        title="Implement orchestrator",
        state=state,
        labels=[
            Label(id=f"label-{index}", name=name)
            for index, name in enumerate(labels or ["backend"], start=1)
        ],
    )


class TestDispatcher:
    async def test_dispatch_filters_include_and_exclude_labels(self) -> None:
        dispatcher = Dispatcher(make_config())
        eligible = make_issue(issue_id="issue-1", labels=["backend"])
        missing_include = make_issue(issue_id="issue-2", labels=["docs"])
        excluded = make_issue(issue_id="issue-3", labels=["backend", "blocked"])
        wrong_state = make_issue(issue_id="issue-4", state="Done", labels=["backend"])

        claims = await dispatcher.dispatch([eligible, missing_include, excluded, wrong_state])

        assert [claim.issue_id for claim in claims] == ["issue-1"]
        assert claims[0].state is ClaimState.CLAIMED

    def test_claimed_issue_is_not_eligible_until_released(self) -> None:
        dispatcher = Dispatcher(make_config())
        issue = make_issue()

        dispatcher.claim(issue)

        assert dispatcher.is_eligible(issue) is False

        dispatcher.release(issue.id)

        assert dispatcher.is_eligible(issue) is True

    def test_release_removes_active_claim(self) -> None:
        dispatcher = Dispatcher(make_config())
        issue = make_issue()
        claim = dispatcher.claim(issue)

        dispatcher.release(issue.id)

        assert claim.state is ClaimState.RELEASED
        assert issue.id not in dispatcher._claims
