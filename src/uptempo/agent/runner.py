"""AgentRunner — Codex app-server JSON-RPC process management.

Lifecycle over stdio (line-delimited JSON-RPC):
  1. ``initialize``      → wait for response
  2. ``initialized``     notification
  3. ``thread/start``    → acquire ``thread_id``
  4. ``turn/start``      → acquire ``turn_id``, stream events
     until ``turn/completed`` | ``turn/failed``

Consecutive turns reuse the same ``thread_id`` without resending the
initial task prompt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from uptempo.config.settings import Config
    from uptempo.workspace.manager import WorkspaceInfo

logger = structlog.get_logger(__name__)


class AgentRunner:
    """Spawn and manage a Codex app-server subprocess."""

    _config: Config

    def __init__(self, config: Config) -> None:
        self._config = config

    async def run(self, workspace: WorkspaceInfo, prompt: str) -> AgentResult:
        """Execute a full agent turn inside *workspace* with *prompt*."""
        raise NotImplementedError

    async def _spawn(self, workspace: WorkspaceInfo) -> _JsonRpcTransport:
        """Start the Codex app-server subprocess and perform handshake."""
        raise NotImplementedError

    async def _initialize(self, transport: _JsonRpcTransport) -> None:
        """Send ``initialize`` and wait for the response, then ``initialized``."""
        raise NotImplementedError

    async def _start_thread(self, transport: _JsonRpcTransport) -> str:
        """Send ``thread/start`` and return the ``thread_id``."""
        raise NotImplementedError

    async def _run_turn(
        self,
        transport: _JsonRpcTransport,
        thread_id: str,
        prompt: str | None,
    ) -> AgentResult:
        """Send ``turn/start``, stream events, return on completion or failure."""
        raise NotImplementedError


class AgentResult:
    """Outcome of a single agent turn."""

    success: bool
    output: str
    thread_id: str
    turn_id: str

    def __init__(self, *, success: bool, output: str, thread_id: str, turn_id: str) -> None:
        self.success = success
        self.output = output
        self.thread_id = thread_id
        self.turn_id = turn_id


class _JsonRpcTransport:
    """Low-level stdio JSON-RPC transport for the Codex subprocess."""

    async def send(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Write a JSON-RPC request/notification to stdin."""
        raise NotImplementedError

    async def receive(self) -> dict[str, Any]:
        """Read the next JSON-RPC message from stdout."""
        raise NotImplementedError

    async def close(self) -> None:
        """Terminate the subprocess."""
        raise NotImplementedError
