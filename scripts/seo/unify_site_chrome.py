#!/usr/bin/env python3
"""全ページのフッターとヘッダーのリンクを統一する。

お問い合わせフォームへのリンクが about.html と image-policy.html の2ページにしか無く、
index.html にも全11テーマページにも1件も無かった（2026-08-12 に実測）。
AdSense の診断でも「必須ページ（プライバシーポリシー・お問い合わせ・運営者情報）への
リンクが確認できない」と指摘された。

あわせてリンク名も揃える。ヘッダーの「データについて」だけでは運営者情報だと分からない。

    運営者情報・調査方法 / お問い合わせ・訂正依頼 / プライバシーポリシー
    / 免責事項 / 画像制作方針

フッターの構造はページによって3種類ある。

    footer.footer        固定ページ（about / privacy / disclaimer / image-policy / 404）
    footer.site-footer   index / usage と一部テーマページ
    style属性のみ        テーマページの多く

いずれも「サイト情報のリンクが並ぶ箇所」を見つけて、その並びごと差し替える。
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONTACT_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSdySbMYxEsLOYmI4jsqjIkSGl6WHF78qLlypOmXAg9tVDy2FQ/viewform"
)

# (href, ラベル) を順序どおりに。about.html はアンカーで用途を分ける。
FOOTER_LINKS: tuple[tuple[str, str], ...] = (
    ("about.html#operator", "運営者情報"),
    ("about.html#method", "調査・編集方法"),
    (CONTACT_URL, "お問い合わせ・訂正依頼"),
    ("privacy.html", "プライバシーポリシー"),
    ("disclaimer.html", "免責事項"),
    ("image-policy.html", "画像制作方針"),
)

NAV_OLD = '<a href="about.html">データについて</a>'
NAV_NEW = '<a href="about.html#method">運営者情報・調査方法</a>'

# 差し替え対象の「サイト情報リンク群」。3つの型それぞれの見つけ方。
# インライン型は style の中身がページごとに違う（color 指定の有無など）ので、
# 「サイト情報のリンクが入っている div」かどうかは中身を見て判定する（_find_inline_block）。
INLINE_OPEN = re.compile(r'<div style="margin-top:8px;[^"]*">')
INLINE_MARKER = "image-policy.html"
SITE_FOOTER_BLOCK = re.compile(
    r'(?P<open><h4>サイト情報</h4><div class="footer-links">)(?P<body>.*?)(?P<close></div>)',
    re.DOTALL,
)
PLAIN_FOOTER_BLOCK = re.compile(
    r'(?P<open><p>© 2026 SNS反応まっぷ — )(?P<body>.*?)(?P<close></p>)',
    re.DOTALL,
)


def _anchor(href: str, label: str, style: str = "") -> str:
    external = href.startswith("http")
    attrs = f' href="{href}"'
    if external:
        attrs += ' target="_blank" rel="noopener"'
    if style:
        attrs += f' style="{style}"'
    return f"<a{attrs}>{label}</a>"


def inline_links() -> str:
    style = "color:rgba(255,255,255,.7);margin-right:16px;"
    last = "color:rgba(255,255,255,.7);"
    parts = []
    for index, (href, label) in enumerate(FOOTER_LINKS):
        parts.append(_anchor(href, label, last if index == len(FOOTER_LINKS) - 1 else style))
    return "\n      " + "\n      ".join(parts) + "\n    "


def site_footer_links() -> str:
    return "".join(_anchor(href, label) for href, label in FOOTER_LINKS)


def plain_footer_links() -> str:
    parts = ['<a href="index.html">トップ</a>']
    parts += [_anchor(href, label) for href, label in FOOTER_LINKS]
    return " · ".join(parts)


def _find_inline_block(content: str) -> tuple[int, int, str] | None:
    """サイト情報のリンクが並ぶ div を返す（開始位置, 終了位置, 開始タグ）。"""
    for match in INLINE_OPEN.finditer(content):
        end = content.find("</div>", match.end())
        if end < 0:
            continue
        body = content[match.end() : end]
        if INLINE_MARKER in body and "<div" not in body:
            return match.start(), end + len("</div>"), match.group(0)
    return None


def apply(content: str) -> tuple[str, list[str]]:
    applied: list[str] = []

    if NAV_OLD in content:
        content = content.replace(NAV_OLD, NAV_NEW)
        applied.append("nav")

    found = _find_inline_block(content)
    if found:
        start, end, open_tag = found
        replacement = open_tag + inline_links() + "</div>"
        if content[start:end] != replacement:
            content = content[:start] + replacement + content[end:]
            applied.append("footer(inline)")

    for name, pattern, body in (
        ("footer(site-footer)", SITE_FOOTER_BLOCK, site_footer_links()),
        ("footer(plain)", PLAIN_FOOTER_BLOCK, plain_footer_links()),
    ):
        match = pattern.search(content)
        if not match or match.group("body") == body:
            continue
        content = (
            content[: match.start()]
            + match.group("open")
            + body
            + match.group("close")
            + content[match.end() :]
        )
        applied.append(name)

    return content, applied


def missing_links(content: str) -> list[str]:
    """フッターに出ているべきリンクのうち、ページに無いもの。"""
    return [label for href, label in FOOTER_LINKS if f">{label}</a>" not in content]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き換えずに、統一リンクが揃っていないページを終了コード1で報告する",
    )
    args = parser.parse_args()

    docs_dir = PROJECT_ROOT / args.docs_dir
    paths = sorted(docs_dir.glob("*.html"))

    if args.check:
        offenders = []
        for path in paths:
            missing = missing_links(path.read_text(encoding="utf-8"))
            if missing:
                offenders.append((path, missing))
        if offenders:
            print(f"NG: 統一リンクが揃っていないページが {len(offenders)} 件")
            for path, missing in offenders:
                print(f"- {path.relative_to(PROJECT_ROOT)}: {', '.join(missing)}")
            return 1
        print(f"OK: 全ページに統一リンクが揃っている（{len(paths)} ファイル）")
        return 0

    changed = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        updated, applied = apply(content)
        if applied:
            changed.append((path, applied))
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")

    action = "変更予定" if args.dry_run else "変更"
    print(f"{action}: {len(changed)} ファイル")
    for path, applied in changed:
        print(f"- {path.relative_to(PROJECT_ROOT)}: {', '.join(applied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
