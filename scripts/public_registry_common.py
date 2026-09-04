#!/usr/bin/env python3
"""課題57: 公開データ契約（テーマJSON・catalog）の共通ロジック。

正規化・ハッシュ規則は `quality/reviews/2026-08-31-public-data-foundation-stage2-proposal.md`
「決定的な生成とハッシュ」節を実装したもの。jsonschema ライブラリは使わず、
この2つのSchemaに必要な範囲だけを自前の最小検証器で読む。
"""
from __future__ import annotations

import hashlib
import json
import re
import ast
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
THEMES_YAML = ROOT / "THEMES.yaml"
TAXONOMY_PATH = ROOT / "configs" / "public-data-taxonomy.json"
PUBLIC_THEME_SCHEMA_PATH = ROOT / "schemas" / "public-theme.schema.json"
PUBLIC_CATALOG_SCHEMA_PATH = ROOT / "schemas" / "public-catalog.schema.json"
PUBLIC_THEMES_DIR = ROOT / "data" / "public" / "themes"
PUBLIC_CATALOG_PATH = ROOT / "data" / "public" / "catalog.json"

INTENSITY_ORDER = ("low", "medium", "high")

# 読者向け照合カードの正典は、各テーマの生成器にある一次資料記録である。
# 公開JSONには投稿本文・投稿IDを入れず、確認済み件数だけを持たせる
# （人が確定した投稿IDの正典は data/{theme}_claim_posts.json、その写しが
#  data/verification/{theme}-claims.json。設計書14章もこの分担で記述している）。
# 各主張は、それが争われている論点（大陸）へ結びつける。課題54の地形は論点単位で
# 実像／ずれ／蜃気楼を塗り分けるため、この対応が無いと段階6で色を決められない。
CLAIM_AUDIT_SOURCES = {
    "bike-blue-ticket": ("scripts/build_bike_process_sections.py", "FACT_CHECKS", "CHECKED_AT", "claim"),
    "bukatsu-chiiki": ("scripts/build_bukatsu_process_sections.py", "FACT_CHECKS", "CHECKED_AT", "claim"),
    "constitutional-amendment": ("scripts/build_constitutional_process_sections.py", "FACT_CHECKS", "CHECKED_AT", "claim"),
    "consumption-tax-cut": ("scripts/build_consumption_tax_page.py", "CLAIM_AUDIT", "CHECKED_ON", "say"),
    "elderly-license-revocation": ("scripts/build_elderly_process_sections.py", "FACT_CHECKS", "CHECKED_AT", "claim"),
    "fukushuto": ("scripts/build_fukushuto_process_sections.py", "FACT_CHECKS", "CHECKED_AT", "claim"),
    "koshitsu-tenpakai": ("scripts/build_koshitsu_process_sections.py", "FACT_CHECKS", "CHECKED_AT", "claim"),
}

# 読者向けの「問い」。テーマ設定として明示し、表示名やHTML文言からは作らない。
# 部活動の地域移行は configs/planet/bukatsu-chiiki.yaml で既に承認済みの表現を転記した
# （課題54の地形設定そのものは公開データJSONの入力にしない）。
# 残り9テーマは各テーマの公開済み subtitle / vote_intro（configs/*-reaction-map.json）の
# 論点をそのまま短い問いに言い換えたもので、新しい主張は加えていない。段階6の総合レビューで
# 独立レビューを受けるまで、この文言はどのページにも表示しない。
QUESTIONS: dict[str, str] = {
    "bukatsu-chiiki": "学校の部活動を地域へ移すべきか",
    "ai-copyright": "生成AIによる著作物の無断学習をどこまで認めるか",
    "bike-blue-ticket": "自転車の交通違反に青切符（反則金）を導入すべきか",
    "constitutional-amendment": "憲法を改正すべきか",
    "consumption-tax-cut": "食料品の消費税率を下げるべきか",
    "elderly-license-revocation": "高齢者の運転免許を年齢で一律に返納させるべきか",
    "fukushuto": "首都機能のバックアップとなる副首都を法律で指定すべきか",
    "henoko-student-accident": "辺野古の修学旅行中の事故を、学校はどう検証すべきか",
    "koshitsu-tenpakai": "皇室典範改正をどう評価するか",
    "school-nickname-ban": "学校で「あだ名禁止」を指導すべきか",
}


class RegistryError(Exception):
    pass


def _literal_from_python(path: Path, variable: str) -> Any:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RegistryError(f"{path}: {variable} がリテラルとして見つかりません")


def _iso_date(value: str) -> str:
    match = re.fullmatch(r"(\d{4})年(\d{1,2})月(\d{1,2})日", value)
    if not match:
        raise RegistryError(f"照合日の形式が不正です: {value!r}")
    return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"


def build_claim_verification(theme_id: str) -> dict[str, Any]:
    source = CLAIM_AUDIT_SOURCES.get(theme_id)
    if source is None:
        return {"status": "not_started", "checked_on": None, "reviewer_type": None, "claims": []}

    relative, checks_name, checked_name, claim_key = source
    script = ROOT / relative
    checks = _literal_from_python(script, checks_name)
    checked_on = _iso_date(_literal_from_python(script, checked_name))
    rows = json.loads((ROOT / "data" / "verification" / f"{theme_id}-claims.json").read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for row in rows:
        claim_id = row.get("claim")
        if not isinstance(claim_id, str):
            raise RegistryError(f"{theme_id}: 検証用投稿に claim がありません")
        counts[claim_id] = counts.get(claim_id, 0) + 1

    issue_defs = load_taxonomy()[theme_id]["issues"]
    issue_order = list(issue_defs)

    claims = []
    for check in checks:
        claim_id = check["key"]
        verdict = check["verdict"]
        if verdict not in {"fact", "gap", "miss"}:
            raise RegistryError(f"{theme_id}/{claim_id}: 判定語が未統一です: {verdict!r}")
        if claim_id not in counts:
            raise RegistryError(f"{theme_id}/{claim_id}: 検証用投稿がありません")
        labels = check.get("issues")
        if labels is None:
            raise RegistryError(f"{theme_id}/{claim_id}: 論点との対応（issues）がありません")
        for label in labels:
            if label not in issue_defs:
                raise RegistryError(f"{theme_id}/{claim_id}: 対応表に無い論点です: {label!r}")
            if issue_defs[label]["kind"] == "other":
                raise RegistryError(f"{theme_id}/{claim_id}: 「その他」へは結びつけられません")
        # 対応表の並び順へ正規化する（同じ入力から必ず同じ出力にする）
        issue_ids = [issue_defs[label]["id"] for label in sorted(set(labels), key=issue_order.index)]
        if "links" in check:
            sources = [{"name": name, "url": url} for url, name in check["links"]]
        else:
            sources = []
            if check.get("url") and check.get("url_label"):
                sources.append({"name": check["url_label"], "url": check["url"]})
            sources.extend(
                {"name": name, "url": url} for url, name in (check.get("extra_links") or [])
            )
        if verdict != "miss" and not sources:
            raise RegistryError(
                f"{theme_id}/{claim_id}: 判定が {verdict} なのに一次資料が1件もありません"
            )
        claims.append({
            "id": claim_id,
            "claim": check[claim_key],
            "verdict": verdict,
            "finding": check["note"],
            "issue_ids": issue_ids,
            "matched_post_count": counts[claim_id],
            "sources": sources,
        })
    if set(counts) != {claim["id"] for claim in claims}:
        raise RegistryError(f"{theme_id}: 検証用投稿と照合カードの主張IDが一致しません")
    return {"status": "complete", "checked_on": checked_on, "reviewer_type": "editorial_review", "claims": claims}


# 公開してよい海面下の項目（設計書3.3・14章）。ここに無い鍵は落とす。
# 投稿ID・本文・AIの内部理由（match_rule の機械一致・除外理由）は公開契約へ入れない。
OCEAN_MAX_SUNK_CONTINENTS = 4
OCEAN_MIN_POSTS_PER_SIDE = 2
OCEAN_REVIEWER_TYPES = {"editorial_review", "ai_assisted"}


def _ocean_date(value: Any, where: str) -> str:
    """海面下の台帳の確認日はISO形式（2026-09-02）で入っている。"""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise RegistryError(f"{where}: 確認日の形式が不正です: {value!r}")
    return value


def _ocean_reviewer(value: Any, where: str) -> str:
    if value not in OCEAN_REVIEWER_TYPES:
        raise RegistryError(f"{where}: 確認者種別が不正です: {value!r}")
    return value


def build_ocean_layer(theme_id: str) -> dict[str, Any]:
    """沈んだ大陸・地下水脈を公開データ契約へ載せる（設計書3.3、14章）。

    公開するのは「人が一次資料を読んで初めて分かること」だけ。台帳にある
    投稿ID・本文・機械一致の結果・除外理由は落とす（段階2で決めた公開契約の原則）。
    地下水脈の代表投稿は、段階6・指摘2と同じ扱いで**件数だけ**を載せる
    （投稿IDの正典は `data/verification/` 側に残す）。

    台帳が無いテーマは、空欄ではなく `not_started` として機械判定できる形で返す。
    """
    empty = {"status": "not_started", "checked_on": None, "reviewer_type": None,
             "sunk_continents": [], "veins": []}
    sc_path = ROOT / "data" / "verification" / f"{theme_id}-sunk-continents.json"
    veins_path = ROOT / "data" / "verification" / f"{theme_id}-veins.json"
    sc_items = json.loads(sc_path.read_text(encoding="utf-8"))["items"] if sc_path.exists() else []
    vein_items = json.loads(veins_path.read_text(encoding="utf-8"))["items"] if veins_path.exists() else []
    if not sc_items and not vein_items:
        return empty

    issue_defs = load_taxonomy()[theme_id]["issues"]
    known_issue_ids = {d["id"] for d in issue_defs.values()}
    checked_dates: list[str] = []
    reviewers: list[str] = []

    if len(sc_items) > OCEAN_MAX_SUNK_CONTINENTS:
        raise RegistryError(
            f"{theme_id}: 沈んだ大陸が{len(sc_items)}件です（設計書3.3.2の上限は"
            f"{OCEAN_MAX_SUNK_CONTINENTS}件）")

    sunk = []
    for item in sc_items:
        where = f"{theme_id}/{item.get('id')}"
        sources = [
            {"name": src["name"], "url": src["url"], "location": src["location"],
             "date": src.get("date")}
            for src in item.get("primary_sources", [])
        ]
        if not sources:
            raise RegistryError(f"{where}: 沈んだ大陸に一次資料が1件もありません")
        bucket = item.get("issue_bucket") or {}
        issue_id = bucket.get("issue_id")
        if issue_id is not None and issue_id not in known_issue_ids:
            raise RegistryError(f"{where}: 対応表に無い論点IDです: {issue_id}")
        if item["sns_count"] > item["sns_base"]:
            raise RegistryError(f"{where}: SNS件数が母数を超えています")
        checked_on = _ocean_date(item["checked_on"], where)
        reviewer = _ocean_reviewer(item["checked_by"], where)
        checked_dates.append(checked_on)
        reviewers.append(reviewer)
        sunk.append({
            "id": item["id"],
            "topic": item["topic"],
            "life_impact": item["life_impact"],
            "sns_count": item["sns_count"],
            "sns_base": item["sns_base"],
            "sns_note": item["sns_note"],
            "nearest_issue_id": issue_id,
            "sources": sources,
            "checked_on": checked_on,
            "reviewer_type": reviewer,
        })

    ledger_reviewer = json.loads(veins_path.read_text(encoding="utf-8")).get("curated_by") \
        if veins_path.exists() else None
    veins = []
    for item in vein_items:
        where = f"{theme_id}/{item.get('id')}"
        issue_ids = list(item.get("issue_ids") or [])
        if not issue_ids:
            raise RegistryError(f"{where}: 地下水脈が論点へ結びついていません")
        for issue_id in issue_ids:
            if issue_id not in known_issue_ids:
                raise RegistryError(f"{where}: 対応表に無い論点IDです: {issue_id}")
        sides = []
        for side in item.get("sides", []):
            posts = side.get("representative_posts", [])
            if len(posts) < OCEAN_MIN_POSTS_PER_SIDE:
                raise RegistryError(
                    f"{where}: 立場「{side.get('stance_label')}」の代表投稿が{len(posts)}件です"
                    f"（設計書3.3.3は各{OCEAN_MIN_POSTS_PER_SIDE}件以上）")
            sides.append({"stance_label": side["stance_label"], "post_count": len(posts)})
        if len(sides) < 2:
            raise RegistryError(f"{where}: 地下水脈は対立する2つ以上の立場が要ります")
        checked_on = _ocean_date(item["checked_on"], where)
        reviewer = _ocean_reviewer(item.get("reviewer_type") or ledger_reviewer, where)
        checked_dates.append(checked_on)
        reviewers.append(reviewer)
        veins.append({
            "id": item["id"],
            "issue_ids": issue_ids,
            "shared_concern": item["shared_concern"],
            "diverging_reason": item["diverging_reason"],
            "sides": sides,
            "checked_on": checked_on,
            "reviewer_type": reviewer,
        })

    # 全体の確認者種別は、いちばん弱いものに合わせる。
    # AIの下読みが1件でも混じっていれば「人が確認した」とは表示しない（設計書3.3）。
    overall = "editorial_review" if all(r == "editorial_review" for r in reviewers) else "ai_assisted"
    return {"status": "complete", "checked_on": max(checked_dates),
            "reviewer_type": overall, "sunk_continents": sunk, "veins": veins}


def load_themes_yaml() -> dict[str, Any]:
    data = yaml.safe_load(THEMES_YAML.read_text(encoding="utf-8"))
    return data["themes"]


def load_taxonomy() -> dict[str, Any]:
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))["themes"]


def canonical_compact(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _record_sort_key(index: int, record: dict[str, Any]) -> tuple:
    tweet_id = record.get("tweet_id")
    if tweet_id is not None:
        return (0, str(tweet_id))
    url = record.get("url")
    if url:
        return (1, str(url))
    return (2, index)


def source_sha256(records: list[dict[str, Any]]) -> str:
    ordered = sorted(enumerate(records), key=lambda item: _record_sort_key(item[0], item[1]))
    lines = [canonical_compact(record) for _, record in ordered]
    blob = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def classification_of(record: dict[str, Any]) -> dict[str, Any]:
    c = record.get("classification")
    return c if isinstance(c, dict) else record


def _flag_field(record: dict[str, Any], key: str) -> Any:
    # 自転車青切符の累積正典は is_opinion をレコード直下に置き、is_relevant を持たない
    # （旧2Dビルダー scripts/build_bike_arena.py の is_opinion() と同じ規則。段階1調査済み。
    # データの再分類はしない）。main_issue/stance/intensity は他テーマ同様 classification 内にある。
    c = record.get("classification")
    if isinstance(c, dict) and key in c:
        return c[key]
    return record.get(key)


def is_opinion_record(record: dict[str, Any]) -> bool:
    is_opinion = _flag_field(record, "is_opinion")
    is_relevant = _flag_field(record, "is_relevant")
    if is_relevant is None:
        return bool(is_opinion)
    return bool(is_relevant) and bool(is_opinion)


_PERIOD_RANGE = re.compile(r"^(\d{4}-\d{2}-\d{2})〜(\d{4}-\d{2}-\d{2})$")
_PERIOD_SINGLE = re.compile(r"^(\d{4}-\d{2}-\d{2})$")


def parse_collection_period(sample_period: Any) -> dict[str, Any]:
    text = str(sample_period).strip() if sample_period else ""
    match = _PERIOD_RANGE.match(text)
    if match:
        return {"start": match.group(1), "end": match.group(2), "status": "known"}
    match = _PERIOD_SINGLE.match(text)
    if match:
        return {"start": match.group(1), "end": None, "status": "start_only"}
    return {"start": None, "end": None, "status": "unknown"}


def build_theme_json(theme_id: str) -> dict[str, Any]:
    themes_yaml = load_themes_yaml()
    if theme_id not in themes_yaml:
        raise RegistryError(f"THEMES.yaml に無いテーマID: {theme_id}")
    theme_meta = themes_yaml[theme_id]
    if theme_meta.get("published") != "done":
        raise RegistryError(f"{theme_id} は published: done ではない")

    taxonomy = load_taxonomy()
    if theme_id not in taxonomy:
        raise RegistryError(f"configs/public-data-taxonomy.json に無いテーマID: {theme_id}")
    issue_defs: dict[str, dict] = taxonomy[theme_id]["issues"]
    stance_defs: dict[str, dict] = taxonomy[theme_id]["stances"]

    other_labels = [label for label, meta in issue_defs.items() if meta["kind"] == "other"]
    if len(other_labels) != 1:
        raise RegistryError(f"{theme_id}: kind=other の論点は必ず1つ必要（現在{len(other_labels)}）")

    question = QUESTIONS.get(theme_id)
    if not question:
        raise RegistryError(
            f"{theme_id}: 公開データ用の「問い」が未設定（scripts/public_registry_common.py の QUESTIONS）"
        )

    sample_file = ROOT / theme_meta["sample_file"]
    if not sample_file.exists():
        raise RegistryError(f"{theme_id}: 非公開正典が見つかりません: {sample_file}")
    records = json.loads(sample_file.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise RegistryError(f"{theme_id}: sample_file の形式が不正です: {sample_file}")

    collected_count = len(records)
    opinions = [classification_of(r) for r in records if is_opinion_record(r)]
    opinion_count = len(opinions)
    if collected_count < opinion_count:
        raise RegistryError(f"{theme_id}: collected_count({collected_count}) < opinion_count({opinion_count})")

    unknown_issues = {c.get("main_issue") for c in opinions} - set(issue_defs.keys())
    if unknown_issues:
        raise RegistryError(f"{theme_id}: 固定ID対応表に無い論点があります: {sorted(unknown_issues)}")
    unknown_stances = {c.get("stance") for c in opinions} - set(stance_defs.keys())
    if unknown_stances:
        raise RegistryError(f"{theme_id}: 固定ID対応表に無い立場があります: {sorted(unknown_stances)}")
    unknown_intensity = {c.get("intensity") for c in opinions} - set(INTENSITY_ORDER)
    if unknown_intensity:
        raise RegistryError(f"{theme_id}: 未知の表現強度があります: {sorted(unknown_intensity)}")

    issues_out = []
    assigned_total = 0
    for label, meta in issue_defs.items():
        issue_opinions = [c for c in opinions if c.get("main_issue") == label]
        count = len(issue_opinions)
        assigned_total += count

        stances_out = [
            {"id": smeta["id"], "label": slabel, "count": sum(1 for c in issue_opinions if c.get("stance") == slabel)}
            for slabel, smeta in stance_defs.items()
        ]
        intensities_out = [
            {"id": level, "count": sum(1 for c in issue_opinions if c.get("intensity") == level)}
            for level in INTENSITY_ORDER
        ]
        issues_out.append(
            {
                "id": meta["id"],
                "label": label,
                "kind": meta["kind"],
                "count": count,
                "stances": stances_out,
                "intensities": intensities_out,
            }
        )

    if assigned_total != opinion_count:
        raise RegistryError(f"{theme_id}: 論点件数合計({assigned_total})が意見数({opinion_count})と不一致")

    src_hash = source_sha256(records)
    html_path = str(theme_meta.get("html", ""))
    page_path = Path(html_path).name
    if not re.match(r"^[a-z0-9][a-z0-9-]*-reaction-map\.html$", page_path):
        raise RegistryError(f"{theme_id}: page_path がSchemaの形式に合いません: {page_path}")

    return {
        "schema_version": "1.0",
        "theme_id": theme_id,
        "title": str(theme_meta.get("title")),
        "question": question,
        "page_path": page_path,
        "data_version": f"v1-{src_hash[:16]}",
        "source_sha256": src_hash,
        "updated_on": str(theme_meta.get("updated_at")),
        "collection_period": parse_collection_period(theme_meta.get("sample_period")),
        "collected_count": collected_count,
        "opinion_count": opinion_count,
        "issue_assigned_count": assigned_total,
        "issues": issues_out,
        "claim_verification": build_claim_verification(theme_id),
        "ocean_layer": build_ocean_layer(theme_id),
    }


def dumps_theme_json(theme_json: dict) -> bytes:
    text = json.dumps(theme_json, sort_keys=True, ensure_ascii=False, indent=2)
    return (text + "\n").encode("utf-8")


def load_theme_json_files() -> dict[str, dict]:
    return {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(PUBLIC_THEMES_DIR.glob("*.json"))
    }


def build_catalog() -> dict[str, Any]:
    themes_yaml = load_themes_yaml()
    entries = []
    for theme_id, data in load_theme_json_files().items():
        if themes_yaml.get(theme_id, {}).get("published") != "done":
            continue
        raw = dumps_theme_json(data)
        named_issue_count = sum(1 for issue in data["issues"] if issue["kind"] == "named")
        entries.append(
            {
                "theme_id": theme_id,
                "title": data["title"],
                "page_path": data["page_path"],
                "updated_on": data["updated_on"],
                "collected_count": data["collected_count"],
                "opinion_count": data["opinion_count"],
                "named_issue_count": named_issue_count,
                "data_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    if not entries:
        raise RegistryError("data/public/themes/ に公開JSONが1件もありません")
    entries.sort(key=lambda e: e["theme_id"])

    totals = {
        "theme_count": len(entries),
        "collected_count": sum(e["collected_count"] for e in entries),
        "opinion_count": sum(e["opinion_count"] for e in entries),
        "latest_updated_on": max(e["updated_on"] for e in entries),
    }
    blob = "\n".join(f"{e['theme_id']}:{e['data_sha256']}" for e in entries).encode("utf-8")
    return {
        "schema_version": "1.0",
        "generated_from": hashlib.sha256(blob).hexdigest(),
        "themes": entries,
        "totals": totals,
    }


def dumps_catalog_json(catalog: dict) -> bytes:
    text = json.dumps(catalog, sort_keys=True, ensure_ascii=False, indent=2)
    return (text + "\n").encode("utf-8")


# ---------------------------------------------------------------- 最小限のJSON Schema検証

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _resolve_ref(ref: str, root_schema: dict) -> dict:
    node = root_schema
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def validate_schema(instance: Any, schema: dict, root_schema: dict | None = None, path: str = "$") -> list[str]:
    root_schema = root_schema or schema
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root_schema)

    if "const" in schema:
        return [] if instance == schema["const"] else [f"{path}: const {schema['const']!r} != {instance!r}"]
    if "enum" in schema:
        return [] if instance in schema["enum"] else [f"{path}: {instance!r} not in {schema['enum']}"]

    errors: list[str] = []
    type_ = schema.get("type")
    if type_:
        types = type_ if isinstance(type_, list) else [type_]
        matched = any(
            (t == "string" and isinstance(instance, str))
            or (t == "integer" and isinstance(instance, int) and not isinstance(instance, bool))
            or (t == "object" and isinstance(instance, dict))
            or (t == "array" and isinstance(instance, list))
            or (t == "null" and instance is None)
            for t in types
        )
        if not matched:
            return [f"{path}: type mismatch, expected {types}, got {type(instance).__name__}"]

    if isinstance(instance, str):
        if schema.get("pattern") and not re.match(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} はパターン {schema['pattern']} に一致しません")
        if schema.get("format") == "date" and not _DATE_RE.match(instance):
            errors.append(f"{path}: {instance!r} は日付形式ではありません")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: 文字列が短すぎます")

    if isinstance(instance, dict) and schema.get("type") == "object":
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: 必須項目 {key!r} がありません")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{path}: 未定義の項目 {key!r} があります")
        for key, subschema in props.items():
            if key in instance:
                errors.extend(validate_schema(instance[key], subschema, root_schema, f"{path}.{key}"))

    if isinstance(instance, list) and schema.get("type") == "array":
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: 配列が minItems={schema['minItems']} を満たしません")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: 配列が maxItems={schema['maxItems']} を超えています")
        items_schema = schema.get("items")
        if items_schema:
            for idx, item in enumerate(instance):
                errors.extend(validate_schema(item, items_schema, root_schema, f"{path}[{idx}]"))

    return errors


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_public_theme(instance: dict) -> list[str]:
    schema = load_schema(PUBLIC_THEME_SCHEMA_PATH)
    return validate_schema(instance, schema, schema)


def validate_public_catalog(instance: dict) -> list[str]:
    schema = load_schema(PUBLIC_CATALOG_SCHEMA_PATH)
    return validate_schema(instance, schema, schema)


# ---------------------------------------------------------------- Schemaでは表せない不変条件


def check_theme_invariants(theme_json: dict) -> list[str]:
    tid = theme_json.get("theme_id", "?")
    errors: list[str] = []
    if theme_json["collected_count"] < theme_json["opinion_count"]:
        errors.append(f"{tid}: collected_count < opinion_count")

    issues = theme_json["issues"]
    issue_sum = sum(i["count"] for i in issues)
    if issue_sum != theme_json["issue_assigned_count"]:
        errors.append(f"{tid}: 論点件数合計が issue_assigned_count と不一致")
    if theme_json["issue_assigned_count"] != theme_json["opinion_count"]:
        errors.append(f"{tid}: issue_assigned_count が opinion_count と不一致")

    other_count = sum(1 for i in issues if i["kind"] == "other")
    if other_count != 1:
        errors.append(f"{tid}: kind=other の論点が{other_count}件（1件である必要）")

    issue_ids = [i["id"] for i in issues]
    if len(issue_ids) != len(set(issue_ids)):
        errors.append(f"{tid}: 論点IDが重複しています")

    for issue in issues:
        s_sum = sum(s["count"] for s in issue["stances"])
        if s_sum != issue["count"]:
            errors.append(f"{tid}/{issue['id']}: 立場別件数合計が論点件数と不一致")
        stance_ids = [s["id"] for s in issue["stances"]]
        if len(stance_ids) != len(set(stance_ids)):
            errors.append(f"{tid}/{issue['id']}: 立場IDが重複しています")

        i_sum = sum(x["count"] for x in issue["intensities"])
        if i_sum != issue["count"]:
            errors.append(f"{tid}/{issue['id']}: 表現強度別件数合計が論点件数と不一致")
        levels = [x["id"] for x in issue["intensities"]]
        if levels != list(INTENSITY_ORDER):
            errors.append(f"{tid}/{issue['id']}: intensities の順序が low/medium/high ではありません")

    period = theme_json["collection_period"]
    status = period["status"]
    if status == "known" and (period["start"] is None or period["end"] is None):
        errors.append(f"{tid}: collection_period status=known なのに日付がnullです")
    if status == "start_only" and (period["start"] is None or period["end"] is not None):
        errors.append(f"{tid}: collection_period status=start_only の形式が不正です")
    if status == "unknown" and (period["start"] is not None or period["end"] is not None):
        errors.append(f"{tid}: collection_period status=unknown なのに日付があります")

    verification = theme_json.get("claim_verification")
    if not isinstance(verification, dict):
        errors.append(f"{tid}: claim_verification がありません")
        return errors
    claims = verification["claims"]
    if verification["status"] == "complete":
        if not claims or verification["checked_on"] is None or verification["reviewer_type"] != "editorial_review":
            errors.append(f"{tid}: 完了済み照合の必須項目が不足しています")
    if verification["status"] == "not_started":
        if claims or verification["checked_on"] is not None or verification["reviewer_type"] is not None:
            errors.append(f"{tid}: 未実施照合に結果が混在しています")
    claim_ids = [claim["id"] for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        errors.append(f"{tid}: 照合主張IDが重複しています")

    # 主張は必ず実在する論点（大陸）に結びつける。「その他」は分類限界の受け皿なので使わない。
    known_issue_ids = {i["id"] for i in issues}
    other_issue_ids = {i["id"] for i in issues if i["kind"] == "other"}
    for claim in claims:
        for issue_id in claim["issue_ids"]:
            if issue_id not in known_issue_ids:
                errors.append(f"{tid}/{claim['id']}: 論点IDが公開JSONに存在しません: {issue_id}")
            elif issue_id in other_issue_ids:
                errors.append(f"{tid}/{claim['id']}: 「その他」の論点へ結びついています")
        # 判定が miss（資料に見当たらない）のときだけ、一次資料が0件でよい。
        if claim["verdict"] != "miss" and not claim["sources"]:
            errors.append(f"{tid}/{claim['id']}: 判定が {claim['verdict']} なのに一次資料が0件です")

    errors.extend(check_ocean_invariants(theme_json, known_issue_ids, other_issue_ids))
    return errors


# 公開契約へ入れてはいけない鍵。投稿を特定できるもの、AIの内部判断、機械一致の作業記録。
# 台帳の内部項目名。作業メモの言葉が読者向けの本文へ紛れ込むのを止める。
OCEAN_INTERNAL_TOKENS = (
    "issue_bucket", "match_rule", "machine_hits", "sns_base", "sns_count",
    "primary_sources", "representative_posts", "checked_by", "classification",
)

OCEAN_FORBIDDEN_KEYS = frozenset({
    "tweet_id", "post_id", "post_ids", "representative_posts", "excerpt", "text",
    "summary", "reason", "confidence", "match_rule", "machine_hits", "excluded",
})


def _forbidden_keys_in(node: Any) -> set[str]:
    if isinstance(node, dict):
        found = {k for k in node if k in OCEAN_FORBIDDEN_KEYS}
        for value in node.values():
            found |= _forbidden_keys_in(value)
        return found
    if isinstance(node, list):
        found: set[str] = set()
        for value in node:
            found |= _forbidden_keys_in(value)
        return found
    return set()


def check_ocean_invariants(theme_json: dict, known_issue_ids: set[str],
                           other_issue_ids: set[str]) -> list[str]:
    """海面下（沈んだ大陸・地下水脈）がSchemaでは表せない条件を満たすか見る。"""
    tid = theme_json.get("theme_id", "?")
    errors: list[str] = []
    ocean = theme_json.get("ocean_layer")
    if not isinstance(ocean, dict):
        return [f"{tid}: ocean_layer がありません"]

    sunk, veins = ocean["sunk_continents"], ocean["veins"]
    if ocean["status"] == "complete":
        if not (sunk or veins) or ocean["checked_on"] is None or ocean["reviewer_type"] is None:
            errors.append(f"{tid}: 完了済み海面下の必須項目が不足しています")
    if ocean["status"] == "not_started":
        # 台帳に無い論点の海面下は、推測で埋めず空のまま出す（設計書3.3）
        if sunk or veins or ocean["checked_on"] is not None or ocean["reviewer_type"] is not None:
            errors.append(f"{tid}: 未実施の海面下に結果が混在しています")

    ids = [x["id"] for x in sunk] + [x["id"] for x in veins]
    if len(ids) != len(set(ids)):
        errors.append(f"{tid}: 海面下のIDが重複しています")

    for item in sunk:
        if item["sns_count"] > item["sns_base"]:
            errors.append(f"{tid}/{item['id']}: SNS件数が母数を超えています")
        near = item["nearest_issue_id"]
        if near is not None and near not in known_issue_ids:
            errors.append(f"{tid}/{item['id']}: 論点IDが公開JSONに存在しません: {near}")

    for vein in veins:
        for issue_id in vein["issue_ids"]:
            if issue_id not in known_issue_ids:
                errors.append(f"{tid}/{vein['id']}: 論点IDが公開JSONに存在しません: {issue_id}")
            elif issue_id in other_issue_ids:
                errors.append(f"{tid}/{vein['id']}: 「その他」の論点へ結びついています")

    leaked = _forbidden_keys_in(ocean)
    if leaked:
        errors.append(f"{tid}: 公開契約に入れてはいけない項目があります: {', '.join(sorted(leaked))}")

    # 読者が読む文章に、台帳の内部項目名が残っていないこと。
    # 台帳は作業用に「issue_bucket参照」のような書き方をするので、そのまま画面へ出さない。
    prose_fields = (
        [(x.get("id"), key, x.get(key, "")) for x in sunk
         for key in ("topic", "life_impact", "sns_note")]
        + [(v.get("id"), key, v.get(key, "")) for v in veins
           for key in ("shared_concern", "diverging_reason")]
    )
    for item_id, key, text in prose_fields:
        for token in OCEAN_INTERNAL_TOKENS:
            if token in text:
                errors.append(
                    f"{tid}/{item_id}: 読者向けの{key}に内部の項目名『{token}』が残っています")

    return errors


def check_catalog_invariants(catalog: dict, theme_jsons: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    ids = [t["theme_id"] for t in catalog["themes"]]
    if len(ids) != len(set(ids)):
        errors.append("catalog: theme_id が重複しています")
    if ids != sorted(ids):
        errors.append("catalog: テーマ順が theme_id の辞書順になっていません")

    totals = catalog["totals"]
    entries = catalog["themes"]
    if totals["theme_count"] != len(entries):
        errors.append("catalog: totals.theme_count が再計算値と不一致")
    if totals["collected_count"] != sum(e["collected_count"] for e in entries):
        errors.append("catalog: totals.collected_count が再計算値と不一致")
    if totals["opinion_count"] != sum(e["opinion_count"] for e in entries):
        errors.append("catalog: totals.opinion_count が再計算値と不一致")
    if entries and totals["latest_updated_on"] != max(e["updated_on"] for e in entries):
        errors.append("catalog: totals.latest_updated_on が再計算値と不一致")

    for entry in entries:
        tid = entry["theme_id"]
        tj = theme_jsons.get(tid)
        if tj is None:
            continue
        named = sum(1 for i in tj["issues"] if i["kind"] == "named")
        if entry["named_issue_count"] != named:
            errors.append(f"catalog/{tid}: named_issue_count が公開JSONと不一致")
        if entry["collected_count"] != tj["collected_count"] or entry["opinion_count"] != tj["opinion_count"]:
            errors.append(f"catalog/{tid}: collected_count/opinion_count が公開JSONと不一致")
        if entry["updated_on"] != tj["updated_on"] or entry["title"] != tj["title"] or entry["page_path"] != tj["page_path"]:
            errors.append(f"catalog/{tid}: title/page_path/updated_on が公開JSONと不一致")

    return errors
