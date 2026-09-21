#!/usr/bin/env python3
"""公開済みページの土台(チャートのデータ・画像/スクリプトの参照先)が壊れていないかを確かめる。

## なぜ要るか(課題84)

廃止済みの `LOOP.md`「① 監査」は、毎回のループでヒートマップ用canvas
(`smCanvasMain` / `smCanvasHeat`)と漫画・投票画像の存在を人が目で確認していた。
2026-08-23の運用ループ廃止でこの項目だけどこにも引き継がれず、次に同種の破損が
起きても偶然誰かがページを開くまで気づけない状態だった(2026-09-13に5テーマで
共有コード修正が反映されていなかった件、2026-09-21に副首都の論点画像7枚が
本番から消えていた件＝課題80、が実例)。

**旧チェックリストをそのまま実装しない。** `smCanvasMain` / `smCanvasHeat` は
「議論の山なみ」リニューアル(課題54)でチャート実装がSVG＋インラインJSON
(`window.PLANET_DATA`)へ変わった結果、現在はCSSにセレクタが残るだけの死んだ
指定になっている(取得したいのは"canvas要素の有無"ではなく"チャートに実データが
入っているか")。実装前に現行ページの実物を確認し、いま実際に使われている技術に
合わせて書き直した。

## 何を見るか

1. **チャートに実データが入っているか**(ページごとに使っている技術を自動判定):
   - `<script id="planet-data">`(山なみ形式)があれば、中の `window.PLANET_DATA` が
     壊れずJSONとして読め、`stances`・`modes` が空でないこと
   - 無ければ `<canvas id="...">`(takaichiの旧アリーナ形式)を探し、対応する
     ローカルscriptファイルが存在し空でないこと
   - どちらも無ければ「未知の形式」としてNG(検査の対象外にせず人に判断を仰ぐ)
2. **静的な画像・スクリプトの参照切れ**: `<img src="…">` や `data-img="…"` が
   ローカルパスを指しているとき、実際にそのファイルが存在すること
   (外部URL・data:URIは対象外)。`<script>` の中身はJSコードであって参照ではない
   ため、`<script>...</script>` の中身は先に空白へ置き換えてから調べる
   (中身に `'+xxxImgPath+'` のような文字列結合の断片が残っていると、実際には
   何も壊れていないのに「参照先が無い」という誤検知になる)
3. **JSが組み立てる論点画像パス**: 一部テーマ(`topic-modern.js` 共通コード側)は
   画像パスをJSで組み立てて挿入する。ページ内に
   `const XImgSlug = {"論点id":"slug", ...}[it.id]; const XImgPath = XImgSlug ? ('接頭辞'+XImgSlug+'接尾辞') : '';`
   という形の宣言があれば、slugごとに実ファイルが存在するかを確認する
   (課題80で実際に消えたのはこの構造の画像)

## 対象外にしたこと(意図的)

**ディスク上にあってページから参照されていない画像の検出はしない。**
`fukushuto-infographic-wide-bousai.webp` と `-bousai-v2.webp` のように、
差し替え後の旧バージョンが正当に残っていることが多く、単純な「参照されていない」
だけでは誤検知になる。「本来あるべき画像の集合と食い違っていないか」は
テーマごとのビルダーに依存するため、課題80側の個別対応に委ねる。

    python3 scripts/verify_page_structure.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    from .sync_portal_stats import ROOT, parse_themes_yaml
except ImportError:  # python3 scripts/verify_page_structure.py
    from sync_portal_stats import ROOT, parse_themes_yaml  # type: ignore[no-redef]

PLANET_DATA_RE = re.compile(r'<script id="planet-data">window\.PLANET_DATA=(.*?)</script>', re.S)
CANVAS_RE = re.compile(r'<canvas\b[^>]*\bid="([^"]+)"', re.I)
SCRIPT_BLOCK_RE = re.compile(r"(<script\b[^>]*>)(.*?)(</script>)", re.S | re.I)
SCRIPT_SRC_RE = re.compile(r'<script\b[^>]*\bsrc="([^"]+)"', re.I)
ASSET_REF_RE = re.compile(r'(?:src|data-img)="([^"]+)"', re.I)
JS_IMG_SLUG_RE = re.compile(
    r"const (\w+)ImgSlug\s*=\s*(\{.*?\})\[it\.id\];\s*"
    r"const \1ImgPath\s*=\s*\1ImgSlug\s*\?\s*\('([^']*)'\+\1ImgSlug\+'([^']*)'\)",
    re.S,
)
SKIP_SCHEMES = ("http://", "https://", "//", "data:", "mailto:", "javascript:", "#")

# チャートのデータファイルは「存在するだけ」では壊れていても気づけない
# (0バイトでも"存在する"ため)。これ未満なら中身が空とみなす。
MIN_DATA_BYTES = 200


def blank_script_bodies(source: str) -> str:
    """<script>...</script> の中身(JSコード)だけを空白に置き換える。

    開始・終了タグ自体は残すので、<script src="…"> の参照は引き続き拾える。
    中身を残すと、JS文字列結合の断片(例: '+aicImgPath+')が
    src="…" / data-img="…" と誤ってマッチしてしまう。"""
    return SCRIPT_BLOCK_RE.sub(lambda m: m.group(1) + " " * len(m.group(2)) + m.group(3), source)


def resolve(page: Path, raw_path: str) -> Path:
    clean = raw_path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
    return (page.parent / clean).resolve()


def check_broken_references(theme: str, page: Path, scrubbed: str) -> list[str]:
    failures = []
    seen: set[str] = set()
    for match in ASSET_REF_RE.finditer(scrubbed):
        raw_path = match.group(1)
        if not raw_path or raw_path.startswith(SKIP_SCHEMES) or raw_path in seen:
            continue
        seen.add(raw_path)
        if not resolve(page, raw_path).is_file():
            failures.append(f"NG  {theme}: 参照先が存在しません: {raw_path}")
    return failures


def check_js_built_images(theme: str, page: Path, source: str) -> list[str]:
    failures = []
    for match in JS_IMG_SLUG_RE.finditer(source):
        _var, mapping_json, prefix, suffix = match.groups()
        try:
            mapping: dict[str, str] = json.loads(mapping_json)
        except json.JSONDecodeError:
            failures.append(f"NG  {theme}: JS組み立ての画像slug一覧がJSONとして読めません")
            continue
        for issue_id, slug in mapping.items():
            candidate = resolve(page, f"{prefix}{slug}{suffix}")
            if not candidate.is_file():
                failures.append(f"NG  {theme}: 論点画像が見つかりません({issue_id} → {prefix}{slug}{suffix})")
    return failures


def check_chart_data(theme: str, page: Path, source: str) -> list[str]:
    planet_match = PLANET_DATA_RE.search(source)
    if planet_match:
        raw = planet_match.group(1).strip()
        if raw.endswith(";"):
            raw = raw[:-1]
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            return [f"NG  {theme}: planet-dataがJSONとして読めません({exc})"]
        failures = []
        if not data.get("stances"):
            failures.append(f"NG  {theme}: planet-dataのstancesが空です")
        if not data.get("modes"):
            failures.append(f"NG  {theme}: planet-dataのmodesが空です")
        return failures

    canvas_match = CANVAS_RE.search(source)
    if canvas_match:
        script_srcs = [v for v in SCRIPT_SRC_RE.findall(source) if not v.startswith(SKIP_SCHEMES)]
        for src in script_srcs:
            candidate = resolve(page, src)
            if candidate.is_file() and candidate.stat().st_size >= MIN_DATA_BYTES:
                return []
        return [f"NG  {theme}: canvas(#{canvas_match.group(1)})用のデータscriptが見つからないか空です"]

    return [f"NG  {theme}: チャートの実装(planet-data / canvas)が見つかりません。新しい形式なら本検査の更新が要ります"]


def main() -> int:
    failures: list[str] = []
    themes = parse_themes_yaml()
    for theme, data in sorted(themes.items()):
        page = ROOT / str(data["html"])
        if not page.is_file():
            failures.append(f"NG  {theme}: ページが見つかりません: {data['html']}")
            continue
        source = page.read_text(encoding="utf-8")
        scrubbed = blank_script_bodies(source)
        failures += check_chart_data(theme, page, source)
        failures += check_broken_references(theme, page, scrubbed)
        failures += check_js_built_images(theme, page, source)

    for line in failures:
        print(line)
    if failures:
        print(f"=== ページ構造の検査: NG {len(failures)}件 ===")
        return 1
    print(f"OK  {len(themes)}ページ、チャートのデータ・画像/スクリプトの参照先とも壊れていません")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
