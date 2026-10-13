"""消費税減税の候補ページを生成し、投票互換性と冪等性を検査する。

ページ本体は scripts/build_consumption_tax_page.py が累積候補から作る。新デザイン公開後（scripts/consumption_tax_layout.py）は、
入力は元HTML（data/page-sources/consumption-tax-cut.html）で、新デザインは公開候補生成の最後に finish が組む。
ここは refresh_topic.py --promote から呼ばれ、候補を2回作って差分がないこと、
投票の選択肢（論点7×立場4＝28通り）と保護タグが変わらないことだけを見る。

ページの「意見の推移」（scripts/build_trend_section.py）は、更新のたびに累積候補から貼り直す
（ページ生成器は回の区別を持たないため、枠ごといったん外して差し戻す作りにしてある）。
2026-10-05に「世論の潮目」（前回と今回の2回比較）は外し、前回との比較は推移の冒頭の1行と帯に移した。
"""

from __future__ import annotations

import hashlib
import json
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
# 新デザインの読書面は、再読データの明細ごとの立場をこの対応表から読む（明細の立場は読み直したときの記録で、
# その後の分類のやり直しを反映していない。2026-10-13 時点で102件が正典と違った）。辺野古・あだ名・自転車と同じく、
# 更新経路で累積候補から作り直し、公開対象に含めて同じ回で揃える（共有の再読データは変えない）
REREAD = Path("data/consumption-tax-cut_4issues-reread.json")
REREAD_STANCES = Path("data/consumption-tax-cut_reread-stances.json")
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

def build_reread_stances(root: Path, candidate_path: Path, output_path: Path, current_date: str) -> dict:
    """累積候補と再読データ（4論点の理由区分の明細）から、立場の対応表を作る（scripts/consumption_tax_reread_stances.py と同じ表）。

    正典はまだ古い（昇格前）ので、立場は累積候補の分類から写し、論点×立場も累積候補で数えて照合する（辺野古の
    refresh_adapters/henoko.py の build_reread_stances と同じ考え方）。新しい意見を追い読みして再読データの明細に足していないと、
    「正典の意見のうち N 件が再読データの明細にありません」で止まる（新デザインの読書面の生成が止まる前に、ここで止める）。
    """
    import yaml

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.consumption_tax_reread_stances import table, text_of

    rows = json.loads(candidate_path.read_text(encoding="utf-8"))
    reread_path = root / REREAD
    reread = json.loads(reread_path.read_text(encoding="utf-8"))
    planet = yaml.safe_load((root / "configs" / "planet" / f"{TOPIC}.yaml").read_text(encoding="utf-8"))
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        c = row.get("classification") or {}
        if c.get("is_opinion") is not True:
            continue
        by = counts.setdefault(str(c.get("main_issue")), {})
        by[str(c.get("stance"))] = by.get(str(c.get("stance")), 0) + 1
    tallied = {
        "updated_on": current_date,
        "issues": [{"label": label, "stances": [{"label": st, "count": n} for st, n in sorted(by.items())]}
                   for label, by in sorted(counts.items())],
    }
    canonical = str(yaml.safe_load((root / "THEMES.yaml").read_text(encoding="utf-8"))["themes"][TOPIC]["sample_file"])
    try:
        # 累積候補は昇格すると正典そのものになる（canonical_sha256 も昇格後の正典と同じ値）
        data = table(rows, reread, planet, tallied, current_date, canonical, _digest(candidate_path), _digest(reread_path))
    except SystemExit as exc:
        raise ValueError(f"消費税減税の立場の対応表を作れません: {exc}。"
                         "新しい意見を追い読みして data/consumption-tax-cut_4issues-reread.json の明細に足してください（DATA_REFRESH.md）") from None
    output_path.write_text(text_of(data), encoding="utf-8")
    return data


def _previous_wave_model(root: Path, current_date: str) -> str | None:
    """前回の更新回（収集日が今回より前で一番新しく、分類モデルの記録がある保存回）の分類モデル。記録が無ければ None。"""
    updates = root / "social-samples" / "updates" / TOPIC
    dates = sorted(path.name for path in updates.iterdir() if path.is_dir() and path.name < current_date) if updates.is_dir() else []
    for date in reversed(dates):
        report = updates / date / "report.json"
        if report.exists():
            data = json.loads(report.read_text(encoding="utf-8"))
            name = ((data.get("provenance") or {}).get("model") or {}).get("name")
            if name:
                return name
    return None


def _current_wave_model(stage: Path) -> str | None:
    report = stage / "report.json"
    if not report.exists():
        return None
    data = json.loads(report.read_text(encoding="utf-8"))
    return ((data.get("provenance") or {}).get("model") or {}).get("name")


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
    # 新デザイン公開後も、旧形式の生成器（ページ生成器・意見の推移・連動表示・検索入口・計算部品）は元HTML（data/page-sources）を
    # 入力にする（consumption_tax_layout.py）。公開候補生成では、隔離コピーの finish がこの元HTMLから新デザインを組み直す
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.consumption_tax_layout import source_for_refresh
    current_page = source_for_refresh(root)
    first_page = stage / "page-candidate.html"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    # 分類に使うAIが前回から変わった回は、推移の注意書きに記録が要る（無ければここで止まる）。
    trend_support.check_model_break(
        root, TOPIC, current_date, _previous_wave_model(root, current_date), _current_wave_model(stage)
    )

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    first_stances = stage / REREAD_STANCES.name
    second_stances = stage / "idempotence" / REREAD_STANCES.name
    _run_builder(root, candidate, current_page, first_page)
    _apply_trend(root, first_page, candidate)
    build_reread_stances(root, candidate, first_stances, current_date)
    _run_builder(root, candidate, first_page, second_page)
    _apply_trend(root, second_page, candidate)
    build_reread_stances(root, candidate, second_stances, current_date)

    # ページと立場の対応表を同じ候補から2回作って比べる
    if (_digest(first_page), _digest(first_stances)) != (_digest(second_page), _digest(second_stances)):
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
    return {PAGE: first_page, REREAD_STANCES: first_stances, **_build_images(stage, candidate)}
