"""皇室典範改正の候補ページを生成し、投票互換性と冪等性を検査する。"""

from __future__ import annotations

import hashlib
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


def _run_process_sections(root: Path, page: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_koshitsu_process_sections.py"),
            "--output-html",
            str(page),
        ],
        cwd=root,
        check=True,
    )


def finalize(root: Path, current_date: str) -> None:
    """候補公開JSONから、ページの管理対象集計を貼り直す。"""
    subprocess.run([sys.executable, str(root / "scripts" / "build_koshitsu_arena.py"), "--public-counts-only", "--output-html", str(root / PAGE)], cwd=root, check=True)


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    current_page = root / PAGE
    first_page = stage / "page-candidate.html"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    _run_builder(root, candidate, current_page, first_page)
    _run_process_sections(root, first_page)
    _apply_tide(root, first_page, stage / "classified-wave.json", current_date)
    _run_builder(root, candidate, first_page, second_page)
    _run_process_sections(root, second_page)
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
