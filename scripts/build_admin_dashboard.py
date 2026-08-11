#!/usr/bin/env python3
"""ローカル専用の管理画面（1枚のHTML）を作る。

公開しない。出力先の admin/ は .gitignore 済みで、GitHub Pages が配信する
docs/ の外にある。

  python3 scripts/build_admin_dashboard.py            # 作るだけ
  python3 scripts/build_admin_dashboard.py --open     # 作ってブラウザで開く
  python3 scripts/build_admin_dashboard.py --fetch    # GA4/GSC/Supabase の実測値も取り直す
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from admin_dashboard import actions, collect, render  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "admin" / "dashboard.html"


def build(*, fetch: bool, today: dt.date) -> str:
    data = {
        "today": today,
        "built_at": dt.datetime.now(),
        "themes": collect.collect_themes(today),
        "kpi": collect.collect_kpi(),
        "x_posts": collect.collect_x_posts(),
        "commits": collect.collect_commits(),
        "data_updates": collect.collect_data_updates(),
        "tasks": collect.collect_tasks(),
        "health": collect.collect_source_health(today),
        "live": collect.fetch_live_metrics() if fetch else None,
        "sample_files": collect.collect_sample_files(),
        "live_cache": collect.read_live_cache(),
    }
    # 次の一手は集めた材料すべてを見て決めるので、dict が揃ってから足す
    data["next"] = actions.next_action(data)
    data["post_breakdown"] = actions.post_breakdown(data["x_posts"], today)
    data["anomalies"] = actions.anomalies(data)
    return render.render(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="ローカル専用の管理画面を作る")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="出力先（既定: admin/dashboard.html）")
    parser.add_argument("--open", action="store_true", help="作成後にブラウザで開く")
    parser.add_argument("--fetch", action="store_true", help="GA4 / Search Console / Supabase から実測値を取り直す（時間がかかる）")
    parser.add_argument("--today", help="今日の日付を上書きする（YYYY-MM-DD、動作確認用）")
    args = parser.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    if args.fetch:
        print("実測値を取得しています（最大3分）…", file=sys.stderr)

    html_text = build(fetch=args.fetch, today=today)

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")
    print(f"管理画面を書き出しました: {output}")

    if args.open:
        subprocess.run(["open", str(output)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
