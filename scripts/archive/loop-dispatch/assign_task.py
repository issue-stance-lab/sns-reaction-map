#!/usr/bin/env python3
"""
課題割り当て・レビュープロンプト生成スクリプト

使い方:
  # 課題を割り当て（実装指示）
  python3 scripts/assign_task.py --ai codex --issue 1
  python3 scripts/assign_task.py --ai antigravity2 --issue 2
  python3 scripts/assign_task.py --ai hermes --issue 3

  # 他AIの成果物をレビューさせる
  python3 scripts/assign_task.py --ai codex --review 1
  python3 scripts/assign_task.py --ai antigravity2 --review 1 --review-files "docs/index.html docs/takaichi-reaction-map.html"

  # カスタム課題を直接指定
  python3 scripts/assign_task.py --ai codex --custom "独自ドメイン設定"

生成されたプロンプトは configs/prompts/{ai}/ に保存され、クリップボードにもコピーされる。
"""

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "configs" / "prompts"
TASK_BOARD = REPO_ROOT / "TASK_BOARD.md"
AI_HANDOFF = REPO_ROOT / "AI_HANDOFF.md"

REVIEW_TEMPLATE = """## レビュー依頼

あなたは「SNS反応まっぷ」プロジェクトの **レビュアー** として、別のAIの成果物をチェックします。

### プロジェクト概要
- サービス名: SNS反応まっぷ
- 概要: SNSで意見が割れる話題を可視化し、投票参加型の独立メディアサイトを作る
- 詳細: AI_HANDOFF.md を参照

### レビュー対象

**課題**: {issue_title}
**実装AI**: {original_ai}
**対象ファイル**: {review_files}

### チェックポイント

以下の観点でレビューし、問題点と改善提案を出力してください:

1. **機能性**: スコープの要件を満たしているか
2. **品質**: コードの読みやすさ、バグの有無、エッジケース
3. **UI/UX**: （HTML/CSSの場合）見た目、レスポンシブ、アクセシビリティ
4. **一貫性**: 既存コードやデザインシステムとの統一感
5. **パフォーマンス**: 不要な処理、重いリソース、最適化の余地
6. **セキュリティ**: XSS、インジェクション等の脆弱性

### 出力フォーマット

```
## レビュー結果: 課題X

### 総合評価: ⭐⭐⭐☆☆ (5段階)

### 良い点
- ...

### 要修正（必須）
- [ ] ファイル名:行番号 — 問題の説明

### 改善提案（任意）
- [ ] 提案内容
```

### 制約
- ファイルを変更しない（レビューコメントのみ）
- 日本語でコミュニケーションする
"""

TEMPLATE = """## 最初に必ず読むファイル

1. **TASK_BOARD.md** — チーム構成・課題一覧・ファイル所有権・連絡メモ
2. **AI_HANDOFF.md** — プロジェクト詳細仕様（技術スタック・運用フロー・UI仕様）

上記2ファイルを読んでから作業を開始してください。

## あなたの位置づけ

あなたは「SNS反応まっぷ」プロジェクトの **4人チームの1人** です。

| AI | 担当課題 |
|----|---------|
| Claude Code（ハブ） | 課題4: パイプライン改善 |
| Codex | 課題3: 集客の仕組み |
| Antigravity2 | 課題2: 投票バックエンド |
| Hermes | 課題1: 公開準備 |

**あなたは {ai} です。**

## あなたの課題

**課題**: {issue_title}

{issue_body}

## 進め方

1. まず TASK_BOARD.md と AI_HANDOFF.md を読む
2. この課題のスコープを確認し、サブタスクに分解する
3. TASK_BOARD.md の「ファイル所有権」を確認し、自分の担当ファイルのみ変更する
4. 実装 → 動作確認を繰り返す
5. 完了したら変更内容のサマリーを出力する

## 制約

- **TASK_BOARD.md のファイル所有権を厳守する**（他AIの担当ファイルを変更しない）
- 他AIへの依頼や質問がある場合は、出力に明記する（人間が仲介する）
- 不明点があれば仮定せず質問する
- 日本語でコミュニケーションする
"""


def parse_issue_from_board(issue_num: int) -> tuple[str, str]:
    content = TASK_BOARD.read_text()
    pattern = rf"### 課題{issue_num}: (.+?)(?=\n)"
    title_match = re.search(pattern, content)
    if not title_match:
        raise ValueError(f"課題{issue_num} が TASK_BOARD.md に見つかりません")

    title = title_match.group(1)
    start = title_match.start()
    next_issue = re.search(r"\n### 課題\d+:", content[start + 1:])
    next_section = re.search(r"\n---", content[start + 1:])

    if next_issue:
        end = start + 1 + next_issue.start()
    elif next_section:
        end = start + 1 + next_section.start()
    else:
        end = len(content)

    body = content[start:end].strip()
    return title, body


AI_ISSUE_MAP = {
    "hermes": 1,
    "antigravity2": 2,
    "codex": 3,
    "claude_code": 4,
}
ISSUE_AI_MAP = {v: k for k, v in AI_ISSUE_MAP.items()}


def generate_prompt(ai: str, issue_title: str, issue_body: str) -> str:
    return TEMPLATE.format(ai=ai, issue_title=issue_title, issue_body=issue_body)


def generate_review_prompt(ai: str, issue_num: int, issue_title: str, review_files: str) -> str:
    original_ai = ISSUE_AI_MAP.get(issue_num, "不明")
    if not review_files:
        from_board = {
            1: "docs/index.html, docs/*-reaction-map.html, docs/*-summary.html",
            2: "投票バックエンド関連ファイル",
            3: "SEO関連ファイル（sitemap.xml, robots.txt等）",
            4: "scripts/build_*.py, scripts/classify_*.py, scripts/fetch_*",
        }
        review_files = from_board.get(issue_num, "TASK_BOARD.md のスコープを参照")
    return REVIEW_TEMPLATE.format(
        issue_title=f"課題{issue_num}: {issue_title}",
        original_ai=original_ai,
        review_files=review_files,
    )


def copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def update_task_board(ai: str, issue_num: int):
    content = TASK_BOARD.read_text()
    today = datetime.now().strftime("%Y-%m-%d")

    pattern = rf"(### 課題{issue_num}: .+?\n\*\*担当\*\*: )（未割当）"
    content = re.sub(pattern, rf"\g<1>{ai}", content)

    pattern = rf"(### 課題{issue_num}: .+?\n.*?\n\*\*状態\*\*: )未着手"
    content = re.sub(pattern, rf"\g<1>進行中", content, flags=re.DOTALL)

    if "（まだ割り当てなし）" in content:
        title_match = re.search(rf"### 課題{issue_num}: (.+?)(?=\n)", content)
        title = title_match.group(1) if title_match else f"課題{issue_num}"
        content = content.replace(
            "| （まだ割り当てなし） | | | | |",
            f"| 課題{issue_num}: {title} | {ai} | {today} | 進行中 | |",
        )
    else:
        title_match = re.search(rf"### 課題{issue_num}: (.+?)(?=\n)", content)
        title = title_match.group(1) if title_match else f"課題{issue_num}"
        content = content.rstrip() + f"\n| 課題{issue_num}: {title} | {ai} | {today} | 進行中 | |\n"

    TASK_BOARD.write_text(content)


def main():
    parser = argparse.ArgumentParser(description="課題割り当て・レビュープロンプト生成")
    parser.add_argument("--ai", required=True, choices=["codex", "antigravity2", "hermes"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--issue", type=int, help="TASK_BOARD.mdの課題番号 (1-5)")
    group.add_argument("--review", type=int, help="レビュー対象の課題番号 (1-5)")
    group.add_argument("--custom", help="カスタム課題の説明")
    parser.add_argument("--review-files", default="", help="レビュー対象ファイル（スペース区切り）")
    parser.add_argument("--no-clipboard", action="store_true")
    parser.add_argument("--no-update-board", action="store_true")
    args = parser.parse_args()

    if args.review:
        issue_title, _ = parse_issue_from_board(args.review)
        prompt = generate_review_prompt(args.ai, args.review, issue_title, args.review_files)
        mode = "review"
        slug = f"review_課題{args.review}"
    elif args.issue:
        issue_title, issue_body = parse_issue_from_board(args.issue)
        prompt = generate_prompt(args.ai, issue_title, issue_body)
        mode = "assign"
        slug = issue_title[:30].replace(" ", "_").replace("/", "_")
    else:
        issue_title = args.custom
        issue_body = "上記の課題を分析し、必要なサブタスクを洗い出して実装してください。"
        prompt = generate_prompt(args.ai, issue_title, issue_body)
        mode = "assign"
        slug = issue_title[:30].replace(" ", "_").replace("/", "_")

    out_dir = PROMPTS_DIR / args.ai
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"{timestamp}_{slug}.md"
    out_file.write_text(prompt)
    print(f"保存: {out_file}")

    if not args.no_clipboard:
        if copy_to_clipboard(prompt):
            print("✅ クリップボードにコピーしました。AIに貼り付けてください。")
        else:
            print("⚠️ クリップボードへのコピーに失敗。ファイルから手動コピーしてください。")

    if mode == "assign" and not args.no_update_board and args.issue:
        update_task_board(args.ai, args.issue)
        print(f"✅ TASK_BOARD.md 更新済み（課題{args.issue} → {args.ai} が担当）")

    if mode == "review":
        original_ai = ISSUE_AI_MAP.get(args.review, "不明")
        print(f"📋 レビューモード: {args.ai} が {original_ai} の課題{args.review}をレビュー")


if __name__ == "__main__":
    main()
