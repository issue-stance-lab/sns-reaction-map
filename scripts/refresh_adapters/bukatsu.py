"""既存の部活動パイロットを共通ランナーから利用するadapter。"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from scripts.refresh_bukatsu_pilot import (
    PAGE,
    PREVIOUS_DATE,
    read_rows,
    sync_candidate_issue_counts,
    validate_candidate,
    write_json,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_once(root: Path, stage: Path, current_date: str, template: Path, output: Path) -> None:
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
            PREVIOUS_DATE,
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
    output.write_text(
        sync_candidate_issue_counts(output.read_text(encoding="utf-8"), rows),
        encoding="utf-8",
    )


def build(root: Path, stage: Path, current_date: str) -> dict[Path, Path]:
    current = read_rows(root / "social-samples" / "bukatsu-chiiki_hermes_classified.json")
    previous = [row for row in current if str(row.get("fetched_at") or "")[:10] == PREVIOUS_DATE]
    if len(previous) != 159:
        raise ValueError(f"前回更新回は159件の想定です: {len(previous)}件")
    write_json(stage / "previous-wave.json", previous)

    first = stage / "page-candidate.html"
    second = stage / "idempotence" / "page-candidate.html"
    second.parent.mkdir(parents=True, exist_ok=True)
    _build_once(root, stage, current_date, PAGE, first)
    _build_once(root, stage, current_date, first, second)
    if _digest(first) != _digest(second):
        raise ValueError("部活動adapterは同じ候補の2回目実行で差分が出ました")

    raw = read_rows(stage / "raw.json")
    new = read_rows(stage / "new-only.json")
    classified = read_rows(stage / "classified-wave.json")
    candidate = read_rows(stage / "cumulative-candidate.json")
    validate_candidate(current, raw, new, classified, candidate, first.read_text(encoding="utf-8"))
    return {PAGE.relative_to(root): first}


def finalize(root: Path, current_date: str) -> None:
    """昇格後に調査条件（取得元・期間・件数）を貼り直す。

    この文言はTHEMES.yamlのsample_periodと累積正典の件数から作られる。どちらも
    昇格の途中で書き換わるので、build()が組み立てる候補ページには新しい値を
    入れられない。パイロット（refresh_bukatsu_pilot.py）は台帳更新の直後に同じ
    スクリプトを呼んでおり、adapter経由でもその一手を再現する。
    """
    subprocess.run(
        [sys.executable, str(root / "scripts" / "build_bukatsu_arena.py")],
        cwd=root,
        check=True,
    )
