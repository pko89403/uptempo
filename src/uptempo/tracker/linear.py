"""Async Linear GraphQL adapter.

Wraps the Linear API to fetch, filter, and update issues.  All responses
are normalised into ``Issue`` / ``Label`` domain models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from uptempo.config.settings import Config
    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class LinearClient:
    """Async client for the Linear GraphQL API."""

    _api_key: str
    _team_id: str

    def __init__(self, config: Config) -> None:
        self._api_key = ""  # resolved from config / env at init
        self._team_id = config.tracker.team_key

    async def fetch_issues(self) -> list[Issue]:
        """Poll Linear for issues matching configured filters."""
        raise NotImplementedError

    async def update_issue_state(self, issue_id: str, state_id: str) -> None:
        """Transition an issue to a new workflow state in Linear."""
        raise NotImplementedError

    async def add_comment(self, issue_id: str, body: str) -> None:
        """Post a comment on a Linear issue."""
        raise NotImplementedError

    async def _execute(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GraphQL request and return the JSON response body."""
        raise NotImplementedError
