#!/usr/bin/env python3
"""収集回ごとの記録に「どのモデルで・どの基準で・どの入力から」が残っているか確かめる。

## なぜ要るか

投稿ごとには「いつ・どの検索語で・どこから」が残っていた。回の単位には残っていなかった。
2026-09-06、`~/.hermes/config.yaml` の `model.default` が誰にも気づかれないまま
別モデルへ替わっていたことが分かった。分類モデルを替えると賛否の構成比は最大4pt動く
（DATA_REFRESH.md、2026-08-18 の実測）。潮目が拾う変化と同じ大きさなので、
記録が無いと「世論が動いた」のか「モデルが変わった」のか永久に区別できない。

指示文に「モデルを記録すること」と書いても、別セッションでは破られる。検査だけが残る。

## 何を見るか

`data/verification/updates/{テーマ}/{日付}/report.json`（公開側の回ごとの記録）に
`provenance` があり、次がそろっているか。

- `model.name`（分類モデル名）— 分類した回だけ。新規0件の回は分類していないので null
- `classifier.script_sha256` / `classifier.taxonomy_sha256`（プロンプト・分類基準の版）
- `input.raw_sha256`（入力の指紋）
- `sources`（回の単位での取得元）

あわせて、非公開の正典側（`social-samples/updates/...`）が手元にある回は、
投稿ごとの必須項目（`fetched_at` / `query` / `source`）がそろっているかも見る。
自転車の青切符の116件は「欠けたまま通ってしまった」から生まれた。

## いつの回から必須か

`REQUIRED_FROM` 以降の回だけ。**それより前の回はさかのぼって埋めない。**
古い回に推測でモデル名を書くと、記録が記録でなくなる。「不明」は不明のまま残す。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_UPDATES = ROOT / "data" / "verification" / "updates"
PRIVATE_UPDATES = ROOT / "social-samples" / "updates"

# この日付以降の収集回から provenance を必須にする。
# 課題63 段階B（2026-09-06）で記録項目を足した。それ以前の回には無い。
REQUIRED_FROM = "2026-09-07"

RECORD_REQUIRED_FIELDS = ("fetched_at", "query", "source")


def _missing_provenance(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    provenance = report.get("provenance")
    if not isinstance(provenance, dict):
        return ["provenance がありません"]

    classifier = provenance.get("classifier")
    if not isinstance(classifier, dict):
        problems.append("provenance.classifier がありません")
    else:
        for key in ("script", "script_sha256", "taxonomy_sha256"):
            if not str(classifier.get(key) or "").strip():
                problems.append(f"provenance.classifier.{key} がありません")

    source = provenance.get("input")
    if not isinstance(source, dict) or not str(source.get("raw_sha256") or "").strip():
        problems.append("provenance.input.raw_sha256 がありません")

    sources = provenance.get("sources")
    raw_records = int((source or {}).get("raw_records", 0) or 0) if isinstance(source, dict) else 0
    if not isinstance(sources, dict):
        problems.append("provenance.sources がありません")
    elif raw_records and not sources:
        # 1件も取れなかった回は取得元も空になる。空が正しい回まで落とさない。
        problems.append("provenance.sources が空です（投稿を取得した回）")

    # 分類した回だけモデル名を要る。新規0件の回は分類していない。
    classified = int(report.get("new", 0) or 0) > 0
    model = provenance.get("model")
    if classified:
        if not isinstance(model, dict) or not str(model.get("name") or "").strip():
            problems.append("provenance.model.name がありません（分類した回）")
    elif model is not None:
        problems.append("新規0件の回に model が入っています（走っていない分類のモデル名は書かない）")
    return problems


def _missing_record_fields(path: Path) -> list[str]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{path.relative_to(ROOT)} を読めません: {error}"]
    if not isinstance(rows, list):
        return [f"{path.relative_to(ROOT)} が配列ではありません"]
    missing: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field in RECORD_REQUIRED_FIELDS:
            value = row.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing[field] = missing.get(field, 0) + 1
    return [
        f"投稿ごとの必須項目が欠けています: " + " / ".join(f"{k} {v}件" for k, v in sorted(missing.items()))
    ] if missing else []


def check(
    public_root: Path = PUBLIC_UPDATES,
    private_root: Path = PRIVATE_UPDATES,
    required_from: str = REQUIRED_FROM,
) -> list[str]:
    failures: list[str] = []
    if not public_root.exists():
        return failures
    for report_path in sorted(public_root.glob("*/*/report.json")):
        date = report_path.parent.name
        topic = report_path.parent.parent.name
        if date < required_from:
            continue
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"{topic} {date}: report.json を読めません: {error}")
            continue
        if not isinstance(report, dict):
            failures.append(f"{topic} {date}: report.json がJSONオブジェクトではありません")
            continue
        for problem in _missing_provenance(report):
            failures.append(f"{topic} {date}: {problem}")

        private_raw = private_root / topic / date / "raw.json"
        if private_raw.exists():
            for problem in _missing_record_fields(private_raw):
                failures.append(f"{topic} {date}: {problem}")
    return failures


def main() -> int:
    # 既定値を呼び出し時に読む。def の既定引数に束ねるとテストから差し替えられない。
    failures = check(PUBLIC_UPDATES, PRIVATE_UPDATES, REQUIRED_FROM)
    for failure in failures:
        print(f"NG {failure}")
    print(f"NG {len(failures)}件")
    if failures:
        return 1
    print("OK 収集回ごとの出所（モデル・基準の版・入力の指紋・取得元）はそろっています")
    return 0


if __name__ == "__main__":
    sys.exit(main())
