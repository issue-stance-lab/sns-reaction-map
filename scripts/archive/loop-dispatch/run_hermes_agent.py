#!/usr/bin/env python3
"""
Hermes CLI をプロジェクトのサブエージェントとして呼び出すラッパー。

例:
  # 課題8をHermesに実行依頼し、回答を保存
  python3 scripts/run_hermes_agent.py --issue 8 --output reviews/hermes-issue8.md

  # レビューだけ依頼
  python3 scripts/run_hermes_agent.py --review 9 --output reviews/hermes-review-issue9.md

  # 任意の依頼
  python3 scripts/run_hermes_agent.py --custom "docs/index.htmlをレビューして改善案を出して"

  # 実行せず、Hermesに渡すプロンプトとコマンドだけ確認
  python3 scripts/run_hermes_agent.py --issue 8 --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from assign_task import (
    AI_HANDOFF,
    TASK_BOARD,
    generate_prompt,
    generate_review_prompt,
    parse_issue_from_board,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "configs" / "prompts" / "hermes"
REVIEWS_DIR = REPO_ROOT / "reviews"

HERMES_SYSTEM_NOTE = """\

## Hermesサブエージェント実行ルール

- このリポジトリ内で作業する前に TASK_BOARD.md と AI_HANDOFF.md を読む。
- TASK_BOARD.md のファイル所有権を守る。
- 変更した場合は、変更ファイル一覧・確認した動作・残課題を最後にまとめる。
- レビュー依頼の場合はファイルを変更せず、指摘と改善案だけを出す。
- 日本語で回答する。
"""


def save_prompt(prompt: str, slug: str) -> Path:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = PROMPTS_DIR / f"{timestamp}_{slug}.md"
    out_file.write_text(prompt)
    return out_file


def build_prompt(args: argparse.Namespace) -> tuple[str, str]:
    if args.review:
        issue_title, _ = parse_issue_from_board(args.review)
        prompt = generate_review_prompt(
            "Hermes",
            args.review,
            issue_title,
            args.review_files,
        )
        return prompt + HERMES_SYSTEM_NOTE, f"review_課題{args.review}"

    if args.issue:
        issue_title, issue_body = parse_issue_from_board(args.issue)
        prompt = generate_prompt("Hermes", issue_title, issue_body)
        slug = issue_title[:30].replace(" ", "_").replace("/", "_")
        return prompt + HERMES_SYSTEM_NOTE, slug

    prompt = generate_prompt(
        "Hermes",
        args.custom,
        "上記の課題を分析し、必要なサブタスクを洗い出して実行してください。",
    )
    slug = args.custom[:30].replace(" ", "_").replace("/", "_")
    return prompt + HERMES_SYSTEM_NOTE, slug


def default_output_path(args: argparse.Namespace) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    if args.review:
        return REVIEWS_DIR / f"hermes-review-issue{args.review}-{timestamp}.md"
    if args.issue:
        return REVIEWS_DIR / f"hermes-issue{args.issue}-{timestamp}.md"
    return REVIEWS_DIR / f"hermes-custom-{timestamp}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes をサブエージェントとして実行")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--issue", type=int, help="TASK_BOARD.md の課題番号")
    group.add_argument("--review", type=int, help="レビュー対象の課題番号")
    group.add_argument("--custom", help="カスタム依頼")
    parser.add_argument("--review-files", default="", help="レビュー対象ファイル")
    parser.add_argument("--output", type=Path, help="Hermesの回答保存先")
    parser.add_argument("--model", help="Hermesのモデル指定")
    parser.add_argument("--provider", help="Hermesのプロバイダ指定")
    parser.add_argument("--toolsets", help="Hermesで有効化するtoolsets")
    parser.add_argument("--worktree", action="store_true", help="Hermesを分離worktreeで実行")
    parser.add_argument("--yolo", action="store_true", help="Hermesの危険操作確認を迂回")
    parser.add_argument("--dry-run", action="store_true", help="実行せず内容だけ表示")
    args = parser.parse_args()

    hermes = shutil.which("hermes")
    if not hermes:
        print("error: hermes コマンドが見つかりません。PATHを確認してください。", file=sys.stderr)
        return 127

    if not TASK_BOARD.exists() or not AI_HANDOFF.exists():
        print("error: TASK_BOARD.md または AI_HANDOFF.md が見つかりません。", file=sys.stderr)
        return 1

    prompt, slug = build_prompt(args)
    prompt_path = save_prompt(prompt, slug)
    output_path = args.output or default_output_path(args)

    cmd = [hermes, "--oneshot", prompt]
    if args.model:
        cmd.extend(["--model", args.model])
    if args.provider:
        cmd.extend(["--provider", args.provider])
    if args.toolsets:
        cmd.extend(["--toolsets", args.toolsets])
    if args.worktree:
        cmd.append("--worktree")
    if args.yolo:
        cmd.append("--yolo")

    print(f"prompt: {prompt_path.relative_to(REPO_ROOT)}")
    print(f"output: {output_path.relative_to(REPO_ROOT) if output_path.is_relative_to(REPO_ROOT) else output_path}")

    if args.dry_run:
        visible_cmd = [cmd[0], "--oneshot", f"@{prompt_path.relative_to(REPO_ROOT)}"]
        visible_cmd.extend(cmd[3:])
        print("dry-run command:", " ".join(visible_cmd))
        return 0

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n\n---\n\n## Hermes stderr\n\n```text\n"
        output += result.stderr.strip()
        output += "\n```\n"
    output_path.write_text(output + "\n")

    if result.returncode != 0:
        print(f"error: hermes exited with {result.returncode}. 詳細は {output_path}", file=sys.stderr)
        return result.returncode

    print(f"saved: {output_path.relative_to(REPO_ROOT) if output_path.is_relative_to(REPO_ROOT) else output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
