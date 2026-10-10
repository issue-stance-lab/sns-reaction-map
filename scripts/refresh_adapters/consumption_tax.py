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

from scripts.refresh_adapters import trend_support

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



def review_records_path(root: Path, current_date: str) -> Path:
    """収集回ごとの本文確認記録（data/verification/consumption-tax-cut-wave-review-YYYYMMDD.json）。"""
    return root / "data" / "verification" / f"consumption-tax-cut-wave-review-{current_date.replace('-', '')}.json"


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
        raise ValueError("消費税減税の本文確認元と保存回が一致しません")
    wave = json.loads(wave_path.read_text(encoding="utf-8"))
    ids = [str(row["tweet_id"]) for row in wave]
    ids_sha = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
    if review["ids_sha256"] != ids_sha or review["reviewed_count"] != len(wave):
        raise ValueError("消費税減税の本文確認対象が保存回と一致しません")
    by_id = {str(row["tweet_id"]): row for row in wave}
    if len(by_id) != len(wave):
        raise ValueError("消費税減税の保存回にID重複があります")
    changes = review["overrides"]
    if len({item["tweet_id"] for item in changes}) != len(changes):
        raise ValueError("消費税減税の本文確認結果にID重複があります")
    allowed = {"is_opinion", "main_issue", "stance", "article_usable", "risk", "summary", "reason"}
    for item in changes:
        tweet_id = item["tweet_id"]
        if tweet_id not in by_id or not item.get("review_reason"):
            raise ValueError(f"消費税減税の本文確認結果が不正です: {tweet_id}")
        values = item["classification"]
        if not values or set(values) - allowed:
            raise ValueError(f"消費税減税の本文確認項目が不正です: {tweet_id}")
        by_id[tweet_id]["classification"].update(values)
    cumulative_path = stage / "cumulative-candidate.json"
    cumulative = json.loads(cumulative_path.read_text(encoding="utf-8"))
    cumulative_by_id = {str(row["tweet_id"]): row for row in cumulative}
    if not set(by_id).issubset(cumulative_by_id):
        raise ValueError("消費税減税の本文確認対象が累積候補にありません")
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


def _apply_trend(root: Path, page: Path, cumulative: Path | None = None) -> None:
    """ページの「意見の推移」の節を、累積候補（無ければ正典）から数え直して貼り直す。

    枠（update-dashboard）はページ生成器が残している。2026-10-05に「世論の潮目」は外したので、
    前回との比較は、推移の冒頭の1行とグラフの帯（build_trend_section）が見せる。
    """
    sys.path.insert(0, str(root / "scripts"))
    from consumption_tax_connected import apply as connect_page

    source = cumulative if cumulative is not None else root / CANONICAL
    html = trend_support.render_trend(root, TOPIC, page.read_text(encoding="utf-8"), source)
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
    """単体で配る画像（意見の推移の折れ線）を作る（作り方は trend_support.build_images）。"""
    return trend_support.build_images(Path(__file__).resolve().parents[2], TOPIC, stage, candidate)


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
