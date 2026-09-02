#!/usr/bin/env python3
"""海面より下（沈んだ大陸・地下水脈）の2ファイルを検査する。

設計書 `quality/designs/reaction-planet-renewal.md` 3.3.2・3.3.3・11章に基準はあったが、
実装はこのファイルまで無かった（課題54 段階5、指摘4への対応）。`data/verification/{theme}-sunk-continents.json`
と `data/verification/{theme}-veins.json` の組を、テーマ名を決め打ちせず data/verification/ から自動で探す。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "data" / "verification"
MAX_SUNK_CONTINENTS = 4
MIN_VEIN_COUNT = 2
MAX_VEIN_COUNT = 4
MIN_REPRESENTATIVE_POSTS_PER_SIDE = 2
NON_EDITORIAL_CHECKED_BY = {"ai_assisted"}


def find_theme_files() -> dict[str, tuple[Path, Path]]:
    """theme_id -> (sunk_continents_path, veins_path) の組を data/verification/ から探す。"""
    pairs: dict[str, tuple[Path, Path]] = {}
    for sunk_path in sorted(VERIFICATION_DIR.glob("*-sunk-continents.json")):
        theme = sunk_path.name[: -len("-sunk-continents.json")]
        veins_path = VERIFICATION_DIR / f"{theme}-veins.json"
        if veins_path.exists():
            pairs[theme] = (sunk_path, veins_path)
    return pairs


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_sunk_continents(theme: str, path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    skipped_match_rule: list[str] = []
    data = load(path)
    items = data.get("items", [])
    if len(items) > MAX_SUNK_CONTINENTS:
        errors.append(f"{theme}: 沈んだ大陸が{len(items)}件で、1テーマ{MAX_SUNK_CONTINENTS}件以内（3.3.2）を超えています")

    required_fields = ["primary_sources", "sns_count", "sns_base", "checked_on", "checked_by"]
    for item in items:
        item_id = item.get("id", "?")
        missing = [f for f in required_fields if not item.get(f) and item.get(f) != 0]
        if missing:
            errors.append(f"{theme}/{item_id}: 必須項目が欠けています（11章）: {missing}")
        for source in item.get("primary_sources", []):
            if not source.get("url"):
                errors.append(f"{theme}/{item_id}: 一次資料にURLがありません（11章）")
            if not source.get("location"):
                errors.append(f"{theme}/{item_id}: 一次資料に該当箇所（location）がありません（11章）")

        rule = item.get("match_rule")
        if not rule:
            errors.append(f"{theme}/{item_id}: match_rule がありません（3.3.2「機械で再現できる条件」）")
            continue
        pattern = rule.get("pattern")
        recorded_hits = set(rule.get("machine_hits", []))
        if pattern is None:
            errors.append(f"{theme}/{item_id}: match_rule.pattern がありません")
            continue
        actual_hits = run_match_rule(theme, rule)
        if actual_hits is None:
            skipped_match_rule.append(item_id)
        elif actual_hits != recorded_hits:
            errors.append(
                f"{theme}/{item_id}: match_rule を再実行した結果が machine_hits と一致しません "
                f"(記録={sorted(recorded_hits)} / 実行={sorted(actual_hits)})"
            )
    return errors, skipped_match_rule


def run_match_rule(theme: str, rule: dict) -> set[str] | None:
    """match_rule.pattern を正典に対して再実行し、ヒットしたtweet_idの集合を返す。

    正典（social-samples/、Git管理外）が無い環境では None を返し、呼び出し側で
    「飛ばした」ことを分かるメッセージにする。
    """
    sample_relpath = find_sample_file(theme)
    if sample_relpath is None:
        return None
    sample_path = ROOT / sample_relpath
    if not sample_path.exists():
        return None

    records = json.loads(sample_path.read_text(encoding="utf-8"))
    pattern = re.compile(rule["pattern"])
    scope = rule.get("scope", "text")
    hits: set[str] = set()
    for record in records:
        classification = record.get("classification", {})
        if not classification.get("is_opinion"):
            continue
        haystack_parts = []
        if "text" in scope:
            haystack_parts.append(record.get("text", ""))
        if "summary" in scope:
            haystack_parts.append(classification.get("summary", ""))
        if "reason" in scope:
            haystack_parts.append(classification.get("reason", ""))
        haystack = "".join(haystack_parts)
        if pattern.search(haystack):
            hits.add(str(record.get("tweet_id")))
    return hits


def find_sample_file(theme: str) -> str | None:
    import yaml

    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8")).get("themes", {})
    entry = themes.get(theme)
    if not entry:
        return None
    return entry.get("sample_file")


def verify_veins(theme: str, path: Path) -> tuple[list[str], bool]:
    errors: list[str] = []
    data = load(path)
    items = data.get("items", [])
    if not (MIN_VEIN_COUNT <= len(items) <= MAX_VEIN_COUNT):
        errors.append(
            f"{theme}: 地下水脈が{len(items)}本で、1テーマ{MIN_VEIN_COUNT}〜{MAX_VEIN_COUNT}本（3.3.3）の範囲外です"
        )

    sample_relpath = find_sample_file(theme)
    sample_path = ROOT / sample_relpath if sample_relpath else None
    canonical_ids: set[str] | None = None
    if sample_path and sample_path.exists():
        records = json.loads(sample_path.read_text(encoding="utf-8"))
        canonical_ids = {str(r.get("tweet_id")) for r in records}

    skipped_existence_check = canonical_ids is None

    for item in items:
        item_id = item.get("id", "?")
        sides = item.get("sides", [])
        for side in sides:
            posts = side.get("representative_posts", [])
            if len(posts) < MIN_REPRESENTATIVE_POSTS_PER_SIDE:
                errors.append(
                    f"{theme}/{item_id}/{side.get('stance_label', '?')}: 代表投稿が{len(posts)}件で、"
                    f"各立場{MIN_REPRESENTATIVE_POSTS_PER_SIDE}件以上（11章）を下回っています"
                )
            if canonical_ids is not None:
                for post in posts:
                    tweet_id = str(post.get("tweet_id"))
                    if tweet_id not in canonical_ids:
                        errors.append(f"{theme}/{item_id}: 代表投稿 {tweet_id} が正典に実在しません（11章）")
    return errors, skipped_existence_check


def verify_no_text_leak(theme: str, path: Path) -> list[str]:
    """data/verification/ に本文・要約を入れない（README規約）。"""
    errors: list[str] = []
    data = load(path)
    for item in data.get("items", []):
        for side in item.get("sides", []):
            for post in side.get("representative_posts", []):
                excerpt = post.get("excerpt")
                if excerpt is not None and excerpt != "not_listed":
                    errors.append(f"{theme}/{item.get('id')}: representative_posts に本文相当の excerpt が残っています")
                if "summary" in post or "text" in post:
                    errors.append(f"{theme}/{item.get('id')}: representative_posts に summary/text が残っています（README規約違反）")
    return errors


def verify_checked_by_not_leaked(theme: str, path: Path, label: str) -> list[str]:
    """checked_by が ai_assisted のものを、公開契約へ載せる経路に通さない（3.3・11章）。

    このリポジトリでは公開データ契約 data/public/themes/{theme}.json に
    海面より下のデータを載せる経路がまだ無い（段階6の仕事）。将来そのビルダーが
    出来たとき、ai_assisted のレコードを取りこぼさず弾けるよう、ここでは
    「ai_assisted のレコードが今も存在すること自体は許すが、公開JSONに
    curated_by/checked_by が ai_assisted のまま接続されていないか」を見る。
    """
    errors: list[str] = []
    data = load(path)
    public_path = ROOT / "data" / "public" / "themes" / f"{theme}.json"
    if not public_path.exists():
        return errors
    public_data = load(public_path)
    if "sunk_continents" in public_data or "veins" in public_data or "underwater" in public_data:
        checked_by = data.get("checked_by") or data.get("curated_by")
        if checked_by in NON_EDITORIAL_CHECKED_BY:
            errors.append(f"{theme}/{label}: checked_by が {checked_by} のまま公開JSONに接続されています（3.3・11章）")
    return errors


def main() -> int:
    pairs = find_theme_files()
    if not pairs:
        print("対象なし: data/verification/*-sunk-continents.json と *-veins.json の組が見つかりません")
        return 0

    errors: list[str] = []
    skipped_existence_themes: list[str] = []
    skipped_match_rule_themes: dict[str, list[str]] = {}
    for theme, (sunk_path, veins_path) in pairs.items():
        sunk_errors, skipped_match_rule = verify_sunk_continents(theme, sunk_path)
        errors.extend(sunk_errors)
        if skipped_match_rule:
            skipped_match_rule_themes[theme] = skipped_match_rule
        vein_errors, skipped = verify_veins(theme, veins_path)
        errors.extend(vein_errors)
        if skipped:
            skipped_existence_themes.append(theme)
        errors.extend(verify_no_text_leak(theme, veins_path))
        errors.extend(verify_checked_by_not_leaked(theme, sunk_path, "sunk-continents"))
        errors.extend(verify_checked_by_not_leaked(theme, veins_path, "veins"))

    for theme in pairs:
        print(f"{theme}: 沈んだ大陸・地下水脈を検査")

    if skipped_existence_themes:
        print(
            f"飛ばしました（正典が無い環境）: {skipped_existence_themes} の代表投稿tweet_id実在確認"
        )
    if skipped_match_rule_themes:
        print(f"飛ばしました（正典が無い環境）: match_rule再実行 {skipped_match_rule_themes}")

    if errors:
        print("NG")
        print("\n".join(errors))
        return 1

    print(f"OK: {len(pairs)}テーマの沈んだ大陸・地下水脈が設計書3.3.2/3.3.3/11章の基準を満たしています")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
