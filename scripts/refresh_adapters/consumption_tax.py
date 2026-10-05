"""消費税減税の候補ページを生成し、投票互換性と冪等性を検査する。

ページ本体は scripts/build_consumption_tax_page.py が累積候補から作る。
ここは refresh_topic.py --promote から呼ばれ、候補を2回作って差分がないこと、
投票の選択肢（論点7×立場4＝28通り）と保護タグが変わらないことだけを見る。

ページの「意見の推移」（scripts/build_trend_section.py）は、更新のたびに累積候補から貼り直す
（ページ生成器は回の区別を持たないため、枠ごといったん外して差し戻す作りにしてある）。
2026-10-05に「世論の潮目」（前回と今回の2回比較）は外し、前回との比較は推移の冒頭の1行と帯に移した。
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

TOPIC = "consumption-tax-cut"
PAGE = Path("docs/consumption-tax-cut-reaction-map.html")
# 「意見の推移」を数え直す既定の元データ。THEMES.yaml の sample_file と同じファイル。
# adapter.build は昇格前の累積候補を渡す。渡されないとき（部分更新など）は正典から作る。
CANONICAL = Path("social-samples/consumption-tax-cut_hermes_arena_classified.json")
VOTE_TOPIC = "consumption-tax-cut-issue-stance-v1"
VOTE_CHOICES = 28
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


def _apply_trend(root: Path, page: Path, cumulative: Path | None = None) -> None:
    """ページの「意見の推移」の節を、累積候補（無ければ正典）から数え直して貼り直す。

    枠（update-dashboard）はページ生成器が残している。2026-10-05に「世論の潮目」は外したので、
    前回との比較は、推移の冒頭の1行とグラフの帯（build_trend_section）が見せる。
    """
    sys.path.insert(0, str(root / "scripts"))
    from consumption_tax_connected import apply as connect_page
    from build_trend_section import render_for  # type: ignore[import-not-found]

    html = page.read_text(encoding="utf-8")
    source = cumulative if cumulative is not None else root / CANONICAL
    if source.is_file():
        html = render_for(TOPIC, html, source)
    # 元データが無い隔離環境（テストなど）では、既存の節をそのまま残す（黙って消さない）。
    page.write_text(connect_page(html), encoding="utf-8")


def _run_builder(root: Path, candidate: Path, template: Path, output: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_consumption_tax_page.py"),
            "--input", str(candidate),
            "--html-template", str(template),
            "--output-html", str(output),
            # 件数の貼り直しは昇格後に refresh_topic.py が公開ページへ行う
            "--skip-issue-counts",
        ],
        cwd=root,
        check=True,
    )


def finalize(root: Path, current_date: str) -> None:
    """昇格後に調査条件（取得元・期間・件数）を貼り直す。

    この文言は THEMES.yaml の sample_period と累積正典の件数から作られる。どちらも
    昇格の途中で書き換わるので、build() が組み立てる候補ページには新しい値を入れられない。
    """
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_consumption_tax_page.py"),
            "--conditions-only",
            "--output-html", str(root / PAGE),
        ],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_consumption_tax_page.py"),
            "--public-counts-only",
            "--output-html", str(root / PAGE),
        ],
        cwd=root,
        check=True,
    )


def _build_images(stage: Path, candidate: Path) -> dict[Path, Path]:
    """単体で配る画像（意見の推移の折れ線）を2回作り、同じバイト列になることを確かめて公開物にする。

    日本語フォントが無い環境では作れず、ここで止まる（文字が□の画像を公開しない）。
    """
    from build_trend_images import render_for as render_images  # type: ignore[import-not-found]
    from build_trend_section import IMAGE_DIR  # type: ignore[import-not-found]

    first = render_images(TOPIC, candidate, stage / "trend-images")
    second = render_images(TOPIC, candidate, stage / "idempotence" / "trend-images")
    for (kind, variant), path in first.items():
        if path.read_bytes() != second[(kind, variant)].read_bytes():
            raise ValueError(f"消費税減税の推移画像（{kind}/{variant}）は同じ候補の2回目実行でバイト列が変わりました")
    return {IMAGE_DIR / path.name: path for path in first.values()}


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    current_page = root / PAGE
    first_page = stage / "page-candidate.html"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    _run_builder(root, candidate, current_page, first_page)
    _apply_trend(root, first_page, candidate)
    _run_builder(root, candidate, first_page, second_page)
    _apply_trend(root, second_page, candidate)

    if _digest(first_page) != _digest(second_page):
        raise ValueError("消費税減税adapterは同じ候補の2回目実行で差分が出ました")

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

    # ページと同じ累積候補から、推移の画像も作って一緒に公開する（ページの <img> がこの画像を指す）。
    return {PAGE: first_page, **_build_images(stage, candidate)}
