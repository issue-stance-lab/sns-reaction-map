#!/usr/bin/env python3
"""
CLI 型AIをプロジェクトのサブエージェントとして呼び出す共通ラッパー。

例:
  # Hermes
  python3 scripts/run_ai_agent.py --ai hermes --issue 8 \
    --cmd-template "hermes --oneshot {prompt}"

  # 任意のCLI型AI。{prompt} はプロンプト本文、{prompt_file} は保存済みプロンプトパスに置換される。
  python3 scripts/run_ai_agent.py --ai example-ai --custom "docs/index.htmlをレビュー" \
    --cmd-template "example-ai run --prompt-file {prompt_file}"

  # 実行せず、生成プロンプトとコマンドだけ確認
  python3 scripts/run_ai_agent.py --ai hermes --issue 8 --dry-run
"""

from __future__ import annotations

import argparse
import shlex
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
PROMPTS_DIR = REPO_ROOT / "configs" / "prompts"
REVIEWS_DIR = REPO_ROOT / "reviews"

DEFAULT_CMD_TEMPLATES = {
    "hermes": "hermes --oneshot {prompt}",
}

COMMON_SYSTEM_NOTE = """\

## サブエージェント実行ルール

- このリポジトリ内で作業する前に TASK_BOARD.md と AI_HANDOFF.md を読む。
- TASK_BOARD.md のファイル所有権を守る。
- 変更した場合は、変更ファイル一覧・確認した動作・残課題を最後にまとめる。
- レビュー依頼の場合はファイルを変更せず、指摘と改善案だけを出す。
- 日本語で回答する。
"""


def normalize_ai_name(ai: str) -> str:
    return ai.strip().lower().replace(" ", "-").replace("_", "-")


def save_prompt(ai: str, prompt: str, slug: str) -> Path:
    out_dir = PROMPTS_DIR / ai
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"{timestamp}_{slug}.md"
    out_file.write_text(prompt)
    return out_file


def build_prompt(args: argparse.Namespace) -> tuple[str, str]:
    display_ai = args.ai_display or args.ai
    if args.review:
        issue_title, _ = parse_issue_from_board(args.review)
        prompt = generate_review_prompt(
            display_ai,
            args.review,
            issue_title,
            args.review_files,
        )
        return prompt + COMMON_SYSTEM_NOTE, f"review_課題{args.review}"

    if args.issue:
        issue_title, issue_body = parse_issue_from_board(args.issue)
        prompt = generate_prompt(display_ai, issue_title, issue_body)
        slug = issue_title[:30].replace(" ", "_").replace("/", "_")
        return prompt + COMMON_SYSTEM_NOTE, slug

    prompt = generate_prompt(
        display_ai,
        args.custom,
        "上記の課題を分析し、必要なサブタスクを洗い出して実行してください。",
    )
    slug = args.custom[:30].replace(" ", "_").replace("/", "_")
    return prompt + COMMON_SYSTEM_NOTE, slug


def default_output_path(ai: str, args: argparse.Namespace) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    if args.review:
        return REVIEWS_DIR / f"{ai}-review-issue{args.review}-{timestamp}.md"
    if args.issue:
        return REVIEWS_DIR / f"{ai}-issue{args.issue}-{timestamp}.md"
    return REVIEWS_DIR / f"{ai}-custom-{timestamp}.md"


def build_command(template: str, prompt: str, prompt_path: Path) -> list[str]:
    prompt_file = str(prompt_path)
    relative_prompt_file = str(prompt_path.relative_to(REPO_ROOT))
    command_text = template.format(
        prompt=shlex.quote(prompt),
        prompt_file=shlex.quote(prompt_file),
        relative_prompt_file=shlex.quote(relative_prompt_file),
    )
    return shlex.split(command_text)


def main() -> int:
    parser = argparse.ArgumentParser(description="CLI型AIをサブエージェントとして実行")
    parser.add_argument("--ai", required=True, help="AI名。例: hermes, codex, claude-code")
    parser.add_argument("--ai-display", help="プロンプト内に表示するAI名")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--issue", type=int, help="TASK_BOARD.md の課題番号")
    group.add_argument("--review", type=int, help="レビュー対象の課題番号")
    group.add_argument("--custom", help="カスタム依頼")
    parser.add_argument("--review-files", default="", help="レビュー対象ファイル")
    parser.add_argument("--cmd-template", help="実行コマンド。{prompt}, {prompt_file}, {relative_prompt_file} が使える")
    parser.add_argument("--output", type=Path, help="AIの回答保存先")
    parser.add_argument("--dry-run", action="store_true", help="実行せず内容だけ表示")
    args = parser.parse_args()

    ai = normalize_ai_name(args.ai)
    template = args.cmd_template or DEFAULT_CMD_TEMPLATES.get(ai)
    if not template:
        print(
            f"error: {ai} の既定コマンドがありません。--cmd-template を指定してください。",
            file=sys.stderr,
        )
        return 2

    if not TASK_BOARD.exists() or not AI_HANDOFF.exists():
        print("error: TASK_BOARD.md または AI_HANDOFF.md が見つかりません。", file=sys.stderr)
        return 1

    prompt, slug = build_prompt(args)
    prompt_path = save_prompt(ai, prompt, slug)
    output_path = args.output or default_output_path(ai, args)
    cmd = build_command(template, prompt, prompt_path)

    executable = shutil.which(cmd[0])
    if not executable:
        print(f"error: {cmd[0]} コマンドが見つかりません。PATHを確認してください。", file=sys.stderr)
        return 127
    cmd[0] = executable

    print(f"prompt: {prompt_path.relative_to(REPO_ROOT)}")
    print(f"output: {output_path.relative_to(REPO_ROOT) if output_path.is_relative_to(REPO_ROOT) else output_path}")

    if args.dry_run:
        dry_cmd = build_command(
            template.replace("{prompt}", "@{relative_prompt_file}"),
            prompt,
            prompt_path,
        )
        print("dry-run command:", " ".join(dry_cmd))
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
        output += f"\n\n---\n\n## {ai} stderr\n\n```text\n"
        output += result.stderr.strip()
        output += "\n```\n"
    output_path.write_text(output + "\n")

    if result.returncode != 0:
        print(f"error: {ai} exited with {result.returncode}. 詳細は {output_path}", file=sys.stderr)
        return result.returncode

    print(f"saved: {output_path.relative_to(REPO_ROOT) if output_path.is_relative_to(REPO_ROOT) else output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
