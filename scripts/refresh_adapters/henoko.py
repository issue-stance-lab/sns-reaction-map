"""辺野古高校生死亡事故の候補ページを生成し、投票互換性と冪等性を検査する。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

TOPIC = "henoko-student-accident"
PAGE = Path("docs/henoko-student-accident-reaction-map.html")
ARENA_DATA = Path("docs/henoko-arena-data.js")
# 新デザイン（scripts/henoko_layout.py）の読書面は、再読データの明細ごとの立場をこの対応表から読む（明細は立場を持たない）。
# あだ名禁止・自転車と同じく、更新経路で累積候補から作り直し、公開対象に含めて同じ回で揃える
REREAD = Path("data/henoko-student-accident_issues-reread.json")
REREAD_STANCES = Path("data/henoko-student-accident_reread-stances.json")
TIDE_SLUG = "henoko"
VOTE_TOPIC = "henoko-student-accident-issue-stance-v1"
VOTE_CHOICES = 18
PROTECTED = ("G-K10S4YCZFH", "ca-pub-2542211932832864", "vote-store.js")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_reread_stances(root: Path, candidate_path: Path, output_path: Path, current_date: str) -> dict:
    """累積候補と再読データ（理由区分の明細）から、立場の対応表を作る（scripts/henoko_reread_stances.py と同じ表）。

    正典はまだ古い（昇格前）ので、立場は累積候補の分類から写し、論点×立場も累積候補で数えて照合する（あだ名禁止の
    refresh_adapters/nickname.py の build_reread_stances と同じ考え方）。新しい意見を追い読みして再読データの明細に足していないと、
    「正典の意見のうち N 件が再読データの明細にありません」で止まる（新デザインの読書面の生成が止まる前に、ここで止める）。
    """
    import yaml

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.henoko_reread_stances import table, text_of

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
        raise ValueError(f"辺野古高校生死亡事故の立場の対応表を作れません: {exc}。"
                         "新しい意見を追い読みして data/henoko-student-accident_issues-reread.json の明細に足してください（DATA_REFRESH.md）") from None
    output_path.write_text(text_of(data), encoding="utf-8")
    return data


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


def _apply_connected_display(root: Path, page: Path) -> None:
    """辺野古の山なみを作り直した後も、課題77の読書面を再接続する。"""
    html = page.read_text(encoding="utf-8")
    if "<!-- HENOKO_CONNECTED_START -->" not in html:
        return
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.henoko_connected import apply as connect_page
    page.write_text(connect_page(html, topic=TOPIC), encoding="utf-8")


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
    _apply_connected_display(root, root / PAGE)


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    # 新デザイン公開後も、旧形式の生成器（山なみの件数・潮目・連動表示・アリーナの点。山なみの入力の版の守り henoko_planet_guard を含む）は
    # 元HTML（data/page-sources）を入力にする（henoko_layout.py）。公開候補生成では、隔離コピーの finish がこの元HTMLから新デザインを組み直す
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.henoko_layout import source_for_refresh
    current_page = source_for_refresh(root)
    first_page = stage / "page-candidate.html"
    first_data = stage / "arena-data-candidate.js"
    second_page = stage / "idempotence" / "page-candidate.html"
    second_data = stage / "idempotence" / "arena-data-candidate.js"
    second_page.parent.mkdir(parents=True, exist_ok=True)

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))
    first_stances = stage / REREAD_STANCES.name
    second_stances = stage / "idempotence" / REREAD_STANCES.name
    _run_builder(root, candidate, current_page, first_page, first_data)
    _apply_tide(root, first_page, stage / "classified-wave.json", current_date)
    _apply_connected_display(root, first_page)
    build_reread_stances(root, candidate, first_stances, current_date)
    _run_builder(root, candidate, first_page, second_page, second_data)
    _apply_tide(root, second_page, stage / "classified-wave.json", current_date)
    _apply_connected_display(root, second_page)
    build_reread_stances(root, candidate, second_stances, current_date)

    # ページとアリーナの点、立場の対応表を同じ候補から2回作って比べる
    if ((_digest(first_page), _digest(first_data), _digest(first_stances))
            != (_digest(second_page), _digest(second_data), _digest(second_stances))):
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

    return {PAGE: first_page, ARENA_DATA: first_data, REREAD_STANCES: first_stances}
