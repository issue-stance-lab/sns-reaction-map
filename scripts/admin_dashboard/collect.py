"""管理画面が表示する材料を、リポジトリ内のファイルから読み出す。

ここでは HTML を作らない。すべて素の dict / list として返し、
描画は render.py に任せる。
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

# THEMES.yaml の工程キーと、オーナー向けの日本語名
STAGES = [
    ("collect", "収集"),
    ("classify", "分類"),
    ("classify2d", "2D分類"),
    ("main_issue", "論点分類"),
    ("page_v3", "ページ"),
    ("manga_data", "漫画データ"),
    ("manga_img", "漫画画像"),
    ("published", "公開"),
]

# page_update_mode の意味（THEMES.yaml 冒頭のコメントより）
UPDATE_MODE_LABEL = {
    "adapter": ("自動", "refresh_topic.py の1コマンドで公開まで更新できる"),
    "adapter_candidate": ("準自動", "冪等だが staging の候補入出力に未対応。公開まで一気通貫では回せない"),
    "migration": ("手動", "一度きりの生成スクリプトしかなく、再実行できない"),
    "manual": ("手動", "再実行できる更新スクリプトが存在しない"),
}


def _as_date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value.strip())
        if match:
            return dt.date(*(int(part) for part in match.groups()))
    return None


def _read_yaml(name: str) -> dict:
    path = ROOT / name
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _read_text(name: str) -> str:
    path = ROOT / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


# ---------------------------------------------------------------- テーマ台帳


def collect_themes(today: dt.date) -> list[dict]:
    """THEMES.yaml を、期限までの残り日数つきのテーマ一覧に変換する。"""
    raw = _read_yaml("THEMES.yaml").get("themes") or {}
    periods = _read_json_file("data/verification/sample-periods.json") or {}

    themes = []
    for key, value in raw.items():
        collect_at = _as_date(value.get("collect_at"))
        refresh_at = _as_date(value.get("refresh_at"))
        mode = value.get("page_update_mode") or "manual"
        mode_label, mode_note = UPDATE_MODE_LABEL.get(mode, ("不明", mode))
        period = periods.get(key) or {}

        themes.append(
            {
                "key": key,
                "title": value.get("title") or key,
                "html": value.get("html"),
                "stages": {stage: value.get(stage) for stage, _ in STAGES},
                "collect_at": collect_at,
                "refresh_at": refresh_at,
                "collect_in": (collect_at - today).days if collect_at else None,
                "refresh_in": (refresh_at - today).days if refresh_at else None,
                "collect_mode": value.get("collect_mode") or "scheduled",
                "updated_at": _as_date(value.get("updated_at")),
                "published_at": _as_date(value.get("published_at")),
                "x_posted_at": _as_date(value.get("x_posted_at")),
                "last_attempt_at": _as_date(value.get("last_refresh_attempt_at")),
                "collect_delta": value.get("collect_delta"),
                "update_mode": mode,
                "update_mode_label": mode_label,
                "update_mode_note": mode_note,
                "records": period.get("records"),
                "sample_min": period.get("min"),
                "sample_max": period.get("max"),
                "notes": value.get("notes") or "",
            }
        )

    themes.sort(key=lambda t: (t["collect_in"] is None, t["collect_in"] if t["collect_in"] is not None else 0))
    return themes


def _read_json_file(relative: str):
    path = ROOT / relative
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


# ------------------------------------------------------------------ 流入 KPI


def collect_kpi() -> dict:
    """GROWTH.yaml の週次スナップショットを、古い順に並べて返す。"""
    growth = _read_yaml("GROWTH.yaml")
    snapshots = []
    for row in (growth.get("kpi") or {}).get("snapshots") or []:
        date = _as_date(row.get("date"))
        if not date:
            continue
        snapshots.append(
            {
                "date": date,
                "weekly_users": row.get("weekly_users"),
                "pageviews": row.get("pageviews"),
                "pages_per_session": row.get("pages_per_session"),
                "votes_total": row.get("votes_total"),
                "gsc_impressions": row.get("gsc_impressions"),
                "gsc_clicks": row.get("gsc_clicks"),
                "x_followers": row.get("x_followers"),
                "notes": row.get("notes") or "",
            }
        )
    snapshots.sort(key=lambda s: s["date"])

    phase = growth.get("phase") or {}
    return {
        "snapshots": snapshots,
        "phase": phase.get("current"),
        "phase_goal": phase.get("until") or {},
        "experiments": _collect_experiments(growth),
        "recurring": _collect_recurring(growth),
    }


def _collect_experiments(growth: dict) -> list[dict]:
    items = []
    for bucket in ("capabilities", "experiments"):
        for key, value in (growth.get(bucket) or {}).items():
            if not isinstance(value, dict):
                continue
            items.append(
                {
                    "bucket": "サイト機能" if bucket == "capabilities" else "施策",
                    "key": key,
                    "title": value.get("title") or key,
                    "status": value.get("status") or "unknown",
                    "metric": value.get("metric") or "",
                    "judge_at": _as_date(value.get("judge_at")),
                    "started_at": _as_date(value.get("started_at")),
                }
            )
    order = {"measuring": 0, "built": 1, "building": 2, "idea": 3, "blocked": 4, "adopted": 5, "rejected": 6}
    items.sort(key=lambda i: (order.get(i["status"], 9), i["title"]))
    return items


def _collect_recurring(growth: dict) -> list[dict]:
    items = []
    for key, value in (growth.get("recurring") or {}).items():
        if not isinstance(value, dict):
            continue
        items.append(
            {
                "key": key,
                "title": value.get("title") or key,
                "cadence": value.get("cadence") or "",
                "last_run": _as_date(value.get("last_run")),
                "needs_human": value.get("needs_human") or "",
            }
        )
    items.sort(key=lambda i: (i["last_run"] is not None, i["last_run"] or dt.date.min))
    return items


# -------------------------------------------------------------------- X 投稿

_POST_HEADING = re.compile(r"^##\s+(.+?実績)\s*(\d{4}-\d{2}-\d{2})(?:（(.*?)）)?\s*$")
_VIEWS = re.compile(r"([\d.]+)\s*([KMk])?\s*$")


def _parse_views(text: str) -> int | None:
    match = _VIEWS.match(text.strip())
    if not match:
        return None
    try:
        number = float(match.group(1))
    except ValueError:
        return None
    suffix = (match.group(2) or "").upper()
    if suffix == "K":
        number *= 1_000
    elif suffix == "M":
        number *= 1_000_000
    return int(number)


def collect_x_posts() -> list[dict]:
    """docs/x-posts.md の「◯◯実績 YYYY-MM-DD」節を、1投稿1行に展開する。

    節には2つの形がある。
      - 表形式（リプライ実績）: 1行 = 1リプライ。views 列あり
      - 箇条書き形式（論点ポスト・通常ポスト）: 節全体で1投稿
    """
    text = _read_text("docs/x-posts.md")
    if not text:
        return []

    lines = text.splitlines()
    sections: list[tuple[str, dt.date, str, list[str]]] = []
    current = None
    for line in lines:
        heading = _POST_HEADING.match(line)
        if heading:
            kind, date_text, suffix = heading.groups()
            current = (kind, _as_date(date_text), suffix or "", [])
            sections.append(current)
            continue
        if line.startswith("## "):
            current = None
            continue
        if current is not None:
            current[3].append(line)

    posts: list[dict] = []
    for kind, date, suffix, body in sections:
        if not date:
            continue
        rows = _table_rows(body)
        if rows:
            for row in rows:
                posts.append(
                    {
                        "date": date,
                        "kind": kind.replace("実績", ""),
                        "theme": row.get("テーマ", ""),
                        "target": row.get("リプライ先", ""),
                        "type": row.get("タイプ", ""),
                        "views": _parse_views(row.get("views", "")),
                        "text": "",
                        "note": suffix,
                    }
                )
        else:
            fields = _field_lines(body)
            posts.append(
                {
                    "date": date,
                    "kind": kind.replace("実績", ""),
                    "theme": fields.get("テーマ", ""),
                    "target": "",
                    "type": fields.get("パターン", ""),
                    "views": _views_in_body(body),
                    "text": _post_text(body),
                    "note": suffix,
                }
            )

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def _table_rows(body: list[str]) -> list[dict]:
    header: list[str] | None = None
    rows: list[dict] = []
    for line in body:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells)))
    if header and "views" not in header:
        return []
    return rows


def _field_lines(body: list[str]) -> dict:
    fields = {}
    for line in body:
        match = re.match(r"^\*{0,2}([^:：*]{1,12})\*{0,2}\s*[:：]\s*(.+)$", line.strip())
        if match:
            fields.setdefault(match.group(1).strip(), match.group(2).strip())
    return fields


def _views_in_body(body: list[str]) -> int | None:
    for line in body:
        match = re.search(r"views\s*[:：]\s*\*{0,2}\s*([\d.]+\s*[KMk]?)", line)
        if match:
            return _parse_views(match.group(1))
    return None


def _post_text(body: list[str]) -> str:
    for line in body:
        match = re.match(r"^投稿文\s*[:：]\s*「?(.+?)」?$", line.strip())
        if match:
            return match.group(1)
    in_fence = False
    buffer: list[str] = []
    for line in body:
        if line.strip().startswith("```"):
            if in_fence:
                break
            in_fence = True
            continue
        if in_fence:
            buffer.append(line.strip())
    return " ".join(part for part in buffer if part)


# --------------------------------------------------------------- 変更履歴


COMMIT_TYPE_LABEL = {
    "feat": "機能追加",
    "fix": "不具合修正",
    "docs": "文書",
    "chore": "雑務",
    "refactor": "整理",
    "test": "テスト",
    "style": "見た目",
    "perf": "高速化",
}


def collect_commits(limit: int = 80) -> list[dict]:
    """git log を、日付と種別つきの一覧にする。マージコミットは除く。"""
    try:
        output = subprocess.run(
            ["git", "log", "--no-merges", f"-{limit}", "--date=short", "--pretty=%h%x1f%ad%x1f%s"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    commits = []
    for line in output.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        sha, date_text, subject = parts
        match = re.match(r"^(\w+)(?:\(([^)]+)\))?!?:\s*(.+)$", subject)
        if match:
            kind, scope, message = match.groups()
        else:
            kind, scope, message = "", "", subject
        commits.append(
            {
                "sha": sha,
                "date": _as_date(date_text),
                "kind": kind,
                "kind_label": COMMIT_TYPE_LABEL.get(kind, kind or "その他"),
                "scope": scope or "",
                "message": message,
            }
        )
    return commits


# ------------------------------------------------------------- データ更新履歴


def collect_data_updates() -> list[dict]:
    """data/verification/updates/<テーマ>/<日付>/report.json を集める。"""
    base = ROOT / "data" / "verification" / "updates"
    if not base.exists():
        return []

    updates = []
    for theme_dir in sorted(base.iterdir()):
        if not theme_dir.is_dir():
            continue
        for date_dir in sorted(theme_dir.iterdir()):
            report = date_dir / "report.json"
            if not report.exists():
                continue
            try:
                data = json.loads(report.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            checks = data.get("checks") or {}
            updates.append(
                {
                    "theme": theme_dir.name,
                    "date": _as_date(data.get("date") or date_dir.name),
                    "raw": data.get("raw"),
                    "duplicates": data.get("duplicates"),
                    "new": data.get("new"),
                    "opinions": data.get("opinions"),
                    "errors": data.get("classification_errors"),
                    "status": data.get("status") or "unknown",
                    "checks_ok": all(bool(v) for v in checks.values()) if checks else None,
                    "next_collect_at": _as_date(data.get("next_collect_at")),
                    "minutes": round(sum((data.get("timings") or {}).values()) / 60) if data.get("timings") else None,
                }
            )
    updates.sort(key=lambda u: (u["date"] or dt.date.min), reverse=True)
    return updates


# ------------------------------------------------------------------ 課題一覧

_TASK_HEADING = re.compile(r"^###\s+課題(\d+)\s*[:：]\s*(.+?)\s*$")


def collect_tasks() -> list[dict]:
    """TASK_BOARD.md のアクティブ課題を、番号・題名・状態の3点に落とす。"""
    text = _read_text("TASK_BOARD.md")
    if not text:
        return []

    tasks = []
    current = None
    for line in text.splitlines():
        heading = _TASK_HEADING.match(line)
        if heading:
            current = {"id": int(heading.group(1)), "title": heading.group(2), "status": ""}
            tasks.append(current)
            continue
        if current is not None and not current["status"]:
            match = re.match(r"^\*\*状態\*\*\s*[:：]\s*(.+)$", line.strip())
            if match:
                current["status"] = match.group(1)
    return tasks


# ------------------------------------------------------- 自動取得の生存確認


def collect_source_health(today: dt.date) -> list[dict]:
    """GA4 / Search Console / Supabase / 非公開バックアップの状態を調べる。

    実際に API を叩くのは --fetch のときだけ。ここでは
    「認証ファイルがあるか」「最後にいつ取れたか」までを見る。
    """
    checks: list[dict] = []

    for label, token in (("GA4（アクセス解析）", "ga4-oauth-token.json"), ("Search Console（検索）", "gsc-oauth-token.json")):
        path = ROOT / "secrets" / token
        expired_siblings = sorted((ROOT / "secrets").glob(token.replace(".json", ".expired-*.json"))) if (ROOT / "secrets").exists() else []
        if not path.exists():
            checks.append({"name": label, "ok": False, "detail": f"認証ファイル secrets/{token} がない"})
            continue
        age = (today - dt.date.fromtimestamp(path.stat().st_mtime)).days
        checks.append(
            {
                "name": label,
                "ok": None,
                "detail": f"認証ファイルは {age} 日前に更新。過去に {len(expired_siblings)} 回失効している（実際に取れるかは「最新の数字を取り直す」で確認）",
            }
        )

    env = ROOT / ".env"
    checks.append(
        {
            "name": "Supabase（投票）",
            "ok": env.exists(),
            "detail": ".env に接続情報あり" if env.exists() else ".env がない",
        }
    )

    backups = Path("/Volumes/HD-LE-B/issue-stance-private-backups")
    if backups.exists():
        files = sorted(backups.glob("private-data-*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            age = (today - dt.date.fromtimestamp(files[0].stat().st_mtime)).days
            checks.append({"name": "非公開データのバックアップ", "ok": age <= 14, "detail": f"最新は {age} 日前（{files[0].name}）"})
        else:
            checks.append({"name": "非公開データのバックアップ", "ok": False, "detail": "外付けHDDに1つもない"})
    else:
        checks.append({"name": "非公開データのバックアップ", "ok": None, "detail": "外付けHDD（HD-LE-B）が接続されていないため確認できず"})

    return checks


# ------------------------------------------------------------ 実測値の取り直し


def fetch_live_metrics(days: int = 7) -> dict:
    """GA4 / Search Console / Supabase を実際に叩く（--fetch のときだけ）。

    どれか1つ落ちても残りは表示する。落ちた理由はそのまま画面に出す。
    """
    import sys

    def run(command: list[str]) -> tuple[object, str]:
        try:
            proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
        except subprocess.TimeoutExpired:
            return None, "180秒で応答がなかった"
        if proc.returncode != 0:
            return None, (proc.stdout or proc.stderr or "").strip()[:300]
        try:
            return json.loads(proc.stdout), ""
        except json.JSONDecodeError:
            return None, (proc.stdout or "").strip()[:300]

    python = sys.executable
    ga4, ga4_error = run([python, "scripts/fetch_ga4_metrics.py", "--days", str(days), "--json"])
    gsc, gsc_error = run([python, "scripts/fetch_gsc_metrics.py", "--days", "28", "--json"])
    votes, votes_error = run([python, "scripts/fetch_supabase_votes.py", "--json"])

    return {
        "fetched_at": dt.datetime.now(),
        "ga4": ga4,
        "ga4_error": ga4_error,
        "gsc": gsc,
        "gsc_error": gsc_error,
        "votes": votes,
        "votes_error": votes_error,
    }
