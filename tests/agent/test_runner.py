from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from uptempo.agent.runner import AgentRunner, _JsonRpcTransport
from uptempo.config.settings import AgentConfig, Config, TrackerConfig, WorkspaceConfig
from uptempo.workspace.manager import WorkspaceInfo


class FakeReader:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = list(lines)

    async def readline(self) -> bytes:
        if not self._lines:
            return b""
        return self._lines.pop(0)


class FakeWriter:
    def __init__(self) -> None:
        self.writes: list[bytes] = []
        self.closed = False

    def write(self, data: bytes) -> None:
        self.writes.append(data)

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        return None


class FakeProcess:
    def __init__(self, *, returncode: int | None = 0) -> None:
        self.returncode = returncode
        self.terminated = False
        self.killed = False
        self.stdin = FakeWriter()
        self.stdout = FakeReader([])

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    async def wait(self) -> int:
        return 0 if self.returncode is None else self.returncode


class FakeTransport:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.sent: list[tuple[str, dict[str, Any] | None, bool]] = []
        self.request_id = 0
        self.closed = False

    async def send(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        expect_response: bool = True,
    ) -> int:
        self.sent.append((method, params, expect_response))
        if expect_response:
            self.request_id += 1
            return self.request_id
        return 0

    async def receive(self) -> dict[str, Any]:
        if not self.responses:
            raise EOFError("no more responses")
        return self.responses.pop(0)

    async def close(self) -> None:
        self.closed = True


def make_config(*, codex_cmd: str = "codex --flag", turn_timeout_ms: int = 300_000) -> Config:
    return Config(
        tracker=TrackerConfig(team_key="UPT"),
        agent=AgentConfig(codex_cmd=codex_cmd, turn_timeout_ms=turn_timeout_ms),
        workspace=WorkspaceConfig(root=Path("workspaces")),
    )


@pytest.mark.asyncio
async def test_transport_send_receive_and_close() -> None:
    reader = FakeReader([b'{"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n'])
    writer = FakeWriter()
    process = FakeProcess(returncode=None)
    transport = _JsonRpcTransport(stdout=reader, stdin=writer, process=process)

    request_id = await transport.send("initialize", {"protocolVersion": "2025-01-01"})
    message = await transport.receive()
    await transport.close()

    assert request_id == 1
    assert json.loads(writer.writes[0]) == {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2025-01-01"},
    }
    assert message == {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
    assert writer.closed is True
    assert process.terminated is True


@pytest.mark.asyncio
async def test_transport_receive_raises_on_eof() -> None:
    transport = _JsonRpcTransport(
        stdout=FakeReader([]),
        stdin=FakeWriter(),
        process=FakeProcess(),
    )

    with pytest.raises(EOFError, match="stream closed"):
        await transport.receive()


@pytest.mark.asyncio
async def test_transport_receive_raises_on_malformed_json() -> None:
    transport = _JsonRpcTransport(
        stdout=FakeReader([b"not-json\n"]),
        stdin=FakeWriter(),
        process=FakeProcess(),
    )

    with pytest.raises(ValueError, match="Malformed JSON-RPC message"):
        await transport.receive()


@pytest.mark.asyncio
async def test_spawn_starts_codex_app_server_in_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    process = FakeProcess()

    async def fake_create_subprocess_exec(*args: Any, **kwargs: Any) -> FakeProcess:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = AgentRunner(make_config())
    workspace = WorkspaceInfo(issue_id="UPT-6", path=Path("/repo/worktree"))

    transport = await runner._spawn(workspace)

    assert isinstance(transport, _JsonRpcTransport)
    assert captured["args"] == ("codex", "--flag", "app-server")
    assert captured["kwargs"]["cwd"] == workspace.path
    assert captured["kwargs"]["stdin"] == asyncio.subprocess.PIPE
    assert captured["kwargs"]["stdout"] == asyncio.subprocess.PIPE


@pytest.mark.asyncio
async def test_initialize_and_start_thread_success() -> None:
    runner = AgentRunner(make_config())
    transport = FakeTransport(
        [
            {"jsonrpc": "2.0", "id": 1, "result": {"server": "codex"}},
            {"jsonrpc": "2.0", "id": 2, "result": {"thread_id": "thread-123"}},
        ]
    )

    await runner._initialize(transport)  # type: ignore[arg-type]
    thread_id = await runner._start_thread(transport)  # type: ignore[arg-type]

    assert thread_id == "thread-123"
    assert transport.sent == [
        ("initialize", {"protocolVersion": "2025-01-01"}, True),
        ("initialized", None, False),
        ("thread/start", None, True),
    ]


@pytest.mark.asyncio
async def test_run_turn_success_aggregates_output() -> None:
    runner = AgentRunner(make_config())
    transport = FakeTransport(
        [
            {"jsonrpc": "2.0", "id": 1, "result": {"turn_id": "turn-1"}},
            {"jsonrpc": "2.0", "method": "turn/progress", "params": {"delta": "Hello "}},
            {
                "jsonrpc": "2.0",
                "method": "turn/progress",
                "params": {"message": {"content": [{"text": "world"}]}},
            },
            {"jsonrpc": "2.0", "method": "turn/completed", "params": {"turn_id": "turn-1"}},
        ]
    )

    result = await runner._run_turn(transport, "thread-1", "Prompt")  # type: ignore[arg-type]

    assert result.success is True
    assert result.thread_id == "thread-1"
    assert result.turn_id == "turn-1"
    assert result.output == "Hello world"
    assert transport.sent == [("turn/start", {"thread_id": "thread-1", "prompt": "Prompt"}, True)]


@pytest.mark.asyncio
async def test_run_turn_failure_returns_unsuccessful_result() -> None:
    runner = AgentRunner(make_config())
    transport = FakeTransport(
        [
            {"jsonrpc": "2.0", "id": 1, "result": {"turn_id": "turn-2"}},
            {"jsonrpc": "2.0", "method": "turn/progress", "params": {"output_text": "partial"}},
            {
                "jsonrpc": "2.0",
                "method": "turn/failed",
                "params": {"turn_id": "turn-2", "error": "model_error"},
            },
        ]
    )

    result = await runner._run_turn(transport, "thread-2", None)  # type: ignore[arg-type]

    assert result.success is False
    assert result.output == "partial"
    assert result.error == "model_error"
    assert transport.sent == [("turn/start", {"thread_id": "thread-2"}, True)]


class HangingTransport(FakeTransport):
    async def receive(self) -> dict[str, Any]:
        await asyncio.sleep(3600)
        raise AssertionError("unreachable")


@pytest.mark.asyncio
async def test_run_turn_raises_on_timeout() -> None:
    runner = AgentRunner(make_config(turn_timeout_ms=1))
    transport = HangingTransport([])

    with pytest.raises(RuntimeError, match="exceeded timeout"):
        await runner._run_turn(transport, "thread-timeout", "Prompt")  # type: ignore[arg-type]
