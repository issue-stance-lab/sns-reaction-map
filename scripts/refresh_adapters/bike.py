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
EDITORIAL_REREAD = Path("data/bike-blue-ticket_issues-reread.json")
OPPOSITION_REREAD = Path("data/bike-blue-ticket_opposition_reread.json")
REREAD_REGISTRY = Path("data/verification/reread/bike-blue-ticket.json")
FETCH_HISTORY_RECOVERY = Path("data/verification/bike-blue-ticket-fetch-history-recovery.json")
SUNK_CONTINENTS = Path("data/verification/bike-blue-ticket-sunk-continents.json")

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


def _tide_note(base: dict, signature_count: int) -> str:
    note = (
        f"比較対象：{base['prev_label']}収集分のうち賛否を含む意見投稿／"
        f"{base['cur_label']}収集分のうち賛否を含む意見投稿。"
        "サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。"
    )
    if signature_count:
        note += (
            f"{base['cur_label']}収集分には、同一文面のオンライン署名の貼り付けが"
            "多数含まれており、反対側の比率を押し上げています。"
        )
    return note


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
    signatures = _signature_count(current_wave)
    base["note"] = _tide_note(base, signatures)
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
    root: Path, candidate: Path, template: Path, output: Path, verification_dest: Path,
    opposition_reread: Path | None = None,
) -> None:
    _run(
        root,
        "build_bike_arena.py",
        "--input", str(candidate),
        "--html-template", str(template),
        "--output-html", str(output),
    )
    command = [
        "build_bike_process_sections.py",
        "--input", str(candidate),
        "--html-template", str(output),
        "--output-html", str(output),
        "--verification-dest", str(verification_dest),
    ]
    if opposition_reread is not None:
        command.extend(("--opposition-reread", str(opposition_reread)))
    _run(root, *command)


def build_unspoken_issue_review(
    root: Path, candidate_path: Path, update_path: Path, output_path: Path
) -> dict:
    """Record the new sample denominator only after all newly adopted posts were reread."""
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    update = json.loads(update_path.read_text(encoding="utf-8"))
    review = update.get("unspoken_issue_review") or {}
    adopted = [item for item in update.get("items", []) if item.get("decision") == "adopt"]
    adopted_ids = {str(item.get("tweet_id") or "") for item in adopted}
    reviewed_ids = set(review.get("reviewed_tweet_ids") or [])
    if (
        not adopted_ids or "" in adopted_ids or reviewed_ids != adopted_ids
        or review.get("result") != "no_new_mentions"
    ):
        raise ValueError("未言及論点を再確認した全投稿が今回の採用投稿と一致しません")
    by_id = {str(row.get("tweet_id") or ""): row for row in candidate}
    newly_adopted = []
    for item in adopted:
        row = by_id.get(str(item["tweet_id"]))
        if (
            row is None
            or row.get("is_opinion") is not True
            or hashlib.sha256(str(row.get("text") or "").encode()).hexdigest() != item.get("text_sha256")
        ):
            raise ValueError(f"未言及論点の再読記録が候補本文と一致しません: {item.get('tweet_id')}")
        newly_adopted.append(row)

    source = json.loads((root / SUNK_CONTINENTS).read_text(encoding="utf-8"))
    if len(source.get("items") or []) != 4:
        raise ValueError("自転車の未言及論点4件の検証記録がありません")
    population = sum(row.get("is_opinion") is True for row in candidate)
    day = str(review.get("reviewed_at"))
    note_suffix = (
        f"2026-09-29に今回新たに採用した{len(newly_adopted)}件を本文確認し、"
        "この事実への新規言及は見つからなかった。母数は前回確認済み分と合わせた全意見数。"
    )
    for item in source["items"]:
        pattern = re.compile(str((item.get("match_rule") or {}).get("pattern") or "(?!)"), re.I)
        matching = [row for row in newly_adopted if pattern.search(str(row.get("text") or ""))]
        if matching:
            raise ValueError(
                f"未言及論点 {item.get('id')} に新規一致候補があります。件数と説明を本文確認してください"
            )
        old_base = int(item.get("sns_base") or 0)
        item["sns_note"] = str(item.get("sns_note") or "").replace(f"{old_base}件", f"{population}件")
        item["sns_note"] = f"{item['sns_note']} {note_suffix}"
        item["sns_base"] = population
        item["checked_on"] = day
        item["checked_by"] = "ai_assisted"
        item["reread_ref"] = update_path.relative_to(root).as_posix()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return source


def _apply_connected_display(root: Path, page: Path) -> None:
    """自転車の候補ページへ、読書面と連動表示を再適用する。

    arena/process のビルダーは既存の山なみページを入力に取るため、連動表示の
    マーカー自体は維持できる。ただし将来のビルダー変更で本文側が置換されても、
    候補生成の最後に同じ処理を通しておけば、公開後の定期更新でも表示が後戻りしない。
    """
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.bike_blue_ticket_connected import apply as connect_page

    page.write_text(connect_page(page.read_text(encoding="utf-8"), topic=TOPIC), encoding="utf-8")


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


def finalize(root: Path, current_date: str) -> None:
    """候補公開JSONから、ページ内の管理対象数字を貼り直す。"""
    _run(
        root,
        "bike_issue_media.py",
        "--write-html",
        "--page", str(root / PAGE),
        "--public-theme", str(root / "data" / "public" / "themes" / "bike-blue-ticket.json"),
    )
    _run(
        root,
        "build_bike_arena.py",
        "--input", str(root / "social-samples" / "bike-blue-ticket_2d_classified.json"),
        "--html-template", str(root / PAGE),
        "--output-html", str(root / PAGE),
    )
    _run(root, "refresh_planet_section.py", "--topic", TOPIC, "--for-docs")


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

    update = root / "data" / "bike-blue-ticket_editorial-updates" / f"{current_date.replace('-', '')}.json"
    if not update.is_file():
        raise FileNotFoundError(f"自転車の本文確認記録がありません: {update}")
    from scripts.build_bike_refresh_candidate import extend_opposition_map
    from scripts.build_bike_fetch_history_recovery import build as build_fetch_history_recovery

    fetch_history = build_fetch_history_recovery(
        candidate,
        root=root,
        canonical_relative_path="social-samples/bike-blue-ticket_2d_classified.json",
    )
    first_fetch_history = first / FETCH_HISTORY_RECOVERY.name
    second_fetch_history = second / FETCH_HISTORY_RECOVERY.name
    first_fetch_history.write_text(json.dumps(fetch_history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    second_fetch_history.write_text(json.dumps(fetch_history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    first_sunk = first / SUNK_CONTINENTS.name
    second_sunk = second / SUNK_CONTINENTS.name
    build_unspoken_issue_review(root, candidate, update, first_sunk)
    build_unspoken_issue_review(root, candidate, update, second_sunk)
    first_opposition = first / "opposition-reread-candidate.json"
    second_opposition = second / "opposition-reread-candidate.json"
    extend_opposition_map(root, update, first_opposition)
    extend_opposition_map(root, update, second_opposition)
    first_editorial = first / "bike-blue-ticket_issues-reread.json"
    second_editorial = second / "bike-blue-ticket_issues-reread.json"
    _run(root, "build_bike_editorial_reread.py", "--input", str(candidate), "--output", str(first_editorial))
    _run(root, "build_bike_editorial_reread.py", "--input", str(candidate), "--output", str(second_editorial))
    first_registry = first / REREAD_REGISTRY.name
    second_registry = second / REREAD_REGISTRY.name
    from scripts.build_bike_refresh_candidate import build_verified_reread_manifest
    build_verified_reread_manifest(
        root, candidate, update, first_editorial, first_opposition, first_registry
    )
    build_verified_reread_manifest(
        root, candidate, update, second_editorial, second_opposition, second_registry
    )

    before_vote = vote_fingerprint(current_page.read_text(encoding="utf-8"))

    _run_builders(root, candidate, current_page, first / "page-candidate.html", first, first_opposition)
    _apply_tide(root, first / "page-candidate.html", current_wave, current_date)
    _apply_connected_display(root, first / "page-candidate.html")
    _run_builders(root, candidate, first / "page-candidate.html", second / "page-candidate.html", second, second_opposition)
    _apply_tide(root, second / "page-candidate.html", current_wave, current_date)
    _apply_connected_display(root, second / "page-candidate.html")

    for name in ("page-candidate.html", REREAD_RECORDS.name, CLAIM_RECORDS.name,
                 "bike-blue-ticket_issues-reread.json", "opposition-reread-candidate.json",
                 REREAD_REGISTRY.name, FETCH_HISTORY_RECOVERY.name, SUNK_CONTINENTS.name):
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
        EDITORIAL_REREAD: first_editorial,
        OPPOSITION_REREAD: first_opposition,
        REREAD_REGISTRY: first_registry,
        FETCH_HISTORY_RECOVERY: first_fetch_history,
        SUNK_CONTINENTS: first_sunk,
    }
