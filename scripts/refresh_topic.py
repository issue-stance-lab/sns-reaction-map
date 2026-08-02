#!/usr/bin/env python3
"""全テーマ共通の収集・分類ランナー。公開処理だけをテーマ別adapterへ委譲する。

公開できないテーマも、収集回を履歴へ保存してバックアップするところまでは同じ経路を通る。
`--promote` を付けない限り、累積正典・公開ページ・updated_at は変更しない。
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


def previous_reports(root: Path, topic: str, before: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    base = root / "data" / "verification" / "updates" / topic
    for path in sorted(base.glob("*/report.json")):
        if path.parent.name < before:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                reports.append(value)
    return reports


def next_collection_date(root: Path, topic: str, current_date: str, report: dict[str, Any]) -> str | None:
    previous = previous_reports(root, topic, current_date)
    latest = previous[-1] if previous else None
    new = int(report.get("new", 0))
    opinions = int(report.get("opinions", 0))
    if new == 0 and latest and int(latest.get("new", -1)) == 0:
        return None
    if opinions < 20 and latest and int(latest.get("opinions", 20)) < 20:
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
        field_pattern = rf"(^    {re.escape(key)}:[ \t]*)[^#\n]*(.*$)"
        block, count = re.subn(field_pattern, rf"\g<1>{rendered}\2", block, count=1, flags=re.MULTILINE)
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
) -> None:
    themes = parse_themes_yaml(root / "THEMES.yaml")
    theme = themes[topic]
    canonical = root / str(theme["sample_file"])
    verification_path = theme.get("verification_file")
    verification = root / str(verification_path) if verification_path else None
    candidate = read_rows(stage / "cumulative-candidate.json")
    write_verification_file(stage / "cumulative-candidate.json", stage / "verification-candidate.json")

    targets = [canonical, root / "THEMES.yaml", root / "configs" / "theme-seo.json"]
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
        next_date = next_collection_date(root, topic, current_date, report)
        registry = root / "THEMES.yaml"
        registry.write_text(
            _replace_theme_fields(
                registry.read_text(encoding="utf-8"),
                topic,
                {
                    "updated_at": current_date,
                    "collect_delta": str(int(report["new"])),
                    "sample_period": sample_period(candidate),
                    "refresh_at": next_date,
                },
            ),
            encoding="utf-8",
        )
        update_seo_date(root / "configs" / "theme-seo.json", topic, current_date)
        run([sys.executable, str(root / "scripts" / "sync_issue_counts.py"), topic], label="sync issue counts", root=root)
        run([sys.executable, str(root / "scripts" / "seo" / "apply_theme_trust.py")], label="apply SEO", root=root)
        run([sys.executable, str(root / "scripts" / "sync_portal_stats.py")], label="sync portal", root=root)
        run([sys.executable, str(root / "scripts" / "seo" / "generate_seo_assets.py"), "--site-url", SITE_URL], label="generate sitemap", root=root)
        run([sys.executable, str(root / "scripts" / "verify_theme_page.py")], label="verify themes", root=root)
        run([sys.executable, str(root / "scripts" / "verify_top_page.py")], label="verify portal", root=root)
        run([sys.executable, str(root / "scripts" / "seo" / "validate_theme_seo.py")], label="verify SEO", root=root)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--backup-dest", type=Path, required=True)
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    parser.add_argument("--wait-ms", default="5000")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    date.fromisoformat(args.date)

    themes = parse_themes_yaml()
    pipelines = load_pipeline_config()
    if args.topic not in themes or args.topic not in pipelines:
        raise ValueError(f"未設定のテーマです: {args.topic}")
    theme = themes[args.topic]
    pipeline = pipelines[args.topic]
    promotion_preflight_error: ValueError | None = None
    if args.promote:
        try:
            ensure_promotion_targets_clean(ROOT, themes)
        except ValueError as exc:
            # 収集窓を失わないよう、データ層は最後まで実行してから公開だけを止める。
            promotion_preflight_error = exc
    canonical = ROOT / str(theme.get("sample_file") or "")
    refresh_config = ROOT / str(theme.get("refresh_config") or "")
    classifier = ROOT / pipeline["classifier"]
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
    record_refresh_attempt(ROOT, args.topic, args.date)

    if not args.resume and not args.skip_smoke:
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix=f"{args.topic}-smoke-") as directory:
            fetch(ROOT, queries[:1], Path(directory) / "smoke.json", args.wait_ms)
        timings["smoke_seconds"] = round(time.monotonic() - started, 2)
        write_json(timings_path, timings)

    if args.resume:
        raw = read_rows(stage / "raw.json")
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
                [sys.executable, str(classifier), "--input", str(stage / "new-only.json"), "--output", str(stage / "classified-test.json"), "--markdown", str(stage / "classified-test.md"), "--limit", str(test_count)],
                label="classify test",
            )
            validate_classified(read_rows(stage / "classified-test.json"), classifier)
            started = time.monotonic()
            run(
                [sys.executable, str(classifier), "--input", str(stage / "new-only.json"), "--output", str(stage / "classified-wave.json"), "--markdown", str(stage / "classified-wave.md")],
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
            "timings": timings,
        })

    classified = read_rows(stage / "classified-wave.json")
    write_json(stage / "cumulative-candidate.json", current + classified)
    report["next_collect_at"] = next_collection_date(ROOT, args.topic, args.date, report)
    archive_wave(ROOT, args.topic, args.date, stage, report, args.backup_dest)
    record_collection_schedule(ROOT, args.topic, args.date, report["next_collect_at"])
    report["status"] = "archived"
    write_json(stage / "report.json", report)

    if args.promote:
        if promotion_preflight_error:
            raise promotion_preflight_error
        adapter_name = pipeline.get("adapter")
        if not adapter_name or theme.get("page_update_mode") != "adapter":
            raise ValueError(f"{args.topic}: 更新回は保存済みですが、page adapterがないため公開できません")
        adapter = importlib.import_module(f"scripts.refresh_adapters.{adapter_name}")
        adapter_targets = adapter.build(ROOT, stage, args.date)
        promote(ROOT, args.topic, args.date, stage, report, adapter_targets, args.backup_dest)
        report["status"] = "promoted"
        write_json(stage / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
