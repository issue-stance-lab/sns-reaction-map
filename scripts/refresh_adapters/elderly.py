"""高齢者免許返納の候補ページを生成し、公開互換性を検査する。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


TOPIC = "elderly-license-revocation"
PAGE = Path("docs/elderly-license-revocation-reaction-map.html")
LEGACY_PREVIOUS_WAVE = Path(
    "social-samples/elderly-license-revocation_hermes_cur_20260726.json"
)
# 新デザイン（scripts/elderly_layout.py）は、理由区分ごとの立場を再読データの明細の stance から数える（自転車のような立場の対応表は無い）
REREAD = Path("data/elderly-license_issues-reread.json")
PLANET = Path("configs/planet/elderly-license-revocation.yaml")
VOTE_TOPIC = "elderly-license-revocation-issue-stance-v1"
VOTE_CHOICES = 18
PROTECTED = (
    "G-K10S4YCZFH",
    "ca-pub-2542211932832864",
    "vote-store.js",
    '<link rel="canonical"',
    'property="og:image"',
)


def review_records_path(root: Path, current_date: str) -> Path:
    """収集回ごとの本文確認記録（data/verification/elderly-license-revocation-wave-review-YYYYMMDD.json）。"""
    return root / "data" / "verification" / f"elderly-license-revocation-wave-review-{current_date.replace('-', '')}.json"


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
        raise ValueError("高齢者免許返納の本文確認元と保存回が一致しません")
    wave = json.loads(wave_path.read_text(encoding="utf-8"))
    ids = [str(row["tweet_id"]) for row in wave]
    ids_sha = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
    if review["ids_sha256"] != ids_sha or review["reviewed_count"] != len(wave):
        raise ValueError("高齢者免許返納の本文確認対象が保存回と一致しません")
    by_id = {str(row["tweet_id"]): row for row in wave}
    if len(by_id) != len(wave):
        raise ValueError("高齢者免許返納の保存回にID重複があります")
    changes = review["overrides"]
    if len({item["tweet_id"] for item in changes}) != len(changes):
        raise ValueError("高齢者免許返納の本文確認結果にID重複があります")
    allowed = {"is_opinion", "main_issue", "stance", "article_usable", "risk", "summary", "reason"}
    for item in changes:
        tweet_id = item["tweet_id"]
        if tweet_id not in by_id or not item.get("review_reason"):
            raise ValueError(f"高齢者免許返納の本文確認結果が不正です: {tweet_id}")
        values = item["classification"]
        if not values or set(values) - allowed:
            raise ValueError(f"高齢者免許返納の本文確認項目が不正です: {tweet_id}")
        by_id[tweet_id]["classification"].update(values)
        if values.get("is_opinion") is True:
            # Kimiが「無関係」とした投稿を本文確認で意見にした場合、公開集計（is_relevant 必須）から落ちないようにする
            by_id[tweet_id]["classification"]["is_relevant"] = True
    cumulative_path = stage / "cumulative-candidate.json"
    cumulative = json.loads(cumulative_path.read_text(encoding="utf-8"))
    cumulative_by_id = {str(row["tweet_id"]): row for row in cumulative}
    if not set(by_id).issubset(cumulative_by_id):
        raise ValueError("高齢者免許返納の本文確認対象が累積候補にありません")
    for tweet_id, row in by_id.items():
        cumulative_by_id[tweet_id]["classification"] = row["classification"]
    (stage / "reviewed-wave.json").write_text(json.dumps(wave, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cumulative_path.write_text(json.dumps(cumulative, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["automated_opinions"] = report["opinions"]
    report["opinions"] = sum(row["classification"]["is_opinion"] is True for row in wave)
    report["body_review"] = str(records_path.relative_to(root))
    report["body_review_changes"] = len(changes)


def check_reread_stances(root: Path) -> int:
    """再読データの明細がすべて立場（stance）を持ち、それが planet 設定の立場かを確かめる。明細の数を返す。

    追い読みで足した明細に立場が無いと、新デザインの理由区分ごとの立場が数えられず、公開候補の生成の最後
    （elderly_layout.finish）で止まる。adapter の段階で、何を直せばよいかが分かる形で先に止める。
    """
    import yaml

    raw = json.loads((root / REREAD).read_text(encoding="utf-8"))
    planet = yaml.safe_load((root / PLANET).read_text(encoding="utf-8"))
    known = {s["key"] for s in planet["stances"]} | {s["label"] for s in planet["stances"]}
    items = raw.get("items") or []
    missing = [str(i.get("tweet_id")) for i in items if not i.get("stance")]
    unknown = sorted({str(i["stance"]) for i in items if i.get("stance") and i["stance"] not in known})
    if missing:
        raise ValueError(
            f"再読データ {REREAD} の明細 {len(missing)} 件に立場（stance）がありません（例: {missing[0]}）。"
            "追い読みで足した明細には、正典の classification.stance をそのまま書いてください。"
            "新デザインの照合が止まるため、ここで停止しました。"
        )
    if unknown:
        raise ValueError(f"再読データ {REREAD} の明細に、planet 設定に無い立場があります: {unknown}")
    return len(items)


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
    return root / LEGACY_PREVIOUS_WAVE, "2026-07-26"


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
            str(root / "scripts" / "build_elderly_arena.py"),
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
    """候補公開JSONから、ページの管理対象集計を貼り直す。"""
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_elderly_arena.py"),
            "--public-counts-only",
            "--output-html",
            str(root / PAGE),
        ],
        cwd=root,
        check=True,
    )
    # 山なみ（PLANET_DATA・冒頭・調査条件・連動表示）を候補の正典から作り直す（自転車の finalize と同じ）。
    # 新デザイン（elderly_layout）の最終生成は PLANET_DATA の意見数を公開JSONと照合するため、
    # ここで作り直しておかないと「元HTMLの更新を先に済ませてください」で止まる（2026-10-13）。
    subprocess.run(
        [sys.executable, str(root / "scripts" / "refresh_planet_section.py"), "--topic", TOPIC, "--for-docs"],
        cwd=root,
        check=True,
    )


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    """候補を2回生成し、2回目に差分がない場合だけ公開対象を返す。"""
    candidate = stage / "cumulative-candidate.json"
    # 新デザイン公開後も、旧形式の生成器（アリーナ・山なみ・潮目・連動表示）は元HTML（data/page-sources）を入力にする
    # （elderly_layout.py）。公開候補生成では、隔離コピーの finish がこの元HTMLから新デザインを組み直す
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.elderly_layout import source_for_refresh
    current_page = source_for_refresh(root)
    check_reread_stances(root)
    current_wave = (
        root
        / "social-samples"
        / "updates"
        / TOPIC
        / current_date
        / "classified.json"
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
        raise ValueError("高齢者免許返納adapterは同じ候補の2回目実行で差分が出ました")

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

    return {PAGE: first_page}
