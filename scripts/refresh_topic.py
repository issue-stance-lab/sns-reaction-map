#!/usr/bin/env python3
"""全テーマ共通の収集・分類ランナー。公開処理だけをテーマ別adapterへ委譲する。

公開できないテーマも、収集回を履歴へ保存してバックアップするところまでは同じ経路を通る。
`--promote` / `--apply-promotion` を付けない限り、累積正典・公開ページ・updated_at は変更しない。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

import yaml

try:
    from .sync_portal_stats import parse_themes_yaml
    from .verification_data import write_verification_file
except ImportError:
    from sync_portal_stats import parse_themes_yaml  # type: ignore[no-redef]
    from verification_data import write_verification_file  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "THEMES.yaml"
PIPELINES = ROOT / "configs" / "refresh-pipeline.yaml"
SEO_CONFIG = ROOT / "configs" / "theme-seo.json"
SITE_URL = "https://issue-stance-lab.github.io/sns-reaction-map/"


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"JSON配列が必要です: {path}")
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def identity(row: dict[str, Any]) -> str:
    tweet_id = str(row.get("tweet_id") or "").strip()
    if tweet_id:
        return f"tweet:{tweet_id}"
    url = str(row.get("url") or "").strip()
    if url:
        parts = urlsplit(url)
        status = re.search(r"/status/(\d+)", parts.path)
        if status:
            return f"tweet:{status.group(1)}"
        canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))
        return f"url:{canonical}"
    text = re.sub(r"\s+", " ", str(row.get("text") or "")).strip()
    if not text:
        raise ValueError("tweet_id、URL、本文のいずれもないレコードです")
    return "text:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def unique(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        key = identity(row)
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def run(command: list[str], *, label: str, root: Path = ROOT) -> None:
    print(f"[{label}] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=root, check=True)


def load_pipeline_config(path: Path = PIPELINES) -> dict[str, dict[str, str]]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    topics = value.get("topics") if isinstance(value, dict) else None
    if not isinstance(topics, dict):
        raise ValueError(f"topics設定がありません: {path}")
    return topics


def load_queries(path: Path) -> list[str]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    queries = value.get("fetch_queries") if isinstance(value, dict) else None
    if not isinstance(queries, list) or not queries:
        raise ValueError(f"fetch_queriesがありません: {path}")
    return [str(query) for query in queries]


def fetch(root: Path, queries: list[str], output: Path, wait_ms: str) -> None:
    command = [
        "node",
        str(root / "scripts" / "fetch_yahoo_realtime_node.mjs"),
        "--output",
        str(output),
        "--markdown",
        str(output.with_suffix(".md")),
        "--dedupe",
        "--wait-ms",
        wait_ms,
    ]
    for query in queries:
        command.extend(("--query", query))
    run(command, label=f"fetch {len(queries)} queries", root=root)


def classification(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("classification")
    return value if isinstance(value, dict) else {}


def classifier_schema(classifier: Path) -> tuple[set[str], set[str]]:
    script_dir = str(classifier.parent)
    inserted = script_dir not in sys.path
    if inserted:
        sys.path.insert(0, script_dir)
    try:
        values = runpy.run_path(str(classifier), run_name=f"refresh_schema_{classifier.stem}")
    finally:
        if inserted:
            sys.path.remove(script_dir)
    issues = values.get("ISSUES")
    stances = values.get("STANCES")
    if not isinstance(issues, (set, list, tuple)) or not isinstance(stances, (set, list, tuple)):
        raise ValueError(f"classifierにISSUES/STANCESがありません: {classifier}")
    return set(issues), set(stances)


def load_adapter(name: str):
    """テーマ別adapterを読み込む。

    `python3 scripts/refresh_topic.py` で起動すると sys.path[0] は scripts/ になり、
    `scripts.refresh_adapters.X` を解決できない（2026-08-07 の takaichi 公開でここに当たった）。
    リポジトリのルートを明示的に通してから読み込む。
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    return importlib.import_module(f"scripts.refresh_adapters.{name}")


def taxonomy_continuity(current: list[dict[str, Any]], classifier: Path) -> dict[str, Any]:
    """累積正典の既存ラベルが、分類器の宣言する taxonomy に収まっているかを見る。

    許可ラベル検査（validate_classified）は「新規分が分類器の宣言どおりか」しか見ない。
    分類器の taxonomy を作り直したのに正典を再分類していないテーマでは、累積した瞬間に
    同義ラベルが二重に並ぶ（2026-08-03 の ai-copyright で判明: 正典は「学習データ・無断利用」、
    分類器は「学習データ無断利用」）。公開すると論点カードの件数が分裂するため、
    収集前に止める。
    """
    issues, stances = classifier_schema(classifier)
    current_issues = {
        value.get("main_issue")
        for value in (classification(row) or row for row in current)
        if isinstance(value, dict) and value.get("main_issue")
    }
    current_stances = {
        value.get("stance")
        for value in (classification(row) or row for row in current)
        if isinstance(value, dict) and value.get("stance")
    }
    return {
        "compatible": bool(current_issues) and current_issues <= issues and current_stances <= stances,
        "canonical_without_main_issue": not current_issues,
        "unknown_issues": sorted(current_issues - issues),
        "unknown_stances": sorted(current_stances - stances),
    }


def validate_classified(rows: list[dict[str, Any]], classifier: Path) -> dict[str, int]:
    issues, stances = classifier_schema(classifier)
    malformed: list[str] = []
    errors = 0
    for index, row in enumerate(rows):
        value = classification(row)
        if value.get("error"):
            errors += 1
            continue
        if (
            value.get("main_issue") not in issues
            or value.get("stance") not in stances
            or not isinstance(value.get("confidence"), (int, float))
        ):
            malformed.append(str(index))
    if malformed:
        raise ValueError(f"形式不正または許可外ラベル: {len(malformed)}件")
    if rows and errors / len(rows) > 0.10:
        raise ValueError(f"分類エラー率が10%を超えました: {errors}/{len(rows)}")
    return {"classification_errors": errors}


def validate_sets(
    current: list[dict[str, Any]],
    raw: list[dict[str, Any]],
    new: list[dict[str, Any]],
    classified: list[dict[str, Any]],
) -> dict[str, Any]:
    current_ids = {identity(row) for row in current}
    raw_ids = {identity(row) for row in raw}
    new_ids = {identity(row) for row in new}
    classified_ids = {identity(row) for row in classified}
    duplicates = len(raw_ids & current_ids)
    candidate = current + classified
    candidate_ids = [identity(row) for row in candidate]
    checks = {
        "raw_equals_duplicates_plus_new": len(raw_ids) == duplicates + len(new_ids),
        "new_equals_classified": new_ids == classified_ids,
        "candidate_count": len(candidate) == len(current) + len(classified),
        "candidate_unique": len(candidate_ids) == len(set(candidate_ids)),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("集合・件数検査に失敗: " + ", ".join(failed))
    return {
        "checks": checks,
        "raw": len(raw_ids),
        "duplicates": duplicates,
        "new": len(new_ids),
        "relevant": sum(bool(classification(row).get("is_relevant")) for row in classified),
        "opinions": sum(bool(classification(row).get("is_opinion")) for row in classified),
        "opinion_flag_available": any(
            classification(row).get("is_opinion") is not None for row in classified
        ),
        "candidate": len(candidate),
    }


def _same_or_write(source: Path, target: Path) -> bool:
    """既存履歴を上書きしない。新規作成した場合はTrue。"""
    if target.exists():
        if source.read_bytes() != target.read_bytes():
            raise FileExistsError(f"同じ日付の履歴が異なる内容で存在します: {target}")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def backup_private(root: Path, destination: Path) -> None:
    try:
        destination.resolve().relative_to(root.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("バックアップ先はリポジトリ外を指定してください")
    run(
        [sys.executable, str(root / "scripts" / "backup_private_data.py"), "--dest", str(destination)],
        label="backup private data",
        root=root,
    )


def ensure_promotion_targets_clean(root: Path, themes: dict[str, dict[str, Any]]) -> None:
    """公開昇格が並行作業を取り込んだり巻き戻したりしないようにする。"""
    if not (root / ".git").exists():
        return
    paths = ["THEMES.yaml", "configs/theme-seo.json", "docs/index.html", "docs/sitemap.xml", "docs/robots.txt"]
    paths.extend(str(theme["html"]) for theme in themes.values() if theme.get("html"))
    dirty = any(
        subprocess.run(command, cwd=root).returncode
        for command in (
            ["git", "diff", "--quiet", "--", *paths],
            ["git", "diff", "--cached", "--quiet", "--", *paths],
        )
    )
    if dirty:
        raise ValueError("公開対象に未コミット差分があります。収集だけ行う場合は--promoteを外してください")


def archive_wave(
    root: Path,
    topic: str,
    current_date: str,
    stage: Path,
    report: dict[str, Any],
    backup_destination: Path,
    *,
    backup_func: Callable[[Path, Path], None] = backup_private,
) -> None:
    """非公開履歴を確定してバックアップ後、公開検証サマリを保存する。"""
    private = root / "social-samples" / "updates" / topic / current_date
    public = root / "data" / "verification" / "updates" / topic / current_date
    write_json(stage / "report.json", report)
    created: list[Path] = []
    try:
        for source_name, target_name in (
            ("raw.json", "raw.json"),
            ("classified-wave.json", "classified.json"),
            ("report.json", "report.json"),
        ):
            if _same_or_write(stage / source_name, private / target_name):
                created.append(private / target_name)
        backup_func(root, backup_destination)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        if private.exists() and not any(private.iterdir()):
            private.rmdir()
        raise

    write_verification_file(stage / "raw.json", stage / "raw-verification.json")
    write_verification_file(stage / "classified-wave.json", stage / "classified-wave-verification.json")
    write_json(stage / "report-verification.json", {
        key: value for key, value in report.items() if key not in {"queries"}
    })
    for source_name, target_name in (
        ("raw-verification.json", "raw.json"),
        ("classified-wave-verification.json", "classified.json"),
        ("report-verification.json", "report.json"),
    ):
        _same_or_write(stage / source_name, public / target_name)


def prepare_archived_resume(
    root: Path,
    topic: str,
    current_date: str,
    stage: Path,
    current: list[dict[str, Any]],
    include_waves: list[str] | None = None,
) -> dict[str, Any] | None:
    """保存済み更新回を改変せず、現在の正典へ足せる分だけをstageへ戻す。

    収集後に別の更新回が正典へ統合されると、当時は新規だった投稿の一部が
    公開時点では重複になる。収集履歴は当時の事実として残し、累積候補だけを
    現在の正典に対して再重複判定する。

    include_waves を渡すと、まだ公開していない過去の更新回も同じ候補へ畳み込む。
    公開できない期間に収集だけが進むと更新回が溜まり、1回ずつ公開しようとすると
    途中の状態が「収集期限が過ぎている」で必ず落ちるため（自転車青切符でも
    2回分をまとめて統合した）。保管された更新回そのものは書き換えない。
    """
    dates = sorted(set(include_waves or []) | {current_date})
    archives = {
        date: {
            "raw": root / "social-samples" / "updates" / topic / date / "raw.json",
            "classified": root / "social-samples" / "updates" / topic / date / "classified.json",
            "report": root / "social-samples" / "updates" / topic / date / "report.json",
        }
        for date in dates
    }
    if not all(path.is_file() for paths in archives.values() for path in paths.values()):
        return None

    raw = read_rows(stage / "raw.json")
    archived_raw_ids = {
        identity(row) for paths in archives.values() for row in read_rows(paths["raw"])
    }
    if {identity(row) for row in raw} != archived_raw_ids:
        label = "・".join(dates)
        raise ValueError(f"{topic}: resume対象のrawが保存済み{label}更新回と一致しません")

    current_ids = {identity(row) for row in current}
    publishable: list[dict[str, Any]] = []
    classified_union: set[str] = set()
    seen = set(current_ids)
    for date in dates:
        paths = archives[date]
        archived_classified = read_rows(paths["classified"])
        archived_ids = {identity(row) for row in archived_classified}
        raw_ids = {identity(row) for row in read_rows(paths["raw"])}
        if not archived_ids <= raw_ids:
            raise ValueError(f"{topic}: 保存済みclassified（{date}）にraw由来でない投稿があります")
        if not raw_ids - archived_ids <= current_ids:
            raise ValueError(f"{topic}: 保存時に除外された重複投稿を現在の正典で確認できません（{date}）")
        # 同じ投稿が複数の更新回で新規と判定されている（どの回も同じ正典と比べたため）。
        # 先に収集した回のものを残す。
        added = [row for row in archived_classified if identity(row) not in seen]
        seen |= {identity(row) for row in added}
        classified_union |= archived_ids
        publishable.extend(added)
    if {identity(row) for row in publishable} != classified_union - current_ids:
        raise ValueError(f"{topic}: 保存済み更新回から公開候補を再構成できません")

    write_json(stage / "new-only.json", publishable)
    write_json(stage / "classified-wave.json", publishable)
    saved_report = json.loads(paths["report"].read_text(encoding="utf-8"))
    if not isinstance(saved_report, dict):
        raise ValueError(f"{topic}: 保存済みreportがJSONオブジェクトではありません")
    return saved_report


def previous_reports(root: Path, topic: str, before: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    base = root / "data" / "verification" / "updates" / topic
    for path in sorted(base.glob("*/report.json")):
        if path.parent.name < before:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                reports.append(value)
    return reports


def new_opinion_count(report: dict[str, Any]) -> int:
    """周期判定に使う「今回の新規意見」件数。

    分類器が is_opinion を出力するテーマでは opinions がその件数になる。
    出力しないテーマ（憲法改正など）では opinions が常に0になり、何件集めても
    既定14日→28日へ流れてしまうため、新規件数そのものを代わりに使う。

    opinion_flag_available を持たない過去のレポートは、opinions が1件以上あれば
    出力ありとみなす（既存4テーマの履歴はこれで正しく判定できる）。
    """
    opinions = int(report.get("opinions", 0) or 0)
    available = report.get("opinion_flag_available")
    if available is None:
        available = opinions > 0
    return opinions if available else int(report.get("new", 0) or 0)


def next_collection_date(root: Path, topic: str, current_date: str, report: dict[str, Any]) -> str | None:
    previous = previous_reports(root, topic, current_date)
    latest = previous[-1] if previous else None
    new = int(report.get("new", 0))
    opinions = new_opinion_count(report)
    if new == 0 and latest and int(latest.get("new", -1)) == 0:
        return None
    if opinions < 20 and latest and new_opinion_count(latest) < 20:
        days = 28
    elif opinions >= 50:
        days = 7
    else:
        days = 14
    return (date.fromisoformat(current_date) + timedelta(days=days)).isoformat()


def _replace_theme_fields(text: str, topic: str, fields: dict[str, str | None]) -> str:
    pattern = rf"(^  {re.escape(topic)}:\n)(.*?)(?=^  [\w-]+:\n|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"THEMES.yamlにテーマがありません: {topic}")
    block = match.group(2)
    for key, value in fields.items():
        rendered = "" if value is None else value
        field_pattern = rf"(^    {re.escape(key)}:)[ \t]*[^#\n]*(.*$)"

        def replace_field(field_match: re.Match[str]) -> str:
            suffix = field_match.group(2)
            comment = f" {suffix}" if suffix else ""
            return f"{field_match.group(1)} {rendered}{comment}"

        block, count = re.subn(
            field_pattern, replace_field, block, count=1, flags=re.MULTILINE
        )
        if count == 0:
            anchor = re.search(r"^    refresh_at:.*$", block, flags=re.MULTILINE)
            if not anchor:
                raise ValueError(f"THEMES.yamlの挿入位置がありません: {topic}.{key}")
            block = block[:anchor.end()] + f"\n    {key}: {rendered}" + block[anchor.end():]
    return text[:match.start(2)] + block + text[match.end(2):]


def record_collection_schedule(root: Path, topic: str, current_date: str, next_date: str | None) -> None:
    path = root / "THEMES.yaml"
    text = _replace_theme_fields(
        path.read_text(encoding="utf-8"),
        topic,
        {
            "collect_at": next_date,
            "collect_mode": "event-driven" if next_date is None else "scheduled",
            "last_refresh_attempt_at": current_date,
        },
    )
    path.write_text(text, encoding="utf-8")


def record_refresh_attempt(root: Path, topic: str, current_date: str) -> None:
    """疎通・収集に失敗しても試行日は残し、collect_atは進めない。"""
    path = root / "THEMES.yaml"
    path.write_text(
        _replace_theme_fields(
            path.read_text(encoding="utf-8"),
            topic,
            {"last_refresh_attempt_at": current_date},
        ),
        encoding="utf-8",
    )


def sample_period(rows: list[dict[str, Any]]) -> str:
    values = [str(row.get("fetched_at") or "")[:10] for row in rows]
    if not values or any(not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) for value in values):
        return "unknown"
    return values[0] if min(values) == max(values) else f'"{min(values)}〜{max(values)}"'


def update_seo_date(path: Path, topic: str, current_date: str) -> None:
    config = json.loads(path.read_text(encoding="utf-8"))
    theme = next(item for item in config["themes"] if item["id"] == topic)
    theme["dateModified"] = current_date
    write_json(path, config)


def promote(
    root: Path,
    topic: str,
    current_date: str,
    stage: Path,
    report: dict[str, Any],
    adapter_targets: dict[Path, Path],
    backup_destination: Path,
    adapter: Any = None,
) -> None:
    themes = parse_themes_yaml(root / "THEMES.yaml")
    theme = themes[topic]
    canonical = root / str(theme["sample_file"])
    verification_path = theme.get("verification_file")
    verification = root / str(verification_path) if verification_path else None
    candidate = read_rows(stage / "cumulative-candidate.json")
    write_verification_file(stage / "cumulative-candidate.json", stage / "verification-candidate.json")

    targets = [
        canonical,
        root / "THEMES.yaml",
        root / "configs" / "theme-seo.json",
        root / "data" / "verification" / "sample-periods.json",
    ]
    if verification:
        targets.append(verification)
    targets.extend(root / relative for relative in adapter_targets)
    targets.extend(
        root / str(item["html"])
        for item in themes.values()
        if item.get("published") and item.get("html")
    )
    targets = list(dict.fromkeys(targets))
    targets.extend((root / "docs" / "index.html", root / "docs" / "sitemap.xml", root / "docs" / "robots.txt"))
    existing = {path for path in targets if path.exists()}
    rollback = stage / "promotion-backup"
    for path in targets:
        if path.exists():
            saved = rollback / path.relative_to(root)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)
    try:
        shutil.copy2(stage / "cumulative-candidate.json", canonical)
        if verification:
            shutil.copy2(stage / "verification-candidate.json", verification)
        for relative, source in adapter_targets.items():
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        next_date = (
            report["next_collect_at"]
            if "next_collect_at" in report
            else next_collection_date(root, topic, current_date, report)
        )
        registry = root / "THEMES.yaml"
        # sample_period_source: owner_confirmed のテーマは、オーナーが確定させた期間を正とする。
        # 上書きすると取得日を持たない古い行のせいで "unknown" になり、
        # verify_sample_periods.py の owner_confirmed 検査（日付形式であること）で必ず落ちる。
        fields = {
            "updated_at": current_date,
            "collect_delta": str(int(report["new"])),
            "refresh_at": next_date,
        }
        if theme.get("sample_period_source") != "owner_confirmed":
            fields["sample_period"] = sample_period(candidate)
        registry.write_text(
            _replace_theme_fields(
                registry.read_text(encoding="utf-8"),
                topic,
                fields,
            ),
            encoding="utf-8",
        )
        update_seo_date(root / "configs" / "theme-seo.json", topic, current_date)
        # 調査条件（取得元・期間・件数）はTHEMES.yamlの新しい値を読む。候補ページを組み立てる
        # build()の時点では台帳がまだ旧期間なので、昇格してからadapterに貼り直させる。
        finalize = getattr(adapter, "finalize", None)
        if finalize is not None:
            finalize(root, current_date)
        run([sys.executable, str(root / "scripts" / "sync_issue_counts.py"), topic], label="sync issue counts", root=root)
        run([sys.executable, str(root / "scripts" / "seo" / "apply_theme_trust.py")], label="apply SEO", root=root)
        run([sys.executable, str(root / "scripts" / "sync_portal_stats.py")], label="sync portal", root=root)
        run([sys.executable, str(root / "scripts" / "seo" / "generate_seo_assets.py"), "--site-url", SITE_URL], label="generate sitemap", root=root)
        # 収集日の検証メタデータはGit管理側にあり、正典が増えると台帳のsample_periodと
        # ズレる。--generate は貼り直したうえで検証まで行うので、ここが不一致のゲートになる。
        run([sys.executable, str(root / "scripts" / "verify_sample_periods.py"), "--generate"], label="sync sample periods", root=root)
        run([sys.executable, str(root / "scripts" / "verify_theme_page.py")], label="verify themes", root=root)
        run([sys.executable, str(root / "scripts" / "verify_number_provenance.py")], label="verify number provenance", root=root)
        run([sys.executable, str(root / "scripts" / "verify_top_page.py")], label="verify portal", root=root)
        run([sys.executable, str(root / "scripts" / "seo" / "validate_theme_seo.py")], label="verify SEO", root=root)
        run([sys.executable, str(root / "scripts" / "build_data_sheet.py")], label="update DATA_SHEET", root=root)
        backup_private(root, backup_destination)
    except Exception:
        for path in targets:
            saved = rollback / path.relative_to(root)
            if saved.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(saved, path)
            elif path not in existing and path.is_file():
                path.unlink()
        raise


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_promotion_manifest(
    root: Path,
    topic: str,
    current_date: str,
    run_id: str,
    stage: Path,
    report: dict[str, Any],
    adapter_targets: dict[Path, Path],
) -> dict[str, Any]:
    """Bind an approval candidate to exact staged bytes without mutating public files."""
    write_verification_file(stage / "cumulative-candidate.json", stage / "verification-candidate.json")
    files = [
        {"role": "canonical", "target": str(parse_themes_yaml(root / "THEMES.yaml")[topic]["sample_file"]), "source": str((stage / "cumulative-candidate.json").relative_to(root))},
        *[
            {"role": "page", "target": str(target), "source": str(source.relative_to(root))}
            for target, source in adapter_targets.items()
        ],
    ]
    for item in files:
        source = root / item["source"]
        if not source.is_file():
            raise FileNotFoundError(f"公開候補がありません: {source}")
        item["sha256"] = _file_sha256(source)
        item["bytes"] = source.stat().st_size
    manifest = {
        "version": 1,
        "status": "prepared",
        "topic": topic,
        "date": current_date,
        "run_id": run_id,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report": {
            "raw": report.get("raw"),
            "new": report.get("new"),
            "opinions": report.get("opinions"),
            "next_collect_at": report.get("next_collect_at"),
        },
        "files": files,
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    path = stage / "promotion-manifest.json"
    manifest["manifest_path"] = str(path.relative_to(root))
    write_json(path, manifest)
    return manifest


def load_promotion_manifest(root: Path, stage: Path, topic: str, current_date: str, run_id: str) -> tuple[dict[str, Any], dict[Path, Path]]:
    path = stage / "promotion-manifest.json"
    if not path.is_file():
        raise FileNotFoundError("承認対象の promotion-manifest.json がありません。先に --prepare-promotion を実行してください")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("topic"), manifest.get("date"), manifest.get("run_id")) != (topic, current_date, run_id):
        raise ValueError("manifest のテーマ・日付・run-id が今回の公開対象と一致しません")
    unsigned = {key: value for key, value in manifest.items() if key not in {"manifest_sha256", "manifest_path"}}
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected_manifest_hash = hashlib.sha256(canonical).hexdigest()
    if manifest.get("manifest_sha256") != expected_manifest_hash:
        raise ValueError("promotion-manifest.json が準備後に変更されています。公開候補を作り直してください")
    targets: dict[Path, Path] = {}
    for item in manifest.get("files") or []:
        source = (root / str(item["source"])).resolve()
        try:
            source.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError("manifest の候補ファイルがリポジトリ外を指しています") from exc
        if not source.is_file() or _file_sha256(source) != item.get("sha256"):
            raise ValueError(f"承認後に公開候補が変わりました: {item.get('source')}")
        if item.get("role") == "page":
            targets[Path(str(item["target"]))] = source
    if not targets:
        raise ValueError("manifest に公開ページ候補がありません")
    return manifest, targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--backup-dest", type=Path, required=True)
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    parser.add_argument("--wait-ms", default="5000")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--include-wave",
        action="append",
        default=[],
        metavar="YYYY-MM-DD",
        help="まだ公開していない過去の更新回も同じ候補へ畳み込む（--resume と併用。複数回指定可）",
    )
    parser.add_argument("--promote", action="store_true")
    parser.add_argument(
        "--prepare-promotion",
        action="store_true",
        help="公開候補とハッシュmanifestだけを作り、正典・公開ページは変更しない",
    )
    parser.add_argument(
        "--apply-promotion",
        action="store_true",
        help="--prepare-promotionで固定した候補をハッシュ確認後に公開へ反映する",
    )
    parser.add_argument(
        "--allow-taxonomy-mismatch",
        action="store_true",
        help="正典と分類器の taxonomy が違っても更新回の保管だけ行う（公開は不可）",
    )
    args = parser.parse_args()
    date.fromisoformat(args.date)
    selected_modes = sum(bool(value) for value in (args.promote, args.prepare_promotion, args.apply_promotion))
    if selected_modes > 1:
        raise ValueError("--promote / --prepare-promotion / --apply-promotion は同時に指定できません")
    if (args.prepare_promotion or args.apply_promotion) and not args.resume:
        raise ValueError("承認前後の公開処理は保存済み更新回を使うため --resume と併用してください")

    themes = parse_themes_yaml()
    pipelines = load_pipeline_config()
    if args.topic not in themes or args.topic not in pipelines:
        raise ValueError(f"未設定のテーマです: {args.topic}")
    theme = themes[args.topic]
    pipeline = pipelines[args.topic]
    if args.include_wave and not args.resume:
        raise ValueError("--include-wave は保存済み更新回を畳み込む指定なので --resume と併用してください")
    if args.date in args.include_wave:
        raise ValueError("--include-wave に --date と同じ日付は指定できません")
    promotion_preflight_error: ValueError | None = None
    if args.promote or args.apply_promotion:
        try:
            ensure_promotion_targets_clean(ROOT, themes)
        except ValueError as exc:
            # 収集窓を失わないよう、データ層は最後まで実行してから公開だけを止める。
            promotion_preflight_error = exc
    canonical = ROOT / str(theme.get("sample_file") or "")
    refresh_config = ROOT / str(theme.get("refresh_config") or "")
    classifier = ROOT / pipeline["classifier"]
    classifier_args = [str(value) for value in (pipeline.get("classifier_args") or [])]
    for label, path in (("sample_file", canonical), ("refresh_config", refresh_config), ("classifier", classifier)):
        if not path.is_file():
            raise FileNotFoundError(f"{args.topic}: {label}がありません: {path}")
    try:
        args.backup_dest.resolve().relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("--backup-destはリポジトリ外を指定してください")

    stage = ROOT / ".staging" / "refresh" / args.topic / args.run_id
    if stage.exists() and not args.resume:
        raise FileExistsError(stage)
    stage.mkdir(parents=True, exist_ok=args.resume)
    timings_path = stage / "timings.json"
    timings: dict[str, float] = json.loads(timings_path.read_text(encoding="utf-8")) if args.resume and timings_path.exists() else {}
    current = read_rows(canonical)
    queries = load_queries(refresh_config)

    taxonomy = taxonomy_continuity(current, classifier)
    if not taxonomy["compatible"]:
        if taxonomy["canonical_without_main_issue"]:
            reason = f"{canonical.name} に main_issue がない（論点別に累積できない）"
        else:
            parts = []
            if taxonomy["unknown_issues"]:
                parts.append(f"論点 {taxonomy['unknown_issues']}")
            if taxonomy["unknown_stances"]:
                parts.append(f"立場 {taxonomy['unknown_stances']}")
            reason = f"正典にある {' / '.join(parts)} を分類器が生成しない"
        message = (
            f"{args.topic}: 正典と分類器の taxonomy が一致しません。{reason}。"
            f" このまま累積すると同義ラベルが分裂します。正典を単一 taxonomy へ再分類してから実行するか、"
            f" 更新回の保管だけが目的なら --allow-taxonomy-mismatch を付けてください（--promote は使えません）。"
        )
        if not args.allow_taxonomy_mismatch:
            raise ValueError(message)
        if args.promote or args.prepare_promotion or args.apply_promotion:
            raise ValueError(f"{args.topic}: taxonomy不一致のまま公開候補を作成・反映できません")
        print(f"WARN {message}")

    record_refresh_attempt(ROOT, args.topic, args.date)

    if not args.resume and not args.skip_smoke:
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix=f"{args.topic}-smoke-") as directory:
            fetch(ROOT, queries[:1], Path(directory) / "smoke.json", args.wait_ms)
        timings["smoke_seconds"] = round(time.monotonic() - started, 2)
        write_json(timings_path, timings)

    archived_report: dict[str, Any] | None = None
    if args.resume:
        raw = read_rows(stage / "raw.json")
        new = read_rows(stage / "new-only.json")
        archived_report = prepare_archived_resume(
            ROOT, args.topic, args.date, stage, current, args.include_wave
        )
        if archived_report is not None:
            new = read_rows(stage / "new-only.json")
    else:
        started = time.monotonic()
        fetch(ROOT, queries, stage / "raw.json", args.wait_ms)
        raw = unique(read_rows(stage / "raw.json"))
        write_json(stage / "raw.json", raw)
        current_ids = {identity(row) for row in current}
        new = [row for row in raw if identity(row) not in current_ids]
        write_json(stage / "new-only.json", new)
        timings["fetch_seconds"] = round(time.monotonic() - started, 2)
        write_json(timings_path, timings)

    if not new:
        write_json(stage / "classified-wave.json", [])
        report = {
            "status": "validated-no-new-records",
            "topic": args.topic,
            "date": args.date,
            "run_id": args.run_id,
            "raw": len(raw),
            "new": 0,
            "relevant": 0,
            "opinions": 0,
            "queries": queries,
            "taxonomy": taxonomy,
            "timings": timings,
        }
    else:
        test_count = min(10, len(new))
        reusable = args.resume and (stage / "classified-wave.json").exists()
        classified = read_rows(stage / "classified-wave.json") if reusable else []
        if reusable and {identity(row) for row in classified} != {identity(row) for row in new}:
            reusable = False
        if not reusable:
            run(
                [sys.executable, str(classifier), "--input", str(stage / "new-only.json"), "--output", str(stage / "classified-test.json"), "--markdown", str(stage / "classified-test.md"), "--limit", str(test_count), *classifier_args],
                label="classify test",
            )
            validate_classified(read_rows(stage / "classified-test.json"), classifier)
            started = time.monotonic()
            run(
                [sys.executable, str(classifier), "--input", str(stage / "new-only.json"), "--output", str(stage / "classified-wave.json"), "--markdown", str(stage / "classified-wave.md"), *classifier_args],
                label="classify full",
            )
            classified = read_rows(stage / "classified-wave.json")
            timings["classify_seconds"] = round(time.monotonic() - started, 2)
            write_json(timings_path, timings)
        quality = validate_classified(classified, classifier)
        report = validate_sets(current, raw, new, classified)
        report.update(quality)
        report.update({
            "status": "validated",
            "topic": args.topic,
            "date": args.date,
            "run_id": args.run_id,
            "queries": queries,
            "taxonomy": taxonomy,
            "timings": timings,
        })

    classified = read_rows(stage / "classified-wave.json")
    write_json(stage / "cumulative-candidate.json", current + classified)
    if archived_report is not None:
        report["next_collect_at"] = archived_report.get("next_collect_at")
        report["saved_wave_new"] = int(archived_report.get("new", 0) or 0)
        report["saved_wave_opinions"] = int(archived_report.get("opinions", 0) or 0)
    else:
        report["next_collect_at"] = next_collection_date(ROOT, args.topic, args.date, report)
        archive_wave(ROOT, args.topic, args.date, stage, report, args.backup_dest)
        record_collection_schedule(ROOT, args.topic, args.date, report["next_collect_at"])
    report["status"] = "archived"
    write_json(stage / "report.json", report)

    if args.promote or args.prepare_promotion or args.apply_promotion:
        adapter_name = pipeline.get("adapter")
        if not adapter_name or theme.get("page_update_mode") != "adapter":
            raise ValueError(f"{args.topic}: 更新回は保存済みですが、page adapterがないため公開できません")
        adapter = load_adapter(adapter_name)

    if args.prepare_promotion:
        adapter_targets = adapter.build(ROOT, stage, args.date)
        manifest = prepare_promotion_manifest(ROOT, args.topic, args.date, args.run_id, stage, report, adapter_targets)
        report["status"] = "prepared"
        report["promotion_manifest"] = manifest["manifest_path"]
        report["promotion_manifest_sha256"] = manifest["manifest_sha256"]
        write_json(stage / "report.json", report)
    elif args.apply_promotion:
        if promotion_preflight_error:
            raise promotion_preflight_error
        manifest, adapter_targets = load_promotion_manifest(ROOT, stage, args.topic, args.date, args.run_id)
        promote(ROOT, args.topic, args.date, stage, report, adapter_targets, args.backup_dest, adapter)
        report["status"] = "promoted"
        report["promotion_manifest"] = manifest["manifest_path"]
        report["promotion_manifest_sha256"] = manifest["manifest_sha256"]
        write_json(stage / "report.json", report)
    elif args.promote:
        if promotion_preflight_error:
            raise promotion_preflight_error
        adapter_targets = adapter.build(ROOT, stage, args.date)
        promote(ROOT, args.topic, args.date, stage, report, adapter_targets, args.backup_dest, adapter)
        report["status"] = "promoted"
        write_json(stage / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
