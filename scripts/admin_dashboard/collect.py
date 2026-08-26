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

# 非公開の正典と更新回履歴の保管先（DATA_REFRESH.md の正規保存先）
BACKUP_ROOT = Path("/Volumes/HD-LE-B/issue-stance-private-backups")


def backup_root() -> Path:
    """バックアップ先。actions.py の実行準備チェックと共有する。"""
    return BACKUP_ROOT


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


def collect_sample_files() -> list[str]:
    """各テーマの正典ファイルのパス。gitignore 対象なので作業コピーには入らない。

    OPERATIONS.md ⓪ の「欠落チェック」と同じものを、管理画面から見えるようにする。
    """
    raw = _read_yaml("THEMES.yaml").get("themes") or {}
    return [value["sample_file"] for value in raw.values() if value.get("sample_file")]


# --------------------------------------------------------------- 会社運営台帳


MILESTONE_LABELS = {
    "first_90_days": "90日目標",
    "first_year": "1年目標",
    "third_year": "3年目標",
}

GOAL_LABELS = {
    "adsense_status": "AdSense",
    "adsense_revenue_yen_min": "AdSense収益",
    "adsense_monthly_revenue_yen": "AdSense月収",
    "monthly_revenue_yen": "月間収益",
    "monthly_pageviews": "月間PV",
    "monthly_pageviews_provisional": "月間PV（仮）",
    "weekly_users": "週間利用者",
    "x_followers": "Xフォロワー",
    "note_new_posts": "note新規記事",
    "votes_total": "累計投票",
    "company_form": "会社形態",
}

DEPARTMENT_ORDER = (
    "executive",
    "editorial",
    "business",
    "engineering-data",
    "corporate",
    "quality",
)


def _mission_from_markdown(relative: str) -> tuple[str, str]:
    """部門文書の見出しと「使命」の最初の段落を読む。"""
    lines = _read_text(relative).splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), Path(relative).stem)
    mission = ""
    for index, line in enumerate(lines):
        if line.strip() != "## 使命":
            continue
        paragraph = []
        for candidate in lines[index + 1:]:
            if candidate.startswith("## "):
                break
            if candidate.strip():
                paragraph.append(candidate.strip())
            elif paragraph:
                break
        mission = " ".join(paragraph)
        break
    return title, mission


def _finance_period(period: dict, limit: int) -> dict:
    revenue = period.get("revenue") or {}
    costs = period.get("costs") or {}
    revenue_known = [value for value in revenue.values() if isinstance(value, (int, float))]
    costs_known = [value for value in costs.values() if isinstance(value, (int, float))]
    unknown_revenue = [key for key, value in revenue.items() if value is None]
    unknown_costs = [key for key, value in costs.items() if value is None]
    revenue_total = sum(revenue_known)
    cost_total = sum(costs_known)
    profit = period.get("profit")
    if profit is None and not unknown_revenue and not unknown_costs:
        profit = revenue_total - cost_total
    return {
        "month": str(period.get("month") or ""),
        "revenue": revenue,
        "costs": costs,
        "revenue_total": revenue_total,
        "cost_total": cost_total,
        "profit": profit,
        "unknown_revenue": unknown_revenue,
        "unknown_costs": unknown_costs,
        "cost_limit": limit,
        "cost_over": not unknown_costs and cost_total > limit,
        "notes": period.get("notes") or "",
    }


def collect_company(today: dt.date) -> dict:
    """CEOが判断するための会社台帳を一度に読む。

    各数値をHTMLに直書きせず、company/の正典をそのまま表示用に
    整える。必須欄の欠落、期限超過、承認待ち、費用上限もここで検知する。
    """
    goals_raw = _read_yaml("company/GOALS.yaml")
    handoffs_raw = _read_yaml("company/HANDOFFS.yaml")
    approvals_raw = _read_yaml("company/APPROVALS.yaml")
    finance_raw = _read_yaml("company/FINANCE.yaml")
    corrections_raw = _read_yaml("company/CORRECTIONS.yaml")

    milestones = []
    for milestone in goals_raw.get("milestones") or []:
        due_at = _as_date(milestone.get("due_at"))
        milestone_goals = [
            {
                "key": key,
                "label": GOAL_LABELS.get(key, key),
                "value": value,
            }
            for key, value in (milestone.get("goals") or {}).items()
        ]
        milestones.append(
            {
                "id": milestone.get("id") or "",
                "label": MILESTONE_LABELS.get(milestone.get("id"), milestone.get("id") or "目標"),
                "due_at": due_at,
                "due_in": (due_at - today).days if due_at else None,
                "goals": milestone_goals,
                "assumptions": milestone.get("assumptions") or {},
            }
        )

    required = handoffs_raw.get("required_fields") or []
    handoffs = []
    ledger_alerts = []
    terminal_statuses = {"completed", "cancelled", "withdrawn"}
    for item in handoffs_raw.get("items") or []:
        due_at = _as_date(item.get("due_at"))
        missing = [field for field in required if field not in item]
        normalized = dict(item)
        normalized["due_at"] = due_at
        normalized["due_in"] = (due_at - today).days if due_at else None
        normalized["missing_fields"] = missing
        handoffs.append(normalized)
        if missing:
            ledger_alerts.append(
                {"tone": "danger", "kind": "ledger", "title": f"{item.get('id', '名前なし')} に必須欄がありません", "detail": " / ".join(missing)}
            )
        if due_at and due_at < today and item.get("status") not in terminal_statuses:
            ledger_alerts.append(
                {
                    "tone": "danger",
                    "kind": "deadline",
                    "title": f"{item.get('id', '業務')} が {(today - due_at).days} 日超過",
                    "detail": item.get("next_action") or "次の一手が未記入です",
                }
            )
    handoffs.sort(key=lambda item: (item["due_at"] is None, item["due_at"] or dt.date.max, item.get("id") or ""))

    approvals = []
    for item in approvals_raw.get("items") or []:
        normalized = dict(item)
        normalized["requested_at"] = _as_date(item.get("requested_at"))
        normalized["decided_at"] = _as_date(item.get("decided_at"))
        approvals.append(normalized)
        if item.get("status") == "pending":
            ledger_alerts.append(
                {
                    "tone": "warn",
                    "kind": "approval",
                    "title": f"CEO承認待ち: {item.get('summary') or item.get('id')}",
                    "detail": item.get("reason") or "判断理由が未記入です",
                }
            )
    approvals.sort(key=lambda item: (item.get("status") != "pending", item.get("requested_at") or dt.date.min), reverse=False)

    limit = int((finance_raw.get("policy") or {}).get("monthly_cost_limit_until_revenue") or 0)
    periods = [_finance_period(period, limit) for period in finance_raw.get("periods") or []]
    periods.sort(key=lambda period: period["month"], reverse=True)
    current_finance = periods[0] if periods else None
    if current_finance:
        unknown = current_finance["unknown_revenue"] + current_finance["unknown_costs"]
        if unknown:
            ledger_alerts.append(
                {
                    "tone": "warn",
                    "kind": "finance",
                    "title": f"{current_finance['month']} の収支が未確定です",
                    "detail": f"未確認: {', '.join(unknown)}。未確認を0円とは扱いません",
                }
            )
        if current_finance["cost_over"]:
            ledger_alerts.append(
                {
                    "tone": "danger",
                    "kind": "finance",
                    "title": f"月間費用が上限 {limit:,} 円を超えています",
                    "detail": f"確定費用 {current_finance['cost_total']:,} 円",
                }
            )

    corrections = []
    for item in corrections_raw.get("items") or []:
        normalized = dict(item)
        normalized["received_at"] = _as_date(item.get("received_at"))
        corrections.append(normalized)
        if item.get("status") not in terminal_statuses | {"resolved", "closed"}:
            ledger_alerts.append(
                {
                    "tone": "danger",
                    "kind": "correction",
                    "title": f"未解決の訂正案件: {item.get('summary') or item.get('id', '名前なし')}",
                    "detail": item.get("next_action") or "対応内容を確認してください",
                }
            )

    departments = []
    for key in DEPARTMENT_ORDER:
        title, mission = _mission_from_markdown(f"company/departments/{key}.md")
        departments.append({"key": key, "title": title, "mission": mission})

    return {
        "north_star": (goals_raw.get("north_star") or {}).get("statement") or "",
        "constraints": goals_raw.get("constraints") or {},
        "milestones": milestones,
        "handoffs": handoffs,
        "approvals": approvals,
        "pending_approvals": [item for item in approvals if item.get("status") == "pending"],
        "finance": periods,
        "current_finance": current_finance,
        "corrections": corrections,
        "departments": departments,
        "alerts": ledger_alerts,
    }


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
_CONVERSATION_HEADING = re.compile(r"^###\s+会話フォロー\s+(\d{4}-\d{2}-\d{2})\s*$")

# 実績表の見出しは以下の2形式だけを認める。
#   旧形式（〜2026-08-03）: views 列。中身は「返信先（元投稿）の表示回数」で、自分の到達ではない
#   現行形式（2026-08-06〜）: 元投稿views と 自リプライ表示 に分かれている
# 2026-08-06 に見出しを変えたとき、未知の見出しを黙って捨てる実装だったため
# 8/6〜8/10 の実測値が5日ぶんダッシュボードから消えていた。見出しを増やすときは
# ここと tests/test_admin_dashboard.py の両方を必ず更新すること。
_COL_LEGACY_PARENT = "views"
_COL_PARENT = "元投稿views"
_COL_OWN = "自リプライ表示"
_KNOWN_VIEW_COLS = {_COL_LEGACY_PARENT, _COL_PARENT, _COL_OWN}
# 投稿を特定する列。これが無い表は投稿一覧ではない（GA4の参照元表など）
_IDENTITY_COLS = ("リプライ先", "引用元", "投稿")
# 投稿表で使ってよい列名。ここに無い列があれば落とす（列名の変更を検知するため）
_KNOWN_POST_COLS = {
    "#", "リプライ先", "引用元", "投稿", "テーマ", "タイプ", "投稿文冒頭",
    _COL_LEGACY_PARENT, _COL_PARENT, _COL_OWN,
    "元投稿の返信数", "元投稿からの経過",
}

# 先頭の数値だけを読む。後続の注記（「（8/8 18:35時点）」など）は無視する。
_VIEWS_RE = re.compile(r"^\*{0,2}\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(万|[KkMm])?")
_MISSING_MARKS = ("未取得", "未計測", "未表示", "要確認", "該当なし")
# 「投稿直後」「投稿7分後」は確定値ではない。8/8の暫定値4は2日後に51、2は37になった。
_PROVISIONAL_RE = re.compile(r"投稿(直後|\s*\d+\s*[分時])")


def _parse_views(text: str) -> int | None:
    """表示回数の文字列を整数にする。太字・カンマ・万・K/M・後続の注記に対応する。"""
    stripped = (text or "").strip()
    match = _VIEWS_RE.match(stripped)
    if not match:
        return None
    try:
        number = float(match.group(1).replace(",", ""))
    except ValueError:
        return None
    suffix = (match.group(2) or "").upper()
    if suffix == "万":
        number *= 10_000
    elif suffix == "K":
        number *= 1_000
    elif suffix == "M":
        number *= 1_000_000
    return int(number)


# 注記に入れた「いいね6・リポスト2」を構造化して取り出す。列を増やさずに
# 後から時間帯・型ごとの分析ができるようにするため（2026-08-10）。
_LIKES_RE = re.compile(r"いいね\s*([\d,]+)")
_REPOSTS_RE = re.compile(r"リポスト\s*([\d,]+)")


def _engagement_in(text: str, pattern: re.Pattern) -> int | None:
    match = pattern.search(text or "")
    if not match:
        return None
    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _views_status(text: str) -> str:
    """measured / provisional / missing を返す。provisional は集計に入れない。

    判定は先頭に数値があるかどうかで行う。注記に「未取得」「投稿7分後」といった
    旧状態への言及が入ることがあり（例: `**74**（8/10計測。旧記録は「未取得」）`）、
    語の有無だけで見ると本計測値を取りこぼす。
    """
    stripped = (text or "").strip()
    if not _VIEWS_RE.match(stripped):
        return "missing"
    # 「8/10計測」「昼計測」など本計測を示す語があれば、注記が旧暫定値に
    # 言及していても確定値として扱う
    if "計測" in stripped:
        return "measured"
    if _PROVISIONAL_RE.search(stripped):
        return "provisional"
    return "measured"


def collect_x_posts() -> list[dict]:
    """content/x/posts.md の「◯◯実績 YYYY-MM-DD」節を、1投稿1行に展開する。

    節には2つの形がある。
      - 表形式（リプライ実績）: 1行 = 1リプライ。views 列あり
      - 箇条書き形式（論点ポスト・通常ポスト）: 節全体で1投稿
    """
    text = _read_text("content/x/posts.md")
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
        label = f"{kind} {date}"
        rows = _table_rows(body, label)
        if rows:
            for row in rows:
                own_raw = row.get(_COL_OWN, "")
                # 旧形式の views 列は元投稿（返信先）の表示回数。自分の到達ではない
                parent_raw = row.get(_COL_PARENT) or row.get(_COL_LEGACY_PARENT, "")
                post_type = row.get("タイプ", "")
                posts.append(
                    {
                        "date": date,
                        "kind": kind.replace("実績", ""),
                        "theme": row.get("テーマ", ""),
                        "target": row.get("リプライ先") or row.get("投稿", ""),
                        "type": post_type,
                        "parent_views": _parse_views(parent_raw),
                        "own_views": _parse_views(own_raw),
                        "own_views_status": _views_status(own_raw),
                        "own_likes": _engagement_in(own_raw, _LIKES_RE),
                        "own_reposts": _engagement_in(own_raw, _REPOSTS_RE),
                        "has_url": _has_url(post_type, kind),
                        "text": "",
                        "note": suffix,
                    }
                )
        else:
            fields = _field_lines(body)
            own_raw = _views_text_in_body(body)
            post_type = fields.get("パターン", "")
            posts.append(
                {
                    "date": date,
                    "kind": kind.replace("実績", ""),
                    "theme": fields.get("テーマ", ""),
                    "target": "",
                    "type": post_type,
                    # 箇条書き形式（論点ポスト・通常ポスト）の表示回数は自分の投稿のもの
                    "parent_views": None,
                    "own_views": _parse_views(own_raw),
                    "own_views_status": _views_status(own_raw),
                    "own_likes": _engagement_in(own_raw, _LIKES_RE),
                    "own_reposts": _engagement_in(own_raw, _REPOSTS_RE),
                    "has_url": _has_url(post_type, kind),
                    "text": _post_text(body),
                    "note": suffix,
                }
            )

    # 会話フォローはリプライ実績節の中にある独立投稿。表の外に記録されるため、
    # 表だけを展開する上の処理では管理画面から欠落する。
    for date, body in _conversation_sections(lines):
        fields = _field_lines(body)
        own_raw = _views_text_in_body(body)
        posts.append(
            {
                "date": date,
                "kind": "会話フォロー",
                "theme": fields.get("テーマ", ""),
                "target": fields.get("返信先", ""),
                "type": "URLなし",
                "parent_views": None,
                "own_views": _parse_views(own_raw),
                "own_views_status": _views_status(own_raw),
                "has_url": False,
                "text": _post_text(body),
                "note": "",
            }
        )

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def _conversation_sections(lines: list[str]) -> list[tuple[dt.date, list[str]]]:
    """`### 会話フォロー YYYY-MM-DD` を独立投稿として切り出す。"""
    sections: list[tuple[dt.date, list[str]]] = []
    for index, line in enumerate(lines):
        match = _CONVERSATION_HEADING.match(line)
        if not match:
            continue
        end = next(
            (i for i in range(index + 1, len(lines)) if lines[i].startswith("## ") or lines[i].startswith("### ")),
            len(lines),
        )
        date = _as_date(match.group(1))
        if date:
            sections.append((date, lines[index + 1:end]))
    return sections


def _has_url(post_type: str, kind: str) -> bool:
    """URLを含む投稿か。タイプ列の語彙から判定する（列は増やさない）。"""
    blob = f"{post_type} {kind}"
    if "URLなし" in blob:
        return False
    return "URL付き" in blob or "URLあり" in blob


def _table_rows(body: list[str], label: str = "") -> list[dict]:
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
    if header is None:
        return []
    # 実績節にはGA4の参照元表など投稿一覧でない表も混ざる。投稿を特定する列が
    # ないものは投稿表とみなさない（従来どおり箇条書き形式として扱う）
    if not any(col in header for col in _IDENTITY_COLS):
        return []
    # 列名が変わったら黙って捨てずに落とす。2026-08-06 の見出し変更を拾えず、
    # 8/6〜8/10の実測値が5日ぶん消えたまま既存テスト13件が通り続けた。
    unknown = [c for c in header if c not in _KNOWN_POST_COLS]
    if unknown:
        raise ValueError(
            f"content/x/posts.md の「{label}」に未対応の列があります: {unknown}\n"
            f"投稿表で使える列は {sorted(_KNOWN_POST_COLS)} です。\n"
            f"表示回数の列は {sorted(_KNOWN_VIEW_COLS)} のいずれかにしてください。\n"
            f"列を増やすときは scripts/admin_dashboard/collect.py と "
            f"tests/test_admin_dashboard.py の両方を更新してください。"
        )
    return rows


def _field_lines(body: list[str]) -> dict:
    fields = {}
    for line in body:
        match = re.match(r"^\*{0,2}([^:：*]{1,12})\*{0,2}\s*[:：]\s*(.+)$", line.strip())
        if match:
            fields.setdefault(match.group(1).strip(), match.group(2).strip())
    return fields


def _views_text_in_body(body: list[str]) -> str:
    """箇条書き形式の「views: 10」「表示回数: **6**（…）」から値の文字列を取り出す。"""
    for line in body:
        match = re.search(r"(?:views|表示回数)\s*[:：]\s*(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return ""


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


# ------------------------------------------------- X計測・週次レビューの滞り

_WEEKLY_REVIEW_HEADING = re.compile(
    r"^###\s+(\d{4}-\d{2}-\d{2})〜(\d{4}-\d{2}-\d{2})\s*$"
)


def collect_x_measurement(now: dt.datetime) -> dict:
    """24〜48時間後の計測と週次レビューが滞っていないかを見る。

    定期タスク（x-daily-measure / x-weekly-review）が黙って止まっても
    気づけるようにするための材料。**タスクの生死ではなく結果で判定する。**
    タスクの登録状態を見に行くと「動いてはいるが毎回失敗している」を見逃す。

    2026-07-09 に止まった daily-growth-loop は、45日間オフのまま誰も気づかなかった。
    同じことを繰り返さないために、滞りは必ずこの画面に出す。
    """
    text = _read_text("content/x/posts.md")
    overdue: list[dict] = []
    if text:
        try:
            import sys

            scripts_dir = str(ROOT / "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            import x_post_views

            for item in x_post_views.find_pending(text, now):
                if item.timing == "waiting":
                    continue
                overdue.append(
                    {
                        "url": item.url,
                        "target": item.target,
                        "kind": item.kind,
                        "age_hours": round(item.age_hours, 1),
                        "timing": item.timing,
                    }
                )
        except Exception as exc:  # 計測の集計に失敗しても画面全体は出す
            return {"error": str(exc), "overdue": [], "review_latest": None}

    review_latest = None
    for line in _read_text("content/x/weekly-reviews.md").splitlines():
        matched = _WEEKLY_REVIEW_HEADING.match(line)
        if matched:
            end = _as_date(matched.group(2))
            if end and (review_latest is None or end > review_latest):
                review_latest = end

    return {
        "error": None,
        "overdue": sorted(overdue, key=lambda item: -item["age_hours"]),
        "review_latest": review_latest,
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


# 課題1件から読み取る欄。状態以外は任意で、書いていなければ空になる。
# 「未着手が何件」より「自分の判断待ちが何件」のほうが行動につながるので、
# 判断待ちと次にすることを別欄として持てるようにしている。
TASK_FIELDS = {
    "状態": "status",
    "優先度": "priority",
    "次にすること": "next_step",
    "判断待ち": "waiting_on",
    "関連テーマ": "related",
}

_TASK_FIELD = re.compile(r"^\*\*(" + "|".join(TASK_FIELDS) + r")\*\*\s*[:：]\s*(.+)$")


def collect_tasks() -> list[dict]:
    """TASK_BOARD.md のアクティブ課題を読む。任意欄は未記入でも落ちない。"""
    text = _read_text("TASK_BOARD.md")
    if not text:
        return []

    tasks = []
    current = None
    for line in text.splitlines():
        heading = _TASK_HEADING.match(line)
        if heading:
            current = {"id": int(heading.group(1)), "title": heading.group(2)}
            current.update({key: "" for key in TASK_FIELDS.values()})
            tasks.append(current)
            continue
        if current is None:
            continue
        match = _TASK_FIELD.match(line.strip())
        # 同じ欄が複数回出てきたら最初のものを採る（状態欄に経緯が続く書き方があるため）
        if match and not current[TASK_FIELDS[match.group(1)]]:
            current[TASK_FIELDS[match.group(1)]] = match.group(2).strip()
    return tasks


# ------------------------------------------------------- 自動取得の生存確認


def collect_source_health(today: dt.date) -> list[dict]:
    """GA4 / Search Console / Supabase / 非公開バックアップの状態を調べる。

    実際に API を叩くのは --fetch のときだけ。ここでは
    「認証ファイルがあるか」「最後にいつ取れたか」までを見る。
    """
    checks: list[dict] = []
    cache = read_live_cache()

    # 判定は「最後に実際に取れたのはいつか」で行う。認証ファイルの更新日では、
    # ファイルが残ったまま失効しているケース（Google は数日で失効しうる）を見逃す。
    for key, label in LIVE_SOURCES:
        entry = cache.get(key) or {}
        success = _as_date(entry.get("last_success_at"))
        attempt = _as_date(entry.get("last_attempt_at"))
        failures = int(entry.get("consecutive_failures") or 0)

        if success is None and attempt is None:
            checks.append(
                {
                    "name": label,
                    "ok": None,
                    "detail": "まだ一度も取得を試していない（--fetch を付けて実行すると分かります）",
                }
            )
            continue

        if success is None:
            checks.append({"name": label, "ok": False, "detail": f"一度も成功していない。最後の失敗: {entry.get('last_error') or '理由不明'}"})
            continue

        age = (today - success).days
        detail = f"最後に取れたのは {age} 日前（{success}）"
        if failures:
            detail += f"。そのあと {failures} 回続けて失敗しています: {entry.get('last_error') or '理由不明'}"
        checks.append({"name": label, "ok": age <= 7 and failures < 2, "detail": detail})

    for label, token in (("GA4の認証ファイル", "ga4-oauth-token.json"), ("Search Consoleの認証ファイル", "gsc-oauth-token.json")):
        path = ROOT / "secrets" / token
        expired_siblings = sorted((ROOT / "secrets").glob(token.replace(".json", ".expired-*.json"))) if (ROOT / "secrets").exists() else []
        if not path.exists():
            checks.append({"name": label, "ok": False, "detail": f"secrets/{token} がない"})
            continue
        age = (today - dt.date.fromtimestamp(path.stat().st_mtime)).days
        checks.append(
            {
                "name": label,
                "ok": None,
                "detail": f"{age} 日前に更新。過去に {len(expired_siblings)} 回失効している",
            }
        )

    env = ROOT / ".env"
    checks.append(
        {
            "name": "Supabaseの接続情報",
            "ok": env.exists(),
            "detail": ".env にあり" if env.exists() else ".env がない",
        }
    )

    backups = backup_root()
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


LIVE_SOURCES = (
    ("ga4", "GA4（アクセス解析）"),
    ("gsc", "Search Console（検索）"),
    ("votes", "Supabase（投票）"),
)

# 取得できた数字の置き場。company/dashboard/ ごと .gitignore 済みなので Git には乗らない
LIVE_CACHE = ROOT / "company" / "dashboard" / "cache" / "live-metrics.json"


def read_live_cache() -> dict:
    """前回までの取得結果。壊れていたら空として扱い、次の成功で上書きする。"""
    if not LIVE_CACHE.exists():
        return {}
    try:
        cached = json.loads(LIVE_CACHE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return cached if isinstance(cached, dict) else {}


def write_live_cache(cache: dict) -> None:
    """書き途中で落ちても前回のキャッシュを壊さないよう、別名で書いてから置き換える。"""
    LIVE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    temporary = LIVE_CACHE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    temporary.replace(LIVE_CACHE)


def merge_live_result(entry: dict | None, value, error: str, now: dt.datetime) -> dict:
    """1つの取得元について、前回のキャッシュに今回の結果を重ねる。

    失敗しても前回の value と last_success_at は残す。ここが上書きされると
    「今日は取れなかった」と「そもそも一度も取れていない」の区別がつかなくなる。
    """
    merged = dict(entry or {})
    merged["last_attempt_at"] = now.isoformat(timespec="seconds")
    if value is None:
        merged["last_error"] = error or "結果を読み取れなかった"
        merged["consecutive_failures"] = int(merged.get("consecutive_failures") or 0) + 1
    else:
        merged["value"] = value
        merged["last_success_at"] = now.isoformat(timespec="seconds")
        merged["last_error"] = ""
        merged["consecutive_failures"] = 0
    return merged


def fetch_live_metrics(days: int = 7) -> dict:
    """GA4 / Search Console / Supabase を実際に叩く（--fetch のときだけ）。

    どれか1つ落ちても残りは表示する。落ちた理由はそのまま画面に出す。

    **失敗したときに、前回取れた数字を消さない。** Google の認証は数日で失効しうるので、
    「今日は失敗したが、2日前の成功値は残っている」と言えることが重要になる。
    そのため成功時だけ value と last_success_at を書き換え、
    失敗時は last_attempt_at と last_error だけを更新する。
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
    commands = {
        "ga4": [python, "scripts/fetch_ga4_metrics.py", "--days", str(days), "--json"],
        "gsc": [python, "scripts/fetch_gsc_metrics.py", "--days", "28", "--json"],
        "votes": [python, "scripts/fetch_supabase_votes.py", "--json"],
    }

    now = dt.datetime.now()
    cache = read_live_cache()
    live: dict = {"fetched_at": now}

    for key, _ in LIVE_SOURCES:
        value, error = run(commands[key])
        cache[key] = merge_live_result(cache.get(key), value, error, now)
        live[key] = value
        live[f"{key}_error"] = "" if value is not None else (error or "結果を読み取れなかった")

    write_live_cache(cache)
    live["cache"] = cache
    return live
