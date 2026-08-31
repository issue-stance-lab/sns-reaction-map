"""辺野古高校生死亡事故の候補ページを生成し、投票互換性と冪等性を検査する。"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

TOPIC = "henoko-student-accident"
PAGE = Path("docs/henoko-student-accident-reaction-map.html")
ARENA_DATA = Path("docs/henoko-arena-data.js")
TIDE_SLUG = "henoko"
VOTE_TOPIC = "henoko-student-accident-issue-stance-v1"
VOTE_CHOICES = 18
PROTECTED = ("G-K10S4YCZFH", "ca-pub-2542211932832864", "vote-store.js")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vote_fingerprint(html: str) -> tuple[str, tuple[str, ...], tuple[str, ...], int]:
    topic = re.search(r"var TOPIC='([^']+)'", html)
    issues = re.search(r"var ISSUES=\[(.*?)\];", html, re.DOTALL)
    stances = re.search(r"var STANCES=\[(.*?)\];", html, re.DOTALL)
    if not topic or not issues or not stances:
        raise ValueError("投票定義をページから読み取れません")
    issue_keys = tuple(re.findall(r"\bk:'([^']+)'", issues.group(1)))
    stance_keys = tuple(re.findall(r"\bk:'([^']+)'", stances.group(1)))
    return topic.group(1), issue_keys, stance_keys, len(issue_keys) * len(stance_keys)


def _latest_previous_wave(root: Path, current_date: str) -> tuple[Path, str]:
    """前回の更新回。まだ無ければ、2026-07-26 の収集分を前回とする。"""
    updates = root / "social-samples" / "updates" / TOPIC
    candidates = sorted(
        (path.parent.name, path)
        for path in updates.glob("*/classified.json")
        if path.parent.name < current_date
    )
    if candidates:
        return candidates[-1][1], candidates[-1][0]
    return root / "social-samples" / "henoko_hermes_cur_20260726.json", "2026-07-26"


def _label(value: str) -> str:
    year, month, day = value.split("-")
    return f"{int(month)}月{int(day)}日"


def _apply_tide(root: Path, page: Path, current_wave: Path, current_date: str) -> None:
    """「世論の潮目」を、更新回どうしの比較で作り直す。

    固定ファイル名（inject_tide_widget.py の prev_file / cur_file）のままだと、
    データが増えても 7月12日×7月26日 の比較が残り続ける。
    """
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
    # 6月発生の話題で、回によっては比較対象が数十件しかない。少数であることは
    # 数字と同じ場所に書く（注記を落とすと、6件の構成比が世論の変化に見える）。
    smallest = min(len(previous), len(current))
    caution = (
        "どちらかの回が少数のため、少数サンプルの傾向としてご参照ください。"
        if smallest < 30
        else ""
    )
    base["note"] = (
        f"比較対象：{base['prev_label']}収集分{len(previous)}件／"
        f"{base['cur_label']}収集分{len(current)}件。"
        "同じ検索語セットで取得した投稿をAIで分類しています。"
        f"{caution}"
        "サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。"
    )
    tide = generate_tide_section(base, previous, current)
    page.write_text(inject_into_html(page, tide, _load_tide_css()), encoding="utf-8")


def _run_builder(root: Path, candidate: Path, template: Path, page: Path, data: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_henoko_arena.py"),
            "--input", str(candidate),
            "--html-template", str(template),
            "--output-html", str(page),
            "--output-data", str(data),
        ],
        cwd=root,
        check=True,
    )


def finalize(root: Path, current_date: str) -> None:
    """候補公開JSONから、ページの管理対象集計を貼り直す。"""
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_henoko_arena.py"),
            "--public-counts-only",
            "--output-html",
            str(root / PAGE),
        ],
        cwd=root,
        check=True,
    )


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    current_page = root / PAGE
    first_page = stage / "page-candidate.html"
    first_data = stage / "arena-data-candidate.js"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_data = stage / "idempotence" / "arena-data-candidate.js"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    _run_builder(root, candidate, current_page, first_page, first_data)
    _apply_tide(root, first_page, stage / "classified-wave.json", current_date)
    _run_builder(root, candidate, first_page, second_page, second_data)
    _apply_tide(root, second_page, stage / "classified-wave.json", current_date)

    if (_digest(first_page), _digest(first_data)) != (_digest(second_page), _digest(second_data)):
        raise ValueError("辺野古adapterは同じ候補の2回目実行で差分が出ました")

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

    return {PAGE: first_page, ARENA_DATA: first_data}
