"""Small, dependency-free client for ``codex app-server``.

The dashboard deliberately talks to app-server over stdio.  Nothing listens on a
network socket and the same Codex home/authentication used by the desktop app is
reused.  The client exposes only the thread/turn operations needed by the local
operations dashboard.
"""

from __future__ import annotations

import json
import queue
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


EventHandler = Callable[[dict[str, Any]], None]


class CodexProtocolError(RuntimeError):
    """Raised when app-server returns a JSON-RPC error or exits unexpectedly."""


class CodexAppServer:
    def __init__(self, *, model: str = "gpt-5.5", executable: str = "codex") -> None:
        self.model = model
        self.executable = executable
        self._process: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._next_id = 1
        self._pending: dict[int, queue.Queue[dict[str, Any]]] = {}
        self._pending_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._handlers: list[EventHandler] = []
        self._server_requests: dict[int, dict[str, Any]] = {}
        self._closed = threading.Event()

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def add_event_handler(self, handler: EventHandler) -> None:
        self._handlers.append(handler)

    def start(self) -> None:
        if self.running:
            return
        self._closed.clear()
        self._process = subprocess.Popen(
            [self.executable, "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._reader = threading.Thread(target=self._read_loop, name="codex-app-server", daemon=True)
        self._reader.start()
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "sns_reaction_map_dashboard",
                    "title": "SNS反応まっぷ 管理画面",
                    "version": "1.0.0",
                }
            },
        )
        self.notify("initialized", {})

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        self._closed.set()

    def _send(self, payload: dict[str, Any]) -> None:
        if not self.running or self._process is None or self._process.stdin is None:
            raise CodexProtocolError("Codexの接続が開いていません")
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with self._write_lock:
            self._process.stdin.write(line + "\n")
            self._process.stdin.flush()

    def request(self, method: str, params: dict[str, Any], *, timeout: float = 30) -> dict[str, Any]:
        if not self.running:
            self.start()
        with self._pending_lock:
            request_id = self._next_id
            self._next_id += 1
            response_queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1)
            self._pending[request_id] = response_queue
        try:
            self._send({"method": method, "id": request_id, "params": params})
            try:
                response = response_queue.get(timeout=timeout)
            except queue.Empty as exc:
                raise CodexProtocolError(f"Codexの応答が時間内に返りませんでした: {method}") from exc
            if response.get("error"):
                message = response["error"].get("message") or str(response["error"])
                raise CodexProtocolError(message)
            return response.get("result") or {}
        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"method": method, "params": params})

    def respond(self, request_id: int, result: dict[str, Any]) -> None:
        self._send({"id": request_id, "result": result})
        self._server_requests.pop(request_id, None)

    def pending_server_request(self, request_id: int) -> dict[str, Any] | None:
        return self._server_requests.get(request_id)

    def start_thread(self, cwd: Path, *, writable: bool, service_name: str) -> str:
        result = self.request(
            "thread/start",
            {
                "model": self.model,
                "cwd": str(cwd),
                "approvalPolicy": "unlessTrusted",
                # The installed desktop build currently expects the legacy kebab-case value here.
                "sandbox": "workspace-write" if writable else "read-only",
                "serviceName": service_name,
            },
        )
        return str(result["thread"]["id"])

    def resume_thread(self, thread_id: str, cwd: Path) -> None:
        self.request("thread/resume", {"threadId": thread_id, "cwd": str(cwd), "model": self.model})

    def start_turn(self, thread_id: str, cwd: Path, prompt: str, *, writable: bool) -> str:
        result = self.request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": [{"type": "text", "text": prompt}],
                "cwd": str(cwd),
                "model": self.model,
                "approvalPolicy": "unlessTrusted",
                "sandboxPolicy": {
                    "type": "workspaceWrite" if writable else "readOnly",
                    **({"writableRoots": [str(cwd)], "networkAccess": True} if writable else {}),
                },
                "summary": "concise",
            },
        )
        return str(result["turn"]["id"])

    def interrupt_turn(self, thread_id: str, turn_id: str) -> None:
        self.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})

    def _read_loop(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        try:
            for line in process.stdout:
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                request_id = message.get("id")
                if request_id is not None and ("result" in message or "error" in message):
                    with self._pending_lock:
                        target = self._pending.get(int(request_id))
                    if target is not None:
                        target.put(message)
                    continue
                # A message with both method and id is a server-initiated request.
                if request_id is not None and message.get("method"):
                    self._server_requests[int(request_id)] = message
                for handler in tuple(self._handlers):
                    try:
                        handler(message)
                    except Exception:
                        # A UI/event consumer must never kill the protocol reader.
                        continue
        finally:
            self._closed.set()
            error = {"error": {"message": "Codexとの接続が終了しました"}}
            with self._pending_lock:
                pending = list(self._pending.values())
            for target in pending:
                try:
                    target.put_nowait(error)
                except queue.Full:
                    pass

    def wait_for_turn(self, thread_id: str, turn_id: str, *, timeout: float = 3600) -> dict[str, Any]:
        """Wait using a temporary event handler; useful for command-line probes and tests."""
        target: queue.Queue[dict[str, Any]] = queue.Queue()

        def handler(message: dict[str, Any]) -> None:
            if message.get("method") != "turn/completed":
                return
            params = message.get("params") or {}
            if params.get("threadId") == thread_id and (params.get("turn") or {}).get("id") == turn_id:
                target.put(message)

        self.add_event_handler(handler)
        try:
            return target.get(timeout=timeout)
        except queue.Empty as exc:
            raise CodexProtocolError("Codex作業の完了を待てませんでした") from exc


def wait_until(predicate: Callable[[], bool], *, timeout: float = 5.0) -> bool:
    """Small polling helper kept here so tests do not need arbitrary sleeps."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()
