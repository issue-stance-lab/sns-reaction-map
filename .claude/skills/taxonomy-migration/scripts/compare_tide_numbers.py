#!/usr/bin/env python3
"""潮目ウィジェットの「変更前」と「変更後」の数字を並べて出す。

論点体系を移行するとき、オーナーに承認をもらうための対照表を作る。
計算は scripts/inject_tide_widget.py の関数をそのまま呼ぶので、
ここで出る数字は再生成後にページへ載る数字と一致する。

立場（stance）も必ず一緒に出す。論点だけ直すつもりでも、再分類は同じ投稿の
賛否も判定し直すため立場の割合が動く。動いたことに気づかないまま公開すると、
オーナーは知らないうちにサイトの数字が変わったことになる。

使い方（リポジトリのルート、または worktree のルートで実行する）:

    python3 .claude/skills/taxonomy-migration/scripts/compare_tide_numbers.py \
      --slug fukushuto \
      --new-prev social-samples/fukushuto_hermes_prev_20260714_v2.json \
      --new-cur  social-samples/fukushuto_hermes_cur_20260726_v2.json

--new-issues を省くと scripts/<slug>_taxonomy.py の ISSUE_ORDER から
「その他」を除いたものを使う。モジュール名が slug から引けないテーマでは明示する。
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


def load_repo_modules(root: Path):
    """リポジトリの scripts/ を import できるようにする。"""
    scripts = root / "scripts"
    if not (scripts / "inject_tide_widget.py").exists():
        sys.exit(
            f"scripts/inject_tide_widget.py が見つからない: {root}\n"
            "リポジトリのルート（または worktree のルート）で実行すること。"
        )
    sys.path.insert(0, str(scripts))
    return importlib.import_module("inject_tide_widget")


def default_issue_labels(slug: str) -> list[str] | None:
    """scripts/<slug>_taxonomy.py から新体系の論点を引く。引けなければ None。"""
    module_name = f"{slug.replace('-', '_')}_taxonomy"
    try:
        taxonomy = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None
    other = getattr(taxonomy, "OTHER", "その他")
    return [name for name in taxonomy.ISSUE_ORDER if name != other]


def resolve(root: Path, value: str) -> Path:
    """パスでもファイル名だけでも受け取れるようにする。"""
    candidate = Path(value)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    for base in (root, root / "social-samples"):
        if (base / value).exists():
            return base / value
    sys.exit(f"ファイルが見つからない: {value}")


def stance_moves(old_path: Path, new_path: Path) -> tuple[int, int]:
    """同じ投稿で立場の判定が変わった件数を tweet_id で突き合わせて数える。

    絞り込み後のリストを順番で比べると、関連判定が変わった投稿の分だけ
    対応がずれて嘘の数字になる。id で照合しないと意味がない。
    """
    def by_id(path: Path) -> dict[str, str]:
        rows = json.loads(path.read_text(encoding="utf-8"))
        return {
            str(row.get("tweet_id")): (row.get("classification") or {}).get("stance", "")
            for row in rows
            if row.get("tweet_id")
        }

    old, new = by_id(old_path), by_id(new_path)
    shared = old.keys() & new.keys()
    return sum(1 for key in shared if old[key] != new[key]), len(shared)


def table(widget, prev_rows, cur_rows, labels, field, prev_label, cur_label) -> str:
    prev_pcts, prev_n = widget.calc_pcts(prev_rows, labels, field)
    cur_pcts, cur_n = widget.calc_pcts(cur_rows, labels, field)
    lines = [
        f"| ラベル | {prev_label} | {cur_label} | 差 |",
        "|---|---:|---:|---:|",
    ]
    for label in labels:
        before, after = prev_pcts[label], cur_pcts[label]
        delta = after - before
        lines.append(f"| {label} | {before}% | {after}% | {delta:+.1f} |")
    lines.append(f"\n母数: {prev_label} {prev_n}件 / {cur_label} {cur_n}件")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True, help="inject_tide_widget.py の THEMES にある slug")
    parser.add_argument("--new-prev", required=True, help="再分類後の「前回」ファイル")
    parser.add_argument("--new-cur", required=True, help="再分類後の「今回」ファイル")
    parser.add_argument("--new-issues", help="新体系の論点をカンマ区切りで。省くと taxonomy から引く")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.repo.resolve()
    widget = load_repo_modules(root)

    theme = next((t for t in widget.THEMES if t["slug"] == args.slug), None)
    if theme is None:
        known = ", ".join(t["slug"] for t in widget.THEMES)
        sys.exit(f"slug が THEMES にない: {args.slug}\n候補: {known}")

    if args.new_issues:
        new_issues = [s.strip() for s in args.new_issues.split(",") if s.strip()]
    else:
        new_issues = default_issue_labels(args.slug)
        if new_issues is None:
            sys.exit(
                f"scripts/{args.slug.replace('-', '_')}_taxonomy.py が無いので "
                "--new-issues で新体系の論点を指定すること。"
            )

    stances = theme["stance_labels"]
    prev_lbl, cur_lbl = theme["prev_label"], theme["cur_label"]
    excl_s = theme.get("exclude_stances")
    excl_i = theme.get("exclude_issues")

    def load(path: Path):
        return widget.load_classified(path, theme["use_relevance_filter"], excl_s, excl_i)

    old_prev = load(resolve(root, theme["prev_file"]))
    old_cur = load(resolve(root, theme["cur_file"]))
    new_prev = load(resolve(root, args.new_prev))
    new_cur = load(resolve(root, args.new_cur))

    print(f"# {args.slug} 潮目ウィジェット 変更前後の対照表\n")
    print("数字が動く理由は、AIが同じ投稿を仕分け直したためであり、世論の変化ではない。\n")

    print("## 論点の変化\n")
    print("### 変更前（現在ページに出ている数字）\n")
    print(table(widget, old_prev, old_cur, theme["issue_labels"], "main_issue", prev_lbl, cur_lbl))
    print("\n### 変更後（再分類・新体系）\n")
    print(table(widget, new_prev, new_cur, new_issues, "main_issue", prev_lbl, cur_lbl))

    print("\n## 立場の変化\n")
    print("### 変更前\n")
    print(table(widget, old_prev, old_cur, stances, "stance", prev_lbl, cur_lbl))
    print("\n### 変更後\n")
    print(table(widget, new_prev, new_cur, stances, "stance", prev_lbl, cur_lbl))

    moved, shared = stance_moves(resolve(root, theme["prev_file"]), resolve(root, args.new_prev))
    print(
        f"\n注: 「{prev_lbl}」分で立場の判定が変わったのは、両方に載っている {shared} 件のうち {moved} 件。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
