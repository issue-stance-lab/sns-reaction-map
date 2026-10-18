"""学校あだ名禁止の候補ページを生成し、公開互換性を検査する。"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


TOPIC = "school-nickname-ban"
PAGE = Path("docs/school-nickname-ban-reaction-map.html")
ARENA_DATA = Path("docs/school-nickname-ban-arena-data.js")
# 新デザイン（scripts/nickname_layout.py）の読書面は、再読データの明細ごとの立場をこの対応表から読む（明細は立場を持たない）。
# 自転車の青切符と同じく、更新経路で累積候補から作り直し、公開対象に含めて同じ回で揃える
REREAD = Path("data/school-nickname-ban_issues-reread.json")
REREAD_STANCES = Path("data/school-nickname-ban_reread-stances.json")
# 更新回どうしの比較を始める前の回。social-samples/updates/ に前回が無いときだけ使う。
LEGACY_PREVIOUS_WAVE = Path("social-samples/school-nickname-ban_hermes_cur_20260726.json")
LEGACY_PREVIOUS_DATE = "2026-07-26"
VOTE_TOPIC = "school-nickname-ban-issue-stance-v1"
VOTE_CHOICES = 18  # 6論点 × 3スタンス
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
    """収集回ごとの本文確認記録（data/verification/school-nickname-ban-wave-review-YYYYMMDD.json）。"""
    return root / "data" / "verification" / f"school-nickname-ban-wave-review-{current_date.replace('-', '')}.json"


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
        raise ValueError("学校でのあだ名禁止の本文確認元と保存回が一致しません")
    wave = json.loads(wave_path.read_text(encoding="utf-8"))
    ids = [str(row["tweet_id"]) for row in wave]
    ids_sha = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
    if review["ids_sha256"] != ids_sha or review["reviewed_count"] != len(wave):
        raise ValueError("学校でのあだ名禁止の本文確認対象が保存回と一致しません")
    by_id = {str(row["tweet_id"]): row for row in wave}
    if len(by_id) != len(wave):
        raise ValueError("学校でのあだ名禁止の保存回にID重複があります")
    changes = review["overrides"]
    if len({item["tweet_id"] for item in changes}) != len(changes):
        raise ValueError("学校でのあだ名禁止の本文確認結果にID重複があります")
    allowed = {"is_opinion", "main_issue", "stance", "article_usable", "risk", "summary", "reason"}
    for item in changes:
        tweet_id = item["tweet_id"]
        if tweet_id not in by_id or not item.get("review_reason"):
            raise ValueError(f"学校でのあだ名禁止の本文確認結果が不正です: {tweet_id}")
        values = item["classification"]
        if not values or set(values) - allowed:
            raise ValueError(f"学校でのあだ名禁止の本文確認項目が不正です: {tweet_id}")
        by_id[tweet_id]["classification"].update(values)
        if values.get("is_opinion") is True:
            # Kimiが「無関係」とした投稿を本文確認で意見にした場合、公開集計（is_relevant 必須）から落ちないようにする
            by_id[tweet_id]["classification"]["is_relevant"] = True
    cumulative_path = stage / "cumulative-candidate.json"
    cumulative = json.loads(cumulative_path.read_text(encoding="utf-8"))
    cumulative_by_id = {str(row["tweet_id"]): row for row in cumulative}
    if not set(by_id).issubset(cumulative_by_id):
        raise ValueError("学校でのあだ名禁止の本文確認対象が累積候補にありません")
    for tweet_id, row in by_id.items():
        cumulative_by_id[tweet_id]["classification"] = row["classification"]
    (stage / "reviewed-wave.json").write_text(json.dumps(wave, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cumulative_path.write_text(json.dumps(cumulative, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["automated_opinions"] = report["opinions"]
    report["opinions"] = sum(row["classification"]["is_opinion"] is True for row in wave)
    report["body_review"] = str(records_path.relative_to(root))
    report["body_review_changes"] = len(changes)


def build_reread_stances(root: Path, candidate_path: Path, output_path: Path, current_date: str) -> dict:
    """累積候補と再読データ（理由区分の明細）から、立場の対応表を作る（scripts/nickname_reread_stances.py と同じ表）。

    正典はまだ古い（昇格前）ので、立場は累積候補の分類から写し、論点×立場も累積候補で数えて照合する（自転車の
    refresh_adapters/bike.py の build_reread_stances と同じ考え方）。新しい意見を追い読みして再読データの明細に足していないと、
    「正典の意見のうち N 件が再読データの明細にありません」で止まる（新デザインの読書面の生成が止まる前に、ここで止める）。
    """
    import yaml

    from scripts.nickname_reread_stances import table, text_of

    rows = json.loads(candidate_path.read_text(encoding="utf-8"))
    reread_path = root / REREAD
    reread = json.loads(reread_path.read_text(encoding="utf-8"))
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
        data = table(rows, reread, tallied, current_date, canonical, _digest(candidate_path), _digest(reread_path))
    except SystemExit as exc:
        raise ValueError(f"学校でのあだ名禁止の立場の対応表を作れません: {exc}。"
                         "新しい意見を追い読みして data/school-nickname-ban_issues-reread.json の明細に足してください（DATA_REFRESH.md）") from None
    output_path.write_text(text_of(data), encoding="utf-8")
    return data


def vote_fingerprint(html: str) -> tuple[str, tuple[str, ...], tuple[str, ...], int]:
    """投票の互換性の指紋。

    このページの投票定義は他テーマと形が違う。論点は `var issues=[{"key":...}]`
    （JSON・ダブルクォート）、スタンスは `var stances=[{key:'...'}]`（シングルクォート）。
    **件数（count）は指紋に入れない。** 件数は更新のたびに変わるのが正しく、
    含めると毎回「投票互換性が変わった」で止まる。
    """
    topic = re.search(r"var TOPIC='([^']+)'", html)
    issues = re.search(r"var issues=(\[[^\n]*?\]);", html)
    stances = re.search(r"var stances=\[(.*?)\];", html, re.DOTALL)
    if not topic or not issues or not stances:
        raise ValueError("投票定義をページから読み取れません")
    issue_keys = tuple(str(item["key"]) for item in json.loads(issues.group(1)))
    stance_keys = tuple(re.findall(r"key:'([^']+)'", stances.group(1)))
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
    base["prev_label"] = _label(previous_date)
    base["cur_label"] = _label(current_date)
    base["note"] = (
        f"比較対象：{base['prev_label']}収集分のうち意見投稿／"
        f"{base['cur_label']}収集分のうち意見投稿。サンプル数が少ないため傾向の参考程度にご覧ください。"
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
    if "<!-- PLANET_SECTION_START -->" in template.read_text(encoding="utf-8"):
        # 初段は未更新の完全なページを保持する。新しい正典・公開JSON・再読台帳が
        # 候補ツリーに揃う finalize で初めて全体を生成する（途中の数字を公開しない）。
        shutil.copy2(template, output)
        shutil.copy2(root / ARENA_DATA, output.parent / ARENA_DATA.name)
        return
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_nickname_arena.py"),
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


def finalize(root: Path, current_date: str) -> None:
    """候補公開JSONから、ページの集計表示を貼り直す（課題57 段階4）。

    `build()` は候補の投稿から直接数えるので、公開データJSONと食い違ってはいけない。
    候補ツリーでは `build_public_registry.py` が同じ候補から公開JSONを作り直した
    あとにここが走るため、ページの数字の出所が公開データ契約側へ一本化される。
    """
    # 図だけを先／後に書き換えず、全体の検査が済んでから書く。
    # 新しい正典に対応する再読が未完了なら builder が書き込み前に停止する。
    subprocess.run(
        [sys.executable, str(root / "scripts" / "build_nickname_arena.py")],
        cwd=root, check=True,
    )
    subprocess.run(
        [sys.executable, str(root / "scripts" / "build_nickname_arena.py"),
         "--public-counts-only", "--output-html", str(root / PAGE)],
        cwd=root, check=True,
    )


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    # 新デザイン公開後も、旧形式の生成器（山なみの件数・潮目・連動表示・アリーナの点）は元HTML（data/page-sources）を入力にする
    # （nickname_layout.py）。公開候補生成では、隔離コピーの finish がこの元HTMLから新デザインを組み直す
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.nickname_layout import source_for_refresh
    current_page = source_for_refresh(root)
    current_wave = root / "social-samples" / "updates" / TOPIC / current_date / "classified.json"
    first = stage
    second = stage / "idempotence"
    second.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    for template, destination in ((current_page, first), (first / "page-candidate.html", second)):
        _run_builder(root, candidate, template, destination / "page-candidate.html")
        _apply_tide(root, destination / "page-candidate.html", current_wave, current_date)
        build_reread_stances(root, candidate, destination / REREAD_STANCES.name, current_date)

    # ページとアリーナの点、両方を突き合わせる。ページだけ見ると、点の側の揺れを見逃す
    # （数字は新しいのに点だけ古いページになる）。立場の対応表も同じ候補から2回作って比べる。
    for name in ("page-candidate.html", ARENA_DATA.name, REREAD_STANCES.name):
        if _digest(first / name) != _digest(second / name):
            raise ValueError(f"学校あだ名adapterは同じ候補の2回目実行で差分が出ました: {name}")

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
        ARENA_DATA: first / ARENA_DATA.name,
        REREAD_STANCES: first / REREAD_STANCES.name,
    }
