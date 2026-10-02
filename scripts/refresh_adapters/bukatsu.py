"""既存の部活動パイロットを共通ランナーから利用するadapter。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.refresh_bukatsu_pilot import (
    PAGE,
    previous_wave,
    read_rows,
    sync_candidate_issue_counts,
    validate_candidate,
    write_json,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wave_model(root: Path, stage: Path, wave_date: str, *, current: bool) -> str | None:
    report = stage / "report.json" if current else root / "missing-report.json"
    if not report.exists():
        return None
    data = json.loads(report.read_text(encoding="utf-8"))
    return ((data.get("provenance") or {}).get("model") or {}).get("name")


def _previous_wave_model(root: Path, previous: list[dict]) -> str | None:
    previous_ids = {str(row.get("tweet_id")) for row in previous if row.get("tweet_id")}
    best: tuple[int, str] | None = None
    updates = root / "social-samples" / "updates" / "bukatsu-chiiki"
    for classified in updates.glob("*/classified.json"):
        rows = json.loads(classified.read_text(encoding="utf-8"))
        overlap = len(previous_ids & {str(row.get("tweet_id")) for row in rows if row.get("tweet_id")})
        if not overlap:
            continue
        report = classified.with_name("report.json")
        if not report.exists():
            continue
        model = (((json.loads(report.read_text(encoding="utf-8")).get("provenance") or {})
                  .get("model") or {}).get("name"))
        if model and (best is None or overlap > best[0]):
            best = (overlap, model)
    return best[1] if best else None


def _preserve_tide_block(template: str, generated: str) -> str:
    pattern = re.compile(r"<!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END -->", re.DOTALL)
    old = pattern.search(template)
    new = pattern.search(generated)
    if not old or not new:
        raise ValueError("潮目カードを保持できません")
    return generated[:new.start()] + old.group(0) + generated[new.end():]


def _sync_head_sample_count(page: str, opinion_count: int) -> str:
    """head内の検索結果用説明を最新の意見件数にそろえる。"""
    head_end = page.find("</head>")
    if head_end < 0:
        raise ValueError("head終了タグがありません")
    head = page[:head_end]
    body = page[head_end:]
    head, matched = re.subn(
        r"SNS反応[\d,]+件で整理します",
        f"SNS反応{opinion_count:,}件で整理します",
        head,
    )
    if matched != 4:
        raise ValueError(f"headのSNS反応件数を4か所更新できません: {matched}か所")
    return head + body


def _sync_seo_sample_count(config: dict, opinion_count: int) -> dict:
    theme = next(item for item in config["themes"] if item["id"] == "bukatsu-chiiki")
    description, matched = re.subn(
        r"SNS反応[\d,]+件で整理します",
        f"SNS反応{opinion_count:,}件で整理します",
        theme["description"],
    )
    if matched != 1:
        raise ValueError(f"SEO説明のSNS反応件数を更新できません: {matched}か所")
    theme["description"] = description
    return config


def _build_once(
    root: Path,
    stage: Path,
    previous_date: str,
    current_date: str,
    template: Path,
    output: Path,
    preserve_tide: bool,
) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "update_bukatsu_tide.py"),
            "--classified",
            str(stage / "cumulative-candidate.json"),
            "--previous-batch",
            str(stage / "previous-wave.json"),
            "--current-batch",
            str(stage / "classified-wave.json"),
            "--previous-date",
            previous_date,
            "--current-date",
            current_date,
            "--html",
            str(template),
            "--output-html",
            str(output),
        ],
        cwd=root,
        check=True,
    )
    rows = read_rows(stage / "cumulative-candidate.json")
    text = output.read_text(encoding="utf-8")
    if preserve_tide:
        text = _preserve_tide_block(template.read_text(encoding="utf-8"), text)
    text = sync_candidate_issue_counts(text, rows)
    from scripts.bukatsu_connected import TOPIC as CONNECTED_TOPIC, apply as connect_page
    text = connect_page(text, topic=CONNECTED_TOPIC)
    output.write_text(text, encoding="utf-8")


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    current = read_rows(root / "social-samples" / "bukatsu-chiiki_hermes_classified.json")
    previous_date, previous = previous_wave(current, current_date)
    write_json(stage / "previous-wave.json", previous)
    previous_model = _previous_wave_model(root, previous)
    current_model = _wave_model(root, stage, current_date, current=True)
    preserve_tide = bool(previous_model and current_model and previous_model != current_model)
    if preserve_tide:
        print(f"注意: 分類モデルが {previous_model} → {current_model} に変わったため、"
              "「世論の潮目」は前回表示を維持します")

    first = stage / "page-candidate.html"
    second = stage / "idempotence" / "page-candidate.html"
    second.parent.mkdir(parents=True, exist_ok=True)
    _build_once(root, stage, previous_date, current_date, PAGE, first, preserve_tide)
    _build_once(root, stage, previous_date, current_date, first, second, preserve_tide)
    if _digest(first) != _digest(second):
        raise ValueError("部活動adapterは同じ候補の2回目実行で差分が出ました")

    raw = read_rows(stage / "raw.json")
    new = read_rows(stage / "new-only.json")
    classified = read_rows(stage / "classified-wave.json")
    candidate = read_rows(stage / "cumulative-candidate.json")
    validate_candidate(current, raw, new, classified, candidate, first.read_text(encoding="utf-8"))
    return {PAGE.relative_to(root): first}


def finalize(root: Path, current_date: str) -> None:
    """昇格後に山なみと調査条件を最新の公開JSONへそろえる。

    この文言はTHEMES.yamlのsample_periodと累積正典の件数から作られる。どちらも
    昇格の途中で書き換わるので、build()が組み立てる候補ページには新しい値を
    入れられない。山なみ化後は、山なみ区画も公開JSONの更新後に作り直す必要がある。
    パイロットで手作業だった2手をadapter経由でも再現する。
    """
    subprocess.run(
        [sys.executable, str(root / "scripts" / "refresh_planet_section.py"),
         "--topic", "bukatsu-chiiki", "--for-docs"],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(root / "scripts" / "build_bukatsu_arena.py")],
        cwd=root,
        check=True,
    )
    public = json.loads((root / "data/public/themes/bukatsu-chiiki.json").read_text(encoding="utf-8"))
    opinion_count = int(public["opinion_count"])
    seo = root / "configs/theme-seo.json"
    seo.write_text(
        json.dumps(
            _sync_seo_sample_count(json.loads(seo.read_text(encoding="utf-8")), opinion_count),
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    page = root / "docs/bukatsu-chiiki-reaction-map.html"
    page.write_text(
        _sync_head_sample_count(page.read_text(encoding="utf-8"), opinion_count),
        encoding="utf-8",
    )
