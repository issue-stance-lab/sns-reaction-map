"""Loopback-only HTTP server for the SNS Reaction Map operations dashboard."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import mimetypes
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import collect
from .jobs import JobManager, TERMINAL_STATES


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "company" / "dashboard"


class DashboardHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], token: str, manager: JobManager) -> None:
        super().__init__(address, DashboardHandler)
        self.token = token
        self.manager = manager
        self.last_heartbeat = time.monotonic()


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardHTTPServer

    def log_message(self, format: str, *args: object) -> None:
        # The dashboard keeps raw request details out of its user-facing output.
        return

    def _host_ok(self) -> bool:
        host = self.headers.get("Host", "")
        return host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        return origin in {None, f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}

    def _cookie_token(self) -> str | None:
        cookie = SimpleCookie(self.headers.get("Cookie"))
        value = cookie.get("sns_dashboard_token")
        return value.value if value else None

    def _authorized(self, query: dict[str, list[str]] | None = None) -> bool:
        supplied = self.headers.get("X-Dashboard-Token") or self._cookie_token()
        if query and query.get("token"):
            supplied = query["token"][0]
        return bool(supplied and secrets.compare_digest(supplied, self.server.token))

    def _send(self, status: int, body: bytes, content_type: str, *, cookie: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        if cookie:
            self.send_header("Set-Cookie", f"sns_dashboard_token={self.server.token}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: Any) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _parse(self) -> tuple[str, dict[str, list[str]]]:
        parsed = urllib.parse.urlparse(self.path)
        return parsed.path, urllib.parse.parse_qs(parsed.query)

    def do_GET(self) -> None:  # noqa: N802
        if not self._host_ok():
            self._error(HTTPStatus.BAD_REQUEST, "このMac以外からは開けません")
            return
        path, query = self._parse()
        if path == "/healthz":
            self._json(HTTPStatus.OK, {"ok": True})
            return
        if not self._authorized(query):
            self._error(HTTPStatus.FORBIDDEN, "起動した管理画面のURLから開いてください")
            return
        if path == "/":
            try:
                # `python3 -m scripts.admin_dashboard.server` で起動した場合。
                from scripts.build_admin_dashboard import build
            except ModuleNotFoundError:
                # Finderの .command → `scripts/build_admin_dashboard.py --serve`
                # で起動した場合。
                from build_admin_dashboard import build

            html = build(fetch=False, today=dt.date.today(), interactive=True, token=self.server.token)
            self.server.last_heartbeat = time.monotonic()
            self._send(HTTPStatus.OK, html.encode("utf-8"), "text/html; charset=utf-8", cookie=True)
            return
        if path == "/api/v1/state":
            self.server.last_heartbeat = time.monotonic()
            self._json(HTTPStatus.OK, self._state())
            return
        if path.startswith("/api/v1/jobs/"):
            parts = path.strip("/").split("/")
            if len(parts) >= 4:
                job = self.server.manager.store.get(parts[3])
                if not job:
                    self._error(HTTPStatus.NOT_FOUND, "作業が見つかりません")
                    return
                if len(parts) == 5 and parts[4] == "artifact":
                    try:
                        artifact = self.server.manager.artifact_path(parts[3], (query.get("path") or [""])[0])
                    except ValueError as exc:
                        self._error(HTTPStatus.BAD_REQUEST, str(exc))
                        return
                    media_type = mimetypes.guess_type(artifact.name)[0] or "application/octet-stream"
                    self._send(HTTPStatus.OK, artifact.read_bytes(), media_type)
                elif len(parts) == 5 and parts[4] == "events":
                    data = f"event: job\ndata: {json.dumps(job, ensure_ascii=False)}\n\n".encode("utf-8")
                    self._send(HTTPStatus.OK, data, "text/event-stream; charset=utf-8")
                else:
                    self._json(HTTPStatus.OK, job)
                return
        self._error(HTTPStatus.NOT_FOUND, "ページが見つかりません")

    def do_POST(self) -> None:  # noqa: N802
        if not self._host_ok() or not self._origin_ok():
            self._error(HTTPStatus.FORBIDDEN, "この画面以外からの操作は受け付けません")
            return
        path, query = self._parse()
        if not self._authorized(query):
            self._error(HTTPStatus.FORBIDDEN, "起動した管理画面から操作してください")
            return
        if self.headers.get_content_type() != "application/json":
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "JSON形式だけ受け付けます")
            return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 64_000)
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ValueError("入力形式が不正です")
            if path == "/api/v1/heartbeat":
                self.server.last_heartbeat = time.monotonic()
                self._json(HTTPStatus.OK, {"ok": True})
                return
            if path == "/api/v1/shutdown":
                active = [job for job in self.server.manager.store.list() if job.get("status") not in TERMINAL_STATES | {"needs_input", "awaiting_approval"}]
                if active:
                    raise ValueError("実行中の作業があるため終了できません")
                self._json(HTTPStatus.OK, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if path == "/api/v1/jobs":
                job = self.server.manager.create(str(payload.get("action") or ""), payload.get("payload") or {})
                self._json(HTTPStatus.ACCEPTED, job)
                return
            if path.startswith("/api/v1/jobs/"):
                parts = path.strip("/").split("/")
                if len(parts) != 5:
                    raise ValueError("作業操作のURLが不正です")
                job_id, operation = parts[3], parts[4]
                if operation == "messages":
                    job = self.server.manager.send_message(job_id, str(payload.get("text") or ""))
                elif operation == "decision":
                    job = self.server.manager.decide(job_id, str(payload.get("decision") or ""))
                elif operation == "cancel":
                    job = self.server.manager.cancel(job_id)
                elif operation == "control":
                    job = self.server.manager.set_control_owner(job_id, str(payload.get("owner") or ""))
                else:
                    raise ValueError("許可されていない作業操作です")
                self._json(HTTPStatus.OK, job)
                return
            self._error(HTTPStatus.NOT_FOUND, "操作先が見つかりません")
        except (ValueError, json.JSONDecodeError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def _state(self) -> dict[str, Any]:
        themes = collect.collect_themes(dt.date.today())
        jobs = self.server.manager.store.list()
        return {
            "model": self.server.manager.codex.model,
            "themes": [
                {
                    "key": item["key"],
                    "title": item["title"],
                    "collect_at": item["collect_at"],
                    "refresh_at": item["refresh_at"],
                    "update_mode": item["update_mode"],
                    "update_mode_label": item["update_mode_label"],
                }
                for item in themes
            ],
            "jobs": jobs[:50],
            "dirty": _shared_dirty(),
            "server_time": dt.datetime.now().isoformat(timespec="seconds"),
        }


def _shared_dirty() -> list[str]:
    result = subprocess_run(["git", "status", "--short"], ROOT)
    return result.stdout.splitlines() if result.returncode == 0 else ["状態を確認できません"]


def subprocess_run(argv: list[str], cwd: Path):
    import subprocess

    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=30)


def idle_monitor(server: DashboardHTTPServer) -> None:
    while True:
        time.sleep(15)
        active = any(
            job.get("status") not in TERMINAL_STATES | {"needs_input", "awaiting_approval"}
            for job in server.manager.store.list()
        )
        if not active and time.monotonic() - server.last_heartbeat > 120:
            server.shutdown()
            return


def serve(*, port: int = 8765, open_browser: bool = True) -> int:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    lock_handle = (RUNTIME / "server.lock").open("a+")
    try:
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        session_file = RUNTIME / "server-session.json"
        try:
            existing_url = json.loads(session_file.read_text(encoding="utf-8"))["url"]
        except (OSError, KeyError, json.JSONDecodeError):
            print("管理画面はすでに起動中です。数秒待ってからもう一度開いてください。")
            return 1
        if open_browser:
            webbrowser.open(existing_url)
        return 0
    token = secrets.token_urlsafe(32)
    manager = JobManager(root=ROOT)
    server = DashboardHTTPServer(("127.0.0.1", port), token, manager)
    threading.Thread(target=idle_monitor, args=(server,), name="dashboard-idle-monitor", daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/?token={urllib.parse.quote(token)}"
    session_file = RUNTIME / "server-session.json"
    session_file.write_text(json.dumps({"url": url, "pid": os.getpid()}), encoding="utf-8")
    session_file.chmod(0o600)
    print(f"管理画面を開きます: http://127.0.0.1:{server.server_port}/")
    if os.environ.get("SNS_DASHBOARD_DEBUG_URL") == "1":
        print(url)
    if open_browser:
        threading.Timer(0.25, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        manager.close()
        server.server_close()
        session_file.unlink(missing_ok=True)
        fcntl.flock(lock_handle, fcntl.LOCK_UN)
        lock_handle.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SNS反応まっぷのローカル管理画面")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    return serve(port=args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    raise SystemExit(main())
