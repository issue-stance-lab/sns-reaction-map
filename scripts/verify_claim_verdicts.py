#!/usr/bin/env python3
"""一次資料照合の内部判定語と、主張ごとの投稿件数の出所を検査する。

件数は3か所に現れる。人が確定した正典 `data/{theme}_claim_posts.json`、ページ生成時に
書き出す写し `data/verification/{theme}-claims.json`、公開JSONの `matched_post_count`。
片方だけ更新すると、ページと公開JSONで違う数字が出る（AdSense3回目の不承認と同じ壊れ方）。
"""
from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"fact", "gap", "miss"}
LEGACY_CONSTITUTIONAL = {
    "原典にある": "fact",
    "原典とずれる": "gap",
    "原典にたどり着けず": "miss",
}
SOURCES = {
    "bike-blue-ticket": ("scripts/build_bike_process_sections.py", "FACT_CHECKS"),
    "bukatsu-chiiki": ("scripts/build_bukatsu_process_sections.py", "FACT_CHECKS"),
    "constitutional-amendment": ("scripts/build_constitutional_process_sections.py", "FACT_CHECKS"),
    "consumption-tax-cut": ("scripts/build_consumption_tax_page.py", "CLAIM_AUDIT"),
    "elderly-license-revocation": ("scripts/build_elderly_process_sections.py", "FACT_CHECKS"),
    "fukushuto": ("scripts/build_fukushuto_process_sections.py", "FACT_CHECKS"),
    "koshitsu-tenpakai": ("scripts/build_koshitsu_process_sections.py", "FACT_CHECKS"),
}


def read_literal(path: Path, variable: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f"{path}: {variable} がリテラルとして見つかりません")


def read_checks(path: Path, variable: str) -> list[dict]:
    value = read_literal(path, variable)
    if isinstance(value, list):
        return value
    raise ValueError(f"{path}: {variable} がリテラルのリストではありません")


def canonical_claim_counts(theme: str) -> dict[str, int]:
    """人が確定した投稿IDの正典から、主張ごとの件数を数える。

    テーマごとに形式が3種類ある。どれかを覚えて判断せず、読んだ構造で分岐する。

    - {"claims": {主張: [id, ...]}}                     自転車・消費税・高齢者・副首都
    - {"claims": [{"id": 主張, "tweet_ids": [...]}, ...]} 憲法
    - {主張: {"tweet_ids": [...]}}                       皇室典範
    """
    raw = json.loads(claim_posts_path(theme).read_text(encoding="utf-8"))
    claims = raw.get("claims")
    if isinstance(claims, dict):
        return {key: len(ids) for key, ids in claims.items()}
    if isinstance(claims, list):
        return {item["id"]: len(item["tweet_ids"]) for item in claims}
    return {
        key: len(value["tweet_ids"])
        for key, value in raw.items()
        if isinstance(value, dict) and "tweet_ids" in value
    }


def claim_posts_path(theme: str) -> Path:
    return ROOT / "data" / f"{theme}_claim_posts.json"


def audit_legacy_words() -> list[str]:
    """確定データに旧語彙が残っていないか見る（段階1で憲法の1ファイルだけ残っていた）。"""
    errors = []
    for theme in SOURCES:
        text = claim_posts_path(theme).read_text(encoding="utf-8")
        found = sorted(word for word in LEGACY_CONSTITUTIONAL if f'"{word}"' in text)
        if found:
            errors.append(f"{theme}: 確定データに旧判定語が残っています: {found}")
    return errors


def verification_claim_counts(theme: str) -> dict[str, int]:
    rows = json.loads((ROOT / "data" / "verification" / f"{theme}-claims.json").read_text(encoding="utf-8"))
    return dict(Counter(row["claim"] for row in rows))


def public_path(theme: str) -> Path:
    return ROOT / "data" / "public" / "themes" / f"{theme}.json"


def public_claim_counts(theme: str) -> dict[str, int]:
    data = json.loads(public_path(theme).read_text(encoding="utf-8"))
    return {c["id"]: c["matched_post_count"] for c in data["claim_verification"]["claims"]}


def coverage_warnings() -> list[str]:
    """人が読んだ範囲が、ページの母数に追いついているかを見る（警告のみ）。

    ページの「意見◯◯件」は定例更新のたびに機械が数え直すが、主張ごとの該当件数は
    人が読んだ時点で止まる。片方だけ動くので、同じページに範囲の違う数字が並ぶ。
    課題54 段階3のレビューで実測した（993件時点の照合が1139件のページに載りかけた）。

    件数の3か所突き合わせ（audit_counts）はこのズレを見つけられない。3か所とも
    同じ確定データから作るため、仲良く一致してしまう。

    本来は公開データ契約へ「照合が対象にした期間」を持たせる（課題54の残課題）。
    それまでの暫定として、確認日 checked_on を読んだ範囲の代わりに使う。
    読み直しの範囲はオーナー判断が要るため、ここでは止めずに警告だけ出す。
    """
    warnings: list[str] = []
    for theme in SOURCES:
        data = json.loads(public_path(theme).read_text(encoding="utf-8"))
        checked_on = (data.get("claim_verification") or {}).get("checked_on")
        period_end = (data.get("collection_period") or {}).get("end")
        if not checked_on or not period_end:
            continue
        if checked_on < period_end:
            warnings.append(
                f"{theme}: 照合の確認日 {checked_on} が公開データの期間末 {period_end} より前です"
                "（増えた投稿を主張へ読み足していない可能性）"
            )
    return warnings


def audit_counts() -> list[str]:
    errors: list[str] = []
    for theme in SOURCES:
        canon = canonical_claim_counts(theme)
        for name, actual in (
            ("data/verification", verification_claim_counts(theme)),
            ("公開JSON", public_claim_counts(theme)),
        ):
            if actual != canon:
                only_canon = {k: v for k, v in canon.items() if actual.get(k) != v}
                errors.append(f"{theme}: {name} の件数が人の確定データと一致しません: {only_canon}")
    return errors


def audit() -> tuple[dict[str, int], list[str]]:
    counts: dict[str, int] = {}
    errors: list[str] = []
    for theme, (relative, variable) in SOURCES.items():
        checks = read_checks(ROOT / relative, variable)
        counts[theme] = len(checks)
        for index, check in enumerate(checks, start=1):
            verdict = check.get("verdict")
            if verdict not in ALLOWED:
                errors.append(f"{theme} #{index}: 不正な判定語 {verdict!r}")
    constitutional_labels = read_literal(
        ROOT / "scripts/build_constitutional_process_sections.py", "VERDICT_LABEL"
    )
    if constitutional_labels != {code: label for label, code in LEGACY_CONSTITUTIONAL.items()}:
        errors.append("constitutional-amendment: 既存の日本語表示ラベルとの写像が一致しません")
    errors.extend(audit_counts())
    errors.extend(audit_legacy_words())
    return counts, errors


def main() -> int:
    counts, errors = audit()
    total = sum(counts.values())
    for theme, count in counts.items():
        print(f"{theme}: {count}主張")
    print(f"合計: {total}主張")
    if errors:
        print("NG")
        print("\n".join(errors))
        return 1
    # テーマ数は SOURCES から数える（固定文字列にすると登録追加のたびに古くなる）
    print(f"OK: {len(SOURCES)}テーマすべてが fact / gap / miss のみを使用")
    print("OK: 主張ごとの件数が 正典 / data\u002fverification / 公開JSON で一致")
    print("OK: 確定データに旧判定語が残っていない")
    warnings = coverage_warnings()
    if warnings:
        print(f"警告 {len(warnings)}件: 照合が公開母数に追いついていません（終了コードは変えません）")
        print("\n".join(f"  - {w}" for w in warnings))
        print("  読み直す範囲はオーナー判断。TASK_BOARD.md 課題54「未着手（レビュー指摘）」を参照")
    else:
        print("OK: 照合の確認日が全テーマで公開データの期間末に追いついている")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
