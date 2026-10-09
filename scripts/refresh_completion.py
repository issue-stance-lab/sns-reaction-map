"""Require editorial evidence for this wave, separately from historical coverage.

Preparing a template never marks a post as read. Evidence uses the existing
reread review schema; this receipt binds it to the final candidate (including
stance) without requiring a migration or rereading of unchanged history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

try:
    from .reread_registry import _validate_review, snapshot_records
    from .public_registry_common import is_opinion_record
    from .sync_portal_stats import parse_themes_yaml
except ImportError:
    from reread_registry import _validate_review, snapshot_records
    from public_registry_common import is_opinion_record
    from sync_portal_stats import parse_themes_yaml


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def indexed(rows):
    result = {}
    for row in rows:
        if not row.get("tweet_id") or not isinstance(row.get("text"), str):
            raise ValueError("完了確認には投稿IDと本文が必要です")
        key = hashlib.sha256(str(row["tweet_id"]).encode()).hexdigest()
        if key in result:
            raise ValueError("完了確認の対象に投稿IDの重複があります")
        result[key] = row
    return result


def body_hash(row):
    return hashlib.sha256(row["text"].encode()).hexdigest()


def judgment(row):
    return (row["text"], row.get("classification"), row.get("is_opinion"), row.get("is_relevant"))


def baseline_path(root, topic):
    return root / str(parse_themes_yaml(root / "THEMES.yaml")[topic]["sample_file"])


def targets(before, after, wave):
    if before.keys() - after.keys():
        raise ValueError("収集済み投稿を候補から削除できません。意見外として記録してください")
    missing = wave.keys() - after.keys()
    if missing:
        raise ValueError(f"今回分が候補から欠落・保留しています: {len(missing)}件")
    if any(body_hash(after[key]) != digest for key, digest in wave.items()):
        raise ValueError("今回分の本文が収集原本と一致しません")
    return set(wave) | {key for key, row in after.items()
                        if key not in before or judgment(row) != judgment(before[key])}


def template(root, topic, stage):
    before = baseline_path(root, topic)
    candidate = stage / "cumulative-candidate.json"
    wave = {key: body_hash(row) for key, row in indexed(read(stage / "new-only.json")).items()}
    after = indexed(read(candidate))
    selected = targets(indexed(read(before)), after, wave)
    return {"schema_version": 1, "topic": topic, "baseline_sha256": sha(before),
            "candidate_sha256": sha(candidate), "wave": wave,
            "records": [{"post_key": key, "review": None} for key in sorted(selected)]}


def reason_members(root, topic, rows, selected, issues, overrides):
    # Reuse the same membership/count checks as the page generator.
    try:
        from . import build_planet_data as bpd
    except ImportError:
        import build_planet_data as bpd
    cfg_path = root / "configs/planet" / f"{topic}.yaml"
    if not cfg_path.is_file():
        raise ValueError(f"理由分類の設定がありません: {topic}")
    cfg = yaml.safe_load(cfg_path.read_text())
    result = {}
    for issue, sc in (cfg.get("sub_issues") or {}).items():
        if issue not in issues:
            continue
        data = read(overrides.get(Path(sc["file"]), root / sc["file"]))
        buckets = bpd.dig(data, sc["path"])
        records = bpd.dig(data, sc.get("items_path", sc["path"][:-1] + ["items"]))
        if sc.get("item_issue_field"):
            records = [r for r in records if r.get(sc["item_issue_field"]) == issue]
        records = bpd.resolve_reread_keys(records, rows, issue)
        current = {str(r["tweet_id"]): r for key, r in indexed(rows).items() if key in selected}
        for record in records:
            row = current.get(str(record["tweet_id"]))
            if row is not None and record.get("text_sha256") != body_hash(row):
                raise ValueError("今回分の理由記録に現在の本文指紋がありません")
            if row is not None and "stance" in record and record["stance"] != row["classification"]["stance"]:
                raise ValueError("今回分の理由記録の賛否が候補と一致しません")
        members = bpd.validate_reread_records(records, buckets, rows, issue,
                                             sum(is_opinion_record(r) and
                                                 (r.get("classification") or {}).get("main_issue") == issue
                                                 for r in rows))
        parent = bpd.dig(data, sc["path"][:-1])
        excluded = bpd.dig(data, sc.get("excluded_items_path", sc["path"][:-1] + ["excluded_items"])) \
            if "excluded_items" in parent else []
        members |= bpd.validate_excluded_reread_records(excluded, rows, issue, members)
        result[issue] = members
    return result


def validate(root, topic, candidate, proof, overrides=None, wave_path=None):
    overrides = overrides or {}
    evidence = read(proof)
    if set(evidence) != {"schema_version", "topic", "baseline_sha256", "candidate_sha256", "wave", "records"}:
        raise ValueError("完了記録に未定義の項目があります。本文・投稿IDを保存しないでください")
    if evidence.get("schema_version") != 1 or evidence.get("topic") != topic:
        raise ValueError("今回分の完了記録の形式・テーマが一致しません")
    before = baseline_path(root, topic)
    if evidence.get("baseline_sha256") != sha(before) or evidence.get("candidate_sha256") != sha(candidate):
        raise ValueError("原本・候補が完了記録の作成後に変わりました。確認し直してください")
    wave = evidence.get("wave")
    if not isinstance(wave, dict):
        raise ValueError("今回の収集対象が完了記録にありません")
    if any(not isinstance(value, str) or len(value) != 64 or
           any(c not in "0123456789abcdef" for c in value) for pair in wave.items() for value in pair):
        raise ValueError("今回の収集対象には本文を含めず指紋を保存してください")
    if wave_path is not None:
        expected = {key: body_hash(row) for key, row in indexed(read(wave_path)).items()}
        if wave != expected:
            raise ValueError("完了記録の対象が今回の収集分と一致しません")
    rows = read(candidate)
    after = indexed(rows)
    selected = targets(indexed(read(before)), after, wave)
    records = evidence.get("records", [])
    if not isinstance(records, list) or any(not isinstance(r, dict) or set(r) != {"post_key", "review"} for r in records):
        raise ValueError("完了記録の投稿別項目が不正です")
    by_key = {r["post_key"]: r for r in records}
    if len(by_key) != len(records) or set(by_key) != selected:
        raise ValueError("完了記録が今回の追加・変更分と一致しません")
    opinions = []
    for key in sorted(selected):
        row = after[key]
        snapshot_records([row])  # Old invalid rows outside this wave are not silently reclassified.
        review = by_key[key].get("review")
        if not review:
            raise ValueError(f"今回分に本文確認の未完了があります: {key[:12]}")
        _validate_review(review)
        if review["evidence_quality"] != "verified" or review["text_sha256"] != body_hash(row):
            raise ValueError("今回分に本文と対応しない読了記録があります")
        source = Path(review["source_file"])
        if source.is_absolute() or ".." in source.parts or source.parts[:2] not in {
                ("data", "verification"), ("quality", "reviews")}:
            raise ValueError("読了の出所は data/verification または quality/reviews に保存してください")
        source_path = overrides.get(source, root / source)
        if not source_path.resolve().is_relative_to(root.resolve()):
            raise ValueError("読了記録の出所がリポジトリ外です")
        if sha(source_path) != review["source_sha256"]:
            raise ValueError("読了記録の出所が変更されています")
        if is_opinion_record(row):
            c = row.get("classification") or {}
            if not c.get("main_issue") or not c.get("stance") or c.get("error"):
                raise ValueError("今回分に論点・賛否の未確定があります")
            opinions.append(row)
    members = reason_members(root, topic, rows, selected,
                             {r["classification"]["main_issue"] for r in opinions}, overrides)
    unfinished = [r for r in opinions if r["classification"]["main_issue"] in members
                  and str(r["tweet_id"]) not in members[r["classification"]["main_issue"]]]
    if unfinished:
        raise ValueError(f"今回分に理由分類・記録への反映の未完了があります: {len(unfinished)}件")
    return evidence


def prepare_targets(root, topic, stage, overrides):
    proof = stage / "editorial-completion.json"
    if not proof.is_file():
        raise ValueError("今回分の完了記録がありません。refresh_completion.py prepare/check を実行してください")
    validate(root, topic, stage / "cumulative-candidate.json", proof, overrides, stage / "new-only.json")
    return {**overrides, Path("data/verification/refresh-completion") / topic / f"{stage.name}.json": proof}


def validate_application(root, staged):
    if not (root / "THEMES.yaml").is_file():
        return  # Page-only utility calls have no collection candidate.
    for topic, theme in parse_themes_yaml(root / "THEMES.yaml").items():
        canonical = Path(str(theme.get("sample_file", "")))
        if canonical not in staged:
            continue
        prefix = Path("data/verification/refresh-completion") / topic
        proofs = [source for target, source in staged.items() if target.parent == prefix]
        if len(proofs) != 1:
            raise ValueError(f"{topic}: 今回分の完了記録が公開候補にありません")
        validate(root, topic, staged[canonical], proofs[0], staged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "check"])
    parser.add_argument("--topic", required=True)
    parser.add_argument("--stage", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    stage = args.stage.resolve()
    proof = stage / "editorial-completion.json"
    if args.command == "prepare":
        if proof.exists():
            raise ValueError("完了記録を上書きしません。既存の証拠を保全してから作り直してください")
        value = template(root, args.topic, stage)
        proof.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        print(f"未確認のひな形を保存: {proof}（読了扱いにはしていません）")
    else:
        validate(root, args.topic, stage / "cumulative-candidate.json", proof,
                 wave_path=stage / "new-only.json")
        print("OK: 今回分の本文確認・採否・必要な理由分類の記録が揃っています")


if __name__ == "__main__":
    main()
