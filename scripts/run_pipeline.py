#!/usr/bin/env python3
"""One-command pipeline for SNS反応まっぷ.

Orchestrates: fetch → classify → build HTML → rebuild portal.

Usage:
    # Full pipeline (queries from CLI)
    python3 scripts/run_pipeline.py --topic ai-copyright \\
      --queries "AI著作権" "生成AI 反対" "AI 規制"

    # Full pipeline (queries from topic YAML's fetch_queries field)
    python3 scripts/run_pipeline.py --topic ai-copyright

    # New topic with config scaffolding
    python3 scripts/run_pipeline.py --topic live-photo-ban \\
      --scaffold --title "ライブ撮影禁止の是非" \\
      --queries "ライブ撮影禁止 賛成" "ライブ撮影禁止 反対"

    # Skip steps
    python3 scripts/run_pipeline.py --topic ai-copyright --skip-fetch
    python3 scripts/run_pipeline.py --topic ai-copyright --skip-fetch --skip-classify

    # Dry run
    python3 scripts/run_pipeline.py --topic ai-copyright --queries "AI著作権" --dry-run

    # Pre-flight topic judgment
    python3 scripts/run_pipeline.py --topic ai-copyright --queries "AI著作権" --judge

    # Reclassify held posts
    python3 scripts/run_pipeline.py --topic ai-copyright --reclassify
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CONFIGS_DIR = PROJECT_ROOT / "configs"
TOPICS_DIR = CONFIGS_DIR / "topics"
SAMPLES_DIR = PROJECT_ROOT / "social-samples"
DOCS_DIR = PROJECT_ROOT / "docs"

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str, *, level: str = "info") -> None:
    icons = {"info": "→", "ok": "✓", "warn": "⚠", "err": "✗", "skip": "⏭"}
    icon = icons.get(level, "→")
    print(f"  {icon} {msg}")


def heading(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}
    import re
    result: dict[str, Any] = {}
    current_key = ""
    current_list: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r'^(\w[\w_]*):\s*(.*)$', line)
        if m:
            if current_key and current_list:
                result[current_key] = current_list
                current_list = []
            key, val = m.group(1), m.group(2).strip()
            current_key = key
            if val and not val.startswith("|"):
                result[key] = val.strip('"').strip("'")
        elif stripped.startswith("- ") and current_key:
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
    if current_key and current_list:
        result[current_key] = current_list
    return result


def resolve_queries(args: argparse.Namespace, topic_config: dict[str, Any] | None) -> list[str]:
    if args.queries:
        return args.queries
    if topic_config and topic_config.get("fetch_queries"):
        queries = topic_config["fetch_queries"]
        if isinstance(queries, list):
            return queries
    return []


def run_cmd(cmd: list[str], *, dry_run: bool = False, label: str = "") -> int:
    display = " ".join(cmd)
    if dry_run:
        log(f"[DRY RUN] {display}", level="skip")
        return 0
    if label:
        log(label)
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        log(f"Failed (exit {result.returncode}): {display}", level="err")
    return result.returncode


# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------

def check_node() -> bool:
    if shutil.which("node"):
        return True
    log("node が見つかりません。fetchステップにはNode.jsが必要です。", level="err")
    return False


def check_ollama() -> bool:
    try:
        req = urllib.request.Request(OLLAMA_TAGS_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception:
        log("Ollama に接続できません。`ollama serve` を起動してください。", level="err")
        return False


def check_config_exists(slug: str, *, scaffold: bool) -> bool:
    topic_yaml = TOPICS_DIR / f"{slug}.yaml"
    reaction_json = CONFIGS_DIR / f"{slug}-reaction-map.json"
    ok = True
    if not topic_yaml.exists() and not scaffold:
        log(f"{topic_yaml.relative_to(PROJECT_ROOT)} が見つかりません。--scaffold で自動生成できます。", level="err")
        ok = False
    if not reaction_json.exists() and not scaffold:
        log(f"{reaction_json.relative_to(PROJECT_ROOT)} が見つかりません。--scaffold で自動生成できます。", level="err")
        ok = False
    return ok


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def step_fetch(slug: str, queries: list[str], *, dry_run: bool = False) -> int:
    heading("Step 1: Yahoo検索で収集")
    output = SAMPLES_DIR / f"{slug}_samples.json"
    markdown = SAMPLES_DIR / f"{slug}_samples.md"
    cmd = ["node", str(SCRIPTS_DIR / "fetch_yahoo_realtime_node.mjs")]
    for q in queries:
        cmd += ["--query", q]
    cmd += ["--dedupe", "--output", str(output), "--markdown", str(markdown)]
    return run_cmd(cmd, dry_run=dry_run, label=f"収集: {len(queries)}クエリ → {output.name}")


def step_classify(slug: str, *, dry_run: bool = False, model: str = "qwen2.5:7b",
                  batch_size: int = 3, timeout: int = 180, avoid_hold: bool = True) -> int:
    heading("Step 2: Ollama分類")
    input_file = SAMPLES_DIR / f"{slug}_samples.json"
    output_file = SAMPLES_DIR / f"{slug}_classified.json"
    markdown = SAMPLES_DIR / f"{slug}_classified.md"
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "classify_unified.py"),
        "--topic", slug,
        "--input", str(input_file),
        "--output", str(output_file),
        "--markdown", str(markdown),
        "--model", model,
        "--batch-size", str(batch_size),
        "--timeout", str(timeout),
    ]
    if avoid_hold:
        cmd.append("--avoid-hold")
    return run_cmd(cmd, dry_run=dry_run, label=f"分類: {input_file.name} → {output_file.name}")


def step_build(slug: str, *, dry_run: bool = False) -> int:
    heading("Step 3: HTMLビルド")
    input_file = SAMPLES_DIR / f"{slug}_classified.json"
    output_file = DOCS_DIR / f"{slug}-reaction-map.html"
    config_file = CONFIGS_DIR / f"{slug}-reaction-map.json"
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "build_reaction_map.py"),
        "--input", str(input_file),
        "--output", str(output_file),
    ]
    if config_file.exists():
        cmd += ["--config", str(config_file)]
    return run_cmd(cmd, dry_run=dry_run, label=f"ビルド: {output_file.name}")


def step_portal(*, dry_run: bool = False) -> int:
    heading("Step 4: ポータル再生成")
    cmd = [sys.executable, str(SCRIPTS_DIR / "build_site_portal.py")]
    return run_cmd(cmd, dry_run=dry_run, label="ポータル: docs/index.html")


def step_stats(slug: str) -> None:
    heading("Step 5: 分類結果サマリー")
    classified_file = SAMPLES_DIR / f"{slug}_classified.json"
    if not classified_file.exists():
        log(f"{classified_file.name} が見つかりません", level="warn")
        return

    data = json.loads(classified_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        log("分類データが配列ではありません", level="warn")
        return

    total = len(data)
    cats: Counter[str] = Counter()
    for d in data:
        cls = d.get("classification") or {}
        cat = cls.get("category", "?")
        cats[cat] += 1

    hold_key = "その他・分類保留"
    others = cats.get(hold_key, 0)
    classified = total - others
    rate = classified * 100 // total if total else 0

    print()
    print(f"  総数: {total}件")
    print(f"  分類済み: {classified}件 ({rate}%)")
    print(f"  保留: {others}件 ({100 - rate}%)")
    print()
    print("  カテゴリ別:")
    for cat, count in cats.most_common():
        pct = count * 100 // total
        bar = "█" * (pct // 2)
        print(f"    {count:4d} ({pct:2d}%) {bar} {cat}")

    print()
    if rate >= 60:
        log("分類率 60%以上 ◎ — そのまま公開できます", level="ok")
    elif rate >= 30:
        log("分類率 30-59% ○ — 公開可。クエリ追加で改善余地あり", level="ok")
    elif rate >= 10:
        log("分類率 10-29% △ — クエリ設計を見直すか、Few-shot例を追加", level="warn")
    else:
        log("分類率 10%未満 ✗ — トピックかクエリを根本的に変更してください", level="err")


# ---------------------------------------------------------------------------
# Config scaffolding
# ---------------------------------------------------------------------------

CONFLICT_TEMPLATES: dict[str, dict[str, Any]] = {
    "regulation": {
        "label": "賛成 vs 反対",
        "categories": [
            "賛成・規制推進",
            "反対・規制不要",
            "条件付き賛成・段階的導入",
            "条件付き反対・代替案提示",
            "中立・判断保留",
            "その他・分類保留",
        ],
        "stances": ["賛成", "反対", "条件付き", "保留", "その他"],
    },
    "scandal": {
        "label": "擁護 vs 批判",
        "categories": [
            "批判・責任追及",
            "擁護・報道批判",
            "中立・事実確認待ち",
            "関連話題・比較",
            "その他・分類保留",
        ],
        "stances": ["批判", "擁護", "中立", "比較", "その他"],
    },
    "faction": {
        "label": "A派 vs B派",
        "categories": [
            "A派・支持",
            "B派・支持",
            "どちらでもない・中間",
            "比較・分析",
            "その他・分類保留",
        ],
        "stances": ["A派", "B派", "中間", "比較", "その他"],
    },
    "everyday": {
        "label": "わかる vs わからない",
        "categories": [
            "共感・わかる",
            "否定・わからない",
            "場合による・条件付き",
            "体験談・エピソード",
            "その他・分類保留",
        ],
        "stances": ["共感", "否定", "条件付き", "体験", "その他"],
    },
    "severity": {
        "label": "やりすぎ vs 甘い",
        "categories": [
            "やりすぎ・過剰対応",
            "甘い・対応不足",
            "妥当・適切な対応",
            "別の観点・論点ずらし",
            "その他・分類保留",
        ],
        "stances": ["やりすぎ", "甘い", "妥当", "別観点", "その他"],
    },
}


def scaffold_topic_yaml(slug: str, title: str, queries: list[str],
                        template: str = "regulation") -> Path:
    tmpl = CONFLICT_TEMPLATES.get(template, CONFLICT_TEMPLATES["regulation"])
    path = TOPICS_DIR / f"{slug}.yaml"
    if path.exists():
        log(f"{path.relative_to(PROJECT_ROOT)} は既存のためスキップ", level="skip")
        return path

    categories_yaml = "\n".join(f'  - "{c}"' for c in tmpl["categories"])
    stances_yaml = "\n".join(f'  - "{s}"' for s in tmpl["stances"])
    queries_yaml = "\n".join(f'  - "{q}"' for q in queries) if queries else '  - "TODO: クエリを追加"'

    content = f'''name: "{slug}"
title: "{title}"

# テンプレート: {tmpl["label"]} ({template})
# TODO: カテゴリ名をトピックに合わせて編集してください

categories:
{categories_yaml}

stances:
{stances_yaml}

fetch_queries:
{queries_yaml}

prompt_intro: "あなたはSNS投稿の論調分類器です。説明や思考は不要です。"

classification_rules: |
  - 【最重要ルール】単なるニュースのURL共有（自分の意見がないもの）、無関係なつぶやきは「その他・分類保留」に分類してください。投稿者の主観的な意見・感情・評価が含まれているものだけを該当カテゴリに分類します。
  - 「賛成」「反対」と明言していなくても、感情や評価から立場が読み取れる場合は分類してください。
  - 皮肉・反語・疑問形も文脈から実際の主張を推定して分類してください。
  - confidence は 0.0 から 1.0。
  - article_usable は代表意見として記事で使いやすい場合 true。
  - TODO: トピック固有のルールを追加してください

few_shot_examples:
  - text: "TODO: 賛成側の投稿例"
    category: "{tmpl["categories"][0]}"
    reason: "TODO: 分類理由"
  - text: "TODO: 反対側の投稿例"
    category: "{tmpl["categories"][1]}"
    reason: "TODO: 分類理由"

avoid_hold_rules: |
  - これは一度保留になった投稿の再分類です。
  - ニュースリンクの共有だけであっても、投稿者の短い一言から明確にスタンスが読める場合は、最も近いカテゴリに割り当ててください。

rule_overrides: []
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log(f"生成: {path.relative_to(PROJECT_ROOT)}", level="ok")
    return path


def scaffold_reaction_map_json(slug: str, title: str, topic_config: dict[str, Any]) -> Path:
    path = CONFIGS_DIR / f"{slug}-reaction-map.json"
    if path.exists():
        log(f"{path.relative_to(PROJECT_ROOT)} は既存のためスキップ", level="skip")
        return path

    categories = topic_config.get("categories", [])
    stances = topic_config.get("stances", [])

    config: dict[str, Any] = {
        "title": f"{title} SNS反応まっぷ",
        "subtitle": f"TODO: {title}に関するSNS投稿の論調分布を可視化したビューです。世論調査ではありません。",
        "source_label": "Yahooリアルタイム検索",
        "vote_intro": f"TODO: {title}の背景説明を2-3行で記述",
        "vote_method": f"TODO: Yahooリアルタイム検索からSNS投稿を取得し、AIが自動分類しました。",
        "vote_labels": [
            "TODO: 選択肢1",
            "TODO: 選択肢2",
            "TODO: 選択肢3",
            "まだ判断できない",
        ],
        "nav_links": [
            {"label": "トップ", "url": "index.html"},
        ],
        "category_order": categories,
        "stance_order": stances,
        "sample_limit_per_category": 3,
        "show_raw_text": True,
        "notes": [
            "これは世論調査ではなく、Yahooリアルタイム検索で取得した投稿サンプルの反応整理です。",
            "投稿本文の転載は最小限にし、要約中心にしてください。",
            "代表投稿は公開前に人間が確認する前提です。",
        ],
        "conflict_axes": [],
        "category_tones": {},
    }

    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"生成: {path.relative_to(PROJECT_ROOT)}", level="ok")
    return path


def scaffold_site_cases_entry(slug: str, title: str) -> None:
    path = CONFIGS_DIR / "site-cases.json"
    if not path.exists():
        log(f"{path.relative_to(PROJECT_ROOT)} が見つかりません", level="err")
        return

    config = json.loads(path.read_text(encoding="utf-8"))
    cases = config.get("cases", [])

    if any(c.get("id") == slug for c in cases):
        log(f"site-cases.json に {slug} は既存のためスキップ", level="skip")
        return

    new_entry = {
        "id": slug,
        "title": title,
        "subtitle": f"TODO: {title}に関するSNS反応の概要",
        "status": "収集中",
        "topic_type": "TODO: ジャンル",
        "source_label": "Yahooリアルタイム検索",
        "data_path": f"social-samples/{slug}_classified.json",
        "reaction_map_url": f"{slug}-reaction-map.html",
        "primary_axes": [],
    }
    cases.append(new_entry)
    config["cases"] = cases
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"site-cases.json に {slug} を追加", level="ok")


def do_scaffold(slug: str, title: str, queries: list[str], template: str) -> bool:
    heading("Step 0: Config自動生成")
    yaml_path = scaffold_topic_yaml(slug, title, queries, template)
    topic_config = load_yaml(yaml_path)
    scaffold_reaction_map_json(slug, title, topic_config)
    scaffold_site_cases_entry(slug, title)
    print()
    log("TODO箇所を編集してからパイプラインを再実行してください", level="info")
    return True


# ---------------------------------------------------------------------------
# Judge (pre-flight topic assessment)
# ---------------------------------------------------------------------------

def step_judge(slug: str, queries: list[str], *, dry_run: bool = False) -> str:
    heading("Pre-flight: トピック適性判定")

    judge_queries = queries[:3]
    tmp_output = SAMPLES_DIR / f"{slug}_judge_sample.json"

    log(f"少量サンプル取得: {len(judge_queries)}クエリ")
    fetch_cmd = ["node", str(SCRIPTS_DIR / "fetch_yahoo_realtime_node.mjs")]
    for q in judge_queries:
        fetch_cmd += ["--query", q]
    fetch_cmd += ["--dedupe", "--output", str(tmp_output)]

    rc = run_cmd(fetch_cmd, dry_run=dry_run, label="判定用サンプル取得中...")
    if rc != 0 or dry_run:
        return "GO" if dry_run else "ERR"

    judge_cmd = [
        sys.executable, str(SCRIPTS_DIR / "trend_judge.py"),
        "--topic", slug,
        "--slug", slug,
        "--input", str(tmp_output),
        "--limit", "50",
    ]
    result = subprocess.run(judge_cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        log(f"trend_judge.py 失敗: {result.stderr[:200]}", level="err")
        return "ERR"

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        log("判定結果のパースに失敗", level="err")
        return "ERR"

    decision = report.get("decision", "?")
    reason = report.get("reason", "")
    score = report.get("total_score", "?")
    opinion = report.get("opinion_ratio_value", 0)

    print()
    if decision == "GO":
        log(f"判定: GO (スコア {score}/10, 意見率 {opinion:.0%})", level="ok")
    elif decision == "HOLD":
        log(f"判定: HOLD (スコア {score}/10, 意見率 {opinion:.0%})", level="warn")
    else:
        log(f"判定: NG (スコア {score}/10, 意見率 {opinion:.0%})", level="err")
    log(f"理由: {reason}")

    if tmp_output.exists():
        tmp_output.unlink()

    return decision


# ---------------------------------------------------------------------------
# Reclassify
# ---------------------------------------------------------------------------

def step_reclassify(slug: str, *, dry_run: bool = False, model: str = "qwen2.5:7b") -> int:
    heading("再分類: 保留投稿を --avoid-hold で再分類")
    classified_file = SAMPLES_DIR / f"{slug}_classified.json"
    if not classified_file.exists():
        log(f"{classified_file.name} が見つかりません", level="err")
        return 1

    cmd = [
        sys.executable, str(SCRIPTS_DIR / "classify_unified.py"),
        "--topic", slug,
        "--input", str(classified_file),
        "--output", str(classified_file),
        "--model", model,
        "--avoid-hold",
    ]
    return run_cmd(cmd, dry_run=dry_run, label=f"再分類: {classified_file.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="SNS反応まっぷ パイプライン — ワンコマンドでfetch→分類→HTML生成→ポータル更新",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--topic", required=True, help="トピックslug (例: ai-copyright)")
    parser.add_argument("--queries", nargs="+", help="Yahoo検索クエリ（複数指定可）")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollamaモデル (default: qwen2.5:7b)")
    parser.add_argument("--batch-size", type=int, default=3, help="分類バッチサイズ (default: 3)")
    parser.add_argument("--timeout", type=int, default=180, help="Ollamaタイムアウト秒 (default: 180)")

    parser.add_argument("--skip-fetch", action="store_true", help="fetchステップをスキップ")
    parser.add_argument("--skip-classify", action="store_true", help="classifyステップをスキップ")
    parser.add_argument("--skip-build", action="store_true", help="HTML buildステップをスキップ")
    parser.add_argument("--skip-portal", action="store_true", help="ポータル再生成をスキップ")
    parser.add_argument("--dry-run", action="store_true", help="実行せずコマンドを表示")

    parser.add_argument("--scaffold", action="store_true", help="config雛形を自動生成")
    parser.add_argument("--title", default="", help="トピックタイトル（--scaffold時に使用）")
    parser.add_argument("--template", default="regulation",
                        choices=list(CONFLICT_TEMPLATES.keys()),
                        help="対立軸テンプレート (default: regulation)")

    parser.add_argument("--judge", action="store_true", help="事前にトピック適性を判定")
    parser.add_argument("--reclassify", action="store_true", help="保留投稿を再分類")

    args = parser.parse_args()
    slug = args.topic

    heading(f"SNS反応まっぷ パイプライン: {slug}")

    # --- Scaffold mode ---
    if args.scaffold:
        title = args.title or slug
        queries = args.queries or []
        do_scaffold(slug, title, queries, args.template)
        return 0

    # --- Reclassify mode ---
    if args.reclassify:
        rc = step_reclassify(slug, dry_run=args.dry_run, model=args.model)
        if rc == 0:
            step_stats(slug)
        return rc

    # --- Prerequisites ---
    topic_yaml = TOPICS_DIR / f"{slug}.yaml"
    topic_config: dict[str, Any] | None = None
    if topic_yaml.exists():
        topic_config = load_yaml(topic_yaml)

    queries = resolve_queries(args, topic_config)

    ok = True
    if not args.skip_fetch:
        if not check_node():
            ok = False
        if not queries:
            log("クエリが指定されていません。--queries か YAML の fetch_queries を設定してください。", level="err")
            ok = False
    if not args.skip_classify:
        if not check_ollama():
            ok = False
    if not check_config_exists(slug, scaffold=False):
        ok = False

    if not ok and not args.dry_run:
        log("前提チェック失敗。上記のエラーを解決してください。", level="err")
        return 1

    # --- Judge ---
    if args.judge and not args.skip_fetch:
        decision = step_judge(slug, queries, dry_run=args.dry_run)
        if decision == "NG":
            log("NG判定のため中断します。クエリを見直してください。", level="err")
            return 1
        if decision == "HOLD":
            log("HOLD判定です。続行しますが、結果に注意してください。", level="warn")

    # --- Pipeline ---
    if not args.skip_fetch:
        rc = step_fetch(slug, queries, dry_run=args.dry_run)
        if rc != 0:
            return rc

    if not args.skip_classify:
        rc = step_classify(slug, dry_run=args.dry_run, model=args.model,
                           batch_size=args.batch_size, timeout=args.timeout)
        if rc != 0:
            return rc

    if not args.skip_build:
        rc = step_build(slug, dry_run=args.dry_run)
        if rc != 0:
            return rc

    if not args.skip_portal:
        rc = step_portal(dry_run=args.dry_run)
        if rc != 0:
            return rc

    step_stats(slug)

    heading("完了")
    html_path = DOCS_DIR / f"{slug}-reaction-map.html"
    log(f"確認: python3 -m http.server 8123 --directory docs", level="info")
    log(f"URL: http://localhost:8123/{html_path.name}", level="info")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
