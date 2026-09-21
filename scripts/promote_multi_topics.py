#!/usr/bin/env python3
"""課題59: 複数テーマの更新回を1つの公開候補としてまとめて準備・適用する。

前提: 対象の各テーマについて、あらかじめ
    python3 scripts/refresh_topic.py --topic <topic> --date <date> --resume
まで実行済みで、`.staging/refresh/<topic>/<run-id>/` に
cumulative-candidate.json と report.json が揃っていること。
--prepare-promotion まで進めている必要はない（テーマごとの個別承認候補は作らない）。

同じ日に2テーマ以上を個別に `--prepare-promotion` すると、後から適用した側の
docs/index.html・catalog・sitemap 等の共有ファイルが先に適用した側の新しいデータを
知らないまま作られ、適用した瞬間に合計値が巻き戻ることがある（課題59）。
このスクリプトは、対象テーマ全部の更新を1つの隔離コピーへ先にまとめてから
共有ファイルを1回だけ再生成することでこれを避け、承認後の適用も
「まとめた全テーマ・run-idが揃っているときだけ」に限定する。

使い方（準備。公開候補とmanifestを作るだけで、正典・公開ページは変更しない）:
    python3 scripts/promote_multi_topics.py --date 2026-09-21 \\
        --entry bike-blue-ticket:.staging/refresh/bike-blue-ticket/20260921_090000 \\
        --entry consumption-tax-cut:.staging/refresh/consumption-tax-cut/20260921_091500 \\
        --combined-stage .staging/refresh/multi/20260921_120000 \\
        --prepare

使い方（承認後の適用。--prepare と同じ --entry / --combined-stage / --date を指定する）:
    python3 scripts/promote_multi_topics.py --date 2026-09-21 \\
        --entry bike-blue-ticket:.staging/refresh/bike-blue-ticket/20260921_090000 \\
        --entry consumption-tax-cut:.staging/refresh/consumption-tax-cut/20260921_091500 \\
        --combined-stage .staging/refresh/multi/20260921_120000 \\
        --apply --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import refresh_topic as rt  # noqa: E402


def _parse_entry(raw: str) -> tuple[str, Path]:
    topic, _, stage = raw.partition(":")
    if not topic or not stage:
        raise ValueError(f"--entry は topic:stage_dir の形式で指定してください: {raw!r}")
    return topic, (ROOT / stage).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--entry",
        action="append",
        required=True,
        metavar="TOPIC:STAGE_DIR",
        help="topic:stage_dir の形式。2件以上指定する",
    )
    parser.add_argument("--combined-stage", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true", help="複数テーマ分を1つの公開候補・manifestへまとめる")
    mode.add_argument("--apply", action="store_true", help="準備済みmanifestをハッシュ確認のうえ公開へ反映する")
    parser.add_argument("--backup-dest", type=Path, help="--apply のとき必須。非公開正典の退避先")
    args = parser.parse_args()

    parsed = [_parse_entry(raw) for raw in args.entry]
    if len(parsed) < 2:
        raise ValueError("2テーマ未満なら通常の refresh_topic.py --prepare-promotion で十分です")
    topics = [topic for topic, _ in parsed]
    if len(set(topics)) != len(topics):
        raise ValueError("同じテーマが --entry に重複しています")

    combined_stage = (ROOT / args.combined_stage).resolve() if not args.combined_stage.is_absolute() else args.combined_stage

    if args.prepare:
        themes = rt.parse_themes_yaml(rt.ROOT / "THEMES.yaml")
        pipelines = rt.load_pipeline_config()
        entries = []
        for topic, stage in parsed:
            if topic not in themes:
                raise ValueError(f"未設定のテーマです: {topic}")
            report_path = stage / "report.json"
            if not report_path.is_file():
                raise FileNotFoundError(
                    f"{topic}: report.json がありません。先に --resume で更新回を保存してください: {report_path}"
                )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            theme = themes[topic]
            pipeline = pipelines.get(topic, {})
            adapter_name = pipeline.get("adapter")
            if not adapter_name or theme.get("page_update_mode") != "adapter":
                raise ValueError(f"{topic}: page adapterが無いため複数テーマ公開の対象にできません")
            adapter = rt.load_adapter(adapter_name)
            adapter_targets = adapter.build(rt.ROOT, stage, args.date)
            entries.append(
                {
                    "topic": topic,
                    "run_id": stage.name,
                    "stage": stage,
                    "report": report,
                    "adapter_targets": adapter_targets,
                    "adapter": adapter,
                }
            )
        targets = rt.prepare_public_candidate_bundle_multi(rt.ROOT, entries, args.date, combined_stage)
        manifest = rt.prepare_multi_promotion_manifest(rt.ROOT, entries, args.date, combined_stage, targets)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    if not args.backup_dest:
        raise ValueError("--apply には --backup-dest が必要です")
    expected = [(topic, stage.name) for topic, stage in parsed]
    manifest, targets = rt.load_multi_promotion_manifest(rt.ROOT, combined_stage, expected, args.date)
    rt.apply_manifest_targets(rt.ROOT, combined_stage, targets, args.backup_dest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
