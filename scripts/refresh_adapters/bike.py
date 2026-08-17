"""自転車青切符の候補ページを生成し、公開互換性を検査する。

このテーマには、機械では埋められない人手の工程が1つ残っている。編集部が新しい
「反対」投稿を1件ずつ読み、5区分へ割り当てる作業（再読）である。ページの中心的な
主張「反対はひとつの塊ではない」は、その割り当てに載っている。

そのため、このadapterは**再読が追いついていなければ意図的に失敗する**。
未再読の tweet_id を並べて止めるので、`data/bike-blue-ticket_opposition_reread.json`
へ追記してから `--promote` を実行し直す。読む以外はすべて自動で作り直す。
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

TOPIC = "bike-blue-ticket"
PAGE = Path("docs/bike-blue-ticket-reaction-map.html")
CONFIG = Path("configs/bike-blue-ticket-reaction-map.json")
REREAD_RECORDS = Path("data/verification/bike-blue-ticket-reread.json")
CLAIM_RECORDS = Path("data/verification/bike-blue-ticket-claims.json")

# 更新回ディレクトリを持たない時代の前回収集回。2026-08-10 以降の更新回が
# social-samples/updates/ に揃うまでの間だけ使う。
LEGACY_PREVIOUS_WAVE = Path("social-samples/bike-blue-ticket_hermes_cur_20260726.json")
LEGACY_PREVIOUS_DATE = "2026-07-26"
# 数字の出所検査に出す前回側のパス。仮名化した公開コピーが無い時代のファイル。
LEGACY_PREVIOUS_PUBLIC = "social-samples/bike-blue-ticket_hermes_cur_20260726.json"

VOTE_TOPIC = "bike-blue-ticket-issue-stance-v1"
VOTE_CHOICES = 18
PROTECTED = (
    "G-K10S4YCZFH",
    "ca-pub-2542211932832864",
    "vote-store.js",
    '<link rel="canonical"',
    'property="og:image"',
)
# change.org の署名定型文。同じ文面の貼り付けが反対側の比率を押し上げるため、
# 何件混じっているかを注記に書く。scripts/build_bike_process_sections.py と同じ文面。
SIGNATURE_PHRASE = "自転車に対する青切符制度（罰金制度）の導入に強く反対します"


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


def _wave(root: Path, date: str) -> Path:
    return root / "social-samples" / "updates" / TOPIC / date / "classified.json"


def _previous_wave(root: Path, current_date: str) -> tuple[Path, str]:
    updates = root / "social-samples" / "updates" / TOPIC
    candidates = sorted(
        (path.parent.name, path)
        for path in updates.glob("*/classified.json")
        if path.parent.name < current_date
    )
    if candidates:
        return candidates[-1][1], candidates[-1][0]
    return root / LEGACY_PREVIOUS_WAVE, LEGACY_PREVIOUS_DATE


def _public_wave_path(root: Path, date: str) -> str:
    """数字の出所検査に見せる、仮名化済みの更新回コピーの相対パス。"""
    if date == LEGACY_PREVIOUS_DATE and not _wave(root, date).is_file():
        return LEGACY_PREVIOUS_PUBLIC
    public = Path("data") / "verification" / "updates" / TOPIC / date / "classified.json"
    if not (root / public).is_file():
        raise FileNotFoundError(f"仮名化した更新回コピーがありません: {public}")
    return str(public)


def _label(value: str) -> str:
    _, month, day = value.split("-")
    return f"{int(month)}月{int(day)}日"


def _signature_count(path: Path) -> int:
    """更新回に混じっている署名定型文の件数。

    更新回の本文には、Yahooリアルタイム検索が検索語を囲むために入れる
    `\\tSTART\\t` / `\\tEND\\t` が残っている。累積正典へ取り込むときに外れるため、
    正典と同じ文字列で照合すると更新回側だけ 0件になる（実際に一度そうなった）。
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    return sum(
        1
        for row in rows
        if SIGNATURE_PHRASE
        in str(row.get("text") or "").replace("\tSTART\t", "").replace("\tEND\t", "")
    )


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
    previous_path, previous_date = _previous_wave(root, current_date)
    if not previous_path.is_file():
        raise FileNotFoundError(f"前回更新回がありません: {previous_path}")
    if not current_wave.is_file():
        raise FileNotFoundError(f"今回更新回がありません: {current_wave}")
    base["prev_label"] = _label(previous_date)
    base["cur_label"] = _label(current_date)
    note = (
        f"比較対象：{base['prev_label']}収集分のうち賛否を含む意見投稿／"
        f"{base['cur_label']}収集分のうち賛否を含む意見投稿。"
        "同じ検索語セットで取得した投稿をAIで分類しています。"
        "サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。"
    )
    signatures = _signature_count(current_wave)
    if signatures:
        # 2026-08-17 に反対が77→142件へ増えた分の約半分がこれだった。
        # 断らずに比率だけ出すと、世論が動いたように読める。
        #
        # ここに件数を書かないのは、更新回の本文を文字列照合して数えた値で、
        # 数字の出所検査（分類結果の集計）から導けないため。正確な件数は STEP3 が
        # data/verification/bike-blue-ticket-reread.json から出している。
        note += (
            f"{base['cur_label']}収集分には、同一文面のオンライン署名の貼り付けが"
            "多数含まれており、反対側の比率を押し上げています。"
        )
    base["note"] = note
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


def _run(root: Path, script: str, *args: str) -> None:
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / script), *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        # 再読の不足はここに出る。理由をそのまま昇格処理のログへ持ち上げる。
        raise ValueError(f"{script} が失敗しました:\n{result.stdout}{result.stderr}".rstrip())


def _run_builders(
    root: Path, candidate: Path, template: Path, output: Path, verification_dest: Path
) -> None:
    _run(
        root,
        "build_bike_arena.py",
        "--input", str(candidate),
        "--html-template", str(template),
        "--output-html", str(output),
    )
    _run(
        root,
        "build_bike_process_sections.py",
        "--input", str(candidate),
        "--html-template", str(output),
        "--output-html", str(output),
        "--verification-dest", str(verification_dest),
    )


def _write_config(root: Path, stage: Path, previous_date: str, current_date: str) -> Path:
    """潮目の出所（前回・今回の更新回）をconfigへ書き戻した候補を作る。

    更新回が変わるたびにここを手で直していると、数字の出所検査だけが古いファイルを
    見続ける。昇格対象に含めてadapterが書くことで、手順から外す。
    """
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    sources = [
        entry
        for entry in config["number_provenance"]["sources"]
        if "tide-card" not in entry.get("selectors", [])
    ]
    for date, side in ((previous_date, "前回側"), (current_date, "今回側")):
        sources.append(
            {
                "path": _public_wave_path(root, date),
                "selectors": ["tide-card"],
                "reason": f"「世論の潮目」{side}（{date}収集分）の分類結果",
            }
        )
    config["number_provenance"]["sources"] = sources
    destination = stage / "reaction-map-config.json"
    destination.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return destination


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    current_page = root / PAGE
    current_wave = _wave(root, current_date)
    _previous_path, previous_date = _previous_wave(root, current_date)

    first = stage / "candidate"
    second = stage / "idempotence"
    for directory in (first, second):
        directory.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))

    _run_builders(root, candidate, current_page, first / "page-candidate.html", first)
    _apply_tide(root, first / "page-candidate.html", current_wave, current_date)
    _run_builders(root, candidate, first / "page-candidate.html", second / "page-candidate.html", second)
    _apply_tide(root, second / "page-candidate.html", current_wave, current_date)

    for name in ("page-candidate.html", REREAD_RECORDS.name, CLAIM_RECORDS.name):
        if _digest(first / name) != _digest(second / name):
            raise ValueError(f"自転車青切符adapterは同じ候補の2回目実行で差分が出ました: {name}")

    current_html = current_page.read_text(encoding="utf-8")
    candidate_html = (first / "page-candidate.html").read_text(encoding="utf-8")
    after_vote = vote_fingerprint(candidate_html)
    if before_vote != after_vote:
        raise ValueError(f"投票互換性が変わりました: {before_vote} -> {after_vote}")
    if after_vote[0] != VOTE_TOPIC or after_vote[3] != VOTE_CHOICES:
        raise ValueError(f"想定外の投票定義です: {after_vote}")
    changed = [
        token for token in PROTECTED if current_html.count(token) != candidate_html.count(token)
    ]
    if changed:
        raise ValueError("保護タグの個数が変わりました: " + ", ".join(changed))

    return {
        PAGE: first / "page-candidate.html",
        REREAD_RECORDS: first / REREAD_RECORDS.name,
        CLAIM_RECORDS: first / CLAIM_RECORDS.name,
        CONFIG: _write_config(root, stage, previous_date, current_date),
    }
