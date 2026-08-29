"""Persistent, allow-listed jobs for the local operations dashboard."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import yaml

from . import collect
from .codex_client import CodexAppServer, CodexProtocolError
from .x_api_usage import append_usage, parse_usage


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "company" / "dashboard"
JOBS_DIR = RUNTIME / "jobs"
BACKUP_ROOT = collect.backup_root()
MODEL = os.environ.get("SNS_DASHBOARD_CODEX_MODEL", "gpt-5.5")

ACTION_IDS = {
    "theme.collect",
    "theme.prepare_release",
    "theme.release",
    "x.prepare",
    "x.record_post",
    "x.measure",
    "metrics.refresh",
    "metrics.explain",
}
MUTATING_ACTIONS = {
    "theme.collect",
    "theme.prepare_release",
    "theme.release",
    "x.record_post",
    "x.measure",
}
TERMINAL_STATES = {"completed", "failed", "cancelled"}
X_STATUS_RE = re.compile(r"^https://(?:www\.)?x\.com/[A-Za-z0-9_]+/status/\d+(?:\?.*)?$")
PUBLIC_BASE = "https://issue-stance-lab.github.io/sns-reaction-map/"


def _now() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec="seconds")


def _run(argv: list[str], *, cwd: Path, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    """Run an exact argv without a shell; callers must use fixed command shapes."""
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=timeout)


def _git_dirty(root: Path) -> list[str]:
    result = _run(["git", "status", "--short"], cwd=root, timeout=30)
    if result.returncode:
        return ["Gitの状態を確認できません"]
    return [line for line in result.stdout.splitlines() if line.strip()]


class JobStore:
    def __init__(self, directory: Path = JOBS_DIR) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def save(self, job: dict[str, Any]) -> None:
        job["updated_at"] = _now()
        target = self.directory / f"{job['id']}.json"
        temporary = target.with_suffix(".tmp")
        with self._lock:
            temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(target)

    def get(self, job_id: str) -> dict[str, Any] | None:
        if not re.fullmatch(r"[a-f0-9]{12}", job_id):
            return None
        target = self.directory / f"{job_id}.json"
        if not target.is_file():
            return None
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def list(self) -> list[dict[str, Any]]:
        jobs = [job for path in self.directory.glob("*.json") if (job := self.get(path.stem))]
        return sorted(jobs, key=lambda item: item.get("created_at") or "", reverse=True)


class JobManager:
    def __init__(self, *, root: Path = ROOT, store: JobStore | None = None, codex: CodexAppServer | None = None) -> None:
        self.root = root
        self.store = store or JobStore()
        self.codex = codex or CodexAppServer(model=MODEL)
        self.codex.add_event_handler(self._on_codex_event)
        self._job_locks: dict[str, threading.Lock] = {}
        self._turn_to_job: dict[str, str] = {}
        self._thread_to_job: dict[str, str] = {}
        self._turn_done: dict[str, threading.Event] = {}
        self._mutation_lock = threading.Lock()
        self._threads: dict[str, threading.Thread] = {}

    def close(self) -> None:
        self.codex.close()

    def themes(self) -> set[str]:
        return {item["key"] for item in collect.collect_themes(dt.date.today())}

    def create(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        if action not in ACTION_IDS:
            raise ValueError("許可されていない操作です")
        theme = payload.get("theme")
        if action.startswith("theme.") and theme not in self.themes():
            raise ValueError("未登録のテーマです")
        if action == "x.record_post" and not X_STATUS_RE.fullmatch(str(payload.get("url") or "")):
            raise ValueError("Xの投稿URLを https://x.com/.../status/... の形で入力してください")
        if action == "metrics.refresh" and payload.get("x_followers") not in {None, ""}:
            try:
                followers = int(payload["x_followers"])
            except (TypeError, ValueError) as exc:
                raise ValueError("Xフォロワー数は0以上の整数で入力してください") from exc
            if followers < 0:
                raise ValueError("Xフォロワー数は0以上の整数で入力してください")
            payload["x_followers"] = followers
        if action in {"theme.prepare_release", "theme.release"}:
            source = self.store.get(str(payload.get("source_job_id") or ""))
            if not source or source.get("theme") != theme:
                raise ValueError("同じテーマの元作業を選んでください")
            payload["source_job_id"] = source["id"]

        job_id = uuid.uuid4().hex[:12]
        job = {
            "id": job_id,
            "action": action,
            "theme": theme,
            "payload": payload,
            "status": "queued",
            "control_owner": "dashboard",
            "created_at": _now(),
            "updated_at": _now(),
            "progress": [{"at": _now(), "state": "queued", "text": "実行待ちです"}],
            "messages": [],
            "thread_id": None,
            "review_thread_id": None,
            "turn_id": None,
            "worktree": None,
            "branch": None,
            "pending_request": None,
            "result": None,
            "error": None,
        }
        self.store.save(job)
        worker = threading.Thread(target=self._run_job, args=(job_id,), name=f"dashboard-job-{job_id}", daemon=True)
        self._threads[job_id] = worker
        worker.start()
        return job

    def send_message(self, job_id: str, text: str) -> dict[str, Any]:
        job = self._require(job_id)
        if job.get("control_owner") != "dashboard":
            raise ValueError("Codexアプリ側に操作権があります")
        if job.get("status") not in TERMINAL_STATES | {"needs_input", "awaiting_approval"}:
            raise ValueError("実行中の作業には、完了または停止後に追加指示を送ってください")
        if not text.strip() or len(text) > 4000:
            raise ValueError("メッセージは1〜4000文字で入力してください")
        cwd = Path(job.get("worktree") or self.root)
        if not job.get("thread_id"):
            raise ValueError("この作業にCodexセッションがありません")
        job.setdefault("messages", []).append({"role": "user", "at": _now(), "text": text.strip()})
        job["status"] = "running"
        self._append(job, "running", "追加指示をCodexへ送りました")
        self.store.save(job)
        worker = threading.Thread(
            target=self._continue_turn,
            args=(job_id, text, cwd, job["action"] in MUTATING_ACTIONS),
            daemon=True,
        )
        worker.start()
        return job

    def decide(self, job_id: str, decision: str) -> dict[str, Any]:
        job = self._require(job_id)
        pending = job.get("pending_request") or {}
        if pending.get("kind") == "runtime":
            if decision not in {"accept", "acceptForSession", "decline", "cancel"}:
                raise ValueError("不正な許可結果です")
            self.codex.respond(int(pending["request_id"]), {"decision": decision})
            job["pending_request"] = None
            job["status"] = "running" if decision.startswith("accept") else "needs_input"
            self._append(job, job["status"], "Codexの操作許可を回答しました")
            self.store.save(job)
            return job
        raise ValueError("現在、回答待ちの許可はありません")

    def cancel(self, job_id: str) -> dict[str, Any]:
        job = self._require(job_id)
        if job.get("turn_id") and job.get("thread_id") and job.get("status") not in TERMINAL_STATES:
            try:
                self.codex.interrupt_turn(job["thread_id"], job["turn_id"])
            except CodexProtocolError:
                pass
        job["status"] = "cancelled"
        self._append(job, "cancelled", "作業を中止しました")
        self.store.save(job)
        return job

    def set_control_owner(self, job_id: str, owner: str) -> dict[str, Any]:
        if owner not in {"dashboard", "codex_app"}:
            raise ValueError("操作権の値が不正です")
        job = self._require(job_id)
        if job.get("status") not in TERMINAL_STATES | {"needs_input", "awaiting_approval"}:
            raise ValueError("実行中は操作権を切り替えられません")
        if owner == "dashboard" and job.get("worktree"):
            conflict = _run(["git", "diff", "--name-only", "--diff-filter=U"], cwd=Path(job["worktree"]), timeout=30)
            if conflict.returncode or conflict.stdout.strip():
                raise ValueError("作業用コピーに競合が残っているため、管理画面へ戻せません")
        job["control_owner"] = owner
        self._append(job, job["status"], "Codexアプリ側へ引き継ぎました" if owner == "codex_app" else "管理画面側へ操作権を戻しました")
        self.store.save(job)
        return job

    def _run_job(self, job_id: str) -> None:
        job = self._require(job_id)
        mutation_acquired = False
        try:
            if job["action"] in MUTATING_ACTIONS:
                mutation_acquired = self._mutation_lock.acquire(blocking=False)
                if not mutation_acquired:
                    raise ValueError("ほかの変更作業が実行中です。完了後にもう一度実行してください")
            job["status"] = "preflight"
            self._append(job, "preflight", "必要なデータと作業場所を確認しています")
            self.store.save(job)
            if job["action"] in MUTATING_ACTIONS and job["action"] not in {"theme.prepare_release", "theme.release"}:
                dirty = _git_dirty(self.root)
                if dirty:
                    raise ValueError("共有の作業場所に未コミットの変更があるため、上書き防止で停止しました: " + " / ".join(dirty[:5]))

            action = job["action"]
            if action == "metrics.refresh":
                self._run_metrics(job)
            elif action == "theme.release":
                self._release(job)
            else:
                cwd, writable = self._job_cwd(job)
                prompt = self._prompt(job)
                self._run_codex(job, cwd, prompt, writable=writable)
                if action == "theme.prepare_release" and job.get("status") == "completed":
                    self._review_release(job, cwd)
        except Exception as exc:
            job = self._require(job_id)
            if job.get("status") != "cancelled":
                job["status"] = "failed"
                job["error"] = str(exc)
                self._append(job, "failed", str(exc))
                self.store.save(job)
                self._notify("管理画面の作業が停止しました", str(exc)[:160])
        finally:
            if mutation_acquired:
                self._mutation_lock.release()

    def _job_cwd(self, job: dict[str, Any]) -> tuple[Path, bool]:
        action = job["action"]
        if action in {"x.prepare", "metrics.explain"}:
            return self.root, False
        if action == "theme.prepare_release":
            source = self._require(job["payload"]["source_job_id"])
            path = Path(source.get("worktree") or "")
            if not path.is_dir():
                raise ValueError("収集作業のworktree（作業用コピー）が見つかりません")
            job["worktree"] = str(path)
            job["branch"] = source.get("branch")
            self.store.save(job)
            return path, True
        worktree = self._create_worktree(job)
        return worktree, True

    def _create_worktree(self, job: dict[str, Any]) -> Path:
        parent = self.root.parent
        worktree = parent / f"isa-wt-dashboard-{job['id']}"
        branch = f"task/dashboard-{job['id']}"
        result = _run(["git", "worktree", "add", str(worktree), "-b", branch], cwd=self.root, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        job["worktree"] = str(worktree)
        job["branch"] = branch
        self._copy_private_inputs(worktree, include_node_modules=job["action"] == "theme.collect")
        self.store.save(job)
        return worktree

    def _copy_private_inputs(self, worktree: Path, *, include_node_modules: bool) -> None:
        themes = yaml.safe_load((self.root / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        for theme in themes.values():
            relative = theme.get("sample_file")
            if not relative:
                continue
            source = self.root / str(relative)
            if source.is_file():
                target = worktree / str(relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        persona = self.root / "configs" / "persona.private.json"
        if persona.is_file():
            target = worktree / "configs" / persona.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(persona, target)
        if include_node_modules and (self.root / "node_modules").is_dir():
            shutil.copytree(self.root / "node_modules", worktree / "node_modules", dirs_exist_ok=True)

    def _prompt(self, job: dict[str, Any]) -> str:
        today = dt.date.today().isoformat()
        action = job["action"]
        theme = job.get("theme")
        if action == "theme.collect":
            return (
                "SNS反応まっぷの定例収集を実行してください。CLAUDE.mdとDATA_REFRESH.mdを守り、"
                f"python3 scripts/refresh_topic.py --topic {theme} --date {today} --backup-dest {BACKUP_ROOT} "
                "を--promoteなしで実行します。収集・分類・検証・更新回の保管まで進め、"
                "公開HTMLと累積正典は更新しないでください。完了後は検査結果を確認し、"
                "収集履歴と台帳の変更をコミットし、取得数・新規数・意見数・次回予定を日本語で報告してください。"
            )
        if action == "theme.prepare_release":
            source = self._require(job["payload"]["source_job_id"])
            run_id = source.get("result", {}).get("run_id") or source["id"]
            run_date = source.get("result", {}).get("date") or today
            return (
                f"テーマ {theme} の公開候補を承認前に準備します。DATA_REFRESH.mdとcompany/QUALITY_GATE.mdを読み、"
                f"python3 scripts/refresh_topic.py --topic {theme} --date {run_date} --run-id {run_id} --backup-dest {BACKUP_ROOT} --resume --prepare-promotion "
                "を実行してください。公開ファイルと正典には反映しません。manifest、差分、検査結果を報告してください。"
            )
        if action == "x.prepare":
            return (
                "$x-daily 今日のSNS反応まっぷのX投稿候補を0〜3件準備してください。"
                "正典のルールを全文確認し、対象者、追加価値、本文、画像、代替テキストを示します。"
                "推奨案の本文は POST_TEXT_BEGIN と POST_TEXT_END の間に、代替テキストは ALT_TEXT_BEGIN と ALT_TEXT_END の間に書いてください。"
                "検索開始時から件数を数え、回答末尾に次のJSONだけの記録ブロックを必ず付けてください。"
                "X_USAGE_JSON_BEGIN {\"mode\":\"chrome\",\"queries_count\":0,\"search_results_loaded\":0,"
                "\"unique_posts_read\":0,\"post_detail_reads\":0,\"unique_users_read\":0,\"owned_posts_read\":0,"
                "\"candidates_shortlisted\":0,\"counts_complete\":true,\"note\":\"\"} X_USAGE_JSON_END。"
                "同じ投稿は24時間内で1件として数えます。数えられなかった項目はnull、途中から計測した場合はcounts_completeをfalseにし、"
                "noteには理由だけを書き、投稿本文・アカウント名・URLは入れないでください。"
                "Xへの投稿・返信の送信は絶対に行わないでください。"
            )
        if action == "x.record_post":
            return (
                "$x-daily ユーザーがXへ投稿した後の記録作業です。"
                f"投稿URLは {job['payload']['url']} です。references/measurement.mdに従い、"
                "content/x/posts.md、THEMES.yaml、必要な同期を行い、検査後にコミットしてください。Xへの送信は行わないでください。"
            )
        if action == "x.measure":
            return (
                "$x-daily references/measurement.mdに従い、24時間以上経過した未計測のX投稿を計測してください。"
                "ログイン済みChromeが使えない場合は他のデータ源で代用せず停止します。"
                "更新と検査が完了したらコミットしてください。Xへの送信は行わないでください。"
            )
        if action == "metrics.explain":
            return (
                "GROWTH.yaml、管理画面の実測キャッシュ、直近の更新履歴を読み、"
                "GA4、Search Console、Supabaseの前回差、異常、テーマ別変化、次に行う1件を、非エンジニア向けに日本語で説明してください。"
                "ファイルは変更しないでください。"
            )
        raise ValueError("この操作のCodex指示がありません")

    def _run_codex(self, job: dict[str, Any], cwd: Path, prompt: str, *, writable: bool) -> None:
        job["status"] = "running"
        self._append(job, "running", "Codexセッションを開始します")
        self.codex.start()
        thread_id = self.codex.start_thread(cwd, writable=writable, service_name="sns_reaction_map_dashboard")
        job["thread_id"] = thread_id
        self._thread_to_job[thread_id] = job["id"]
        self.store.save(job)
        turn_id = self.codex.start_turn(thread_id, cwd, prompt, writable=writable)
        job["turn_id"] = turn_id
        self._turn_to_job[turn_id] = job["id"]
        done = self._turn_done.setdefault(turn_id, threading.Event())
        self.store.save(job)
        if not done.wait(timeout=60 * 60):
            raise TimeoutError("Codex作業が60分以内に完了しませんでした")
        latest = self._require(job["id"])
        if latest.get("status") == "failed":
            raise RuntimeError(latest.get("error") or "Codex作業が失敗しました")
        if latest.get("status") != "cancelled":
            latest["status"] = "completed"
            self._append(latest, "completed", "Codex作業が完了しました")
            latest["result"] = self._result_from_worktree(latest) or latest.get("result") or {}
            if latest["action"] == "x.prepare":
                usage = parse_usage(latest.get("messages") or [], recorded_at=latest["updated_at"])
                if usage:
                    latest["result"]["x_api_usage"] = usage
                    append_usage(usage, source_id=latest["id"], source="dashboard")
                    self._append(latest, "completed", "X検索件数とAPI換算費用を記録しました")
                else:
                    latest["result"]["x_api_usage_missing"] = True
                    self._append(latest, "completed", "候補は作成しましたが、検索件数は記録できませんでした")
            self.store.save(latest)
            self._notify("管理画面の作業が完了しました", latest["action"])

    def _continue_turn(self, job_id: str, text: str, cwd: Path, writable: bool) -> None:
        job = self._require(job_id)
        try:
            self.codex.resume_thread(job["thread_id"], cwd)
            turn_id = self.codex.start_turn(job["thread_id"], cwd, text, writable=writable)
            job["turn_id"] = turn_id
            self._turn_to_job[turn_id] = job_id
            done = self._turn_done.setdefault(turn_id, threading.Event())
            self.store.save(job)
            if not done.wait(timeout=3600):
                raise TimeoutError("追加指示が60分以内に完了しませんでした")
            latest = self._require(job_id)
            if latest.get("status") not in {"failed", "cancelled"}:
                latest["status"] = "completed"
                self._append(latest, "completed", "追加指示が完了しました")
                latest["result"] = self._result_from_worktree(latest) or latest.get("result")
                self.store.save(latest)
        except Exception as exc:
            job = self._require(job_id)
            job["status"] = "failed"
            job["error"] = str(exc)
            self.store.save(job)

    def _review_release(self, job: dict[str, Any], cwd: Path) -> None:
        latest = self._require(job["id"])
        latest["status"] = "reviewing"
        self._append(latest, "reviewing", "制作と別のCodexセッションで品質監査します")
        self.store.save(latest)
        prompt = (
            "あなたはSNS反応まっぷの独立した品質監査AIです。company/QUALITY_GATE.mdを全文読み、"
            f"テーマ {job['theme']} の .staging 内にある最新のpromotion-manifest.jsonと公開候補を読み取り専用で検査してください。"
            "最後に必ず1行で VERDICT: ready_for_ceo / needs_revision / stop のいずれかを出し、根拠と残るリスクを日本語で示してください。"
        )
        self.codex.start()
        thread_id = self.codex.start_thread(cwd, writable=False, service_name="sns_reaction_map_quality_review")
        latest["review_thread_id"] = thread_id
        self._thread_to_job[thread_id] = latest["id"]
        self.store.save(latest)
        turn_id = self.codex.start_turn(thread_id, cwd, prompt, writable=False)
        self._turn_to_job[turn_id] = latest["id"]
        done = self._turn_done.setdefault(turn_id, threading.Event())
        if not done.wait(timeout=3600):
            raise TimeoutError("品質監査が完了しませんでした")
        latest = self._require(job["id"])
        text = "\n".join(message.get("text", "") for message in latest.get("messages") or [] if message.get("role") == "assistant")
        match = re.search(r"VERDICT:\s*(ready_for_ceo|needs_revision|stop)", text)
        verdict = match.group(1) if match else "needs_revision"
        review_path = cwd / "quality" / "reviews" / f"{dt.date.today()}-website-{job['theme']}-{job['id']}.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(f"# 公開候補の品質監査\n\n- 判定: `{verdict}`\n- 作業ID: `{job['id']}`\n\n{text}\n", encoding="utf-8")
        latest["quality"] = {"verdict": verdict, "review": str(review_path.relative_to(cwd))}
        latest["status"] = "awaiting_approval" if verdict == "ready_for_ceo" else "needs_input"
        self._append(latest, latest["status"], "CEO承認待ちです" if verdict == "ready_for_ceo" else "公開前に修正が必要です")
        self.store.save(latest)

    def _run_metrics(self, job: dict[str, Any]) -> None:
        job["status"] = "running"
        self._append(job, "running", "GA4・Search Console・Supabaseの実測を取得しています")
        self.store.save(job)
        result: dict[str, Any] | None = None
        for attempt in range(3):
            result = collect.fetch_live_metrics()
            errors = [value for key, value in result.items() if key.endswith("_error") and value]
            if not errors:
                break
            if attempt < 2:
                self._append(job, "running", f"通信エラーのため再試行します（{attempt + 1}/2）")
                self.store.save(job)
                time.sleep(2 * (attempt + 1))
        job["result"] = result
        if job.get("payload", {}).get("x_followers") is not None:
            job["result"]["x_followers_manual"] = job["payload"]["x_followers"]
            cache = collect.read_live_cache()
            cache["x_followers"] = {
                "value": job["payload"]["x_followers"],
                "last_success_at": _now(),
                "source": "owner_input",
            }
            collect.write_live_cache(cache)
        errors = [value for key, value in (result or {}).items() if key.endswith("_error") and value]
        job["status"] = "needs_input" if errors else "completed"
        job["error"] = " / ".join(errors) if errors else None
        self._append(job, job["status"], "実測値の取得が完了しました" if not errors else "認証または取得先の確認が必要です")
        self.store.save(job)

    def _release(self, job: dict[str, Any]) -> None:
        source = self._require(job["payload"]["source_job_id"])
        if (source.get("quality") or {}).get("verdict") != "ready_for_ceo" or source.get("status") != "awaiting_approval":
            raise ValueError("品質監査が ready_for_ceo の公開候補だけ承認できます")
        dirty = _git_dirty(self.root)
        if dirty:
            raise ValueError("公開先mainに未コミット変更があるため停止しました: " + " / ".join(dirty[:5]))
        worktree = Path(source["worktree"])
        manifest = next(worktree.glob(".staging/refresh/*/*/promotion-manifest.json"), None)
        if manifest is None:
            raise ValueError("承認対象のpromotion-manifest.jsonがありません")
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        job["worktree"] = str(worktree)
        job["branch"] = source["branch"]
        job["status"] = "applying"
        self._append(job, "applying", "CEO承認を台帳へ記録し、候補を適用します")
        self.store.save(job)
        approval_id = self._record_approval(worktree, source, manifest_data)
        args = [
            "python3", "scripts/refresh_topic.py", "--topic", source["theme"], "--date", manifest_data["date"],
            "--run-id", manifest_data["run_id"], "--backup-dest", str(BACKUP_ROOT), "--resume", "--apply-promotion",
        ]
        result = _run(args, cwd=worktree, timeout=3600)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout[-2000:])
        _run(["git", "add", "-A"], cwd=worktree, timeout=60)
        commit = _run(["git", "commit", "-m", f"feat(data): {source['theme']} の承認済み更新を公開"], cwd=worktree, timeout=120)
        if commit.returncode:
            raise RuntimeError(commit.stderr.strip() or commit.stdout.strip())
        self._copy_private_back(worktree)
        job["status"] = "verifying"
        self._append(job, "verifying", "mainへ統合し、公開前検査を実行します")
        self.store.save(job)
        merge = _run(["git", "merge", "--no-ff", source["branch"], "-m", f"Merge branch '{source['branch']}'"], cwd=self.root, timeout=180)
        if merge.returncode:
            _run(["git", "merge", "--abort"], cwd=self.root, timeout=30)
            raise RuntimeError("統合時に衝突したため、mainを元の状態に戻して停止しました")
        for command in (["python3", "scripts/verify_theme_page.py"], ["python3", "scripts/verify_number_provenance.py"], ["python3", "scripts/verify_top_page.py"], ["python3", "-m", "unittest", "discover", "-s", "tests"]):
            check = _run(command, cwd=self.root, timeout=1800)
            if check.returncode:
                raise RuntimeError("マージ後のmainの検査が失敗したためpushしていません: " + (check.stderr or check.stdout)[-1200:])
        push = _run(["git", "push"], cwd=self.root, timeout=300)
        if push.returncode:
            raise RuntimeError("pushに失敗しました: " + (push.stderr or push.stdout)[-1000:])
        live = self._verify_live_pages(source["theme"], manifest_data)
        backup = _run(["python3", "scripts/backup_private_data.py", "--dest", str(BACKUP_ROOT)], cwd=self.root, timeout=600)
        if backup.returncode:
            raise RuntimeError("公開後のバックアップに失敗しました")
        remove = _run(["git", "worktree", "remove", str(worktree)], cwd=self.root, timeout=180)
        if remove.returncode:
            raise RuntimeError("公開は完了しましたが、worktreeの片付けに失敗しました")
        job["result"] = {"approval_id": approval_id, "manifest": manifest_data, "push": "completed", "live_verification": live}
        job["status"] = "completed"
        self._append(job, "completed", "承認済み候補をmainへ統合し、pushとバックアップまで完了しました")
        self.store.save(job)

    def _record_approval(self, worktree: Path, source: dict[str, Any], manifest: dict[str, Any]) -> str:
        path = worktree / "company" / "APPROVALS.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        prefix = f"approval-{dt.date.today():%Y%m%d}-"
        used = [str(item.get("id")) for item in data.get("items") or []]
        sequence = 1
        while f"{prefix}{sequence:03d}" in used:
            sequence += 1
        approval_id = f"{prefix}{sequence:03d}"
        review = (source.get("quality") or {}).get("review")
        manifest_rel = str(Path(manifest["manifest_path"])) if manifest.get("manifest_path") else ".staging/.../promotion-manifest.json"
        data.setdefault("items", []).append({
            "id": approval_id,
            "department": "engineering-data",
            "action": "website_publication",
            "summary": f"{source['theme']} の収集結果をWebsiteへ公開する",
            "reason": "公開候補の品質監査が ready_for_ceo と判定され、管理画面でCEOが承認したため",
            "risks": ["公開後の数値とページ表示を自動検査する"],
            "recommendation": "approve",
            "evidence": [value for value in (review, manifest_rel) if value],
            "status": "approved",
            "requested_at": dt.date.today().isoformat(),
            "decided_at": dt.date.today().isoformat(),
            "decision_note": f"管理画面でCEOが承認。候補SHA256: {manifest.get('manifest_sha256', '記録なし')}",
        })
        data["updated_at"] = dt.date.today().isoformat()
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return approval_id

    def _copy_private_back(self, worktree: Path) -> None:
        themes = yaml.safe_load((worktree / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        for theme in themes.values():
            relative = theme.get("sample_file")
            if not relative:
                continue
            source = worktree / str(relative)
            if source.is_file():
                target = self.root / str(relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

    def _result_from_worktree(self, job: dict[str, Any]) -> dict[str, Any] | None:
        worktree = job.get("worktree")
        if not worktree:
            return None
        reports = sorted(Path(worktree).glob(".staging/refresh/*/*/report.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not reports:
            return None
        try:
            result = json.loads(reports[0].read_text(encoding="utf-8"))
            manifest_path = result.get("promotion_manifest")
            if manifest_path:
                candidate = Path(manifest_path)
                if not candidate.is_absolute():
                    candidate = Path(worktree) / candidate
                if candidate.is_file():
                    manifest = json.loads(candidate.read_text(encoding="utf-8"))
                    result["manifest"] = manifest
                    result["artifacts"] = [
                        {"label": Path(item["target"]).name, "path": item["source"], "target": item["target"]}
                        for item in manifest.get("files", [])
                    ]
            return result
        except json.JSONDecodeError:
            return None

    def artifact_path(self, job_id: str, requested: str) -> Path:
        """Resolve only files explicitly bound by an approved-candidate manifest."""
        job = self._require(job_id)
        worktree = Path(job.get("worktree") or "").resolve()
        artifacts = (job.get("result") or {}).get("artifacts") or []
        allowed = {str(item.get("path")) for item in artifacts}
        if requested not in allowed:
            raise ValueError("公開候補に含まれないファイルです")
        path = Path(requested)
        if not path.is_absolute():
            path = worktree / path
        path = path.resolve()
        if worktree not in path.parents or not path.is_file():
            raise ValueError("公開候補ファイルが見つかりません")
        return path

    def _verify_live_pages(self, theme: str, manifest: dict[str, Any]) -> dict[str, str]:
        themes = yaml.safe_load((self.root / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        page_name = Path(themes[theme]["html"]).name
        expected_page = (self.root / themes[theme]["html"]).read_bytes()
        expected_top = (self.root / "index.html").read_bytes()
        checks = {
            "theme_page": (PUBLIC_BASE + page_name, expected_page),
            "top_page": (PUBLIC_BASE, expected_top),
        }
        pending = dict(checks)
        verified: dict[str, str] = {}
        # GitHub Pagesの反映待ち。通信確認だけを最大2回再試行する。
        for attempt in range(3):
            for key, (url, expected) in list(pending.items()):
                try:
                    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "sns-dashboard/1"})
                    with urllib.request.urlopen(request, timeout=30) as response:
                        body = response.read()
                    if body == expected:
                        verified[key] = url
                        pending.pop(key, None)
                except (urllib.error.URLError, TimeoutError):
                    pass
            if not pending:
                return verified
            if attempt < 2:
                time.sleep(20 * (attempt + 1))
        names = " / ".join(pending)
        raise RuntimeError(f"push後の本番反映を確認できませんでした: {names}")

    def _on_codex_event(self, event: dict[str, Any]) -> None:
        method = event.get("method") or ""
        params = event.get("params") or {}
        turn_id = params.get("turnId") or (params.get("turn") or {}).get("id")
        thread_id = params.get("threadId") or (params.get("thread") or {}).get("id")
        job_id = self._turn_to_job.get(str(turn_id)) if turn_id else None
        if not job_id and thread_id:
            job_id = self._thread_to_job.get(str(thread_id))
        if not job_id:
            return
        job = self.store.get(job_id)
        if not job:
            return
        if method == "item/reasoning/summaryTextDelta":
            delta = str(params.get("delta") or "").strip()
            if delta:
                job["live_summary"] = (job.get("live_summary") or "") + delta
        elif method == "item/completed":
            item = params.get("item") or {}
            if item.get("type") == "agentMessage" and item.get("text"):
                job.setdefault("messages", []).append({"role": "assistant", "at": _now(), "text": item["text"]})
                job["live_summary"] = ""
        elif method in {"item/commandExecution/requestApproval", "item/fileChange/requestApproval", "item/permissions/requestApproval"}:
            job["status"] = "needs_input"
            job["pending_request"] = {
                "kind": "runtime",
                "request_id": event.get("id"),
                "method": method,
                "reason": params.get("reason") or "Codexが操作許可を求めています",
                "command": params.get("command"),
            }
            self._append(job, "needs_input", "Codexの操作許可が必要です")
            self._notify("Codexの確認が必要です", str(job["pending_request"]["reason"])[:160])
        elif method == "error":
            error = params.get("error") or {}
            job["error"] = error.get("message") or str(error)
        elif method == "turn/completed":
            turn = params.get("turn") or {}
            if turn.get("status") == "failed":
                job["status"] = "failed"
                job["error"] = (turn.get("error") or {}).get("message") or job.get("error") or "Codex作業が失敗しました"
            done = self._turn_done.setdefault(str(turn_id), threading.Event())
            done.set()
        self.store.save(job)

    def _append(self, job: dict[str, Any], state: str, text: str) -> None:
        job.setdefault("progress", []).append({"at": _now(), "state": state, "text": text})
        job["progress"] = job["progress"][-80:]

    def _require(self, job_id: str) -> dict[str, Any]:
        job = self.store.get(job_id)
        if not job:
            raise ValueError("作業が見つかりません")
        return job

    def _notify(self, title: str, message: str) -> None:
        if os.uname().sysname != "Darwin":
            return
        safe_title = title.replace('"', "'")
        safe_message = message.replace('"', "'")
        subprocess.run(
            ["osascript", "-e", f'display notification "{safe_message}" with title "{safe_title}"'],
            capture_output=True,
            text=True,
            timeout=10,
        )
