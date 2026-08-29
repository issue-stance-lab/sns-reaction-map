import datetime as dt
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from scripts.admin_dashboard.codex_client import CodexAppServer, CodexProtocolError
from scripts.admin_dashboard.jobs import JobManager, JobStore
from scripts.admin_dashboard.server import DashboardHTTPServer
from scripts.admin_dashboard.x_api_usage import append_usage, parse_usage, read_usage_ledger, summarize_jobs, summarize_usage
from scripts.build_admin_dashboard import build


ROOT = Path(__file__).resolve().parents[1]


class FakeCodex:
    model = "test-model"

    def add_event_handler(self, handler):
        self.handler = handler

    def close(self):
        pass


class ApprovalCompatibilityTests(unittest.TestCase):
    def test_old_cli_approval_name_is_retried(self):
        client = object.__new__(CodexAppServer)
        calls = []

        def request(method, params):
            calls.append((method, dict(params)))
            if params["approvalPolicy"] == "unlessTrusted":
                raise CodexProtocolError("Invalid request: unknown variant `unlessTrusted`")
            return {"ok": True}

        client.request = request
        result = client._request_with_approval_compat("thread/start", {"approvalPolicy": "unlessTrusted"})
        self.assertEqual(result, {"ok": True})
        self.assertEqual([item[1]["approvalPolicy"] for item in calls], ["unlessTrusted", "on-request"])

    def test_unrelated_protocol_errors_are_not_retried(self):
        client = object.__new__(CodexAppServer)
        client.request = lambda method, params: (_ for _ in ()).throw(CodexProtocolError("different error"))
        with self.assertRaisesRegex(CodexProtocolError, "different error"):
            client._request_with_approval_compat("thread/start", {"approvalPolicy": "unlessTrusted"})


class JobStoreTests(unittest.TestCase):
    def test_job_store_survives_a_new_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            first = JobStore(Path(directory))
            first.save({"id": "a" * 12, "created_at": "2026-08-29T00:00:00", "status": "queued"})
            second = JobStore(Path(directory))
            self.assertEqual(second.get("a" * 12)["status"], "queued")

    def test_unknown_actions_and_invalid_x_urls_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = JobManager(root=ROOT, store=JobStore(Path(directory)), codex=FakeCodex())
            with self.assertRaisesRegex(ValueError, "許可されていない"):
                manager.create("shell.run", {"command": "rm -rf"})
            with self.assertRaisesRegex(ValueError, "Xの投稿URL"):
                manager.create("x.record_post", {"url": "https://example.com/not-x"})
            with self.assertRaisesRegex(ValueError, "未登録のテーマ"):
                manager.create("theme.collect", {"theme": "unknown-theme"})
            with self.assertRaisesRegex(ValueError, "Xフォロワー数"):
                manager.create("metrics.refresh", {"x_followers": "-1"})


class InteractiveRenderTests(unittest.TestCase):
    def test_static_dashboard_has_no_execution_controls(self):
        html = build(fetch=False, today=dt.date(2026, 8, 29))
        self.assertNotIn('id="operations"', html)
        self.assertNotIn("/api/v1/jobs", html)

    def test_loopback_dashboard_has_allowlisted_controls(self):
        html = build(fetch=False, today=dt.date(2026, 8, 29), interactive=True, token="test-token")
        self.assertIn('id="operations"', html)
        self.assertIn("theme.collect", html)
        self.assertIn("metrics.refresh", html)
        self.assertNotIn("shell.run", html)
        self.assertIn('id="x-api-usage"', html)


class XApiUsageTests(unittest.TestCase):
    def test_usage_block_is_parsed_without_post_content(self):
        messages = [{"role": "assistant", "text": "candidate text\nX_USAGE_JSON_BEGIN\n"
                     '{"mode":"chrome","queries_count":4,"search_results_loaded":44,'
                     '"unique_posts_read":40,"post_detail_reads":6,"unique_users_read":35,'
                     '"owned_posts_read":1,"candidates_shortlisted":3,"counts_complete":true,'
                     '"note":"all counted"}\nX_USAGE_JSON_END'}]
        usage = parse_usage(messages, recorded_at="2026-08-29T10:00:00+09:00")
        self.assertEqual(usage["unique_posts_read"], 40)
        self.assertEqual(usage["estimated_cost_usd"]["posts_only"], 0.196)
        self.assertEqual(usage["estimated_cost_usd"]["posts_and_users"], 0.546)
        self.assertNotIn("candidate text", json.dumps(usage))

    def test_missing_counts_are_not_invented(self):
        usage = parse_usage([{"role": "assistant", "text": "X_USAGE_JSON_BEGIN "
                             '{"mode":"chrome","unique_posts_read":null,"counts_complete":false}'
                             " X_USAGE_JSON_END"}], recorded_at="2026-08-29T10:00:00+09:00")
        self.assertIsNone(usage["estimated_cost_usd"])

    def test_jobs_are_summarized_for_cost_planning(self):
        usage = parse_usage([{"role": "assistant", "text": "X_USAGE_JSON_BEGIN "
                             '{"mode":"chrome","unique_posts_read":20,"unique_users_read":15,'
                             '"owned_posts_read":0,"counts_complete":true} X_USAGE_JSON_END'}],
                            recorded_at="2026-08-29T10:00:00+00:00")
        result = summarize_jobs([{"result": {"x_api_usage": usage}}], now=dt.datetime(2026, 8, 29, 12, tzinfo=dt.timezone.utc))
        self.assertEqual(result["days_30"]["unique_posts_read"], 20)
        self.assertEqual(result["days_30"]["posts_and_users_usd"], 0.25)

    def test_shared_ledger_is_idempotent_and_contains_no_post_text(self):
        usage = parse_usage([{"role": "assistant", "text": "X_USAGE_JSON_BEGIN "
                             '{"mode":"chrome","search_results_loaded":8,"unique_posts_read":6,'
                             '"unique_users_read":5,"candidates_shortlisted":2,"counts_complete":true,'
                             '"note":"https://x.com/example/status/1 @example を確認"} X_USAGE_JSON_END'}],
                            recorded_at="2026-08-29T10:00:00+00:00")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usage.json"
            append_usage(usage, source_id="same-run", source="codex_app", path=path)
            append_usage(usage, source_id="same-run", source="codex_app", path=path)
            rows = read_usage_ledger(path)
        self.assertEqual(len(rows), 1)
        self.assertNotIn("x.com/example", rows[0]["note"])
        self.assertNotIn("@example", rows[0]["note"])
        self.assertEqual(summarize_usage(rows, now=dt.datetime(2026, 8, 29, 12, tzinfo=dt.timezone.utc))["days_7"]["runs"], 1)

    def test_impossible_count_relationship_is_rejected(self):
        usage = parse_usage([{"role": "assistant", "text": "X_USAGE_JSON_BEGIN "
                             '{"mode":"chrome","search_results_loaded":3,"unique_posts_read":4,'
                             '"counts_complete":true} X_USAGE_JSON_END'}], recorded_at="2026-08-29T10:00:00+09:00")
        self.assertIsNone(usage)


class LoopbackSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = JobManager(root=ROOT, store=JobStore(Path(self.temp.name)), codex=FakeCodex())
        self.server = DashboardHTTPServer(("127.0.0.1", 0), "secret-token", self.manager)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def test_api_requires_launch_token(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(self.base + "/api/v1/state", timeout=5)
        self.assertEqual(error.exception.code, 403)

    def test_launch_url_returns_interactive_dashboard(self):
        with urllib.request.urlopen(self.base + "/?token=secret-token", timeout=5) as response:
            html = response.read().decode("utf-8")
        self.assertIn('id="operations"', html)
        self.assertIn("theme.collect", html)

    def test_wrong_origin_is_rejected(self):
        request = urllib.request.Request(
            self.base + "/api/v1/heartbeat",
            data=b"{}",
            method="POST",
            headers={
                "X-Dashboard-Token": "secret-token",
                "Content-Type": "application/json",
                "Origin": "https://attacker.example",
            },
        )
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(error.exception.code, 403)

    def test_token_allows_state_but_not_unknown_post(self):
        request = urllib.request.Request(
            self.base + "/api/v1/state",
            headers={"X-Dashboard-Token": "secret-token"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.load(response)
        self.assertEqual(payload["model"], "test-model")

        request = urllib.request.Request(
            self.base + "/api/v1/not-allowed",
            data=b"{}",
            method="POST",
            headers={
                "X-Dashboard-Token": "secret-token",
                "Content-Type": "application/json",
                "Origin": self.base,
            },
        )
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
