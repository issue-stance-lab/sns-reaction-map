#!/usr/bin/env python3
"""部活動テーマの差分収集を staging で検証し、合格時だけ公開する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import yaml

try:
    from .bukatsu_taxonomy import ISSUES, STANCES, TOPIC_ID, VOTE_ISSUES, VOTE_STANCES
    from .sync_portal_stats import parse_themes_yaml
    from .verification_data import write_verification_file
except ImportError:
    from bukatsu_taxonomy import ISSUES, STANCES, TOPIC_ID, VOTE_ISSUES, VOTE_STANCES  # type: ignore[no-redef]
    from sync_portal_stats import parse_themes_yaml  # type: ignore[no-redef]
    from verification_data import write_verification_file  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
SLUG = "bukatsu-chiiki"
PAGE = ROOT / "docs" / "bukatsu-chiiki-reaction-map.html"
THEMES = ROOT / "THEMES.yaml"
SEO_CONFIG = ROOT / "configs" / "theme-seo.json"
SITE_URL = "https://issue-stance-lab.github.io/sns-reaction-map/"
PROTECTED = ("G-K10S4YCZFH", "ca-pub-2542211932832864", "vote-store.js", TOPIC_ID)


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"JSON array of objects required: {path}")
    return rows


def collection_date(row: dict[str, Any]) -> str:
    return str(row.get("fetched_at") or "")[:10]


def previous_collection_date(rows: list[dict[str, Any]], current_date: str) -> str:
    """潮目の比較対象になる前回の収集日を、正典から決める。

    今回より前でいちばん新しい収集日が前回にあたる。以前はここが日付のべた書きで、
    更新のたびに手で書き換える必要があった。書き換え忘れても件数チェックは前々回の
    件数で通ってしまい、1回分ずれた比較がそのまま公開される事故になっていた。
    """
    dates = {collection_date(row) for row in rows}
    candidates = sorted(
        date for date in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) and date < current_date
    )
    if not candidates:
        raise ValueError(f"{current_date} より前の収集日が正典にありません")
    return candidates[-1]


def previous_wave(rows: list[dict[str, Any]], current_date: str) -> tuple[str, list[dict[str, Any]]]:
    """前回の収集日と、その日に収集した行を返す。"""
    previous_date = previous_collection_date(rows, current_date)
    wave = [row for row in rows if collection_date(row) == previous_date]
    if not wave:
        raise ValueError(f"前回更新回（{previous_date}）の行が正典にありません")
    return previous_date, wave


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
        canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))
        return f"url:{canonical}"
    text = re.sub(r"\s+", " ", str(row.get("text") or "")).strip()
    if not text:
        raise ValueError("record has no tweet_id, URL, or text")
    return "text:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def unique(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for row in rows:
        key = identity(row)
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def run(command: list[str], *, label: str, cwd: Path = ROOT) -> None:
    print(f"[{label}] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def load_queries(refresh_config: Path) -> list[str]:
    config = yaml.safe_load(refresh_config.read_text(encoding="utf-8"))
    queries = config.get("fetch_queries") if isinstance(config, dict) else None
    if not isinstance(queries, list) or len(queries) != 10:
        raise ValueError(f"exactly 10 fetch_queries required: {refresh_config}")
    return [str(query) for query in queries]


def fetch(queries: list[str], output: Path) -> None:
    command = [
        "node", str(ROOT / "scripts" / "fetch_yahoo_realtime_node.mjs"),
        "--output", str(output), "--markdown", str(output.with_suffix(".md")),
        "--dedupe", "--wait-ms", "5000",
    ]
    for query in queries:
        command.extend(("--query", query))
    run(command, label=f"fetch {len(queries)} queries")


def classification(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("classification")
    return value if isinstance(value, dict) else {}


def validate_classified(rows: list[dict[str, Any]]) -> None:
    invalid = []
    for row in rows:
        value = classification(row)
        if value.get("main_issue") not in ISSUES or value.get("stance") not in STANCES:
            invalid.append(identity(row))
        if not isinstance(value.get("confidence"), (int, float)):
            invalid.append(identity(row))
    if invalid:
        raise ValueError(f"invalid classifications: {len(set(invalid))}")


def sync_candidate_issue_counts(page: str, rows: list[dict[str, Any]]) -> str:
    opinions = [row for row in rows if classification(row).get("is_opinion")]
    counts = {issue: sum(classification(row).get("main_issue") == issue for row in opinions) for issue in ISSUES}
    config = json.loads((ROOT / "configs" / "bukatsu-chiiki-reaction-map.json").read_text(encoding="utf-8"))
    for card in config["issue_counts"]["cards"]:
        count = sum(counts.get(label, 0) for label in card["main_issue"])
        pattern = rf'(<span class="explainer-count" id="issue-count-{SLUG}-{re.escape(card["slug"])}">)[\d,]+件(</span>)'
        page, matched = re.subn(pattern, rf"\g<1>{count:,}件\g<2>", page, count=1)
        if matched != 1:
            raise ValueError(f"candidate issue count marker missing: {card['slug']}")
    return page


def validate_candidate(current: list[dict[str, Any]], raw: list[dict[str, Any]], new: list[dict[str, Any]], classified: list[dict[str, Any]], candidate: list[dict[str, Any]], page: str) -> dict[str, Any]:
    current_ids = {identity(row) for row in current}
    raw_ids = {identity(row) for row in raw}
    new_ids = {identity(row) for row in new}
    classified_ids = {identity(row) for row in classified}
    candidate_ids = [identity(row) for row in candidate]
    duplicates = len(raw_ids & current_ids)
    checks = {
        "raw_equals_duplicates_plus_new": len(raw_ids) == duplicates + len(new_ids),
        "new_equals_classified": new_ids == classified_ids,
        "candidate_count": len(candidate) == len(current) + len(classified),
        "candidate_unique": len(candidate_ids) == len(set(candidate_ids)),
        "topic_v1": f"var TOPIC='{TOPIC_ID}'" in page,
        "vote_choices_21": len(VOTE_ISSUES) * len(VOTE_STANCES) == 21,
        "protected_tokens": all(page.count(token) == PAGE.read_text(encoding="utf-8").count(token) for token in PROTECTED),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("candidate validation failed: " + ", ".join(failed))
    opinions = sum(bool(classification(row).get("is_opinion")) for row in classified)
    relevant = sum(bool(classification(row).get("is_relevant")) for row in classified)
    return {"checks": checks, "raw": len(raw_ids), "duplicates": duplicates, "new": len(new_ids), "relevant": relevant, "opinions": opinions, "candidate": len(candidate)}


def update_theme_registry(text: str, current_date: str, delta: int, next_date: str) -> str:
    block_pattern = r"(^  bukatsu-chiiki:\n)(.*?)(?=^  [\w-]+:\n)"
    match = re.search(block_pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError("bukatsu theme block missing")
    block = match.group(2)
    replacements = {
        "sample_period": f'"2026-06-27〜{current_date}"',
        "refresh_at": next_date,
        "updated_at": current_date,
        "collect_delta": str(delta),
    }
    for key, value in replacements.items():
        block, count = re.subn(rf"(^    {key}:\s*)[^#\n]*(.*$)", rf"\g<1>{value}\2", block, count=1, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"THEMES field missing: {key}")
    if re.search(r"^    last_refresh_attempt_at:", block, flags=re.MULTILINE):
        block = re.sub(r"(^    last_refresh_attempt_at:\s*)[^#\n]*", rf"\g<1>{current_date}", block, count=1, flags=re.MULTILINE)
    else:
        block = re.sub(r"(^    refresh_at:.*$)", rf"\1\n    last_refresh_attempt_at: {current_date}", block, count=1, flags=re.MULTILINE)
    return text[:match.start(2)] + block + text[match.end(2):]


def update_seo_date(path: Path, current_date: str) -> None:
    config = json.loads(path.read_text(encoding="utf-8"))
    theme = next(item for item in config["themes"] if item["id"] == SLUG)
    theme["dateModified"] = current_date
    write_json(path, config)


def promote(stage: Path, current_date: str, report: dict[str, Any]) -> None:
    themes = parse_themes_yaml()
    canonical = ROOT / themes[SLUG]["sample_file"]
    verification = ROOT / themes[SLUG]["verification_file"]
    history = ROOT / "social-samples" / "updates" / SLUG / current_date
    public_history = ROOT / "data" / "verification" / "updates" / SLUG / current_date
    public_raw = public_history / "raw.json"
    public_classified = public_history / "classified.json"
    private_raw = history / "raw.json"
    private_classified = history / "classified.json"
    targets = [canonical, verification, private_raw, private_classified, public_raw, public_classified, PAGE, THEMES, SEO_CONFIG, ROOT / "docs" / "index.html", ROOT / "docs" / "sitemap.xml", ROOT / "docs" / "robots.txt"]
    existing_targets = {target for target in targets if target.exists()}
    backup = stage / "backup"
    backup.mkdir(exist_ok=True)
    for target in targets:
        if target.exists():
            saved = backup / target.relative_to(ROOT)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
    try:
        shutil.copy2(stage / "cumulative-candidate.json", canonical)
        shutil.copy2(stage / "verification-candidate.json", verification)
        public_history.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / "raw-verification.json", public_raw)
        shutil.copy2(stage / "classified-wave-verification.json", public_classified)
        shutil.copy2(stage / "page-candidate.html", PAGE)
        history.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / "raw.json", private_raw)
        shutil.copy2(stage / "classified-wave.json", private_classified)
        opinions = int(report["opinions"])
        interval = 7 if opinions >= 50 else 14
        next_date = (date.fromisoformat(current_date) + timedelta(days=interval)).isoformat()
        THEMES.write_text(update_theme_registry(THEMES.read_text(encoding="utf-8"), current_date, int(report["new"]), next_date), encoding="utf-8")
        update_seo_date(SEO_CONFIG, current_date)
        run([sys.executable, str(ROOT / "scripts" / "build_bukatsu_arena.py")], label="sync research conditions")
        run([sys.executable, str(ROOT / "scripts" / "sync_issue_counts.py"), SLUG], label="sync issue counts")
        run([sys.executable, str(ROOT / "scripts" / "seo" / "apply_theme_trust.py")], label="apply SEO")
        run([sys.executable, str(ROOT / "scripts" / "sync_portal_stats.py")], label="sync portal")
        run([sys.executable, str(ROOT / "scripts" / "seo" / "generate_seo_assets.py"), "--site-url", SITE_URL], label="generate sitemap")
        run([sys.executable, str(ROOT / "scripts" / "verify_top_page.py")], label="verify portal")
        run([sys.executable, str(ROOT / "scripts" / "seo" / "validate_theme_seo.py")], label="verify SEO")
        run([sys.executable, "-m", "unittest", "tests.test_bukatsu_taxonomy", "tests.test_portal_stats"], label="unit tests")
    except Exception:
        for target in targets:
            saved = backup / target.relative_to(ROOT)
            if saved.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(saved, target)
            elif target not in existing_targets and target.is_file():
                target.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--no-promote", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    date.fromisoformat(args.date)
    stage = ROOT / ".staging" / "refresh" / SLUG / args.run_id
    if stage.exists() and not args.resume:
        raise FileExistsError(stage)
    stage.mkdir(parents=True, exist_ok=args.resume)
    timing_path = stage / "timings.json"
    timings: dict[str, float] = json.loads(timing_path.read_text(encoding="utf-8")) if args.resume and timing_path.exists() else {}
    themes = parse_themes_yaml()
    theme = themes[SLUG]
    canonical = ROOT / str(theme["sample_file"])
    refresh_config = ROOT / str(theme["refresh_config"])
    current = read_rows(canonical)
    queries = load_queries(refresh_config)

    if not args.resume and not args.skip_smoke:
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="bukatsu-smoke-") as directory:
            fetch(queries[:1], Path(directory) / "smoke.json")
        timings["smoke_seconds"] = round(time.monotonic() - started, 2)
        write_json(timing_path, timings)

    current_ids = {identity(row) for row in current}
    if args.resume:
        raw = read_rows(stage / "raw.json")
        new = read_rows(stage / "new-only.json")
    else:
        started = time.monotonic()
        fetch(queries, stage / "raw.json")
        raw = unique(read_rows(stage / "raw.json"))
        write_json(stage / "raw.json", raw)
        new = [row for row in raw if identity(row) not in current_ids]
        write_json(stage / "new-only.json", new)
        timings["fetch_seconds"] = round(time.monotonic() - started, 2)
        write_json(timing_path, timings)
    if not new:
        report = {"status": "no-new-records", "raw": len(raw), "new": 0, "timings": timings}
        write_json(stage / "report.json", report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    classifier = ROOT / "scripts" / "classify_bukatsu_arena_hermes.py"
    if args.resume and (stage / "classified-wave.json").exists() and len(read_rows(stage / "classified-wave.json")) == len(new):
        classified = read_rows(stage / "classified-wave.json")
    else:
        test_count = min(10, len(new))
        run([sys.executable, str(classifier), "--input", str(stage / "new-only.json"), "--output", str(stage / "classified-test.json"), "--markdown", str(stage / "classified-test.md"), "--limit", str(test_count)], label="classify test")
        validate_classified(read_rows(stage / "classified-test.json"))
        started = time.monotonic()
        run([sys.executable, str(classifier), "--input", str(stage / "new-only.json"), "--output", str(stage / "classified-wave.json"), "--markdown", str(stage / "classified-wave.md")], label="classify full")
        classified = read_rows(stage / "classified-wave.json")
        timings["classify_seconds"] = round(time.monotonic() - started, 2)
        write_json(timing_path, timings)
    validate_classified(classified)
    candidate = current + classified
    write_json(stage / "cumulative-candidate.json", candidate)
    write_verification_file(
        stage / "cumulative-candidate.json", stage / "verification-candidate.json"
    )
    write_verification_file(stage / "raw.json", stage / "raw-verification.json")
    write_verification_file(
        stage / "classified-wave.json", stage / "classified-wave-verification.json"
    )
    previous_date, previous = previous_wave(current, args.date)
    write_json(stage / "previous-wave.json", previous)
    run([
        sys.executable, str(ROOT / "scripts" / "update_bukatsu_tide.py"),
        "--classified", str(stage / "cumulative-candidate.json"),
        "--previous-batch", str(stage / "previous-wave.json"),
        "--current-batch", str(stage / "classified-wave.json"),
        "--previous-date", previous_date, "--current-date", args.date,
        "--html", str(PAGE), "--output-html", str(stage / "page-candidate.html"),
    ], label="build page candidate")
    page = sync_candidate_issue_counts((stage / "page-candidate.html").read_text(encoding="utf-8"), candidate)
    (stage / "page-candidate.html").write_text(page, encoding="utf-8")
    report = validate_candidate(current, raw, new, classified, candidate, page)
    report.update({"status": "validated", "date": args.date, "run_id": args.run_id, "queries": queries, "timings": timings})
    write_json(stage / "report.json", report)
    if not args.no_promote:
        promote(stage, args.date, report)
        report["status"] = "promoted"
        write_json(stage / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
