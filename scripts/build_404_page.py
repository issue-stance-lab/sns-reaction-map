#!/usr/bin/env python3
"""公開サイトの 404 ページを生成する。

GitHub Pages の汎用404が出ていた（技術的な欠陥として審査で減点されやすい）。
テーマ一覧は configs/site-cases.json から作る。ここにべた書きすると、
テーマを増やしたときに404だけ古くなる。
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_CASES = PROJECT_ROOT / "configs/site-cases.json"
OUTPUT = PROJECT_ROOT / "docs/404.html"

CONTACT_FORM_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSdySbMYxEsLOYmI4jsqjIkSGl6WHF78qLlypOmXAg9tVDy2FQ/viewform"
)


def published_cases(cases: list[dict]) -> list[dict]:
    """公開ページが実在するテーマだけを返す。"""
    out = []
    for case in cases:
        url = case.get("reaction_map_url")
        if not url:
            continue
        if not (PROJECT_ROOT / "docs" / url).exists():
            continue
        out.append(case)
    return out


def render(cases: list[dict]) -> str:
    items = "\n".join(
        f'        <li><a href="{html.escape(case["reaction_map_url"], quote=True)}">'
        f'{html.escape(case["title"])}</a></li>'
        for case in cases
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ページが見つかりません — SNS反応まっぷ</title>
  <meta name="description" content="お探しのページは見つかりませんでした。公開中のテーマ一覧から目的のページを探せます。">
  <meta name="robots" content="noindex">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="icon" href="favicon.ico">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <link rel="stylesheet" href="site-tokens.css">
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --accent: #1769d1;
      --accent-soft: #e7f1ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", "Noto Sans JP", sans-serif;
      line-height: 1.7;
    }}
    header {{
      background: #fff;
      border-bottom: 1px solid var(--line);
      padding: 28px min(5vw, 56px) 24px;
    }}
    .code {{
      display: inline-block;
      font-size: 13px;
      font-weight: 700;
      color: var(--accent);
      background: var(--accent-soft);
      border-radius: 999px;
      padding: 4px 12px;
      margin-bottom: 10px;
    }}
    h1 {{ margin: 0 0 8px; font-size: clamp(22px, 3.2vw, 32px); }}
    .lead {{ color: var(--muted); margin: 0; }}
    main {{ max-width: 800px; margin: 0 auto; padding: 32px min(5vw, 56px) 48px; }}
    h2 {{
      font-size: 18px;
      margin: 32px 0 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid var(--accent-soft);
    }}
    p {{ margin: 0 0 14px; color: var(--muted); }}
    ul {{ margin: 0 0 14px; padding-left: 22px; color: var(--muted); }}
    li {{ margin-bottom: 6px; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 8px; }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--accent);
      color: #fff;
      border-radius: 8px;
      padding: 10px 18px;
      font-size: 14px;
      font-weight: 700;
    }}
    .btn.secondary {{ background: #fff; color: var(--accent); border: 1px solid var(--accent); }}
    .footer {{
      border-top: 1px solid var(--line);
      padding: 20px min(5vw, 56px) 32px;
      font-size: 12px;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <header>
    <span class="code">404</span>
    <h1>ページが見つかりません</h1>
    <p class="lead">お探しのページは、移動または公開を終了した可能性があります。</p>
  </header>
  <main>
    <div class="actions">
      <a class="btn" href="index.html">トップページへ</a>
      <a class="btn secondary" href="about.html">運営者情報・調査方法</a>
    </div>
    <h2>公開中のテーマ</h2>
    <p>意見が分かれている社会のテーマを、賛成・反対それぞれの理由まで分けて整理しています。</p>
    <ul>
{items}
    </ul>
    <h2>リンク切れを見つけた場合</h2>
    <p>
      サイト内のリンクが切れていた場合は、
      <a href="{CONTACT_FORM_URL}" target="_blank" rel="noopener">お問い合わせフォーム</a>
      からお知らせいただけると助かります。
    </p>
  </main>
  <footer class="footer">
    <p>© 2026 SNS反応まっぷ — <a href="index.html">トップ</a> · <a href="about.html">運営者情報・調査方法</a> · <a href="image-policy.html">画像制作方針</a> · <a href="privacy.html">プライバシーポリシー</a> · <a href="disclaimer.html">免責事項</a> · <a href="{CONTACT_FORM_URL}" target="_blank" rel="noopener">お問い合わせ</a></p>
  </footer>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="書き換えずに差分の有無だけ報告する")
    args = parser.parse_args()

    cases = published_cases(json.loads(SITE_CASES.read_text(encoding="utf-8"))["cases"])
    if not cases:
        print("ERROR: 公開中のテーマが1件も見つかりません")
        return 1
    rendered = render(cases)
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""

    if args.check:
        if rendered != current:
            print(f"NG  docs/404.html が最新でない（テーマ{len(cases)}件）")
            return 1
        print(f"OK  docs/404.html は最新（テーマ{len(cases)}件）")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"{'unchanged' if rendered == current else 'wrote'} {OUTPUT.relative_to(PROJECT_ROOT)}（テーマ{len(cases)}件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
