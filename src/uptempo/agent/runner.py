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

import asyncio
import json
import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

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
        transport = await self._spawn(workspace)
        try:
            await self._initialize(transport)
            thread_id = await self._start_thread(transport)
            return await self._run_turn(transport, thread_id, prompt)
        finally:
            await transport.close()

    async def _spawn(self, workspace: WorkspaceInfo) -> _JsonRpcTransport:
        """Start the Codex app-server subprocess and perform handshake."""
        cmd = shlex.split(self._config.agent.codex_cmd)
        if not cmd:
            raise ValueError("agent.codex_cmd must not be empty")
        if "app-server" not in cmd[1:]:
            cmd.append("app-server")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=workspace.path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        if process.stdin is None or process.stdout is None:
            raise RuntimeError("Codex app-server stdio pipes are unavailable")

        logger.debug("agent_process_spawned", command=cmd, workspace=str(workspace.path))
        return _JsonRpcTransport(stdout=process.stdout, stdin=process.stdin, process=process)

    async def _initialize(self, transport: _JsonRpcTransport) -> None:
        """Send ``initialize`` and wait for the response, then ``initialized``."""
        request_id = await transport.send("initialize", {"protocolVersion": "2025-01-01"})
        response = await self._receive_response(transport, request_id)
        if "result" not in response:
            raise RuntimeError("initialize response missing result")
        await transport.send("initialized", expect_response=False)

    async def _start_thread(self, transport: _JsonRpcTransport) -> str:
        """Send ``thread/start`` and return the ``thread_id``."""
        request_id = await transport.send("thread/start")
        response = await self._receive_response(transport, request_id)
        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("thread/start response missing result object")
        thread_id = result.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise RuntimeError("thread/start response missing thread_id")
        return thread_id

    async def _run_turn(
        self,
        transport: _JsonRpcTransport,
        thread_id: str,
        prompt: str | None,
    ) -> AgentResult:
        """Send ``turn/start``, stream events, return on completion or failure."""
        params: dict[str, Any] = {"thread_id": thread_id}
        if prompt is not None:
            params["prompt"] = prompt

        request_id = await transport.send("turn/start", params)
        output_parts: list[str] = []
        turn_id: str | None = None

        while True:
            message = await transport.receive()
            if "id" in message:
                if message["id"] != request_id:
                    raise RuntimeError(
                        f"Unexpected response id {message['id']} while waiting for turn/start"
                    )
                if "error" in message:
                    raise RuntimeError(f"turn/start failed: {message['error']}")
                result = message.get("result")
                if isinstance(result, dict):
                    turn_id = self._coerce_identifier(result, "turn_id") or turn_id
                    output_parts.extend(_extract_text_fragments(result))
                continue

            method = message.get("method")
            if not isinstance(method, str):
                raise RuntimeError("JSON-RPC notification missing method")
            params_obj = message.get("params")
            if params_obj is None:
                params_obj = {}
            if not isinstance(params_obj, dict):
                raise RuntimeError(f"JSON-RPC notification params must be an object for {method}")

            output_parts.extend(_extract_text_fragments(params_obj))
            turn_id = self._coerce_identifier(params_obj, "turn_id") or turn_id

            if method == "turn/completed":
                if turn_id is None:
                    raise RuntimeError("turn/completed received before turn_id was established")
                return AgentResult(
                    success=True,
                    output="".join(output_parts),
                    thread_id=thread_id,
                    turn_id=turn_id,
                )
            if method == "turn/failed":
                if turn_id is None:
                    raise RuntimeError("turn/failed received before turn_id was established")
                error = self._coerce_identifier(params_obj, "error")
                return AgentResult(
                    success=False,
                    output="".join(output_parts),
                    thread_id=thread_id,
                    turn_id=turn_id,
                    error=error,
                )

    async def _receive_response(
        self,
        transport: _JsonRpcTransport,
        request_id: int,
    ) -> dict[str, Any]:
        message = await transport.receive()
        if message.get("id") != request_id:
            raise RuntimeError(f"Expected response id {request_id}, received {message.get('id')}")
        if "error" in message:
            raise RuntimeError(f"JSON-RPC request failed: {message['error']}")
        return message

    @staticmethod
    def _coerce_identifier(payload: dict[str, Any], key: str) -> str | None:
        value = payload.get(key)
        return value if isinstance(value, str) and value else None


@dataclass(slots=True)
class AgentResult:
    """Outcome of a single agent turn."""

    success: bool
    output: str
    thread_id: str
    turn_id: str
    error: str | None = None


class _ReadableStream(Protocol):
    async def readline(self) -> bytes: ...


class _WritableStream(Protocol):
    def write(self, data: bytes) -> object: ...

    async def drain(self) -> object: ...

    def close(self) -> object: ...

    async def wait_closed(self) -> object: ...


class _ProcessLike(Protocol):
    @property
    def returncode(self) -> int | None: ...

    def terminate(self) -> object: ...

    def kill(self) -> object: ...

    async def wait(self) -> int: ...


class _JsonRpcTransport:
    """Low-level stdio JSON-RPC transport for the Codex subprocess."""

    _stdout: _ReadableStream
    _stdin: _WritableStream
    _process: _ProcessLike
    _next_request_id: int

    def __init__(
        self,
        *,
        stdout: _ReadableStream,
        stdin: _WritableStream,
        process: _ProcessLike,
    ) -> None:
        self._stdout = stdout
        self._stdin = stdin
        self._process = process
        self._next_request_id = 1

    async def send(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        expect_response: bool = True,
    ) -> int:
        """Write a JSON-RPC request/notification to stdin."""
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        request_id = 0
        if expect_response:
            request_id = self._next_request_id
            self._next_request_id += 1
            message["id"] = request_id
        payload = json.dumps(message).encode("utf-8") + b"\n"
        self._stdin.write(payload)
        await self._stdin.drain()
        return request_id

    async def receive(self) -> dict[str, Any]:
        """Read the next JSON-RPC message from stdout."""
        raw = await self._stdout.readline()
        if raw == b"":
            raise EOFError("JSON-RPC stream closed")
        try:
            message = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Malformed JSON-RPC message: {raw.decode('utf-8', errors='replace')}"
            ) from exc
        if not isinstance(message, dict):
            raise ValueError(f"JSON-RPC message must be an object, got {type(message).__name__}")
        return message

    async def close(self) -> None:
        """Terminate the subprocess."""
        self._stdin.close()
        try:
            await self._stdin.wait_closed()
        except (BrokenPipeError, ConnectionResetError):
            logger.debug("agent_stdin_already_closed")

        if self._process.returncode is not None:
            await self._process.wait()
            return

        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5)
        except TimeoutError:
            self._process.kill()
            await self._process.wait()


def _extract_text_fragments(payload: object) -> list[str]:
    fragments: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, str) and key in {"message", "delta", "output_text", "text"}:
                fragments.append(value)
            else:
                fragments.extend(_extract_text_fragments(value))
    elif isinstance(payload, list):
        for item in payload:
            fragments.extend(_extract_text_fragments(item))
    return fragments
