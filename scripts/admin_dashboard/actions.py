"""次に何をすればいいかを1つ決め、そのまま貼れるコマンドに変換する。

collect.py は「リポジトリのファイルを読むだけ」の役割なので、
判断（何を先にやるか）と組み立て（どのコマンドを出すか）はここに分ける。

このモジュールが守っている約束が3つある。どれも実際に事故った箇所なので、
変更するときは tests/test_admin_dashboard.py の該当テストを先に読むこと。

1. `--date` には**実行する日**を入れる。THEMES.yaml の collect_at（予定日）は入れない。
   予定日を渡すと検査に掛からないまま次回更新日がずれ、更新が静かに止まる
2. コマンドは必ず `git worktree add` から始める。管理画面は共有ツリーで作られるので、
   出したコマンドをその場で実行させると OPERATIONS.md ⓪ の運用ルールを破ることになる
3. `--promote`（公開まで）は page_update_mode が adapter のテーマにしか出さない
"""

from __future__ import annotations

import datetime as dt
import statistics
import subprocess
from pathlib import Path

from .collect import ROOT, backup_root

# 収集した非公開データの保管先。DATA_REFRESH.md と同じ場所を指す
BACKUP_DEST = "/Volumes/HD-LE-B/issue-stance-private-backups"


def _git(root: Path, args: list[str]) -> str | None:
    """git の出力を返す。git が無い・失敗した場合は None（判定不能）。"""
    try:
        proc = subprocess.run(
            ["git", *args], cwd=root, text=True, capture_output=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def main_worktree(root: Path = ROOT) -> Path | None:
    """共有の作業ツリー（git worktree list の先頭）を返す。"""
    output = _git(root, ["worktree", "list", "--porcelain"])
    if not output:
        return None
    for line in output.splitlines():
        if line.startswith("worktree "):
            return Path(line[len("worktree "):])
    return None


def worktrees(root: Path = ROOT) -> list[str]:
    """いま存在する作業ツリーのパス一覧。片付け忘れの検知に使う。"""
    output = _git(root, ["worktree", "list", "--porcelain"])
    if not output:
        return []
    return [line[len("worktree "):] for line in output.splitlines() if line.startswith("worktree ")]


def _same_path(left: Path | None, right: Path | None) -> bool:
    if not left or not right:
        return False
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return False


# ------------------------------------------------------------ 実行できる状態か


def readiness(theme: dict | None, *, root: Path = ROOT, sample_files: list[str] | None = None) -> list[dict]:
    """更新コマンドを実行してよい状態かを6点で返す。

    1つでも False があれば、画面はコマンド欄をグレーにして実行を促さない。
    「作業用コピー」は共有ツリーで管理画面を作る限り必ず False になる。
    それが正しい表示で、コマンド欄の先頭に worktree の作成手順が載る理由でもある。
    """
    checks: list[dict] = []

    main = main_worktree(root)
    here = Path(root)
    in_shared = _same_path(main, here)
    checks.append(
        {
            "name": "作業用コピー（worktree）",
            "ok": None if main is None else not in_shared,
            "detail": (
                "gitの情報を読めなかった"
                if main is None
                else "共有の作業ツリーにいます。下の手順の1〜2行目で専用のコピーを作ってください"
                if in_shared
                else f"専用のコピーで作業中（{here.name}）"
            ),
        }
    )

    backup = backup_root()
    checks.append(
        {
            "name": "外付けHDD（バックアップ先）",
            "ok": backup.exists(),
            "detail": "接続済み" if backup.exists() else f"{backup} が見つからない。接続しないと収集が途中で止まります",
        }
    )

    missing = [path for path in (sample_files or []) if not (Path(root) / path).exists()]
    checks.append(
        {
            "name": "非公開の正典データ",
            "ok": not missing,
            "detail": "全テーマぶんあり" if not missing else f"{len(missing)}件が見つからない（{missing[0]} など）",
        }
    )

    playwright = Path(root) / "node_modules" / "playwright"
    checks.append(
        {
            "name": "収集ツール（node_modules）",
            "ok": playwright.exists(),
            "detail": "使用可能" if playwright.exists() else "playwright が無い。収集が最初の疎通確認で止まります",
        }
    )

    dirty = _git(root, ["status", "--porcelain"])
    if dirty is None:
        dirty_detail = "gitの情報を読めなかった"
    elif dirty == "":
        dirty_detail = "なし"
    else:
        dirty_detail = f"{len(dirty.splitlines())}件の変更が残っています。先にコミットするか、専用のコピーで作業してください"
    checks.append(
        {
            "name": "未コミットの変更",
            "ok": None if dirty is None else dirty == "",
            "detail": dirty_detail,
        }
    )

    if theme is not None:
        promotable = theme["update_mode"] == "adapter"
        checks.append(
            {
                "name": "公開まで一気に更新できるか",
                "ok": promotable,
                "detail": "できる（--promote を付けられます）" if promotable else f"できない（{theme['update_mode_note']}）",
            }
        )

    return checks


# ---------------------------------------------------------------- コマンド組み立て


def command_block(theme: dict, today: dt.date, *, promote: bool, root: Path = ROOT) -> dict | None:
    """1テーマ分の手順を、注釈つきのコマンド列にする。

    promote=True は page_update_mode が adapter のテーマにしか作らない。
    それ以外で公開まで進めようとすると refresh_topic.py 側で弾かれるため、
    実行できない手順を画面に出さない。
    """
    if promote and theme["update_mode"] != "adapter":
        return None

    topic = theme["key"]
    shared = main_worktree(root)
    shared_name = shared.name if shared else "issue-stance-aggregator"
    branch = f"task/{topic}-{today:%Y%m%d}"
    tree = f"../isa-wt-{topic}"

    steps = [
        ("専用の作業コピーを作る（共有の作業場所では実行しない）", f"git worktree add {tree} -b {branch}"),
        ("作ったコピーへ移動する", f"cd {tree}"),
        (
            "非公開の正典データを戻す（gitに入っていないのでコピーされない）",
            f'tar xzf "$(ls -t {BACKUP_DEST}/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json',
        ),
        ("収集ツールを入れる（これも git に入っていない）", f"cp -R ../{shared_name}/node_modules ."),
        (
            "収集して分類する" if not promote else "収集・分類して、ページを更新して公開する",
            " ".join(
                [
                    "python3 scripts/refresh_topic.py",
                    f"--topic {topic}",
                    # 予定日ではなく「実行する日」。ここを間違えると次回更新日がずれる
                    f"--date {today:%Y-%m-%d}",
                    f"--backup-dest {BACKUP_DEST}",
                ]
                + (["--promote"] if promote else [])
            ),
        ),
    ]

    status = "promoted" if promote else "validated"
    return {
        "label": "公開まで進める" if promote else "収集だけ行う",
        "impact": "公開ページを更新します" if promote else "公開ページは変更しません",
        "recommended": False,
        "steps": [{"note": note, "command": command} for note, command in steps],
        "script": "\n".join(command for _, command in steps),
        "success": (
            f"data/verification/updates/{topic}/{today:%Y-%m-%d}/report.json ができて、"
            f"その中の status が {status} になっていれば成功です"
        ),
        "verify": "python3 scripts/build_admin_dashboard.py --open",
        "verify_note": "この画面を作り直すと、上の予定が消えて「データ更新の履歴」に新しい行が増えます",
    }


# ------------------------------------------------------------------ 次の一手


def due_items(themes: list[dict], today: dt.date, *, within: int = 7) -> list[dict]:
    """期限が来ている／近い予定を、切迫している順に並べる。

    収集（collect_at）と公開更新（refresh_at）を同じ土俵に載せる。
    公開更新は収集も兼ねるので、同じ日に両方来ていたら公開更新を先に置く。
    """
    items = []
    for theme in themes:
        collect_in, refresh_in = theme["collect_in"], theme["refresh_in"]
        # 同じ日に収集と公開更新が並んでいたら1件にまとめる。--promote は収集も行うので、
        # 2行に分けると「同じ日に2回やる作業」に見えてしまう
        merged = collect_in is not None and collect_in == refresh_in
        for kind, field, promote in (("収集", "collect_in", False), ("公開更新", "refresh_in", True)):
            days = theme[field]
            if days is None or days > within:
                continue
            if merged and not promote:
                continue
            items.append(
                {
                    "kind": "公開更新（収集も行う）" if merged else kind,
                    "theme": theme,
                    "promote": promote,
                    "days": days,
                    "date": theme["collect_at"] if field == "collect_in" else theme["refresh_at"],
                }
            )
    # 超過が大きいものから。同じ日なら公開更新（収集も兼ねる）を先に
    items.sort(key=lambda item: (item["days"], not item["promote"]))
    return items


def pending_measurements(posts: list[dict], today: dt.date) -> list[dict]:
    """表示回数を記録し忘れている投稿。投稿頻度とは別の話なので分けて出す。

    投稿直後の値は当てにならず（8/8は4→51に動いた）1〜2日後に測り直す運用。
    当日ぶんは「まだ測る時期ではない」ので対象外にする。
    """
    return [
        post
        for post in posts
        if post["own_views_status"] != "measured" and 1 <= (today - post["date"]).days <= 7
    ]


# ------------------------------------------------------- X投稿を型ごとに束ねる

# 返信先の規模帯。実測で到達率は0.007%〜5.8%（約800倍）ばらつくので、
# 「1万views以上が理想」のような単一のしきい値では選べない
PARENT_BANDS = (
    (1_000, "〜1千"),
    (10_000, "1千〜1万"),
    (100_000, "1万〜10万"),
    (None, "10万〜"),
)

# 実測がこの件数に満たないグループは「参考値」として扱う
MIN_SAMPLES = 3


def parent_band(parent_views: int | None) -> str:
    if parent_views is None:
        return "記録なし"
    for limit, label in PARENT_BANDS:
        if limit is None or parent_views < limit:
            return label
    return PARENT_BANDS[-1][1]


def _summarize(posts: list[dict]) -> dict:
    """1グループの実績。中央値だけだと誤読するので、件数と幅も一緒に返す。

    到達率が高くても表示回数が5回なら意味がない、という取り違えを防ぐため、
    「到達率」と「自分の表示回数」は必ず並べて持つ。
    """
    measured = [p for p in posts if p["own_views_status"] == "measured" and p["own_views"] is not None]
    views = sorted(p["own_views"] for p in measured)
    reaches = sorted(
        p["own_views"] / p["parent_views"] * 100
        for p in measured
        if p["parent_views"]
    )
    return {
        "posts": len(posts),
        "measured": len(measured),
        "views_median": statistics.median(views) if views else None,
        "views_min": views[0] if views else None,
        "views_max": views[-1] if views else None,
        "reach_median": statistics.median(reaches) if reaches else None,
        "reach_min": reaches[0] if reaches else None,
        "reach_max": reaches[-1] if reaches else None,
        "reference_only": len(measured) < MIN_SAMPLES,
    }


def post_breakdown(posts: list[dict], today: dt.date, *, days: int = 60) -> list[dict]:
    """直近の投稿を3つの軸で束ねる。明日どれに返信するかの判断材料にする。"""
    recent = [p for p in posts if (today - p["date"]).days <= days]

    axes = [
        ("リンクの有無", lambda p: "URL付き" if p["has_url"] else "URLなし"),
        ("返信先の規模", lambda p: parent_band(p["parent_views"])),
        ("投稿の種類", lambda p: p["kind"] or "不明"),
    ]

    out = []
    for axis_name, key_of in axes:
        groups: dict[str, list[dict]] = {}
        for post in recent:
            groups.setdefault(key_of(post), []).append(post)
        rows = [{"group": name, **_summarize(items)} for name, items in groups.items()]
        # 到達率の中央値が高い順。測れていないグループは後ろへ
        rows.sort(key=lambda row: (row["reach_median"] is None, -(row["reach_median"] or 0)))
        out.append({"axis": axis_name, "rows": rows})
    return out


# --------------------------------------------------------------- CEO日次報告


def executive_brief(data: dict) -> list[dict]:
    """「昨日 / 今日 / 問題 / 承認」を、1画面の4行にまとめる。

    完了の根拠は git・データ更新・X投稿の実績から拾い、今日の作業と
    承認は company/ の台帳から拾う。記録が無いときは推測で埋めない。
    """
    today = data["today"]
    yesterday = today - dt.timedelta(days=1)
    company = data.get("company") or {}

    commits = [item for item in data.get("commits") or [] if item.get("date") == yesterday]
    updates = [item for item in data.get("data_updates") or [] if item.get("date") == yesterday]
    posts = [item for item in data.get("x_posts") or [] if item.get("date") == yesterday]
    result_parts = []
    if updates:
        result_parts.append(f"データ更新 {len(updates)}テーマ")
    if posts:
        result_parts.append(f"X投稿 {len(posts)}件")
    if commits:
        result_parts.append(f"作業記録 {len(commits)}件（{commits[0]['message']}）")
    yesterday_text = " / ".join(result_parts) if result_parts else "昨日の完了記録はまだありません"

    active = [
        item
        for item in company.get("handoffs") or []
        if item.get("status") not in {"completed", "cancelled", "withdrawn"}
    ]
    due_now = [item for item in active if item.get("due_in") is not None and item["due_in"] <= 0]
    focus = (due_now or active)[0] if (due_now or active) else None
    today_text = focus.get("next_action") if focus else "今日が期限の進行中業務はありません"

    company_alerts = company.get("alerts") or []
    health_failures = [item for item in data.get("health") or [] if item.get("ok") is False]
    found_anomalies = data.get("anomalies") or []
    overdue_measurements = ((data.get("x_measurement") or {}).get("overdue") or [])
    problem_count = len(company_alerts) + len(health_failures) + len(found_anomalies)
    if overdue_measurements:
        problem_count += 1
    if company_alerts:
        problem_text = f"{problem_count}件。最優先: {company_alerts[0]['title']}"
    elif health_failures:
        problem_text = f"{problem_count}件。最優先: {health_failures[0]['name']} を確認"
    elif found_anomalies:
        problem_text = f"{problem_count}件。最優先: {found_anomalies[0]['title']}"
    elif overdue_measurements:
        problem_text = f"1件。X投稿の表示回数が {len(overdue_measurements)} 件未計測"
    else:
        problem_text = "台帳が検知した遅れ・問題はありません"

    pending = company.get("pending_approvals") or []
    if pending:
        approval = pending[0]
        approval_text = f"{approval.get('summary')}（推奨: {approval.get('recommendation') or '未記入'}）"
    else:
        approval_text = "CEOの承認待ちはありません"

    return [
        {"key": "yesterday", "label": "昨日の結果", "text": yesterday_text, "tone": "calm"},
        {"key": "today", "label": "今日進めること", "text": today_text, "tone": "focus"},
        {"key": "problem", "label": "遅れ・問題", "text": problem_text, "tone": "danger" if problem_count else "calm"},
        {"key": "approval", "label": "承認事項", "text": approval_text, "tone": "warn" if pending else "calm"},
    ]


def typical_minutes(data_updates: list[dict], topic: str) -> int | None:
    """そのテーマの過去の所要時間の中央値。「どれくらいかかるか」の目安に使う。"""
    minutes = [u["minutes"] for u in data_updates if u["theme"] == topic and u["minutes"]]
    if not minutes:
        return None
    return int(statistics.median(minutes))


def last_result(data_updates: list[dict], topic: str) -> dict | None:
    """そのテーマの直近の更新結果。「実行できたのか分からない」を防ぐために出す。"""
    for update in data_updates:
        if update["theme"] == topic:
            return update
    return None


def next_action(data: dict) -> dict | None:
    """いま最初にやること1件。無ければ None。

    優先順位は「期限が過ぎた更新 → 今日明日の更新 → 記録漏れ → 週次KPI」。
    予定を全部並べると判断できなくなるので、ここでは必ず1件だけ返す。
    """
    today = data["today"]
    themes = data["themes"]
    updates = data["data_updates"]

    items = due_items(themes, today, within=1)
    if items:
        head = items[0]
        theme = head["theme"]
        promote = head["promote"]
        # 公開更新の予定日でも、adapter でなければ公開まで進められない
        if promote and theme["update_mode"] != "adapter":
            promote = False
        # 収集だけ（公開ページに触らない安全な方）を必ず先に出し、
        # 公開まで進められるテーマだけ --promote 版を続けて出す。どちらを実行するかは owner が選ぶ
        blocks = [command_block(theme, today, promote=False)]
        publish = command_block(theme, today, promote=True)
        if publish:
            publish["recommended"] = promote
            blocks.append(publish)
        blocks[0]["recommended"] = not promote or publish is None
        overdue = head["days"] < 0
        return {
            "kind": "refresh",
            "title": f"{theme['title']} の{head['kind']}",
            "why": (
                f"{head['kind']}の予定が {-head['days']} 日過ぎています"
                if overdue
                else f"{head['kind']}の予定は{'今日' if head['days'] == 0 else '明日'}です"
            ),
            "tone": "danger" if overdue else "warn",
            "minutes": typical_minutes(updates, theme["key"]),
            "last": last_result(updates, theme["key"]),
            "readiness": readiness(theme, sample_files=data.get("sample_files") or []),
            "blocks": blocks,
            "rest": items_after(themes, today, head),
        }

    pending = pending_measurements(data["x_posts"], today)
    if pending:
        return {
            "kind": "measure",
            "title": f"X投稿 {len(pending)} 件の表示回数を記録する",
            "why": "投稿から1日以上経っているのに、表示回数が記録されていません",
            "tone": "warn",
            "minutes": 5,
            "last": None,
            "readiness": [],
            "blocks": [],
            "rest": [],
            "pending": pending,
        }

    snapshots = data["kpi"]["snapshots"]
    if snapshots and (today - snapshots[-1]["date"]).days > 10:
        return {
            "kind": "kpi",
            "title": "週次の流入記録を1行足す",
            "why": f"前回の記録から {(today - snapshots[-1]['date']).days} 日経っています（週1回が想定）",
            "tone": "warn",
            "minutes": 10,
            "last": None,
            "readiness": [],
            "blocks": [],
            "rest": [],
        }

    return None


# -------------------------------------------------------------- 気になる変化


def anomalies(data: dict) -> list[dict]:
    """履歴を眺めなくても気づけるように、いつもと違うところだけを拾う。

    期限切れはここでは出さない（「今日の次の一手」と重複するため）。
    """
    today = data["today"]
    found: list[dict] = []

    # 更新回どうしを、テーマごとに新しい順で見比べる
    by_theme: dict[str, list[dict]] = {}
    for update in data["data_updates"]:
        by_theme.setdefault(update["theme"], []).append(update)

    for topic, updates in by_theme.items():
        updates = sorted(updates, key=lambda u: u["date"] or dt.date.min, reverse=True)
        latest = updates[0]
        previous = updates[1] if len(updates) > 1 else None

        if previous and latest["opinions"] and previous["opinions"]:
            if latest["opinions"] <= previous["opinions"] / 2:
                found.append(
                    {
                        "tone": "warn",
                        "title": f"{topic}: 意見の数が前回の半分以下です",
                        "detail": f"{previous['opinions']}件 → {latest['opinions']}件（{fmt_date(latest['date'])}）。話題が落ち着いたのか、検索語が合わなくなったのかを見る価値があります",
                    }
                )

        if previous and (latest["errors"] or 0) > (previous["errors"] or 0):
            found.append(
                {
                    "tone": "warn",
                    "title": f"{topic}: 分類エラーが増えました",
                    "detail": f"{previous['errors']}件 → {latest['errors']}件。分類器が扱えない投稿が混ざっている可能性があります",
                }
            )

        zero_runs = [u for u in updates[:2] if u["new"] == 0]
        if len(zero_runs) == 2:
            found.append(
                {
                    "tone": "danger",
                    "title": f"{topic}: 新規0件が2回続いています",
                    "detail": "収集は成功しているのに新しい投稿が取れていません。検索語が実態と合わなくなっているおそれがあります",
                }
            )

    # X の表示回数が普段と大きく違う日
    measured = [
        p for p in data["x_posts"]
        if p["own_views_status"] == "measured" and p["own_views"] and (today - p["date"]).days <= 30
    ]
    if len(measured) >= 5:
        median = statistics.median(p["own_views"] for p in measured)
        for post in measured:
            if median and post["own_views"] >= median * 5:
                found.append(
                    {
                        "tone": "ok",
                        "title": f"{fmt_date(post['date'])} の投稿がいつもの{post['own_views'] / median:.0f}倍読まれました",
                        "detail": f"{post['own_views']}回（普段は{int(median)}回ほど）。{post['target'] or post['theme'] or '対象不明'}。何が効いたのかを見ておく価値があります",
                    }
                )

    # 実測の取得が続けて失敗している
    for key, label in LIVE_SOURCE_LABELS:
        entry = (data.get("live_cache") or {}).get(key) or {}
        if int(entry.get("consecutive_failures") or 0) >= 2:
            found.append(
                {
                    "tone": "danger",
                    "title": f"{label} の取得が {entry['consecutive_failures']} 回続けて失敗しています",
                    "detail": entry.get("last_error") or "理由不明。認証の作り直しが要るかもしれません",
                }
            )

    # 台帳が「更新した」と言っているのに、ページ側にその形跡がない場合だけを出す。
    #
    # 逆向き（ページのほうが新しい）は出さない。共有パーツの変更やシェアボタンの修正で
    # 全テーマのページが一斉に変わるのは通常の運用で、これを拾うと11テーマ中7件が
    # 毎回並んで警告として読まれなくなる（2026-08-10 の #73 #74 で実際にそうなった）。
    #
    # ファイルの更新日時（mtime）も使えない。worktree を作り直すたびに全ファイルが
    # 「いま」になるため、git の履歴を見る。
    for theme in data["themes"]:
        page = theme.get("html")
        updated = theme.get("updated_at")
        if not page or not updated:
            continue
        if not (ROOT / page).exists():
            found.append({"tone": "danger", "title": f"{theme['title']}: 公開ページのファイルがありません", "detail": page})
            continue
        committed = last_commit_date(page)
        if committed and (updated - committed).days > 3:
            found.append(
                {
                    "tone": "danger",
                    "title": f"{theme['title']}: 台帳は更新済みなのにページが変わっていません",
                    "detail": (
                        f"THEMES.yaml の updated_at は {updated} ですが、ページを最後に変えたのは {committed} です。"
                        "公開したつもりで反映されていない可能性があります"
                    ),
                }
            )

    # 片付いていない作業用コピー
    trees = worktrees()
    if len(trees) - 1 >= 5:
        found.append(
            {
                "tone": "warn",
                "title": f"作業用コピーが {len(trees) - 1} 本残っています",
                "detail": "使い終わったものは git worktree remove で片付けてください。放置すると、どれが最新か分からなくなります",
            }
        )

    order = {"danger": 0, "warn": 1, "ok": 2}
    found.sort(key=lambda item: order.get(item["tone"], 3))
    return found


def last_commit_date(relative: str, *, root: Path = ROOT) -> dt.date | None:
    """そのファイルを最後に変更したコミットの日付。

    ファイルの mtime は使えない。worktree を作り直すたびに全ファイルが「いま」になり、
    「ページの更新日」として意味を持たなくなる。
    """
    output = _git(root, ["log", "-1", "--format=%ad", "--date=short", "--", relative])
    if not output:
        return None
    try:
        return dt.date.fromisoformat(output.strip())
    except ValueError:
        return None


def fmt_date(value: dt.date | None) -> str:
    return "—" if value is None else f"{value.month}/{value.day}"


LIVE_SOURCE_LABELS = (
    ("ga4", "GA4（アクセス解析）"),
    ("gsc", "Search Console（検索）"),
    ("votes", "Supabase（投票）"),
)


def items_after(themes: list[dict], today: dt.date, head: dict) -> list[dict]:
    """次の一手より後ろに控えている予定（7日以内）。畳んで出す。"""
    rest = []
    for item in due_items(themes, today, within=7):
        if item["theme"]["key"] == head["theme"]["key"] and item["kind"] == head["kind"]:
            continue
        rest.append(item)
    return rest
