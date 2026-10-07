#!/usr/bin/env python3
"""生成AIと著作権の、ある収集回の判定を、現在のAI・指示文で判定し直した結果で置き換える（2026-10-07〜）。

背景: 2026-09-05の回だけ、分類の傾向が他の回と違った。「関連あり」が92.8%（他の回は74〜81%）、
中立・情報が35.1%（他の回は20〜30%）、要約の長さは約2倍。分類の指示文は2026-08-07から変わっていないので、
分類したAIが他の回と違った可能性が高い（ログでは2026-09-03〜06に、Hermesの既定が別のモデルだった形跡がある）。
同じ458件を現行のAI（kimi-k2.7-code）で分類し直すと、関連率74.2%・中立・情報22.3%と、前後の回と同じ水準に戻った。

ここでやること（正典を書き換えるのは apply だけ。--dry-run なら何も書かず、結果だけ表示する）:
  1. 検証 … 結果が、正典のその回の投稿と過不足なく対応し（tweet_id・本文の指紋）、エラーが無く、
            分類モデルの設定が想定どおりであること
  2. 退避 … 置き換え前の正典と再読の記録、分類の入力・出力を、作業用のフォルダ（非公開）へ残す
  3. 置き換え … その回の投稿の判定（関連・意見か・論点・立場・要約など）を新しい判定にする
  4. 再読の記録 … 意見でなくなった、または論点が変わった投稿を、再読の記録から外す（読み直しはしない。
            外した投稿は「新しい判定のもとでは読んでいない」ので未読として数える）
  5. 記録 … 公開してよい記録（件数と指紋だけ。本文・投稿IDなし）を data/verification/rejudge/ に書く

元の保存回（social-samples/updates/ai-copyright/{日付}/）は書き換えない。記録の無い旧回を後から「確認済み」にしない。
"""

from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

JST = dt.timezone(dt.timedelta(hours=9))
TOPIC = "ai-copyright"
CLASSIFIER = ROOT / "scripts" / "classify_aicopyright_arena_hermes.py"
REREAD = ROOT / "data" / "ai-copyright_issues-reread.json"
RECORD_DIR = ROOT / "data" / "verification" / "rejudge"
# 再読の記録のキーと、その論点名（scripts/ai_copyright_taxonomy.py のラベル）
REREAD_ISSUES = {
    "learning_data": "学習データ・無断利用",
    "creator_rights": "クリエイター保護・権利",
    "other": "その他",
    "generated_work_rights": "AI生成物の権利・創作性",
    "tech_promotion": "技術競争・推進",
}
EXPECTED_MODEL = "kimi-k2.7-code"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def text_sha256(row: dict) -> str:
    return sha256_bytes(str(row.get("text") or "").encode("utf-8"))


def canonical_path() -> Path:
    import yaml

    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    return ROOT / themes[TOPIC]["sample_file"]


def collected_day(row: dict) -> str:
    stamp = dt.datetime.fromisoformat(row["fetched_at"].replace("Z", "+00:00"))
    return stamp.astimezone(JST).date().isoformat()


def is_opinion(classification: dict) -> bool:
    return bool(classification.get("is_relevant")) and bool(classification.get("is_opinion"))


def dump_json(value) -> str:
    """正典・再読の記録と同じ書式（字下げ2・日本語そのまま・末尾に改行）。"""
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def model_settings() -> dict:
    from refresh_topic import classifier_model  # type: ignore[import-not-found]

    return classifier_model()


# ------------------------------------------------------------------ 検証

def verify(rows: list[dict], redone: list[dict], date: str) -> list[dict]:
    """置き換える回の投稿を返す。結果が正典と過不足なく対応しなければ止める。"""
    wave = [row for row in rows if collected_day(row) == date]
    if not wave:
        raise ValueError(f"正典に{date}の回の投稿がありません")
    ids = [str(row["tweet_id"]) for row in wave]
    if len(set(ids)) != len(ids):
        raise ValueError("正典の中で tweet_id が重複しています")
    redone_ids = [str(row.get("tweet_id")) for row in redone]
    if len(set(redone_ids)) != len(redone_ids):
        raise ValueError("分類し直した結果の中で tweet_id が重複しています")
    missing, extra = set(ids) - set(redone_ids), set(redone_ids) - set(ids)
    if missing or extra:
        raise ValueError(f"分類し直した結果と正典の回が対応しません（結果に無い{len(missing)}件・余分{len(extra)}件）")
    errors = [row for row in redone if (row.get("classification") or {}).get("error")]
    if errors:
        raise ValueError(f"分類し直した結果に、提供元の拒否・エラーが{len(errors)}件あります。本文を読んで扱いを決めてから進めてください")
    by_id = {str(row["tweet_id"]): row for row in wave}
    mismatched = [row["tweet_id"] for row in redone if text_sha256(row) != text_sha256(by_id[str(row["tweet_id"])])]
    if mismatched:
        raise ValueError(f"本文が正典と一致しない投稿が{len(mismatched)}件あります")
    for row in redone:
        classification = row.get("classification") or {}
        for key in ("is_relevant", "is_opinion", "main_issue", "stance", "confidence"):
            if key not in classification:
                raise ValueError(f"分類し直した結果に {key} が無い投稿があります")
    return wave


# ------------------------------------------------------------------ 置き換え

def replace(rows: list[dict], redone: list[dict], date: str) -> list[dict]:
    new = {str(row["tweet_id"]): row["classification"] for row in redone}
    out = []
    for row in rows:
        row = copy.deepcopy(row)
        if collected_day(row) == date:
            row["classification"] = copy.deepcopy(new[str(row["tweet_id"])])
        out.append(row)
    return out


def summarize(before: list[dict], after: list[dict]) -> dict:
    """置き換え前後の、その回の件数と変化（本文・IDは含めない）。"""
    pairs = list(zip(before, after))
    kept = [(b, a) for b, a in pairs if is_opinion(b["classification"]) and is_opinion(a["classification"])]
    stance_moves = collections.Counter(
        f"{b['classification']['stance']}→{a['classification']['stance']}"
        for b, a in kept if b["classification"]["stance"] != a["classification"]["stance"]
    )
    issue_moves = collections.Counter(
        f"{b['classification']['main_issue']}→{a['classification']['main_issue']}"
        for b, a in kept if b["classification"]["main_issue"] != a["classification"]["main_issue"]
    )
    return {
        "rows": len(pairs),
        "relevant_before": sum(1 for b, _ in pairs if b["classification"].get("is_relevant")),
        "relevant_after": sum(1 for _, a in pairs if a["classification"].get("is_relevant")),
        "opinions_before": sum(1 for b, _ in pairs if is_opinion(b["classification"])),
        "opinions_after": sum(1 for _, a in pairs if is_opinion(a["classification"])),
        "opinion_lost": sum(1 for b, a in pairs if is_opinion(b["classification"]) and not is_opinion(a["classification"])),
        "opinion_gained": sum(1 for b, a in pairs if not is_opinion(b["classification"]) and is_opinion(a["classification"])),
        "kept_opinions": len(kept),
        "stance_changed": sum(stance_moves.values()),
        "issue_changed": sum(issue_moves.values()),
        "stance_moves": dict(sorted(stance_moves.items(), key=lambda kv: -kv[1])),
        "issue_moves": dict(sorted(issue_moves.items(), key=lambda kv: -kv[1])),
    }


# ------------------------------------------------------------------ 再読の記録

def prune_reread(reread: dict, rows_after: list[dict], date: str) -> tuple[dict, dict[str, list[str]]]:
    """意見でなくなった、または論点が変わった投稿を、再読の記録から外す。外した投稿IDを論点ごとに返す。"""
    after = {str(row["tweet_id"]): row["classification"] for row in rows_after}
    # 外すのは、置き換えた回の投稿だけ。ほかの回の記録は、何かの食い違いがあっても黙って外さない。
    wave_ids = {str(row["tweet_id"]) for row in rows_after if collected_day(row) == date}
    reread = copy.deepcopy(reread)
    removed: dict[str, list[str]] = {}
    for key, label in REREAD_ISSUES.items():
        block = reread[key]
        keep, gone = [], []
        for item in block["items"]:
            tweet_id = str(item["tweet_id"])
            classification = after.get(tweet_id)
            still_valid = classification is not None and is_opinion(classification) and classification["main_issue"] == label
            if tweet_id in wave_ids and not still_valid:
                gone.append(item)
            else:
                keep.append(item)
        if not gone:
            continue
        for item in gone:
            block["buckets"][item["bucket"]]["count"] -= 1
        empty = [bucket for bucket, value in block["buckets"].items() if value["count"] <= 0]
        if empty:
            raise ValueError(f"{label}: 区分{empty}が0件になります。区分の扱い（残す・統合）を決めてから進めてください")
        block["items"] = keep
        removed[label] = [str(item["tweet_id"]) for item in gone]
    if removed:
        history = reread.setdefault("removed_after_read", [])
        history.append({
            "date": dt.datetime.now(JST).date().isoformat(),
            "wave": date,
            "count": sum(len(ids) for ids in removed.values()),
            "per_issue": {label: len(ids) for label, ids in removed.items()},
            "reason": f"{date}の回の判定を現在のAIで判定し直した結果、意見でなくなった、または論点が変わった投稿。"
                      "新しい判定のもとでは読んでいないため、読了の記録から外した（読み直しはしていない）。",
        })
    return reread, removed


# ------------------------------------------------------------------ 実行

def apply(date: str, redone_path: Path, input_path: Path, directory: Path, expected_model: str, dry_run: bool) -> dict:
    source = canonical_path()
    rows = json.loads(source.read_text(encoding="utf-8"))
    redone = json.loads(redone_path.read_text(encoding="utf-8"))
    wave = verify(rows, redone, date)
    model = model_settings()
    if model.get("name") != expected_model:
        raise RuntimeError(f"分類モデルの設定が想定と違います: {model.get('name')}（想定 {expected_model}）")
    new_rows = replace(rows, redone, date)
    new_wave = [row for row in new_rows if collected_day(row) == date]
    stats = summarize(wave, new_wave)
    reread = json.loads(REREAD.read_text(encoding="utf-8"))
    new_reread, removed = prune_reread(reread, new_rows, date)
    stats["reread_removed"] = {label: len(ids) for label, ids in removed.items()}
    if stats["opinion_lost"] == 0 and stats["opinion_gained"] == 0 and stats["stance_changed"] == 0 and stats["issue_changed"] == 0:
        raise ValueError("置き換えても変わる判定がありません。すでに適用済みの可能性があります")
    if dry_run:
        return stats

    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "canonical-before.json").exists():
        raise FileExistsError(f"{directory} には退避ずみのファイルがあります。消さずに止めます")
    shutil.copy2(source, directory / "canonical-before.json")
    shutil.copy2(REREAD, directory / "reread-before.json")
    shutil.copy2(redone_path, directory / "redone.json")
    shutil.copy2(input_path, directory / "redone-input.json")
    (directory / "reread-removed-ids.json").write_text(dump_json(removed), encoding="utf-8")

    before_sha = sha256_file(source)
    source.write_text(dump_json(new_rows), encoding="utf-8")
    REREAD.write_text(dump_json(new_reread), encoding="utf-8")

    from refresh_topic import taxonomy_fingerprint  # type: ignore[import-not-found]

    today = dt.datetime.now(JST).date().isoformat().replace("-", "")
    record_path = RECORD_DIR / f"ai-copyright-wave-{date.replace('-', '')}-rejudge-{today}.json"
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": 1,
        "topic": TOPIC,
        "purpose": f"{date}の回だけ、分類の傾向が他の回と違った（関連あり・中立・情報・要約の長さ）ため、"
                   "現在の指示文・同じモデルで判定し直し、その回の判定を置き換えた記録。本文・投稿IDは含まない。",
        "run": {
            "wave": date,
            "created_at": dt.datetime.now(JST).isoformat(timespec="seconds"),
            "model": model,
            "classifier": {
                "script": CLASSIFIER.relative_to(ROOT).as_posix(),
                "script_sha256": sha256_file(CLASSIFIER),
                "taxonomy_sha256": taxonomy_fingerprint(CLASSIFIER),
            },
            "input_sha256": sha256_file(input_path),
            "output_sha256": sha256_file(redone_path),
            "canonical_sha256_before": before_sha,
            "canonical_sha256_after": sha256_file(source),
            **stats,
        },
    }
    record_path.write_text(dump_json(record), encoding="utf-8")
    try:
        stats["record"] = record_path.relative_to(ROOT).as_posix()
    except ValueError:  # 作業場所の外へ書いたとき（テスト）
        stats["record"] = str(record_path)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", required=True, help="置き換える回の収集日（日本時間、例: 2026-09-05）")
    parser.add_argument("--redone", type=Path, required=True, help="現行のAIで分類し直した結果（classify_aicopyright_arena_hermes.py の出力）")
    parser.add_argument("--input", type=Path, required=True, help="分類し直したときの入力（本文つき。出所の指紋を残す）")
    parser.add_argument("--dir", type=Path, help="退避先（省略時は social-samples/updates/ai-copyright/rejudge-{今日}）")
    parser.add_argument("--expect-model", default=EXPECTED_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="何も書かず、置き換えた場合の件数だけ表示する")
    args = parser.parse_args()
    today = dt.datetime.now(JST).date().isoformat().replace("-", "")
    directory = args.dir or ROOT / "social-samples" / "updates" / TOPIC / f"rejudge-{today}"
    stats = apply(args.date, args.redone, args.input, directory, args.expect_model, args.dry_run)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print("（--dry-run: 何も書き換えていません）" if args.dry_run else "置き換えました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
