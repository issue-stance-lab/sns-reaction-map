#!/usr/bin/env python3
"""GROWTH.yaml の最新スナップショットに x_followers を記録する。

使い方:
  python3 scripts/record_x_followers.py --count 5
  python3 scripts/record_x_followers.py --count 5 --date 2026-08-20
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
GROWTH_YAML = ROOT / "GROWTH.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="GROWTH.yaml に X フォロワー数を記録する")
    parser.add_argument("--count", type=int, required=True, help="フォロワー数（整数）")
    parser.add_argument("--date", default=None, help="記録日 YYYY-MM-DD（省略時は今日）")
    args = parser.parse_args()

    record_date = args.date or datetime.date.today().isoformat()

    text = GROWTH_YAML.read_text(encoding="utf-8")

    # 最新スナップショットを見つける：`  - date:` の最初の出現箇所を基点にして
    # その後の `x_followers: null` を 1 件だけ置換する
    snapshot_start = text.find("    - date:")
    if snapshot_start == -1:
        print("エラー: GROWTH.yaml にスナップショットが見つかりません", file=sys.stderr)
        sys.exit(1)

    # 最初のスナップショットブロック内の x_followers: null を置換
    # 次のスナップショット（    - date:）が現れる前の範囲だけ対象にする
    next_snapshot = text.find("    - date:", snapshot_start + 1)
    block = text[snapshot_start:next_snapshot] if next_snapshot != -1 else text[snapshot_start:]

    if f"x_followers: null" not in block and f"x_followers:" not in block:
        print("エラー: 最新スナップショットに x_followers フィールドが見つかりません", file=sys.stderr)
        sys.exit(1)

    # すでに数値が入っている場合は上書き確認
    existing = re.search(r"x_followers:\s*(\d+)", block)
    if existing:
        current = int(existing.group(1))
        print(f"最新スナップショットには既に x_followers: {current} が記録されています。")
        print(f"{args.count} に上書きしますか？ [y/N] ", end="", flush=True)
        ans = input().strip().lower()
        if ans != "y":
            print("中止しました。")
            sys.exit(0)

    # 置換: null → 数値（コメントは保持）
    new_block = re.sub(
        r"(x_followers:)\s*null(\s*#.*)?",
        lambda m: f"{m.group(1)} {args.count}{('  ' + m.group(2).strip()) if m.group(2) else ''}",
        block,
        count=1,
    )
    # すでに数値の場合も置換
    new_block = re.sub(
        r"(x_followers:)\s*\d+(\s*#.*)?",
        lambda m: f"{m.group(1)} {args.count}{('  ' + m.group(2).strip()) if m.group(2) else ''}",
        new_block,
        count=1,
    )

    new_text = text[:snapshot_start] + new_block + (text[next_snapshot:] if next_snapshot != -1 else "")
    GROWTH_YAML.write_text(new_text, encoding="utf-8")
    print(f"記録しました: x_followers = {args.count}（{record_date}）")
    print("次のコマンドで管理画面を更新してください:")
    print("  python3 scripts/build_admin_dashboard.py")


if __name__ == "__main__":
    main()
