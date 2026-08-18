#!/usr/bin/env python3
"""公開ページ同士で、本文の言い回しが使い回されていないことを確かめる。

## なぜ機械で見張るか

AdSense の診断（2026-08-16）で「自動生成コンテンツの疑い」が OK になった根拠は
**「定型的な繰り返しがなく、論点ごとに異なる構造」**だった。テーマを増やすときに
先行事例のページを見本として読ませるため、見出しと導入文がそのまま複製されやすい。
実際 2026-08-18 に、自転車の「STEP 2 — 確かめ方」と同じ見出し・7割一致の導入文が
高齢者免許返納にも入った。発注書には禁止と書いてあったが、守られなかった。

**文章で書いた禁止は破られる。検査だけが残る。** 審査員は1ページではなくサイト全体を
見るので、同じ形の記事が並んだ時点で根拠が裏返る。ここで止める。

## 何を見るか

各テーマページの「編集で書いた本文」だけを対象にする（フッター・調査条件・免責など、
全ページで同じなのが当たり前の部分は除く）。

1. **丸ごと同じ文**: 20文字以上の文が2ページ以上に同じ形で出ていたら NG
2. **似すぎた見出し・導入文**: 2ページの見出し（または導入文）の類似度が 0.70 以上なら NG

数字と記号は比較前に落とす。「181件」と「364件」の違いで似ていないことにしない。

## 例外

    configs/page-originality.json
    {
      "shared_selectors": ["research-conditions", …],   // 全ページ共通で当たり前の領域
      "allow": [ { "text": "…", "reason": "…" } ]        // 理由つきで見逃す文
    }

`reason` の無い例外は書けない。**理由が書けない重複は、たいてい手抜きの複製。**

    python3 scripts/verify_page_originality.py
    python3 scripts/verify_page_originality.py -v      # 通った組み合わせの最大類似度も出す
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

try:
    from .sync_portal_stats import ROOT, parse_themes_yaml
    from .verify_number_provenance import in_regions, selector_regions
except ImportError:  # python3 scripts/verify_page_originality.py
    from sync_portal_stats import ROOT, parse_themes_yaml  # type: ignore[no-redef]
    from verify_number_provenance import in_regions, selector_regions  # type: ignore[no-redef]

CONFIG = ROOT / "configs" / "page-originality.json"

# 見出しと、その直後の導入文。ページの「顔」にあたる部分で、いちばん複製されやすい。
HEADING_RE = re.compile(r"<h([1-4])\b[^>]*>(.*?)</h\1>", re.S | re.I)
PARA_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)
SCRIPT_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"<[^>]+>")
SENTENCE_END = re.compile(r"(?<=[。！？])")

MIN_SENTENCE = 20        # これより短い文は、偶然一致することがある
SIMILAR_ENOUGH = 0.70    # 見出し・導入文がこれ以上似ていたら複製とみなす
COMPARE_HEAD = 120       # 導入文は先頭だけを比べる。後半はテーマ固有の話に分かれるため


def load_config() -> dict[str, Any]:
    if not CONFIG.is_file():
        return {"shared_selectors": [], "allow": []}
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    for entry in data.get("allow") or []:
        if not entry.get("text") or not entry.get("reason"):
            raise SystemExit(f"{CONFIG.name}: allow には text と reason の両方が要ります: {entry!r}")
    return data


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub("", fragment)).strip()


def normalize(text: str) -> str:
    """比べる前に、数字・記号・空白を落とす。件数違いを「別の文」にしないため。"""
    text = re.sub(r"[0-9０-９,，.．%％]+", "", text)
    text = re.sub(r"[\s　「」『』（）()【】…—―\-–—:：/／]+", "", text)
    return text


def visible_parts(path: Path, shared: list[str]) -> tuple[list[str], list[str], list[str]]:
    """(見出し, 見出し直後の導入文, 全段落) を、共通領域を除いて返す。

    似すぎの判定は「見出しとその導入文」だけに掛ける。図の凡例や操作の説明は、
    テーマ名を入れ替えただけの文が並ぶのが正しい姿で、そこまで別々に書き分けても
    読者の利益にならない。**編集で書き分けるべきなのは、見出しと書き出し。**"""
    source = path.read_text(encoding="utf-8")
    source = COMMENT_RE.sub(lambda m: " " * len(m.group(0)), source)
    source = SCRIPT_RE.sub(lambda m: " " * len(m.group(0)), source)
    regions = selector_regions(source, shared)
    paragraph_spans = [
        (match.start(), strip_tags(match.group(1)))
        for match in PARA_RE.finditer(source)
        if not in_regions(match.start(), regions)
    ]
    headings, leads = [], []
    for match in HEADING_RE.finditer(source):
        if in_regions(match.start(), regions):
            continue
        text = strip_tags(match.group(2))
        if not text:
            continue
        headings.append(text)
        following = next(
            (body for start, body in paragraph_spans
             if start > match.end() and len(body) >= MIN_SENTENCE),
            None,
        )
        if following:
            leads.append(following)
    paragraphs = [body for _start, body in paragraph_spans if len(body) >= MIN_SENTENCE]
    return headings, leads, paragraphs


def sentences(paragraphs: list[str]) -> list[str]:
    out = []
    for para in paragraphs:
        for piece in SENTENCE_END.split(para):
            piece = piece.strip()
            if len(piece) >= MIN_SENTENCE:
                out.append(piece)
    return out


def duplicated_sentences(pages: dict[str, list[str]], allow: list[str]) -> list[tuple[str, list[str]]]:
    allowed = {normalize(text) for text in allow}
    seen: dict[str, tuple[str, list[str]]] = {}
    for theme, items in pages.items():
        for sentence in items:
            key = normalize(sentence)
            if not key or key in allowed:
                continue
            if key in seen:
                if theme not in seen[key][1]:
                    seen[key][1].append(theme)
            else:
                seen[key] = (sentence, [theme])
    return [(text, themes) for text, themes in seen.values() if len(themes) > 1]


def drop_allowed(pages: dict[str, list[str]], allow: list[str]) -> dict[str, list[str]]:
    """見逃すと決めた文は、丸ごと一致の検査からも似すぎの検査からも外す。

    段落の中に共通の断り書きが1文だけ混ざることがあるので、文単位で取り除く。
    残りが短くなりすぎたものは、比べる意味が無いので落とす。
    """
    allowed = {normalize(text) for text in allow}
    result: dict[str, list[str]] = {}
    for theme, items in pages.items():
        kept = []
        for item in items:
            pieces = [
                piece for piece in SENTENCE_END.split(item)
                if piece.strip() and normalize(piece) not in allowed
            ]
            rest = "".join(pieces).strip()
            if rest and normalize(rest) not in allowed and len(normalize(rest)) >= MIN_SENTENCE:
                kept.append(rest)
        result[theme] = kept
    return result


def similar_pairs(pages: dict[str, list[str]], label: str) -> tuple[list[str], float]:
    failures: list[str] = []
    worst = 0.0
    for (theme_a, items_a), (theme_b, items_b) in combinations(pages.items(), 2):
        for text_a in items_a:
            key_a = normalize(text_a)[:COMPARE_HEAD]
            if len(key_a) < MIN_SENTENCE:
                continue
            for text_b in items_b:
                key_b = normalize(text_b)[:COMPARE_HEAD]
                if len(key_b) < MIN_SENTENCE:
                    continue
                ratio = difflib.SequenceMatcher(None, key_a, key_b).ratio()
                worst = max(worst, ratio)
                if ratio >= SIMILAR_ENOUGH:
                    failures.append(
                        f"NG  {label}が似すぎています（{ratio:.2f}）\n"
                        f"      {theme_a}: {text_a[:70]}\n"
                        f"      {theme_b}: {text_b[:70]}"
                    )
    return failures, worst


def main() -> int:
    parser = argparse.ArgumentParser(description="ページ本文の言い回しが使い回されていないかを確かめる")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--suggest-allow",
        action="store_true",
        help="いま重複している文を、configs/page-originality.json に貼れる形で出す（理由は自分で書く）",
    )
    args = parser.parse_args()

    config = load_config()
    shared = [str(name) for name in config.get("shared_selectors") or []]
    allow = [str(entry["text"]) for entry in config.get("allow") or []]

    headings: dict[str, list[str]] = {}
    leads: dict[str, list[str]] = {}
    body: dict[str, list[str]] = {}
    for theme, data in parse_themes_yaml().items():
        path = ROOT / str(data["html"])
        if not path.is_file():
            print(f"NG  {theme}: ページが見つかりません: {data['html']}")
            return 1
        page_headings, page_leads, paragraphs = visible_parts(path, shared)
        headings[theme] = page_headings
        leads[theme] = page_leads
        body[theme] = sentences(paragraphs)

    headings = drop_allowed(headings, allow)
    leads = drop_allowed(leads, allow)
    body = drop_allowed(body, allow)

    if args.suggest_allow:
        found = duplicated_sentences(headings, []) + duplicated_sentences(body, [])
        print(json.dumps(
            [{"text": text, "reason": f"TODO（{len(themes)}ページ共通）"} for text, themes in sorted(found)],
            ensure_ascii=False, indent=2,
        ))
        return 0

    failures: list[str] = []
    for text, themes in sorted(duplicated_sentences(headings, allow)):
        failures.append(f"NG  同じ見出しが複数ページにあります: 「{text}」\n      {', '.join(sorted(themes))}")
    for text, themes in sorted(duplicated_sentences(body, allow)):
        failures.append(f"NG  同じ文が複数ページにあります: 「{text[:60]}」\n      {', '.join(sorted(themes))}")

    heading_fail, heading_worst = similar_pairs(headings, "見出し")
    lead_fail, lead_worst = similar_pairs(leads, "見出し直後の書き出し")
    failures += heading_fail + lead_fail

    for line in dict.fromkeys(failures):
        print(line)
    if args.verbose:
        print(f"    見出しの最大類似度 {heading_worst:.2f} / 書き出しの最大類似度 {lead_worst:.2f}"
              f"（しきい値 {SIMILAR_ENOUGH}）")
    failures = list(dict.fromkeys(failures))
    if failures:
        print(f"=== 言い回しの使い回し: NG {len(failures)}件 ===")
        return 1
    print(f"OK  {len(headings)}ページに、使い回された見出し・文はありません")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
