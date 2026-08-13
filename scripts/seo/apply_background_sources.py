#!/usr/bin/env python3
"""「この争点の背景」に一次情報へのリンクを追加する。

官公庁・国会などの一次資料へのリンクが、公開中の11テーマのうち4テーマにしか無かった
（2026-08-12 に実測。ai-copyright 6本 / bike-blue-ticket 4本 /
elderly-license-revocation 4本 / bukatsu-chiiki 3本、残る7テーマは0本）。

SNS投稿とAI分類だけを根拠にしたページに見えないよう、争点そのものの一次情報を
背景解説の末尾に置く。出典はテーマ設定 configs/*.json の `background.sources` で管理する。

**リンクが生きているかはこの環境では確認できない**（作業環境の通信制限で官公庁ドメインへ
到達できない）。反映後に `python3 scripts/verify_theme_page.py <theme>` を
通信制限のない環境で実行して確認すること。同スクリプトに HTTP 200 の検査が既にある。
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BLOCK_START = "<!-- BACKGROUND_SOURCES_START -->"
BLOCK_END = "<!-- BACKGROUND_SOURCES_END -->"
BLOCK_PATTERN = re.compile(
    re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END), re.DOTALL
)
# 背景セクションの書き方はテーマで2種類ある。
#   <section class="panel background-panel">        …ほとんどのテーマ
#   <section class="panel" id="background-section"> …takaichi
# どちらも「この争点の背景」の見出しを持つので、それを目印にする。
BACKGROUND_SECTION = re.compile(
    r"(?P<open><section[^>]*>(?:(?!</section>).)*?<h2>この争点の背景</h2>"
    r"(?:(?!</section>).)*?)(?P<close></section>)",
    re.DOTALL,
)


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def sources_block(sources: list[dict[str, str]], note: str | None) -> str:
    items = "".join(
        f'<li><a href="{html.escape(str(s["url"]), quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(str(s["label"]))}</a></li>'
        for s in sources
    )
    note_html = f'<p class="background-sources-note">{html.escape(note)}</p>' if note else ""
    return (
        f'{BLOCK_START}<div class="background-sources"><h3>一次情報</h3>'
        f"<ul>{items}</ul>{note_html}</div>{BLOCK_END}"
    )


def apply_to_page(content: str, block: str) -> str:
    if BLOCK_PATTERN.search(content):
        return BLOCK_PATTERN.sub(lambda _: block, content, count=1)
    match = BACKGROUND_SECTION.search(content)
    if not match:
        raise ValueError("この争点の背景セクションが見つかりません")
    return (
        content[: match.start()]
        + match.group("open")
        + block
        + match.group("close")
        + content[match.end() :]
    )


def theme_configs() -> dict[str, Path]:
    """テーマID → configs/*.json。THEMES.yaml の html 名から対応づける。"""
    text = (PROJECT_ROOT / "THEMES.yaml").read_text(encoding="utf-8")
    out: dict[str, Path] = {}
    for match in re.finditer(
        r"^  ([\w-]+):\s*$(.*?)(?=^  [\w-]+:\s*$|\Z)", text, re.MULTILINE | re.DOTALL
    ):
        body = match.group(2)
        if not re.search(r"^    published:\s*done", body, re.MULTILINE):
            continue
        html_match = re.search(r"^    html:\s*(\S+)", body, re.MULTILINE)
        if not html_match:
            continue
        stem = Path(html_match.group(1)).stem
        config = PROJECT_ROOT / "configs" / f"{stem}.json"
        if not config.exists() and match.group(1) == "takaichi":
            config = PROJECT_ROOT / "configs/takaichi-reaction-map.json"
        out[match.group(1)] = config
    return out


def load_sources(config_path: Path) -> tuple[list[dict[str, str]], str | None]:
    if not config_path.exists():
        return [], None
    data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    background = data.get("background") or {}
    return list(background.get("sources") or []), background.get("sources_note")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き換えずに、設定と食い違うページがあれば終了コード1で報告する",
    )
    args = parser.parse_args()

    text = (PROJECT_ROOT / "THEMES.yaml").read_text(encoding="utf-8")
    pages = {
        m.group(1): PROJECT_ROOT / re.search(r"^    html:\s*(\S+)", m.group(2), re.MULTILINE).group(1)
        for m in re.finditer(
            r"^  ([\w-]+):\s*$(.*?)(?=^  [\w-]+:\s*$|\Z)", text, re.MULTILINE | re.DOTALL
        )
        if re.search(r"^    published:\s*done", m.group(2), re.MULTILINE)
        and re.search(r"^    html:\s*(\S+)", m.group(2), re.MULTILINE)
    }

    configs = theme_configs()
    changed = failures = 0
    for theme_id, page_path in sorted(pages.items()):
        sources, note = load_sources(configs.get(theme_id, Path("/nonexistent")))
        if not sources:
            print(f"skip     {theme_id}: background.sources なし")
            continue
        block = sources_block(sources, note)
        content = page_path.read_text(encoding="utf-8")
        updated = apply_to_page(content, block)
        if updated == content:
            print(f"OK       {theme_id}: 一次情報 {len(sources)}本")
            continue
        if args.check:
            print(f"NG       {theme_id}: ページが設定と一致しない（一次情報 {len(sources)}本）")
            failures += 1
            continue
        changed += 1
        print(f"{'変更予定' if args.dry_run else '変更'}  {theme_id}: 一次情報 {len(sources)}本")
        if not args.dry_run:
            page_path.write_text(updated, encoding="utf-8")

    if args.check:
        return 1 if failures else 0
    print(f"\n{'変更予定' if args.dry_run else '変更'}: {changed} ファイル")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
