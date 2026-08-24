"""副首都法案の候補ページを生成し、投票互換性と冪等性を検査する。

ページ本体は scripts/build_fukushuto_arena.py が正典（または累積候補）から作る。
ここは refresh_topic.py --promote から呼ばれ、候補を2回作って差分がないこと、
投票の選択肢（論点7×立場3＝21通り）と保護タグが変わらないことだけを見る。
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

TOPIC = "fukushuto"
PAGE = Path("docs/fukushuto-reaction-map.html")
CLAIM_RECORDS = Path("data/verification/fukushuto-claims.json")
# 更新回がまだ1回も無かった頃の比較対象。潮目ウィジェットの「前回」に使う。
LEGACY_PREVIOUS_WAVE = Path("social-samples/fukushuto_hermes_cur_20260726_v2.json")
LEGACY_PREVIOUS_DATE = "2026-07-26"
VOTE_TOPIC = "fukushuto-issue-stance-v1"
VOTE_CHOICES = 21
PROTECTED = (
    "G-K10S4YCZFH",
    "ca-pub-2542211932832864",
    "vote-store.js",
    '<link rel="canonical"',
    'property="og:image"',
)


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
    updates = root / "social-samples" / "updates" / TOPIC
    candidates = sorted(
        (path.parent.name, path)
        for path in updates.glob("*/classified.json")
        if path.parent.name < current_date
    )
    if candidates:
        return candidates[-1][1], candidates[-1][0]
    return root / LEGACY_PREVIOUS_WAVE, LEGACY_PREVIOUS_DATE


def _label(value: str) -> str:
    _, month, day = value.split("-")
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

    base = next(item for item in THEMES if item["slug"] == TOPIC).copy()
    previous_path, previous_date = _latest_previous_wave(root, current_date)
    if not previous_path.is_file():
        raise FileNotFoundError(f"前回更新回がありません: {previous_path}")
    if not current_wave.is_file():
        raise FileNotFoundError(f"今回更新回がありません: {current_wave}")
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


def _run_builder(root: Path, candidate: Path, template: Path, output: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_fukushuto_arena.py"),
            "--input",
            str(candidate),
            "--html-template",
            str(template),
            "--output-html",
            str(output),
        ],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_fukushuto_process_sections.py"),
            "--input",
            str(candidate),
            "--html-template",
            str(output),
            "--output-html",
            str(output),
            "--verification-dest",
            str(output.parent),
        ],
        cwd=root,
        check=True,
    )


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    current_page = root / PAGE
    current_wave = root / "social-samples" / "updates" / TOPIC / current_date / "classified.json"
    first_page = stage / "page-candidate.html"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    _run_builder(root, candidate, current_page, first_page)
    _apply_tide(root, first_page, current_wave, current_date)
    _run_builder(root, candidate, first_page, second_page)
    _apply_tide(root, second_page, current_wave, current_date)

    if _digest(first_page) != _digest(second_page):
        raise ValueError("副首都adapterは同じ候補の2回目実行で差分が出ました")
    first_claims = stage / CLAIM_RECORDS.name
    second_claims = stage / "idempotence" / CLAIM_RECORDS.name
    if _digest(first_claims) != _digest(second_claims):
        raise ValueError(f"副首都adapterは同じ候補の2回目実行で差分が出ました: {CLAIM_RECORDS.name}")

    current_html = current_page.read_text(encoding="utf-8")
    candidate_html = first_page.read_text(encoding="utf-8")
    after_vote = vote_fingerprint(candidate_html)
    if before_vote != after_vote:
        raise ValueError(f"投票互換性が変わりました: {before_vote} -> {after_vote}")
    if after_vote[0] != VOTE_TOPIC or after_vote[3] != VOTE_CHOICES:
        raise ValueError(f"想定外の投票定義です: {after_vote}")
    changed = [token for token in PROTECTED if current_html.count(token) != candidate_html.count(token)]
    if changed:
        raise ValueError("保護タグの個数が変わりました: " + ", ".join(changed))

    return {PAGE: first_page, CLAIM_RECORDS: first_claims}
