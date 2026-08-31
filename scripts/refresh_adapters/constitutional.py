"""憲法改正論議の候補ページを生成し、投票互換性と冪等性を検査する。"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

TOPIC = "constitutional-amendment"
PAGE = Path("docs/constitutional-amendment-reaction-map.html")
TIDE_SLUG = "constitutional-amendment"
VOTE_TOPIC = "constitutional-amendment-issue-stance-v1"
VOTE_CHOICES = 24
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
    """投票の選択肢とその並び。

    choiceIdx は `論点の位置 * 立場の数 + 立場の位置` で保存済みなので、順序が1つでも
    入れ替わると過去の投票の意味が変わる。このページの論点は JSON、立場はJSリテラルで
    書かれていて引用符が違うため、それぞれの形で読み取る。
    """
    topic = re.search(r"const TOPIC='([^']+)'", html)
    issues = re.search(r"const issues=\[(.*?)\];", html, re.DOTALL)
    stances = re.search(r"const stances=\[(.*?)\];", html, re.DOTALL)
    if not topic or not issues or not stances:
        raise ValueError("投票定義をページから読み取れません")
    issue_keys = tuple(re.findall(r'"k":\s*"([^"]+)"', issues.group(1)))
    stance_keys = tuple(re.findall(r"\bk:'([^']+)'", stances.group(1)))
    if not issue_keys or not stance_keys:
        raise ValueError("投票の選択肢を読み取れません")
    return topic.group(1), issue_keys, stance_keys, len(issue_keys) * len(stance_keys)


def _previous_wave(root: Path, current_date: str) -> tuple[Path, str]:
    """潮目の比較対象になる前回の更新回。

    このページの潮目は 2026-07-26 まで手作業の値で、比較元にできるファイルが残って
    いない。更新回（social-samples/updates/）が正典なので、そこから今回より前の
    最新回を選ぶ。見つからなければ、合成値で埋めずに落とす。
    """
    updates = root / "social-samples" / "updates" / TOPIC
    candidates = sorted(
        (path.parent.name, path)
        for path in updates.glob("*/classified.json")
        if path.parent.name < current_date
    )
    if not candidates:
        raise FileNotFoundError(
            f"{current_date} より前の更新回がありません: {updates}"
        )
    return candidates[-1][1], candidates[-1][0]


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

    base = next(item for item in THEMES if item["slug"] == TIDE_SLUG).copy()
    previous_path, previous_date = _previous_wave(root, current_date)
    if not current_wave.is_file():
        raise FileNotFoundError(f"今回更新回がありません: {current_wave}")
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
    if not previous or not current:
        raise ValueError(
            f"潮目の比較対象が0件です（前回{len(previous)}件 / 今回{len(current)}件）"
        )
    tide = generate_tide_section(base, previous, current)
    page.write_text(inject_into_html(page, tide, _load_tide_css()), encoding="utf-8")


def _run_builder(root: Path, candidate: Path, template: Path, output: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_constitutional_arena.py"),
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
            str(root / "scripts" / "build_constitutional_process_sections.py"),
            "--input",
            str(candidate),
            "--html-template",
            str(output),
            "--output-html",
            str(output),
            "--verification-dest",
            str(output.parent / "verification"),
        ],
        cwd=root,
        check=True,
    )


def finalize(root: Path, current_date: str) -> None:
    """候補公開JSONから、ページの管理対象集計を貼り直す。"""
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_constitutional_arena.py"),
            "--public-counts-only",
            "--output-html", str(root / PAGE),
        ],
        cwd=root,
        check=True,
    )


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    current_page = root / PAGE
    current_wave = (
        root / "social-samples" / "updates" / TOPIC / current_date / "classified.json"
    )
    first_page = stage / "page-candidate.html"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    _run_builder(root, candidate, current_page, first_page)
    _apply_tide(root, first_page, current_wave, current_date)
    _run_builder(root, candidate, first_page, second_page)
    _apply_tide(root, second_page, current_wave, current_date)

    if _digest(first_page) != _digest(second_page):
        raise ValueError("憲法改正adapterは同じ候補の2回目実行で差分が出ました")

    current_html = current_page.read_text(encoding="utf-8")
    candidate_html = first_page.read_text(encoding="utf-8")
    after_vote = vote_fingerprint(candidate_html)
    if before_vote != after_vote:
        raise ValueError(f"投票互換性が変わりました: {before_vote} -> {after_vote}")
    if after_vote[0] != VOTE_TOPIC or after_vote[3] != VOTE_CHOICES:
        raise ValueError(f"想定外の投票定義です: {after_vote}")
    changed = [
        token for token in PROTECTED
        if current_html.count(token) != candidate_html.count(token)
    ]
    if changed:
        raise ValueError("保護タグの個数が変わりました: " + ", ".join(changed))

    return {PAGE: first_page}
