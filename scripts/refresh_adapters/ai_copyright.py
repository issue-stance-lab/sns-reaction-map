"""生成AIと著作権の候補ページを生成し、投票互換性と冪等性を検査する。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.refresh_adapters import trend_support

TOPIC = "ai-copyright"
PAGE = Path("docs/ai-copyright-reaction-map.html")
ARENA_DATA = Path("docs/ai-copyright-arena-data.js")
VOTE_TOPIC = "ai-copyright-issue-stance-v1"
VOTE_CHOICES = 21
PROTECTED = ("G-K10S4YCZFH", "ca-pub-2542211932832864", "vote-store.js")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_records_path(root: Path, current_date: str) -> Path:
    """収集回ごとの本文確認記録（data/verification/ai-copyright-wave-review-YYYYMMDD.json）。"""
    return root / "data" / "verification" / f"ai-copyright-wave-review-{current_date.replace('-', '')}.json"


def review_candidate(root: Path, stage: Path, current_date: str, report: dict) -> None:
    """保存回は不変のまま、本文確認結果を公開候補だけへ適用する（refresh_adapters/consumption_tax.py と同じ形式）。

    10/9の新ルール: 今回分は全件本文確認し、採否・論点・立場の補正をこの記録で候補へ適用する。
    記録が無い回は補正なし。今回分の読了証拠そのものは refresh_completion.py が別に検査する。
    """
    records_path = review_records_path(root, current_date)
    if not records_path.is_file():
        return
    review = json.loads(records_path.read_text(encoding="utf-8"))
    wave_path = stage / "classified-wave.json"
    if review["source_sha256"] != _digest(wave_path):
        raise ValueError("生成AIと著作権の本文確認元と保存回が一致しません")
    wave = json.loads(wave_path.read_text(encoding="utf-8"))
    ids = [str(row["tweet_id"]) for row in wave]
    ids_sha = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
    if review["ids_sha256"] != ids_sha or review["reviewed_count"] != len(wave):
        raise ValueError("生成AIと著作権の本文確認対象が保存回と一致しません")
    by_id = {str(row["tweet_id"]): row for row in wave}
    if len(by_id) != len(wave):
        raise ValueError("生成AIと著作権の保存回にID重複があります")
    changes = review["overrides"]
    if len({item["tweet_id"] for item in changes}) != len(changes):
        raise ValueError("生成AIと著作権の本文確認結果にID重複があります")
    allowed = {"is_opinion", "main_issue", "stance", "article_usable", "risk", "summary", "reason"}
    for item in changes:
        tweet_id = item["tweet_id"]
        if tweet_id not in by_id or not item.get("review_reason"):
            raise ValueError(f"生成AIと著作権の本文確認結果が不正です: {tweet_id}")
        values = item["classification"]
        if not values or set(values) - allowed:
            raise ValueError(f"生成AIと著作権の本文確認項目が不正です: {tweet_id}")
        by_id[tweet_id]["classification"].update(values)
        # 本文確認で意見と確定した投稿は、テーマに関係する投稿でもある。Kimiが「関係なし」と
        # していると意見集計（is_relevant かつ is_opinion）から漏れるので揃える（2026-10-15、25件）。
        if values.get("is_opinion") is True:
            by_id[tweet_id]["classification"]["is_relevant"] = True
    cumulative_path = stage / "cumulative-candidate.json"
    cumulative = json.loads(cumulative_path.read_text(encoding="utf-8"))
    cumulative_by_id = {str(row["tweet_id"]): row for row in cumulative}
    if not set(by_id).issubset(cumulative_by_id):
        raise ValueError("生成AIと著作権の本文確認対象が累積候補にありません")
    for tweet_id, row in by_id.items():
        cumulative_by_id[tweet_id]["classification"] = row["classification"]
    (stage / "reviewed-wave.json").write_text(json.dumps(wave, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cumulative_path.write_text(json.dumps(cumulative, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["automated_opinions"] = report["opinions"]
    report["opinions"] = sum(row["classification"]["is_opinion"] is True for row in wave)
    report["body_review"] = str(records_path.relative_to(root))
    report["body_review_changes"] = len(changes)


def vote_fingerprint(html: str) -> tuple[str, tuple[str, ...], tuple[str, ...], int]:
    topic = re.search(r"var TOPIC='([^']+)'", html)
    issues = re.search(r"var VOTE_ISSUES=\[(.*?)\];", html, re.DOTALL)
    stances = re.search(r"var STANCES=\[(.*?)\];", html, re.DOTALL)
    if not topic or not issues or not stances:
        raise ValueError("投票定義をページから読み取れません")
    issue_keys = tuple(re.findall(r"\bk:'([^']+)'", issues.group(1)))
    stance_keys = tuple(re.findall(r"\bk:'([^']+)'", stances.group(1)))
    return topic.group(1), issue_keys, stance_keys, len(issue_keys) * len(stance_keys)


def _run_builder(root: Path, candidate: Path, template: Path, page: Path, data: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_ai_copyright_arena.py"),
            "--input", str(candidate),
            "--html-template", str(template),
            "--output-html", str(page),
            "--output-data", str(data),
            "--skip-issue-counts",
        ],
        cwd=root,
        check=True,
    )
    from scripts.ai_copyright_connected import TOPIC as CONNECTED_TOPIC, apply as connect_page
    text = connect_page(page.read_text(encoding="utf-8"), topic=CONNECTED_TOPIC)
    # 「意見の推移」は、ページに残してある枠の中へ、累積候補から数え直して貼り直す。
    text = trend_support.render_trend(root, TOPIC, text, candidate)
    page.write_text(text, encoding="utf-8")


def finalize(root: Path, current_date: str) -> None:
    """候補公開JSONから、ページの管理対象集計を貼り直す。

    山なみ形式の本番ページでは、旧アリーナ生成器は調査条件のみを
    更新する。山の PLANET_DATA も同じ公開JSONから再生成し、件数と面積を
    同じ候補版にそろえる。
    """
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_ai_copyright_arena.py"),
            "--public-counts-only",
            "--output-html", str(root / PAGE),
        ],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "refresh_planet_section.py"),
            "--topic", TOPIC,
            "--for-docs",
        ],
        cwd=root,
        check=True,
    )
    # 山の外にある「立場ごとの内訳」も、候補正典と公開JSONが
    # 揃った後に貼り直す。このビルダは山なみ本体を変更しない。
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_ai_copyright_arena.py"),
            "--skip-issue-counts",
        ],
        cwd=root,
        check=True,
    )


def _previous_wave_model(root: Path, current_date: str) -> str | None:
    """前回の更新回（収集日が今回より前で一番新しい保存回）の分類モデル。記録が無い古い回は None。"""
    updates = root / "social-samples" / "updates" / TOPIC
    dates = sorted(path.name for path in updates.iterdir() if path.is_dir() and path.name < current_date) if updates.is_dir() else []
    for date in reversed(dates):
        report = updates / date / "report.json"
        if report.exists():
            data = json.loads(report.read_text(encoding="utf-8"))
            return ((data.get("provenance") or {}).get("model") or {}).get("name")
    return None


def _current_wave_model(stage: Path) -> str | None:
    report = stage / "report.json"
    if not report.exists():
        return None
    data = json.loads(report.read_text(encoding="utf-8"))
    return ((data.get("provenance") or {}).get("model") or {}).get("name")


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    # 新デザイン公開後も、旧形式の生成器（連動表示・意見の推移の貼り直しを含む）は元HTML（data/page-sources）を入力にする
    # （ai_copyright_layout.py）。推移の画像（trend_support.build_images）も同じ累積候補から作る
    from scripts.ai_copyright_layout import source_for_refresh
    current_page = source_for_refresh(root)
    first_page = stage / "page-candidate.html"
    first_data = stage / "arena-data-candidate.js"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_data = stage / "idempotence" / "arena-data-candidate.js"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    # 分類に使うAIが前回から変わった回は、推移の注意書きに記録が要る（無ければここで止まる）。
    trend_support.check_model_break(
        root, TOPIC, current_date, _previous_wave_model(root, current_date), _current_wave_model(stage)
    )

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    _run_builder(root, candidate, current_page, first_page, first_data)
    _run_builder(root, candidate, first_page, second_page, second_data)

    if (_digest(first_page), _digest(first_data)) != (_digest(second_page), _digest(second_data)):
        raise ValueError("生成AIadapterは同じ候補の2回目実行で差分が出ました")

    candidate_html = first_page.read_text(encoding="utf-8")
    after_vote = vote_fingerprint(candidate_html)
    if before_vote != after_vote:
        raise ValueError(f"投票互換性が変わりました: {before_vote} -> {after_vote}")
    if after_vote[0] != VOTE_TOPIC or after_vote[3] != VOTE_CHOICES:
        raise ValueError(f"想定外の投票定義です: {after_vote}")
    current_html = current_page.read_text(encoding="utf-8")
    changed = [t for t in PROTECTED if current_html.count(t) != candidate_html.count(t)]
    if changed:
        raise ValueError("保護タグの個数が変わりました: " + ", ".join(changed))

    # ページと同じ累積候補から、推移の画像も作って一緒に公開する（ページの <img> がこの画像を指す）。
    return {
        PAGE: first_page,
        ARENA_DATA: first_data,
        **trend_support.build_images(root, TOPIC, stage, candidate),
    }
