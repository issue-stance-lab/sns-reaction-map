#!/usr/bin/env python3
"""単体で配る「意見の推移」の画像が、ページの数字と合っているかを確かめる（公開ファイルだけで回る）。

画像（PNG）は日本語フォントのある手元で作り、docs/images/trend/ へ置く（ひと目版・詳細版の2種類）。
更新でページの数字だけ変わって画像が古いまま残ると、他のサイトに貼られた画像と本文の数字が食い違う。そこで、

- ページの節に埋めたグラフのデータ（labels と rounds）から指紋（sha256）を作り、
- 画像の PNG の Description に入れた指紋と最新の収集日が、同じか

を見る。ほかに、画像の実寸、ページの <img> の参照先とalt（時点）、埋め込みコードの画像URLも見る。
画像を作り直すには `python3 scripts/build_trend_images.py --topic <テーマ> --apply`。
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_trend_images as images  # noqa: E402
import build_trend_section as trend  # noqa: E402

PANELS_RE = re.compile(r"const panels = (\{.*\});\n\s*const NS", re.S)
DESCRIPTION_RE = re.compile(r"asof=(\d{4}-\d{2}-\d{2}); kind=(\w+); variant=(\w+); sha256=([0-9a-f]{64})")


def page_panels(page_html: str) -> dict:
    found = PANELS_RE.search(page_html)
    if not found:
        raise ValueError("ページに「意見の推移」のグラフのデータが見つかりません")
    return json.loads(found.group(1))


def check_theme(slug: str, root: Path = ROOT) -> list[str]:
    """問題の一覧を返す。空なら合格。"""
    problems: list[str] = []
    base = trend._theme_base(slug)
    page_path = root / base["html"]
    if not page_path.is_file():
        return [f"{slug}: ページがありません: {page_path}"]
    page_html = page_path.read_text(encoding="utf-8")
    try:
        panels = page_panels(page_html)
    except ValueError as error:
        return [f"{slug}: {error}"]
    for kind in ("stance", "issue"):
        if kind not in panels:
            continue
        panel = panels[kind]
        expected = images.series_digest(panel["labels"], panel["rounds"])
        last = panel["rounds"][-1]["d"]
        codes = [html.unescape(item) for item in re.findall(r'<textarea class="trend-share-code"[^>]*>(.*?)</textarea>', page_html, re.S)]
        for variant in trend.IMAGE_VARIANTS:
            name = trend.image_filename(slug, kind, variant)
            png = root / trend.IMAGE_DIR / name
            label = f"{slug}/{kind}/{variant}"
            if not png.is_file():
                problems.append(f"{label}: 画像がありません（{png.relative_to(root)}）。`python3 scripts/build_trend_images.py --topic {slug} --apply` で作る")
                continue
            with Image.open(png) as image:
                size = image.size
                description = image.info.get("Description", "")
            if size != trend.IMAGE_SIZE:
                problems.append(f"{label}: 画像の実寸が{size[0]}×{size[1]}です（{trend.IMAGE_SIZE[0]}×{trend.IMAGE_SIZE[1]}のはず）")
            found = DESCRIPTION_RE.fullmatch(description)
            if not found:
                problems.append(f"{label}: 画像に数字の指紋（Description）がありません。作り直す")
            else:
                if found.group(2) != kind or found.group(3) != variant:
                    problems.append(f"{label}: 画像の種類が{found.group(2)}/{found.group(3)}です（{kind}/{variant}のはず）")
                if found.group(1) != last:
                    problems.append(f"{label}: 画像の収集日が{found.group(1)}で、ページの最新（{last}）より古い。画像を作り直す")
                elif found.group(4) != expected:
                    problems.append(f"{label}: 画像の数字がページの数字と一致しません（同じ収集日で数字が変わった）。画像を作り直す")
            relative = f"{trend.IMAGE_DIR.relative_to('docs')}/{name}"
            if f'src="{relative}"' not in page_html:
                problems.append(f"{label}: ページの <img> が{relative}を指していません")
            year_date = trend.jp_date(last, year=True)
            alt = re.search(rf'<img src="{re.escape(relative)}"[^>]*alt="([^"]*)"', page_html)
            if not alt or year_date + "時点" not in html.unescape(alt.group(1)):
                problems.append(f"{label}: 画像のaltに最新の時点（{year_date}時点）がありません")
            image_url = trend.SITE_URL + relative
            if not any(image_url in code for code in codes):
                problems.append(f"{label}: 埋め込みコードに画像URL（{image_url}）がありません")
    return problems


def main() -> int:
    failures = 0
    for slug, theme in trend.TREND_THEMES.items():
        if not theme.get("share_images"):
            continue
        problems = check_theme(slug)
        if problems:
            failures += len(problems)
            for problem in problems:
                print(f"NG  {problem}")
        else:
            print(f"OK  {slug}: 推移の画像（立場・論点 × ひと目版・詳細版）が、ページの数字・最新の時点・埋め込みコードと一致しています")
    print(f"=== 推移の画像: NG {failures}件 ===")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
