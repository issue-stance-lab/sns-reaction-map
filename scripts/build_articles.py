#!/usr/bin/env python3
"""サイト内記事（docs/articles/）を content/articles/{テーマ}/*.md の原稿から作る（課題51）。

**なぜ要るか。** テーマページは1テーマ1本で、2.5万〜5万字を1つのURLに詰めている。
検索は「1つの疑問に1ページで答える」形を評価するため、「部活動 地域移行 費用」「〜 問題点」を
1ページで全部取ることはできない（2026-10-17、28日間の検索表示がサイト全体で99回）。
疑問ごとの記事を足すための生成器。手書きのHTMLを docs/ に置くと次の生成で消えるか、
検査（再生成可能性）が落ちるので、記事も原稿から作る。

**SNSの件数は原稿に手で書かない。** `{{issue:費用・家庭負担:慎重・反対}}` のように書き、
公開データ（data/public/themes/{テーマ}.json）から差し込む。データ更新で件数が変わったら
このスクリプトを流し直すだけで記事も揃う。本文で「AがBより多い」と言い切った箇所は
原稿の `asserts` に書く。更新で大小が入れ替わったら生成が止まり、文章の直し忘れを防ぐ。

使い方:
    python3 scripts/build_articles.py          # docs/articles/ を作り直す
    python3 scripts/build_articles.py --check  # 作り直した結果が docs/articles/ と同じか確かめる（CI）
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "content" / "articles"
OUT_DIR = ROOT / "docs" / "articles"
PUBLIC_THEMES = ROOT / "data" / "public" / "themes"
THEME_SEO = ROOT / "configs" / "theme-seo.json"
OUT_PREFIX = "articles"
# 原稿を置かないフォルダー（下書き置き場）
SKIP_DIRS = {"drafts"}

sys.path.insert(0, str(ROOT / "scripts" / "seo"))
from unify_site_chrome import CONTACT_URL, FOOTER_LINKS  # noqa: E402  フッターのリンクは全ページで1か所が正典

# 立場の並び順と色。色だけで区別させないため、凡例には必ず名前と件数を出す。
STANCE_ORDER: tuple[tuple[str, str], ...] = (
    ("移行支持", "s1"),
    ("条件付き・改善要求", "s2"),
    ("中立・情報", "s3"),
    ("慎重・反対", "s4"),
)

PLACEHOLDER_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
BLOCK_RE = re.compile(r"^\[\[chart:([^\]]+)\]\]$")
ASSERT_RE = re.compile(r"^[0-9.\s<>=!]+$")


class BuildError(Exception):
    """原稿かデータの食い違い。記事を出さずに止める。"""


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------- データ

@dataclass
class ThemeData:
    theme_id: str
    title: str
    url: str
    image: str
    collected: int
    opinions: int
    period_start: date
    period_end: date
    updated_on: date
    issues: dict[str, dict[str, int]]  # 論点名 -> {"_total": n, 立場名: n}

    @property
    def named_issues(self) -> list[str]:
        return [label for label in self.issues if label != "その他"]


def _stance_label(stance_id: str) -> str:
    """公開データの立場ID（bukatsu-chiiki-cautious など）を表示名に直す。"""
    suffix = stance_id.rsplit("-", 1)[-1]
    names = {
        "support": "移行支持",
        "cautious": "慎重・反対",
        "conditional": "条件付き・改善要求",
        "neutral": "中立・情報",
    }
    if suffix not in names:
        raise BuildError(f"知らない立場IDです: {stance_id}（build_articles.py の対応表に足す）")
    return names[suffix]


def load_theme(theme_id: str) -> ThemeData:
    path = PUBLIC_THEMES / f"{theme_id}.json"
    if not path.is_file():
        raise BuildError(f"公開データがありません: {rel(path)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    seo = {t["id"]: t for t in json.loads(THEME_SEO.read_text(encoding="utf-8"))["themes"]}
    if theme_id not in seo:
        raise BuildError(f"configs/theme-seo.json に {theme_id} がありません")
    issues: dict[str, dict[str, int]] = {}
    for issue in data["issues"]:
        row = {"_total": int(issue["count"])}
        for stance in issue.get("stances") or []:
            row[_stance_label(stance["id"])] = int(stance["count"])
        issues[issue["label"]] = row
    period = data["collection_period"]
    return ThemeData(
        theme_id=theme_id,
        title=data["title"],
        url=seo[theme_id]["url"],
        image=seo[theme_id]["image"],
        collected=int(data["collected_count"]),
        opinions=int(data["opinion_count"]),
        period_start=date.fromisoformat(period["start"]),
        period_end=date.fromisoformat(period["end"]),
        updated_on=date.fromisoformat(data["updated_on"]),
        issues=issues,
    )


def jp_date(value: date) -> str:
    return f"{value.year}年{value.month}月{value.day}日"


def jp_period(start: date, end: date) -> str:
    tail = f"{end.month}月{end.day}日" if start.year == end.year else jp_date(end)
    return f"{jp_date(start)}〜{tail}"


def pct(part: int, whole: int) -> str:
    if whole <= 0:
        raise BuildError("割合の分母が0です")
    return f"{part / whole * 100:.1f}%"


# ---------------------------------------------------------------- 差し込み

def resolve_placeholder(key: str, theme: ThemeData) -> str:
    parts = [p.strip() for p in key.split(":")]
    head = parts[0]

    def issue_row(label: str) -> dict[str, int]:
        if label not in theme.issues:
            raise BuildError(f"論点名が公開データにありません: 「{label}」（{theme.theme_id}）")
        return theme.issues[label]

    def stance_count(row: dict[str, int], stance: str) -> int:
        if stance not in dict(STANCE_ORDER):
            raise BuildError(f"立場名が違います: 「{stance}」")
        return row.get(stance, 0)

    def stance_total(stance: str) -> int:
        return sum(stance_count(row, stance) for row in theme.issues.values())

    if head == "opinions" and len(parts) == 1:
        return f"{theme.opinions:,}"
    if head == "collected" and len(parts) == 1:
        return f"{theme.collected:,}"
    if head == "period" and len(parts) == 1:
        return jp_period(theme.period_start, theme.period_end)
    if head == "updated" and len(parts) == 1:
        return jp_date(theme.updated_on)
    if head == "issue" and len(parts) == 2:
        return f"{issue_row(parts[1])['_total']:,}"
    if head == "issue" and len(parts) == 3:
        return f"{stance_count(issue_row(parts[1]), parts[2]):,}"
    if head == "pct" and len(parts) == 3:
        row = issue_row(parts[1])
        return pct(stance_count(row, parts[2]), row["_total"])
    if head == "share" and len(parts) == 2:
        return pct(issue_row(parts[1])["_total"], theme.opinions)
    if head == "stance" and len(parts) == 2:
        return f"{stance_total(parts[1]):,}"
    if head == "stance_pct" and len(parts) == 2:
        return pct(stance_total(parts[1]), theme.opinions)
    raise BuildError(f"差し込みの書き方が違います: {{{{{key}}}}}")


def fill(text: str, theme: ThemeData) -> str:
    return PLACEHOLDER_RE.sub(lambda m: resolve_placeholder(m.group(1), theme), text)


def check_asserts(article: "Article", theme: ThemeData) -> None:
    for expression in article.asserts:
        filled = fill(expression, theme).replace(",", "").replace("%", "")
        if not ASSERT_RE.match(filled):
            raise BuildError(f"{article.slug}: asserts は数字と比較記号だけにする: {expression}")
        if not eval(filled, {"__builtins__": {}}, {}):  # noqa: S307 数字と比較記号だけを確認済み
            raise BuildError(
                f"{article.slug}: 本文の言い切りがデータと合わなくなりました: {expression} → {filled}\n"
                f"  原稿 content/articles/{article.theme}/{article.slug}.md の該当箇所を直してから流し直す"
            )


# ---------------------------------------------------------------- 原稿

@dataclass
class Source:
    name: str
    url: str
    checked_on: date


@dataclass
class Article:
    slug: str
    theme: str
    title: str
    description: str
    published_on: date
    updated_on: date
    body: str
    asserts: list[str]
    sources: list[Source]
    path: Path
    order: int = 100

    @property
    def url(self) -> str:
        return f"{OUT_PREFIX}/{self.slug}.html"


def _as_date(value: Any, label: str, slug: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise BuildError(f"{slug}: {label} が日付として読めません: {value!r}") from exc


def load_article(path: Path) -> Article:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        raise BuildError(f"{rel(path)}: 先頭に --- で囲んだ設定がありません")
    meta = yaml.safe_load(match.group(1)) or {}
    slug = str(meta.get("slug") or "")
    if slug != path.stem:
        raise BuildError(f"{rel(path)}: slug（{slug}）とファイル名が違います")
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise BuildError(f"{slug}: slug は英小文字・数字・ハイフンだけにする")
    for key in ("theme", "title", "description", "published_on", "updated_on"):
        if not meta.get(key):
            raise BuildError(f"{slug}: {key} がありません")
    if meta["theme"] != path.parent.name:
        raise BuildError(f"{slug}: theme（{meta['theme']}）と置き場所のフォルダー名が違います")
    if len(str(meta["title"])) > 32:
        raise BuildError(f"{slug}: title が32字を超えています（{len(str(meta['title']))}字）")
    sources = []
    for item in meta.get("sources") or []:
        if not item.get("name") or not str(item.get("url", "")).startswith("http"):
            raise BuildError(f"{slug}: sources には name と http で始まる url が要ります: {item!r}")
        sources.append(Source(
            name=str(item["name"]),
            url=str(item["url"]),
            checked_on=_as_date(item.get("checked_on"), "sources.checked_on", slug),
        ))
    if not sources:
        raise BuildError(f"{slug}: sources（使った一次資料）がありません")
    return Article(
        slug=slug,
        theme=str(meta["theme"]),
        title=str(meta["title"]),
        description=str(meta["description"]).strip(),
        published_on=_as_date(meta["published_on"], "published_on", slug),
        updated_on=_as_date(meta["updated_on"], "updated_on", slug),
        body=match.group(2).strip() + "\n",
        asserts=[str(x) for x in meta.get("asserts") or []],
        sources=sources,
        path=path,
        order=int(meta.get("order", 100)),
    )


def load_articles(src_dir: Path | None = None) -> list[Article]:
    articles = []
    for path in sorted((src_dir or SRC_DIR).glob("*/*.md")):
        if path.parent.name in SKIP_DIRS:
            continue
        articles.append(load_article(path))
    slugs = [a.slug for a in articles]
    duplicated = {s for s in slugs if slugs.count(s) > 1}
    if duplicated:
        raise BuildError(f"slug が重複しています: {sorted(duplicated)}")
    # order は同じテーマの中での並び（テーマページ・トップ・あわせて読むの順。小さいほど先）
    return sorted(articles, key=lambda a: (a.theme, a.order, a.published_on, a.slug))


# ---------------------------------------------------------------- Markdown（使う書き方だけ）

INLINE_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+|[^)\s]+\.html(?:#[^)\s]*)?)\)")
INLINE_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def inline(text: str) -> str:
    """リンクと強調だけを HTML にする。それ以外の記号はそのまま文字として出す。"""
    out, pos = [], 0
    for match in INLINE_LINK.finditer(text):
        out.append(_bold(html.escape(text[pos:match.start()], quote=False)))
        label, href = match.group(1), match.group(2)
        external = href.startswith("http")
        attrs = f' href="{html.escape(href)}"'
        if external:
            attrs += ' target="_blank" rel="noopener"'
        out.append(f"<a{attrs}>{_bold(html.escape(label, quote=False))}</a>")
        pos = match.end()
    out.append(_bold(html.escape(text[pos:], quote=False)))
    return "".join(out)


def _bold(escaped: str) -> str:
    return INLINE_BOLD.sub(r"<strong>\1</strong>", escaped)


def markdown_to_html(body: str, theme: ThemeData, article: Article) -> tuple[str, list[tuple[str, str]]]:
    """本文を HTML にし、目次用に (id, 見出し) の一覧も返す。"""
    lines = body.splitlines()
    html_parts: list[str] = []
    toc: list[tuple[str, str]] = []
    paragraph: list[str] = []
    i = 0

    def flush() -> None:
        if paragraph:
            html_parts.append(f"<p>{inline(''.join(paragraph))}</p>")
            paragraph.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            flush()
            i += 1
            continue
        if stripped.startswith("<"):
            raise BuildError(f"{article.slug}: 本文にHTMLタグは書かない: {stripped[:40]}")
        block = BLOCK_RE.match(stripped)
        if block:
            flush()
            html_parts.append(render_chart(block.group(1).strip(), theme, article))
            i += 1
            continue
        if stripped.startswith("### "):
            flush()
            html_parts.append(f"<h3>{inline(stripped[4:].strip())}</h3>")
            i += 1
            continue
        if stripped.startswith("## "):
            flush()
            text = stripped[3:].strip()
            anchor = f"s{len(toc) + 1}"
            toc.append((anchor, text))
            html_parts.append(f'<h2 id="{anchor}">{inline(text)}</h2>')
            i += 1
            continue
        if stripped.startswith("# "):
            raise BuildError(f"{article.slug}: 見出しは ## と ### だけ（# は題名に使う）")
        if stripped.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            html_parts.append(render_table(rows, article))
            continue
        if re.match(r"^- ", stripped) or re.match(r"^\d+\. ", stripped):
            flush()
            ordered = bool(re.match(r"^\d+\. ", stripped))
            items = []
            pattern = r"^\d+\. " if ordered else r"^- "
            while i < len(lines) and re.match(pattern, lines[i].strip()):
                items.append(re.sub(pattern, "", lines[i].strip(), count=1))
                i += 1
            tag = "ol" if ordered else "ul"
            html_parts.append(f"<{tag}>" + "".join(f"<li>{inline(item)}</li>" for item in items) + f"</{tag}>")
            continue
        paragraph.append(stripped)
        i += 1
    flush()
    return "\n".join(html_parts), toc


def render_table(rows: list[str], article: Article) -> str:
    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    if len(rows) < 2 or not re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?", rows[1]):
        raise BuildError(f"{article.slug}: 表の2行目は |---|---| にする: {rows[:2]}")
    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    for row in body:
        if len(row) != len(head):
            raise BuildError(f"{article.slug}: 表の列数が揃っていません: {row}")
    thead = "".join(f'<th scope="col">{inline(c)}</th>' for c in head)
    tbody = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in body)
    return f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>'


# ---------------------------------------------------------------- 図

def _bar(row: dict[str, int]) -> str:
    total = row["_total"]
    segs = []
    for stance, cls in STANCE_ORDER:
        n = row.get(stance, 0)
        if n:
            segs.append(f'<span class="seg {cls}" style="width:{n / total * 100:.2f}%"></span>')
    return "".join(segs)


def _legend(row: dict[str, int]) -> str:
    total = row["_total"]
    items = []
    for stance, cls in STANCE_ORDER:
        n = row.get(stance, 0)
        items.append(f'<li><i class="{cls}"></i>{stance} {n:,}件（{pct(n, total)}）</li>')
    return "".join(items)


def _aria(label: str, row: dict[str, int]) -> str:
    total = row["_total"]
    parts = [f"{stance}{row.get(stance, 0):,}件（{pct(row.get(stance, 0), total)}）" for stance, _ in STANCE_ORDER]
    return f"{label}の意見{total:,}件の内訳: " + "、".join(parts)


def render_chart(target: str, theme: ThemeData, article: Article) -> str:
    period = jp_period(theme.period_start, theme.period_end)
    if target == "all":
        rows = []
        for label in theme.named_issues:
            row = theme.issues[label]
            rows.append(
                '<div class="chart-row">'
                f'<div class="chart-label">{html.escape(label)}<span>{row["_total"]:,}件</span></div>'
                f'<div class="bar" role="img" aria-label="{html.escape(_aria(label, row))}">{_bar(row)}</div>'
                "</div>"
            )
        legend = "".join(f'<li><i class="{cls}"></i>{stance}</li>' for stance, cls in STANCE_ORDER)
        return (
            '<figure class="stance-chart article-chrome">'
            f'<figcaption>論点ごとの立場の内訳（意見{theme.opinions:,}件、{period}）</figcaption>'
            + "".join(rows)
            + f'<ul class="legend">{legend}</ul>'
            '<p class="chart-note">Xの公開投稿のサンプルを分類した件数です。社会全体の世論調査ではありません。</p>'
            "</figure>"
        )
    if target not in theme.issues:
        raise BuildError(f"{article.slug}: [[chart:{target}]] の論点名が公開データにありません")
    row = theme.issues[target]
    return (
        '<figure class="stance-chart article-chrome">'
        f'<figcaption>「{html.escape(target)}」の意見{row["_total"]:,}件の立場（{period}）</figcaption>'
        f'<div class="bar" role="img" aria-label="{html.escape(_aria(target, row))}">{_bar(row)}</div>'
        f'<ul class="legend">{_legend(row)}</ul>'
        '<p class="chart-note">Xの公開投稿のサンプルを分類した件数です。社会全体の世論調査ではありません。</p>'
        "</figure>"
    )


# ---------------------------------------------------------------- ページ

CSS = """
:root{color-scheme:light;--accent:#1769d1;--accent-soft:#e7f1ff;--s1:#2f6fdf;--s2:#8fb4ef;--s3:#c9cfd8;--s4:#e08a3c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-body);line-height:1.85;-webkit-text-size-adjust:100%}
a{color:var(--accent)}
.site-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 16px;background:#fff;border-bottom:1px solid var(--line)}
.site-bar .brand{font-weight:900;color:var(--ink);text-decoration:none;letter-spacing:.02em}
.site-bar nav{display:flex;gap:14px;font-size:14px;font-weight:700}
.site-bar nav a{text-decoration:none}
.article-wrap{max-width:760px;margin:0 auto;padding:20px 16px 48px}
.crumbs{font-size:13px;color:var(--muted);margin:0 0 14px}
.crumbs a{color:var(--muted)}
.article-head .kicker{margin:0 0 6px;font-size:13px;font-weight:700;color:var(--accent)}
h1{margin:0 0 10px;font-size:clamp(23px,5.6vw,32px);line-height:1.45}
.byline{margin:0 0 18px;font-size:13px;color:var(--muted)}
.toc{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:12px 16px;margin:0 0 24px;font-size:14px}
.toc p{margin:0 0 4px;font-weight:700;color:var(--ink)}
.toc ol{margin:0;padding-left:20px}
.toc li{margin:2px 0}
.article-body>p:first-child{font-size:17px;color:var(--ink)}
.article-body h2{font-size:21px;line-height:1.5;margin:38px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--accent-soft)}
.article-body h3{font-size:17px;margin:26px 0 8px}
.article-body p,.article-body li{color:#2b3445}
.article-body ul,.article-body ol{padding-left:22px}
.table-wrap{overflow-x:auto;margin:14px 0 20px;border:1px solid var(--line);border-radius:var(--radius);background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.6}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f3f5f9;white-space:nowrap}
th:first-child,td:first-child{min-width:6em}
tr:last-child td{border-bottom:0}
.stance-chart{margin:18px 0 24px;padding:14px 16px;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius)}
.stance-chart figcaption{font-weight:700;font-size:14px;margin:0 0 10px}
.bar{display:flex;height:18px;border-radius:4px;overflow:hidden;background:#eef1f5}
.seg{display:block;height:100%}
.s1{background:var(--s1)}.s2{background:var(--s2)}.s3{background:var(--s3)}.s4{background:var(--s4)}
.chart-row{margin:0 0 10px}
.chart-label{display:flex;justify-content:space-between;font-size:13px;margin:0 0 3px}
.chart-label span{color:var(--muted)}
.legend{list-style:none;display:flex;flex-wrap:wrap;gap:4px 14px;padding:0;margin:10px 0 0;font-size:13px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.chart-note{margin:8px 0 0;font-size:12px;color:var(--muted)}
.data-note,.cta,.sources,.related{margin:28px 0 0;padding:16px;border-radius:var(--radius);background:var(--panel);border:1px solid var(--line);font-size:14px}
.data-note h2,.sources h2,.related h2,.cta h2{font-size:16px;margin:0 0 8px;border:0;padding:0}
.data-note p,.sources p{margin:0 0 6px;color:var(--muted)}
.sources ul,.related ul{margin:0;padding-left:20px}
.sources li{margin:0 0 6px}
.sources small{color:var(--muted)}
.cta{background:var(--accent-soft);border-color:#c7dcf8}
.cta p{margin:0 0 10px}
.cta a.button{display:inline-block;padding:10px 16px;border-radius:999px;background:var(--accent);color:#fff;font-weight:700;text-decoration:none}
.footer{margin-top:40px;text-align:center;color:var(--muted);font-size:13px}
.footer a{color:var(--accent);text-decoration:none}
.list-intro{color:var(--muted)}
.article-list{list-style:none;padding:0;margin:16px 0 0}
.article-list li{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;margin:0 0 12px}
.article-list a{font-weight:700;text-decoration:none;font-size:16px}
.article-list p{margin:6px 0 0;font-size:14px;color:var(--muted)}
"""

ADSENSE_TAG = """<!-- ADSENSE_TAG_START -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2542211932832864" crossorigin="anonymous"></script>
<!-- ADSENSE_TAG_END -->"""

GA_TAG = """<!-- GA_TAG_START -->
  <script>
    (function(){
      var allowedHosts = ["sns-reaction-map.jp"];
      if (allowedHosts.indexOf(window.location.hostname) === -1) return;
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function(){window.dataLayer.push(arguments);};
      var script = document.createElement('script');
      script.async = true;
      script.src = 'https://www.googletagmanager.com/gtag/js?id=G-K10S4YCZFH';
      document.head.appendChild(script);
      window.gtag('js', new Date());
      window.gtag('config', 'G-K10S4YCZFH');
    })();
  </script>
<!-- GA_TAG_END -->"""

# 記事から出ていくリンクのクリックを数える（OPERATIONS.md「計測できない施策は実装しない」）。
# 内部リンクに utm を付けるとセッションの流入元が上書きされるため、GA4 のイベントで数える。
CLICK_SCRIPT = """<script>
document.addEventListener("click", function (event) {
  var link = event.target.closest && event.target.closest("a[data-article-link]");
  if (!link || typeof window.gtag !== "function") return;
  window.gtag("event", "article_link_click", {
    article: document.body.getAttribute("data-article") || "index",
    link_type: link.getAttribute("data-article-link"),
    link_url: link.getAttribute("href")
  });
});
</script>"""


def site_config() -> dict[str, Any]:
    return json.loads(THEME_SEO.read_text(encoding="utf-8"))


def footer_html() -> str:
    links = ['<a href="../">トップ</a>']
    for href, label in FOOTER_LINKS:
        if href.startswith("http"):
            links.append(f'<a href="{href}" target="_blank" rel="noopener">{label}</a>')
        else:
            links.append(f'<a href="../{href}">{label}</a>')
    return '<footer class="footer"><p>© 2026 SNS反応まっぷ — ' + " · ".join(links) + "</p></footer>"


def head_html(*, title: str, description: str, canonical: str, image: str, json_ld: list[dict[str, Any]]) -> str:
    esc = html.escape
    ld = "\n".join(
        '<script type="application/ld+json">\n' + json.dumps(item, ensure_ascii=False, indent=2) + "\n</script>"
        for item in json_ld
    )
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="google-site-verification" content="m7TnCK7r49LynKemf0lmuJkzY4MoTTHDFgL3fW2bPlc" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}｜SNS反応まっぷ</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(canonical)}">
  <meta property="og:site_name" content="SNS反応まっぷ">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(image)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{esc(image)}">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="icon" href="../favicon.ico">
  <link rel="apple-touch-icon" href="../apple-touch-icon.png">
  <link rel="stylesheet" href="../site-tokens.css">
  <style>{CSS}</style>
{ADSENSE_TAG}
{GA_TAG}
{ld}
</head>"""


def related_html(article: Article, siblings: list[Article], theme: ThemeData) -> str:
    items = [
        f'<li><a href="{a.slug}.html" data-article-link="related">{html.escape(a.title)}</a></li>'
        for a in siblings
        if a.slug != article.slug
    ]
    items.append(
        f'<li><a href="../{theme.url}" data-article-link="theme">{html.escape(theme.title)}のテーマページ'
        "（全論点・代表的な投稿・投票）</a></li>"
    )
    return (
        '<section class="related article-chrome"><h2>あわせて読む</h2><ul>'
        + "".join(items)
        + '</ul><p><a href="index.html" data-article-link="index">記事の一覧</a></p></section>'
    )


def render_article(article: Article, theme: ThemeData, siblings: list[Article], site: dict[str, Any]) -> str:
    check_asserts(article, theme)
    body_html, toc = markdown_to_html(fill(article.body, theme), theme, article)
    description = fill(article.description, theme)
    if PLACEHOLDER_RE.search(body_html + description):
        raise BuildError(f"{article.slug}: 差し込みが残っています")
    base = site["site_url"].rstrip("/") + "/"
    canonical = base + article.url
    image = base + theme.image
    org = {
        "@type": "Organization",
        "name": site["organization"]["name"],
        "url": base + site["organization"]["url"],
    }
    json_ld = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article.title,
            "description": description,
            "image": [image],
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
            "datePublished": article.published_on.isoformat(),
            "dateModified": article.updated_on.isoformat(),
            "author": org,
            "publisher": org,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "トップ", "item": base},
                {"@type": "ListItem", "position": 2, "name": theme.title, "item": base + theme.url},
                {"@type": "ListItem", "position": 3, "name": article.title, "item": canonical},
            ],
        },
    ]
    toc_html = ""
    if len(toc) >= 3:
        toc_html = (
            '<nav class="toc article-chrome" aria-label="目次"><p>目次</p><ol>'
            + "".join(f'<li><a href="#{anchor}">{inline(text)}</a></li>' for anchor, text in toc)
            + "</ol></nav>"
        )
    dates = f"公開 {jp_date(article.published_on)}"
    if article.updated_on != article.published_on:
        dates += f"・更新 {jp_date(article.updated_on)}"
    period = jp_period(theme.period_start, theme.period_end)
    sources = "".join(
        f'<li><a href="{html.escape(s.url)}" target="_blank" rel="noopener">{html.escape(s.name)}</a>'
        f" <small>（{jp_date(s.checked_on)}確認）</small></li>"
        for s in article.sources
    )
    return f"""{head_html(title=article.title, description=description, canonical=canonical, image=image, json_ld=json_ld)}
<body data-article="{article.slug}">
<header class="site-bar article-chrome"><a class="brand" href="../">SNS反応まっぷ</a><nav><a href="index.html">記事一覧</a><a href="../{theme.url}" data-article-link="theme-nav">テーマのページ</a></nav></header>
<main class="article-wrap">
<nav class="crumbs article-chrome" aria-label="現在地"><a href="../">トップ</a> › <a href="../{theme.url}">{html.escape(theme.title)}</a> › 記事</nav>
<article>
<header class="article-head">
<p class="kicker article-chrome">{html.escape(theme.title)}</p>
<h1>{html.escape(article.title)}</h1>
<p class="byline article-chrome">SNS反応まっぷ編集部・{dates}</p>
</header>
{toc_html}
<div class="article-body">
{body_html}
</div>
<aside class="data-note article-chrome"><h2>データについて</h2><p>SNSの件数は、Yahoo!リアルタイム検索で{period}に集めたXの公開投稿{theme.collected:,}件のうち、意見と判定した{theme.opinions:,}件を論点と立場に分けた件数です（{jp_date(theme.updated_on)}更新）。投稿した人の中での内訳で、社会全体の世論調査ではありません。</p><p>制度の説明は、下の資料を確認日の時点で読んだ内容です。その後に変わっている場合があります。誤りのご指摘は<a href="{CONTACT_URL}" target="_blank" rel="noopener">お問い合わせフォーム</a>からお寄せください。</p></aside>
<section class="sources article-chrome"><h2>この記事で使った資料</h2><ul>{sources}</ul></section>
<aside class="cta article-chrome"><h2>論点ごとの意見と投票は、テーマのページで</h2><p>{html.escape(theme.title)}について集めた意見{theme.opinions:,}件を、論点ごとの代表的な投稿とあわせて読めます。あなたの考えに近い立場を選ぶ投票もあります。</p><a class="button" href="../{theme.url}" data-article-link="theme-cta">{html.escape(theme.title)}のページを見る</a></aside>
{related_html(article, siblings, theme)}
</article>
{footer_html()}
</main>
{CLICK_SCRIPT}
</body>
</html>
"""


def render_index(articles: list[Article], themes: dict[str, ThemeData], site: dict[str, Any]) -> str:
    base = site["site_url"].rstrip("/") + "/"
    # サイトマップ・canonical・内部リンクを index.html で揃える（トップ以外は sitemap に載る形がそのまま正規URL）
    canonical = base + f"{OUT_PREFIX}/index.html"
    title = "記事一覧"
    description = "SNS反応まっぷの記事一覧。意見が分かれる社会の話題について、検索される疑問ごとに、制度の答えとSNSで意見が分かれている理由をまとめています。"
    sections = []
    for theme_id in sorted({a.theme for a in articles}):
        theme = themes[theme_id]
        items = "".join(
            f'<li><a href="{a.slug}.html" data-article-link="index-item">{html.escape(a.title)}</a>'
            f"<p>{html.escape(fill(a.description, theme))}</p></li>"
            for a in articles
            if a.theme == theme_id
        )
        sections.append(
            f'<h2>{html.escape(theme.title)}</h2><ul class="article-list">{items}</ul>'
            f'<p><a href="../{theme.url}" data-article-link="theme">{html.escape(theme.title)}のテーマページへ</a></p>'
        )
    json_ld = [{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{title}｜SNS反応まっぷ",
        "description": description,
        "url": canonical,
    }]
    return f"""{head_html(title=title, description=description, canonical=canonical, image=base + "ogp/default.png", json_ld=json_ld)}
<body data-article="index">
<header class="site-bar article-chrome"><a class="brand" href="../">SNS反応まっぷ</a><nav><a href="../">トップ</a></nav></header>
<main class="article-wrap">
<nav class="crumbs article-chrome" aria-label="現在地"><a href="../">トップ</a> › 記事一覧</nav>
<h1>記事一覧</h1>
<p class="list-intro">検索される疑問に1ページずつ答える記事です。制度の答えは国や自治体の資料で確かめ、SNSで意見が分かれている点は、集めた投稿の件数とあわせて書いています。</p>
{"".join(sections)}
{footer_html()}
</main>
{CLICK_SCRIPT}
</body>
</html>
"""


# ---------------------------------------------------------------- 入口

# ---------------------------------------------------------------- 他のページからの入口

def entry_articles(theme: str | None = None, root: Path | None = None) -> list[Article]:
    """トップ・テーマページから張る記事（theme を渡すとそのテーマだけ）。並びは load_articles と同じ。
    root は生成するリポジトリの根（定期更新の隔離コピーで作るときに、そのコピーの原稿を読む）。"""
    src_dir = Path(root) / "content" / "articles" if root is not None else None
    return [a for a in load_articles(src_dir) if theme is None or a.theme == theme]


def entry_script(source: str) -> str:
    """トップ・テーマページの記事リンクのクリック計測（GA4 の article_link_click。記事ページと同じイベント名）。
    article に張った側のページ、link_type に "entry" を入れて、記事ページ内のクリックと分ける。"""
    if not re.fullmatch(r"[a-z0-9-]+", source):
        raise BuildError(f"計測の source は英小文字・数字・ハイフンだけにする: {source!r}")
    return f"""<script id="article-entry-tracking">
document.addEventListener("click", function (event) {{
  var link = event.target.closest && event.target.closest("a[data-article-entry]");
  if (!link || typeof window.gtag !== "function") return;
  window.gtag("event", "article_link_click", {{
    article: "{source}",
    link_type: "entry",
    link_url: link.getAttribute("href")
  }});
}});
</script>"""


def build() -> dict[Path, str]:
    """出力パス -> 中身。ディスクには書かない。"""
    articles = load_articles()
    site = site_config()
    themes = {theme_id: load_theme(theme_id) for theme_id in {a.theme for a in articles}}
    outputs: dict[Path, str] = {}
    for article in articles:
        siblings = [a for a in articles if a.theme == article.theme]
        outputs[OUT_DIR / f"{article.slug}.html"] = render_article(article, themes[article.theme], siblings, site)
    if articles:
        outputs[OUT_DIR / "index.html"] = render_index(articles, themes, site)
    return outputs


def article_pages() -> list[tuple[str, str]]:
    """サイトマップに載せる (docs/ からの相対パス, lastmod)。generate_seo_assets.py と
    validate_theme_seo.py が同じ一覧を使う（サイトマップと検査の食い違いを作らない）。"""
    articles = load_articles()
    if not articles:
        return []
    pages = [(a.url, a.updated_on.isoformat()) for a in articles]
    pages.append((f"{OUT_PREFIX}/index.html", max(a.updated_on for a in articles).isoformat()))
    return sorted(pages)


def main() -> int:
    parser = argparse.ArgumentParser(description="サイト内記事を原稿から作る")
    parser.add_argument("--check", action="store_true", help="作り直した結果が docs/articles/ と同じか確かめる")
    args = parser.parse_args()
    try:
        outputs = build()
    except BuildError as exc:
        print(f"NG  {exc}")
        return 1
    existing = set(OUT_DIR.glob("*.html")) if OUT_DIR.is_dir() else set()
    if args.check:
        problems = []
        for path, content in outputs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                problems.append(f"作り直すと変わります: {rel(path)}")
        for path in sorted(existing - set(outputs)):
            problems.append(f"原稿の無い記事があります: {rel(path)}")
        if problems:
            print("\n".join(f"NG  {p}" for p in problems))
            print("=> python3 scripts/build_articles.py を実行して docs/articles/ を作り直す"
                  "（データ更新で件数が変わったときにも必要）")
            return 1
        print(f"OK  記事{len(outputs) - (1 if outputs else 0)}本は原稿と公開データから作り直せます")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    for path in sorted(existing - set(outputs)):
        path.unlink()
        print(f"削除: {rel(path)}（原稿が無い）")
    print(f"記事{len(outputs) - (1 if outputs else 0)}本と一覧を {rel(OUT_DIR)}/ に書きました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
