#!/usr/bin/env python3
"""X投稿の埋め込みに、読み込めなかったときの出典表示（フォールバック）を入れる。

公開ページの埋め込みはこの形だった（2026-08-12 に142件）。

    <blockquote class="twitter-tweet" ...><a href="https://x.com/…/status/…"></a></blockquote>

リンクの表示文字が空なので、X の widgets.js が読み込めなかった場合、読者にも
クローラーにも「空の箱」しか残らない。誰の投稿なのかも、元投稿へ辿る手段も無い。
投稿が削除された場合や、通信がブロックされた場合も同じ。

blockquote の中に出典と元投稿へのリンクを置く。widgets.js が読み込めたときは
blockquote ごと実際の投稿カードへ置き換わるので、通常の読者の見え方は変わらない。

**要旨は複製しない。** 投稿の要旨は直前の <p> に既にあり、クローラーからも読める。
中に同じ文を入れると、同一文が2回並ぶ。同じ文の反復は「質の低いコンテンツ」の
兆候として扱われるため、審査対策として逆効果になる（2026-08-12 に一度入れて戻した）。
ここで補うのは、元から欠けていた出典とリンクだけ。

投稿本文の全文転載はしない（about.html に明記した「引用の範囲で要旨を紹介し、
元投稿へのリンクを併記」に従う）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from x_embed import fallback_link  # noqa: E402  出力の形は生成器と同じものを使う

# 中身が空の blockquote。
# <a …></a> が空であることを条件にしているので、一度処理した箇所は二度目にマッチしない。
EMBED_PATTERN = re.compile(
    r'(?P<open><blockquote class="twitter-tweet"[^>]*>)'
    r'<a href="(?P<url>https://x\.com/(?P<handle>[^/"]+)/status/\d+)"></a>'
    r'(?P<close></blockquote>)'
)

# 未処理の空 blockquote（--check 用。上のパターンに合わない取りこぼしも拾う）
EMPTY_EMBED = re.compile(
    r'<blockquote class="twitter-tweet"[^>]*><a href="[^"]*"></a></blockquote>'
)


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _fallback(match: re.Match[str]) -> str:
    return f'{match.group("open")}{fallback_link(match.group("url"))}{match.group("close")}'


def add_fallback(content: str) -> tuple[str, int]:
    return EMBED_PATTERN.subn(_fallback, content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き換えずに、中身が空の埋め込みが残っていれば終了コード1で報告する",
    )
    args = parser.parse_args()

    docs_dir = resolve(args.docs_dir)
    paths = sorted(docs_dir.glob("*.html"))

    if args.check:
        offenders = []
        for path in paths:
            empty = len(EMPTY_EMBED.findall(path.read_text(encoding="utf-8")))
            if empty:
                offenders.append((path, empty))
        if offenders:
            print(f"NG: 中身が空の埋め込みが {len(offenders)} ファイルに残っています")
            for path, empty in offenders:
                print(f"- {path.relative_to(PROJECT_ROOT)}: {empty}件")
            return 1
        print(f"OK: 中身が空の埋め込みなし（{len(paths)} ファイルを確認）")
        return 0

    changed: list[tuple[Path, int, int]] = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        updated, added = add_fallback(content)
        if added:
            remaining = len(EMPTY_EMBED.findall(updated))
            changed.append((path, added, remaining))
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")

    action = "補う予定" if args.dry_run else "補った"
    total = sum(added for _, added, _ in changed)
    leftover = sum(remaining for _, _, remaining in changed)
    print(f"{action}: {len(changed)} ファイル / {total} 件")
    for path, added, remaining in changed:
        note = f"（未処理 {remaining}件）" if remaining else ""
        print(f"- {path.relative_to(PROJECT_ROOT)}: {added} 件{note}")
    if leftover:
        print(f"注意: パターンに合わない空の埋め込みが {leftover} 件残っています")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
