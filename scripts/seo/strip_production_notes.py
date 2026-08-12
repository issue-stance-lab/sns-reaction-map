#!/usr/bin/env python3
"""公開ページに残った制作指示の文を取り除く。

「代表投稿は公開前に人間が確認する前提です。」のようなワーカーAI向けの指示が
公開ページの「注意」欄に残っていた（2026-08-12 に8テーマ・14文を検出）。
審査する側からは未完成の下書きに見えるうえ、同じページ上部の
「人間による代表投稿の確認あり」と矛盾する。

読者に向けた注意（世論調査ではない旨・検索語の偏り）は残し、
制作者に向けた指示だけを消す。何度実行しても結果は変わらない。
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 制作指示と判定する文。verify_theme_page.py からも参照される。
PRODUCTION_NOTE_PATTERNS: tuple[str, ...] = (
    r"代表投稿は公開前に人間が確認する前提です。",
    r"投稿本文の転載は最小限にし、[^<]*?してください。",
    r"分類は初期のルールベース分類です。公開前にはOllama分類または人間レビューで精度確認してください。",
)

# 上の文を含む <li> をまとめて消す。直前の改行とインデントも一緒に落とす。
_LI_PATTERNS = tuple(
    re.compile(rf"\n?[ \t]*<li>(?:(?!</li>).)*?{body}(?:(?!</li>).)*?</li>", re.DOTALL)
    for body in PRODUCTION_NOTE_PATTERNS
)

_SENTENCE_PATTERNS = tuple(re.compile(body) for body in PRODUCTION_NOTE_PATTERNS)

# <li> を消した結果、項目が1つも残らなかった <ul> を畳む。
_EMPTY_UL = re.compile(r"\n?[ \t]*<ul>\s*</ul>")


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def strip_notes(content: str) -> tuple[str, int]:
    """制作指示の <li> を除いた HTML と、除いた件数を返す。"""
    removed = 0
    for pattern in _LI_PATTERNS:
        content, count = pattern.subn("", content)
        removed += count
    content = _EMPTY_UL.sub("", content)
    return content, removed


def find_remaining(content: str) -> list[str]:
    """まだ残っている制作指示の文を返す（属性値の中は対象外）。"""
    body = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", "", content)
    visible = re.sub(r"<[^>]+>", " ", body)
    found: list[str] = []
    for pattern in _SENTENCE_PATTERNS:
        found.extend(match.group(0) for match in pattern.finditer(visible))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き換えずに、残っている制作指示があれば終了コード1で報告する",
    )
    args = parser.parse_args()

    docs_dir = resolve(args.docs_dir)
    paths = sorted(docs_dir.glob("*.html"))

    if args.check:
        offenders: list[tuple[Path, list[str]]] = []
        for path in paths:
            remaining = find_remaining(path.read_text(encoding="utf-8"))
            if remaining:
                offenders.append((path, remaining))
        if offenders:
            print(f"NG: 制作指示が {len(offenders)} ファイルに残っています")
            for path, remaining in offenders:
                for sentence in remaining:
                    print(f"- {path.relative_to(PROJECT_ROOT)}: {sentence}")
            return 1
        print(f"OK: 制作指示なし（{len(paths)} ファイルを確認）")
        return 0

    changed: list[tuple[Path, int]] = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        updated, removed = strip_notes(content)
        if removed:
            changed.append((path, removed))
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")

    action = "削除予定" if args.dry_run else "削除"
    total = sum(count for _, count in changed)
    print(f"{action}: {len(changed)} ファイル / {total} 文")
    for path, removed in changed:
        print(f"- {path.relative_to(PROJECT_ROOT)}: {removed} 文")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
