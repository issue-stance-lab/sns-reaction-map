#!/usr/bin/env python3
"""部活動の地域移行の「賛否（stance）」を、現在の判定基準で数え直す（2026-10-06〜）。

2026-09-12に、AIが賛否を判定する基準（コミット e81f86b5。要求の無い問題指摘だけの投稿は「中立・情報」など）を
見直したが、見直し前の回の投稿は数え直していなかった。そのため正典の中で、見直し前の回と後の回で
賛否の物差しが違い、「意見の推移」の立場のグラフに存在しない動きが出た（中立・情報 約3% → 約3割）。

ここでやること:
  prepare … 見直し前の回の「意見」の投稿を、作業用のフォルダへ分けて保存する（正典は変えない）
  run     … 分類器（classify_bukatsu_arena_hermes.py。新しい回と同じ指示文・同じモデル）を並列に回す
  merge   … 結果を1つにまとめ、件数・エラー・モデル設定が途中で変わっていないことを確かめる
  report  … 旧と新の賛否を回ごとに比べた表を出す（本文は出さない）
  apply   … 正典の賛否（stance）だけを、新しい判定に書き換える。他の項目（関連・意見か・論点）は変えない
  record  … 公開してよい記録（件数と指紋だけ。本文・投稿IDなし）を data/verification/rejudge/ に書く

賛否だけを採る理由: 変わったのは賛否の基準だけで、論点や「意見か」の基準は変えていない。
他の項目まで取り込むと、ページの意見の件数・論点の件数・投票・再読記録の対象が全部動く。
正典を書き換えるのは apply だけ。書き換え前の正典は、作業用のフォルダに残す。
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

JST = dt.timezone(dt.timedelta(hours=9))
CLASSIFIER = ROOT / "scripts" / "classify_bukatsu_arena_hermes.py"
DEFAULT_DIR = ROOT / "social-samples" / "updates" / "bukatsu-chiiki" / "rejudge-20261006"
# 賛否の判定基準を見直した後の、最初の収集日（2026-09-12に見直し、その後の最初の収集）。これより前の回を数え直す。
DEFAULT_CUTOFF = "2026-09-15"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collected_day(row: dict) -> str:
    stamp = dt.datetime.fromisoformat(row["fetched_at"].replace("Z", "+00:00"))
    return stamp.astimezone(JST).date().isoformat()


def canonical_path() -> Path:
    import yaml

    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    return ROOT / themes["bukatsu-chiiki"]["sample_file"]


def is_opinion(row: dict) -> bool:
    classification = row.get("classification") or {}
    return bool(classification.get("is_relevant")) and bool(classification.get("is_opinion"))


def select_rows(rows: list[dict], cutoff: str, since: str | None = None) -> list[dict]:
    """数え直す対象: cutoff より前の回（since があれば since 以降）の、関連あり・意見ありの投稿。

    意見でない投稿の賛否は「中立・情報」で固定なので対象外。
    """
    chosen = [row for row in rows if is_opinion(row) and collected_day(row) < cutoff
              and (since is None or collected_day(row) >= since)]
    return sorted(chosen, key=lambda row: (row["fetched_at"], str(row.get("tweet_id"))))


def model_settings() -> dict:
    from refresh_topic import classifier_model  # type: ignore[import-not-found]

    return classifier_model()


def prepare(directory: Path, cutoff: str, shards: int, since: str | None = None) -> dict:
    source = canonical_path()
    rows = json.loads(source.read_text(encoding="utf-8"))
    chosen = select_rows(rows, cutoff, since)
    if not chosen:
        raise ValueError("数え直す投稿がありません")
    if len({str(row.get("tweet_id")) for row in chosen}) != len(chosen):
        raise ValueError("tweet_id が重複しています")
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.glob("in*.json")):
        raise ValueError(f"{directory} には作業中の入力があります。消さずに止めます")
    inputs = []
    for index in range(shards):
        part = chosen[index::shards]
        path = directory / f"in{index}.json"
        path.write_text(json.dumps(part, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inputs.append({"file": path.name, "rows": len(part), "sha256": sha256(path)})
    from refresh_topic import taxonomy_fingerprint  # type: ignore[import-not-found]

    plan = {
        "created_at": dt.datetime.now(JST).isoformat(timespec="seconds"),
        "cutoff": cutoff,
        "since": since,
        "rows": len(chosen),
        "per_round": dict(sorted(collections.Counter(collected_day(row) for row in chosen).items())),
        "canonical_sha256": sha256(source),
        "model": model_settings(),
        "classifier": {
            "script": CLASSIFIER.relative_to(ROOT).as_posix(),
            "script_sha256": sha256(CLASSIFIER),
            "taxonomy_sha256": taxonomy_fingerprint(CLASSIFIER),
        },
        "inputs": inputs,
    }
    (directory / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return plan


def run(directory: Path) -> None:
    """各入力を並列に分類する。途中で止まっても、もう一度 run すれば続きから再開する（--resume）。"""
    plan = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
    if model_settings() != plan["model"]:
        raise RuntimeError(f"分類モデルの設定が準備のときと違います: {plan['model']} → {model_settings()}")
    processes = []
    for item in plan["inputs"]:
        index = item["file"][2:-5]
        log = (directory / f"run{index}.log").open("a", encoding="utf-8")
        processes.append(subprocess.Popen(
            [sys.executable, str(CLASSIFIER), "--input", str(directory / item["file"]),
             "--output", str(directory / f"out{index}.json"), "--markdown", str(directory / f"out{index}.md"), "--resume"],
            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
        ))
    codes = [process.wait() for process in processes]
    if any(codes):
        raise RuntimeError(f"分類が途中で止まりました（終了コード {codes}）。同じコマンドで続きから再開できます")
    if model_settings() != plan["model"]:
        raise RuntimeError("分類の途中でモデルの設定が変わりました。結果を採用せず、確認してください")


def merge(directory: Path) -> list[dict]:
    plan = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
    merged: list[dict] = []
    for item in plan["inputs"]:
        index = item["file"][2:-5]
        expected = json.loads((directory / item["file"]).read_text(encoding="utf-8"))
        out = json.loads((directory / f"out{index}.json").read_text(encoding="utf-8"))
        if [str(row["tweet_id"]) for row in out] != [str(row["tweet_id"]) for row in expected]:
            raise ValueError(f"{item['file']}: 結果の投稿が入力と一致しません（{len(out)}/{len(expected)}件）")
        merged.extend(out)
    errors = [row["tweet_id"] for row in merged if row["classification"].get("error")]
    if errors:
        raise ValueError(f"分類できなかった投稿が{len(errors)}件あります（提供元の拒否など）。扱いを決めるまで採用しません: {errors[:5]}")
    if model_settings() != plan["model"]:
        raise ValueError("モデルの設定が準備のときと違います")
    (directory / "rejudged.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return merged


def compare(rows: list[dict], rejudged: list[dict]) -> dict:
    """旧と新の賛否を、回ごとに比べる（件数だけ。本文は含めない）。"""
    old = {str(row["tweet_id"]): row for row in rows}
    labels = ["移行支持", "条件付き・改善要求", "慎重・反対", "中立・情報"]
    per_round: dict[str, dict] = {}
    changes: collections.Counter = collections.Counter()
    for row in rejudged:
        key = str(row["tweet_id"])
        before = old[key]["classification"]["stance"]
        after = row["classification"]["stance"]
        day = collected_day(row)
        slot = per_round.setdefault(day, {"n": 0, "old": collections.Counter(), "new": collections.Counter(), "same": 0})
        slot["n"] += 1
        slot["old"][before] += 1
        slot["new"][after] += 1
        slot["same"] += before == after
        if before != after:
            changes[(before, after)] += 1
    total = sum(slot["n"] for slot in per_round.values())
    same = sum(slot["same"] for slot in per_round.values())
    return {
        "labels": labels,
        "rows": total,
        "same": same,
        "per_round": {
            day: {"n": slot["n"], "same": slot["same"],
                  "old": [slot["old"][label] for label in labels], "new": [slot["new"][label] for label in labels]}
            for day, slot in sorted(per_round.items())
        },
        "changes": {f"{a}→{b}": n for (a, b), n in changes.most_common()},
    }


def apply(directory: Path) -> dict:
    """正典の賛否（stance）だけを、新しい判定に書き換える。書き換え前の正典は作業用フォルダに残す。"""
    plan = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
    source = canonical_path()
    if sha256(source) != plan["canonical_sha256"]:
        raise ValueError("正典が準備のあとで変わっています。数え直しの対象がずれるので、準備からやり直してください")
    rows = json.loads(source.read_text(encoding="utf-8"))
    rejudged = {str(row["tweet_id"]): row["classification"] for row in json.loads((directory / "rejudged.json").read_text(encoding="utf-8"))}
    backup = directory / "canonical-before.json"
    if backup.exists():
        raise ValueError(f"{backup} がすでにあります。二重に適用しないため止めます")
    # 先に全件を確かめてから書く（途中で止まって、書き換えと控えが半端に残らないように）。
    changes = []
    for row in rows:
        key = str(row.get("tweet_id"))
        if key not in rejudged:
            continue
        if (not is_opinion(row) or collected_day(row) >= plan["cutoff"]
                or (plan.get("since") and collected_day(row) < plan["since"])):
            raise ValueError(f"対象外の投稿が混ざっています: {key}")
        if row["classification"]["stance"] != rejudged[key]["stance"]:
            changes.append((row, rejudged[key]["stance"]))
    backup.write_bytes(source.read_bytes())
    for row, stance in changes:
        row["classification"]["stance"] = stance
    source.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"rows": len(rejudged), "changed": len(changes)}


PUBLIC_RECORD = ROOT / "data" / "verification" / "rejudge" / "bukatsu-chiiki-stance-20261006.json"


def public_record(directories: list[Path]) -> dict:
    """数え直しの公開記録。件数・回ごとの旧新の割合・指紋だけで、本文・URL・投稿IDは含めない。"""
    runs = []
    for directory in directories:
        plan = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
        before = json.loads((directory / "canonical-before.json").read_text(encoding="utf-8"))
        rejudged = json.loads((directory / "rejudged.json").read_text(encoding="utf-8"))
        result = compare(before, rejudged)
        runs.append({
            "name": directory.name,
            "created_at": plan["created_at"],
            "since": plan.get("since"),
            "cutoff": plan["cutoff"],
            "rows": plan["rows"],
            "same_stance": result["same"],
            "labels": result["labels"],
            "per_round": result["per_round"],
            "changes": result["changes"],
            "model": plan["model"],
            "classifier": plan["classifier"],
            "canonical_sha256_before": sha256(directory / "canonical-before.json"),
            "inputs_sha256": [item["sha256"] for item in plan["inputs"]],
        })
    return {
        "schema_version": 1,
        "topic": "bukatsu-chiiki",
        "purpose": "2026-09-12の賛否の判定基準の見直しより前の回の賛否を、現在の指示文・モデルで判定し直した記録。"
                   "正典で書き換えたのは賛否（stance）だけ。関連・意見か・論点は変えていない。",
        "runs": runs,
        "canonical_sha256_after": sha256(canonical_path()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["prepare", "run", "merge", "report", "apply", "record"])
    parser.add_argument("--dir", type=Path, action="append", help="作業用フォルダ（record では複数指定できる）")
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    parser.add_argument("--since", help="この日以降の回だけを対象にする（2回目の追加判定用）")
    parser.add_argument("--shards", type=int, default=4)
    args = parser.parse_args()
    dirs = args.dir or [DEFAULT_DIR]
    args.dir = dirs[0]
    if args.command == "prepare":
        plan = prepare(args.dir, args.cutoff, args.shards, args.since)
        print(json.dumps({key: plan[key] for key in ("rows", "per_round", "model", "inputs")}, ensure_ascii=False, indent=2))
    elif args.command == "run":
        run(args.dir)
        print("分類が終わりました。次は merge")
    elif args.command == "merge":
        merged = merge(args.dir)
        print(f"{len(merged)}件をまとめました: {args.dir / 'rejudged.json'}")
    elif args.command == "report":
        rows = json.loads(canonical_path().read_text(encoding="utf-8"))
        merged = json.loads((args.dir / "rejudged.json").read_text(encoding="utf-8"))
        print(json.dumps(compare(rows, merged), ensure_ascii=False, indent=2))
    elif args.command == "record":
        PUBLIC_RECORD.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC_RECORD.write_text(json.dumps(public_record(dirs), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"書きました: {PUBLIC_RECORD}")
    else:
        print(json.dumps(apply(args.dir), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
