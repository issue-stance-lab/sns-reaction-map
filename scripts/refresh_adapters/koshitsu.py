"""皇室典範改正の候補ページを生成し、投票互換性と冪等性を検査する。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

TOPIC = "koshitsu-tenpakai"
PAGE = Path("docs/koshitsu-tenpakai-reaction-map.html")
TIDE_SLUG = "koshitsu-tenpakai"
VOTE_TOPIC = "koshitsu-tenpakai-issue-stance-v2"
VOTE_CHOICES = 24
PROTECTED = ("G-K10S4YCZFH", "ca-pub-2542211932832864", "vote-store.js")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vote_fingerprint(html: str) -> tuple[str, tuple[str, ...], tuple[str, ...], int]:
    topic = re.search(r"var TOPIC='([^']+)'", html)
    issues = re.search(r"var VOTE_ISSUES=\[(.*?)\];", html, re.DOTALL)
    stances = re.search(r"var STANCES=\[(.*?)\];", html, re.DOTALL)
    if not topic or not issues or not stances:
        raise ValueError("投票定義をページから読み取れません")
    issue_keys = tuple(re.findall(r"\bk:'([^']+)'", issues.group(1)))
    stance_keys = tuple(re.findall(r"\bk:'([^']+)'", stances.group(1)))
    return topic.group(1), issue_keys, stance_keys, len(issue_keys) * len(stance_keys)


def review_records_path(root: Path, current_date: str) -> Path:
    """収集回ごとの本文確認記録（data/verification/koshitsu-tenpakai-wave-review-YYYYMMDD.json）。"""
    return root / "data" / "verification" / f"koshitsu-tenpakai-wave-review-{current_date.replace('-', '')}.json"


def review_candidate(root: Path, stage: Path, current_date: str, report: dict) -> None:
    """保存回は不変のまま、本文確認結果を公開候補だけへ適用する（refresh_adapters/fukushuto.py と同じ形式）。

    10/9の新ルール: 今回分は全件本文確認し、採否・論点・立場の補正をこの記録で候補へ適用する。
    記録が無い回は補正なし。今回分の読了証拠そのものは refresh_completion.py が別に検査する。
    """
    records_path = review_records_path(root, current_date)
    if not records_path.is_file():
        return
    review = json.loads(records_path.read_text(encoding="utf-8"))
    wave_path = stage / "classified-wave.json"
    if review["source_sha256"] != _digest(wave_path):
        raise ValueError("皇室典範改正の本文確認元と保存回が一致しません")
    wave = json.loads(wave_path.read_text(encoding="utf-8"))
    ids = [str(row["tweet_id"]) for row in wave]
    ids_sha = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
    if review["ids_sha256"] != ids_sha or review["reviewed_count"] != len(wave):
        raise ValueError("皇室典範改正の本文確認対象が保存回と一致しません")
    by_id = {str(row["tweet_id"]): row for row in wave}
    if len(by_id) != len(wave):
        raise ValueError("皇室典範改正の保存回にID重複があります")
    changes = review["overrides"]
    if len({item["tweet_id"] for item in changes}) != len(changes):
        raise ValueError("皇室典範改正の本文確認結果にID重複があります")
    allowed = {"is_opinion", "main_issue", "stance", "article_usable", "risk", "summary", "reason"}
    for item in changes:
        tweet_id = item["tweet_id"]
        if tweet_id not in by_id or not item.get("review_reason"):
            raise ValueError(f"皇室典範改正の本文確認結果が不正です: {tweet_id}")
        values = item["classification"]
        if not values or set(values) - allowed:
            raise ValueError(f"皇室典範改正の本文確認項目が不正です: {tweet_id}")
        by_id[tweet_id]["classification"].update(values)
        if values.get("is_opinion") is True:
            # Kimiが「無関係」とした投稿を本文確認で意見にした場合、公開集計（is_relevant 必須）から落ちないようにする
            by_id[tweet_id]["classification"]["is_relevant"] = True
    cumulative_path = stage / "cumulative-candidate.json"
    cumulative = json.loads(cumulative_path.read_text(encoding="utf-8"))
    cumulative_by_id = {str(row["tweet_id"]): row for row in cumulative}
    if not set(by_id).issubset(cumulative_by_id):
        raise ValueError("皇室典範改正の本文確認対象が累積候補にありません")
    for tweet_id, row in by_id.items():
        cumulative_by_id[tweet_id]["classification"] = row["classification"]
    (stage / "reviewed-wave.json").write_text(json.dumps(wave, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cumulative_path.write_text(json.dumps(cumulative, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["automated_opinions"] = report["opinions"]
    report["opinions"] = sum(row["classification"]["is_opinion"] is True for row in wave)
    report["body_review"] = str(records_path.relative_to(root))
    report["body_review_changes"] = len(changes)


def _latest_previous_wave(root: Path, current_date: str) -> tuple[Path, str]:
    """前回の更新回。まだ無ければ、正典そのもの（2026-07-26 収集分）を前回とする。

    課題31: このページの潮目ウィジェットの前回値は合成データ（_prev_synthetic）由来で
    残っている。初回の実更新でここを実データ同士の比較へ置き換える。
    """
    updates = root / "social-samples" / "updates" / TOPIC
    candidates = sorted(
        (path.parent.name, path)
        for path in updates.glob("*/classified.json")
        if path.parent.name < current_date
    )
    if candidates:
        return candidates[-1][1], candidates[-1][0]
    return root / "social-samples" / "koshitsu-tenpakai_hermes_cur_20260726.json", "2026-07-26"


def _label(value: str) -> str:
    year, month, day = value.split("-")
    return f"{int(month)}月{int(day)}日"


def _apply_tide(root: Path, page: Path, current_wave: Path, current_date: str) -> None:
    sys.path.insert(0, str(root / "scripts"))
    from inject_tide_widget import (  # type: ignore[import-not-found]
        THEMES,
        _load_tide_css,
        generate_tide_section,
        inject_into_html,
        load_classified,
    )

    base = next(item for item in THEMES if item["slug"] == TIDE_SLUG).copy()
    previous_path, previous_date = _latest_previous_wave(root, current_date)
    if not previous_path.is_file():
        raise FileNotFoundError(f"前回更新回がありません: {previous_path}")
    if "synthetic" in previous_path.name:
        raise ValueError(f"合成データを潮目の比較対象にはできません: {previous_path}")
    base["prev_label"] = _label(previous_date)
    base["cur_label"] = _label(current_date)
    base["note"] = (
        f"比較対象：{base['prev_label']}収集分のうち意見投稿／"
        f"{base['cur_label']}収集分のうち意見投稿。同じ検索語セットで取得した投稿をAIで分類しています。"
        "サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。"
    )
    previous = load_classified(
        previous_path,
        base["use_relevance_filter"],
        base.get("exclude_stances"),
        base.get("exclude_issues"),
    )
    current = load_classified(
        current_wave,
        base["use_relevance_filter"],
        base.get("exclude_stances"),
        base.get("exclude_issues"),
    )
    tide = generate_tide_section(base, previous, current)
    page.write_text(inject_into_html(page, tide, _load_tide_css()), encoding="utf-8")


def _run_builder(root: Path, candidate: Path, template: Path, page: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_koshitsu_arena.py"),
            "--input",
            str(candidate),
            "--html-template",
            str(template),
            "--output-html",
            str(page),
        ],
        cwd=root,
        check=True,
    )


def _run_process_sections(root: Path, page: Path, candidate: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_koshitsu_process_sections.py"),
            "--output-html",
            str(page),
            "--input",
            str(candidate),
        ],
        cwd=root,
        check=True,
    )


def finalize(root: Path, current_date: str) -> None:
    """候補公開JSONから、ページの管理対象集計を貼り直す。"""
    subprocess.run([sys.executable, str(root / "scripts" / "build_koshitsu_arena.py"), "--public-counts-only", "--output-html", str(root / PAGE)], cwd=root, check=True)


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。

    候補統合方式（koshitsu_production.py）は2026-09-15の候補統合時点でのみ使う
    1回きりの経路だった。定期更新では他9テーマと同じく、build_koshitsu_arena.py
    自身のPLANET_SECTION分岐（refresh_verified_planet + apply_koshitsu_extras）
    が正典から山なみ全体を作り直す（課題69・koshitsu標準化）。
    """
    candidate = stage / "cumulative-candidate.json"
    # 新デザイン公開後も、旧形式の生成器は元HTML（data/page-sources）を入力にする（koshitsu_layout.py）
    from scripts.koshitsu_layout import source_for_refresh
    current_page = source_for_refresh(root)
    first_page = stage / "page-candidate.html"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    _run_builder(root, candidate, current_page, first_page)
    _run_process_sections(root, first_page, candidate)
    _apply_tide(root, first_page, stage / "classified-wave.json", current_date)
    _run_builder(root, candidate, first_page, second_page)
    _run_process_sections(root, second_page, candidate)
    _apply_tide(root, second_page, stage / "classified-wave.json", current_date)

    if _digest(first_page) != _digest(second_page):
        raise ValueError("皇室典範adapterは同じ候補の2回目実行で差分が出ました")

    candidate_html = first_page.read_text(encoding="utf-8")
    after_vote = vote_fingerprint(candidate_html)
    if before_vote != after_vote:
        raise ValueError(f"投票互換性が変わりました: {before_vote} -> {after_vote}")
    if after_vote[0] != VOTE_TOPIC or after_vote[3] != VOTE_CHOICES:
        raise ValueError(f"想定外の投票定義です: {after_vote}")
    current_html = current_page.read_text(encoding="utf-8")
    changed = [token for token in PROTECTED if current_html.count(token) != candidate_html.count(token)]
    if changed:
        raise ValueError("保護タグの個数が変わりました: " + ", ".join(changed))

    return {PAGE: first_page}
