#!/usr/bin/env python3
"""ルート（issue-stance-lab.github.io）のトップページを正典から生成する。

ルートは AdSense と検索エンジンがサイト全体を評価するときの入口だが、
2026-08-14 時点で Google に一度もクロールされていなかった（URL 検査の
「前回のクロール: 該当なし」）。中身がテーマ名の羅列だけだったため、
初回クロールで「クロール済み・インデックス未登録」になる恐れがあった。

このスクリプトはテーマの説明・件数・更新日を正典から読んで生成する。
ルート側に数字を手書きしないので、テーマ側と食い違うことがない。

2026-08-14 の初版は「文章ばかりで面白みがない」「ボタンを押すとまた同じような
ページが出る」という指摘を受けた。実測すると、ルートはポータル（docs/index.html）と
ヒーロー・件数・工程説明・テーマ一覧・注意書き・読み方まで重複しており、
画像だけが無い劣化コピーになっていた。そのため第2版では

  * ポータルと重複する説明（3ステップ・数字の読み方・編集方針の列挙）を削除し、
    docs/about.html へ寄せる
  * 各テーマにヒーロー画像と、テーマページ実物のスタンス内訳バーを載せる

という方針に変えている。ルートは「読ませるページ」ではなく「選ばせる入口」。

正典
  THEMES.yaml            … テーマID・表示名・更新日
  configs/theme-seo.json … 説明文・ページURL・最終更新日
  docs/index.html        … 分類済み件数（sync_portal_stats.py が算出した値）
  docs/<テーマページ>.html … 1本目のスタンス内訳バー（ラベル・幅・凡例）
  docs/images/topics/<id>/ … ヒーロー画像

件数を docs/index.html から読むのは、算出元の social-samples/ が本文を含み
Git 管理外のため。ポータルの表示値をそのまま引き写すことで二重集計を避ける。
スタンス内訳もテーマページの表示をそのまま引き写す。ルート側で数え直さないので、
テーマページと食い違うことがない。

使い方
  python3 scripts/build_root_index.py --output ../issue-stance-lab.github.io/index.html
  python3 scripts/build_root_index.py --output ... --check   # 差分があれば exit 1
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
THEMES_YAML = ROOT / "THEMES.yaml"
THEME_SEO = ROOT / "configs" / "theme-seo.json"
PORTAL_HTML = ROOT / "docs" / "index.html"

SITE_URL = "https://issue-stance-lab.github.io/"
MAP_BASE = "/sns-reaction-map/"
CONTACT_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSdySbMYxEsLOYmI4jsqjIkSGl6WHF78qLlypOmXAg9tVDy2FQ/viewform"
)

# 表示順とカテゴリ。docs/index.html のカテゴリ表記に揃えてある。
THEME_ORDER: list[tuple[str, str]] = [
    ("ai-copyright", "テクノロジー"),
    ("consumption-tax-cut", "税・財政"),
    ("fukushuto", "政治・統治機構"),
    ("bukatsu-chiiki", "教育・子ども"),
    ("koshitsu-tenpakai", "政治・皇室"),
    ("constitutional-amendment", "政治・法律"),
    ("takaichi", "政治・ネット選挙"),
    ("school-nickname-ban", "教育・子ども"),
    ("henoko-student-accident", "教育・基地問題"),
    ("elderly-license-revocation", "交通・福祉"),
    ("bike-blue-ticket", "交通・安全"),
]


class BuildError(RuntimeError):
    """正典どうしが食い違っているときに投げる。"""


def load_themes() -> dict[str, dict]:
    data = yaml.safe_load(THEMES_YAML.read_text(encoding="utf-8"))
    return data["themes"]


def load_seo() -> dict[str, dict]:
    data = json.loads(THEME_SEO.read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in data["themes"]}


def load_counts() -> dict[str, int]:
    """docs/index.html の分類済み件数を読む。"""
    portal = PORTAL_HTML.read_text(encoding="utf-8")
    found = re.findall(
        r'<strong id="topic-count-([a-z0-9-]+)">([0-9,]+)</strong>', portal
    )
    if not found:
        raise BuildError(f"{PORTAL_HTML} から分類済み件数を読めませんでした")
    return {theme: int(value.replace(",", "")) for theme, value in found}


# スタンス内訳バーの色。テーマページはそれぞれ独自の配色を持つが、ルートでは
# 11枚のカードが並ぶため、立場の向きだけを揃えた共通パレットにする。
# キーはテーマページの .temp-seg に付いているクラス名。
SEG_COLORS: dict[str, str] = {
    # 否定・反対・批判側
    "neg": "#dc2626",
    "con": "#dc2626",
    "oppose": "#dc2626",
    "accuse": "#dc2626",
    # 中立・情報共有
    "neu": "#94a3b8",
    "neutral": "#94a3b8",
    "mid": "#94a3b8",
    # 肯定・賛成・擁護側
    "pos": "#2563eb",
    "pro": "#2563eb",
    "support": "#2563eb",
    "defend": "#2563eb",
    # 手続き・留保
    "process": "#f59e0b",
    "cautious": "#f59e0b",
}


def find_card_image(page: Path, theme: str) -> str:
    """カードに載せる画像を1枚選び、/sns-reaction-map/ からのパスを返す。

    ヒーロー画像（*-hero.webp）は使わない。ポータル（docs/index.html）が
    テーマカードに同じ絵を使っているので、ルートで再利用すると
    「ボタンを押すとまた同じページ」に見えてしまう。

    代わりにテーマページで最初に出てくる論点別インフォグラフィックを使う。
    ページ内の出現順は論点順なので、これは論点1の図であり、
    カードに並べるスタンス内訳バー（同じく論点1）と対になる。
    """
    text = page.read_text(encoding="utf-8")
    found = re.findall(
        r'src="(images/topics/[^"]*infographic-wide[^"]*\.webp)"', text
    )
    if not found:
        raise BuildError(f"{page} に論点別インフォグラフィックがありません")
    path = found[0]
    if not (PORTAL_HTML.parent / path).is_file():
        raise BuildError(f"{page} が参照する {path} が見つかりません")
    if f"/topics/{theme}/" not in f"/{path}":
        raise BuildError(f"{page} の画像 {path} が {theme} のものではありません")
    return MAP_BASE + path


def _slice_div(text: str, start: int) -> str:
    """start 位置の <div> に対応する </div> までを切り出す。"""
    depth = 0
    for match in re.finditer(r"<div\b|</div>", text[start:]):
        depth += 1 if match.group(0).startswith("<div") else -1
        if depth == 0:
            return text[start : start + match.end()]
    raise BuildError("div の対応が取れませんでした")


def _strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment)).strip()


def extract_stance(page: Path) -> dict | None:
    """テーマページの1本目のスタンス内訳バーを読む。

    バーが無いテーマ（bukatsu-chiiki / elderly-license-revocation / fukushuto）は
    None を返す。無いものを作らず、カードから省く。
    """
    text = page.read_text(encoding="utf-8")
    # takaichi のように role/aria-label が付くテーマがあるので属性を許す。
    head_match = re.search(r'<div class="temp-bar-label"[\s>]', text)
    if head_match is None:
        return None
    head = head_match.start()

    spans = re.findall(r"<span>(.*?)</span>", _slice_div(text, head), re.S)
    if len(spans) < 2:
        raise BuildError(f"{page} のスタンスバーの見出しを読めませんでした")
    caption, summary = (_strip_tags(span) for span in spans[:2])

    bar_match = re.compile(r'<div class="temp-bar"[\s>]').search(text, head)
    if bar_match is None:
        raise BuildError(f"{page} にスタンスバー本体がありません")
    segments = [
        {"cls": cls.split()[0], "width": width}
        for cls, width in re.findall(
            r'<div class="temp-seg ([^"]+)" style="width:\s*([\d.]+)%"',
            _slice_div(text, bar_match.start()),
        )
    ]
    if not segments:
        raise BuildError(f"{page} のスタンスバーに区画がありません")

    legend_match = re.compile(r'<div class="temp-bar-legend"[\s>]').search(
        text, bar_match.start()
    )
    legend: list[str] = []
    if legend_match is not None:
        legend = [
            _strip_tags(span)
            for span in re.findall(
                r"<span>(.*?)</span>", _slice_div(text, legend_match.start()), re.S
            )
        ]
    if len(legend) != len(segments):
        raise BuildError(
            f"{page} のスタンスバーで区画数({len(segments)})と"
            f"凡例数({len(legend)})が合いません"
        )

    for segment, label in zip(segments, legend):
        if segment["cls"] not in SEG_COLORS:
            raise BuildError(
                f"{page} に未知のスタンス区画 .{segment['cls']} があります。"
                "SEG_COLORS に色を足してください"
            )
        segment["color"] = SEG_COLORS[segment["cls"]]
        segment["label"] = label
    return {"caption": caption, "summary": summary, "segments": segments}


def format_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.year}年{parsed.month}月{parsed.day}日"


def collect_entries() -> list[dict]:
    themes = load_themes()
    seo = load_seo()
    counts = load_counts()

    known = set(themes) & set(seo) & set(counts)
    listed = {theme for theme, _ in THEME_ORDER}
    if listed != known:
        raise BuildError(
            "テーマの一覧が正典と一致しません: "
            f"表示順のみ={sorted(listed - known)}, 正典のみ={sorted(known - listed)}"
        )

    entries = []
    for theme, category in THEME_ORDER:
        meta = seo[theme]
        page = PORTAL_HTML.parent / meta["url"]
        entries.append(
            {
                "id": theme,
                "category": category,
                "title": themes[theme]["title"],
                "description": meta["description"],
                "url": MAP_BASE + meta["url"],
                "count": counts[theme],
                "modified": meta["dateModified"],
                "hero": find_card_image(page, theme),
                "stance": extract_stance(page),
            }
        )
    return entries


def stance_block(stance: dict | None) -> str:
    """カード内のスタンス内訳バー。テーマページの表示をそのまま引き写す。"""
    if stance is None:
        return ""
    segments = "".join(
        '<i style="width:{width}%;background:{color}" title="{label}"></i>'.format(
            width=segment["width"],
            color=segment["color"],
            label=html.escape(segment["label"], quote=True),
        )
        for segment in stance["segments"]
    )
    legend = "".join(
        '<li><i style="background:{color}"></i>{label}</li>'.format(
            color=segment["color"], label=html.escape(segment["label"])
        )
        for segment in stance["segments"]
    )
    return (
        '<span class="stance-cap">論点1・{caption}</span>'
        '<span class="stance-bar">{segments}</span>'
        '<span class="stance-num">{summary}</span>'
        '<ul class="stance-leg">{legend}</ul>'
    ).format(
        caption=html.escape(stance["caption"]),
        segments=segments,
        summary=html.escape(stance["summary"]),
        legend=legend,
    )


def topic_cards(entries: list[dict]) -> str:
    rows = []
    for entry in entries:
        rows.append(
            "      <li><a href=\"{url}\">"
            "<img src=\"{hero}\" alt=\"\" loading=\"lazy\" decoding=\"async\""
            " width=\"1915\" height=\"821\">"
            "<span class=\"body\">"
            "<span class=\"cat\">{category}</span>"
            "<span class=\"ttl\">{title}</span>"
            "<span class=\"sum\">{description}</span>"
            "{stance}"
            "<span class=\"meta\">分類済み <b>{count:,}</b>件"
            "<span class=\"sep\">/</span>最終更新 {modified}</span>"
            "</span></a></li>".format(
                url=html.escape(entry["url"]),
                hero=html.escape(entry["hero"]),
                category=html.escape(entry["category"]),
                title=html.escape(entry["title"]),
                description=html.escape(entry["description"]),
                stance=stance_block(entry["stance"]),
                count=entry["count"],
                modified=html.escape(format_date(entry["modified"])),
            )
        )
    return "\n".join(rows)


def recent_updates(entries: list[dict], limit: int = 3) -> str:
    latest = sorted(entries, key=lambda e: e["modified"], reverse=True)[:limit]
    rows = []
    for entry in latest:
        rows.append(
            "        <li><span class=\"when\">{modified}</span>"
            "<a href=\"{url}\">{title}</a>"
            "<span class=\"what\">分類済み {count:,}件に更新</span></li>".format(
                modified=html.escape(format_date(entry["modified"])),
                url=html.escape(entry["url"]),
                title=html.escape(entry["title"]),
                count=entry["count"],
            )
        )
    return "\n".join(rows)


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Issue Stance Lab — 意見が割れる社会の争点を、理由から整理する</title>
<meta name="description" content="Issue Stance Lab は、SNS上の公開投稿を収集・分類し、社会で意見が割れている{theme_count}のテーマを「賛成・反対それぞれの理由」とともに整理している個人運営のプロジェクトです。">
<link rel="canonical" href="{site_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Issue Stance Lab">
<meta property="og:title" content="Issue Stance Lab — 意見が割れる社会の争点を、理由から整理する">
<meta property="og:description" content="SNSの公開投稿サンプルを収集・AI分類し、賛成・反対それぞれの理由と背景を整理して公開しています。">
<meta property="og:url" content="{site_url}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2542211932832864" crossorigin="anonymous"></script>
<style>
:root{{--blue:#075ef2;--orange:#ff5426;--navy:#071a3d;--muted:#61708a;--line:#e6ebf3;--shadow:0 12px 32px rgba(16,47,91,.09);--shadow-sm:0 5px 18px rgba(16,47,91,.08);--font:-apple-system,BlinkMacSystemFont,'Hiragino Sans','Noto Sans JP','Yu Gothic',sans-serif}}
*{{box-sizing:border-box}}
body{{margin:0;background:#f8faff;color:var(--navy);font-family:var(--font);line-height:1.8;-webkit-font-smoothing:antialiased}}
a{{color:var(--blue)}}
.shell{{max-width:880px;margin:0 auto;padding:0 20px}}
header.site{{background:#fff;border-bottom:1px solid var(--line)}}
header.site .shell{{display:flex;align-items:center;justify-content:space-between;height:66px;gap:16px}}
.brand{{font-weight:900;font-size:18px;letter-spacing:-.02em;text-decoration:none;color:var(--navy)}}
.brand span{{display:block;font-size:10px;font-weight:600;color:var(--muted)}}
header.site nav a{{font-size:12px;font-weight:700;text-decoration:none;margin-left:16px}}
.hero{{background:#fff;border-bottom:1px solid var(--line);padding:44px 0 38px}}
h1{{font-size:clamp(26px,4.2vw,38px);line-height:1.4;letter-spacing:-.03em;margin:0 0 16px;font-weight:900}}
.lead{{font-size:15px;color:#35435b;margin:0 0 22px}}
.cta{{display:inline-flex;align-items:center;gap:10px;padding:14px 24px;border-radius:999px;background:linear-gradient(135deg,var(--blue),#087dff);color:#fff;text-decoration:none;font-weight:800;font-size:15px;box-shadow:0 10px 24px rgba(7,94,242,.22)}}
.facts{{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0 0;padding:0;list-style:none}}
.facts li{{background:#f4f8ff;border:1px solid var(--line);border-radius:10px;padding:8px 14px;font-size:12px;color:var(--muted)}}
.facts b{{display:block;font-size:17px;color:var(--navy);letter-spacing:-.02em}}
main{{padding:8px 0 56px}}
section{{margin-top:40px}}
h2{{font-size:20px;letter-spacing:-.02em;margin:0 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line)}}
h3{{font-size:15px;margin:0 0 6px}}
p{{margin:0 0 14px;font-size:14px}}
.note{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--orange);border-radius:10px;padding:14px 18px;font-size:13px;color:#4a5872;box-shadow:var(--shadow-sm)}}
.note strong{{display:block;color:var(--navy);margin-bottom:4px;font-size:13px}}
.topics{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:0;padding:0;list-style:none}}
.topics a{{display:flex;flex-direction:column;height:100%;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;text-decoration:none;color:var(--navy);box-shadow:var(--shadow-sm);transition:transform .2s,box-shadow .2s}}
.topics a:hover{{transform:translateY(-2px);box-shadow:var(--shadow)}}
.topics img{{display:block;width:100%;height:auto;aspect-ratio:1915/821;object-fit:cover;background:#eef2f9;border-bottom:1px solid var(--line)}}
.topics .body{{display:flex;flex-direction:column;flex:1;padding:14px 16px 16px}}
.topics .cat{{display:inline-block;align-self:flex-start;margin-bottom:6px;padding:3px 8px;border-radius:6px;background:#eef5ff;color:var(--blue);font-size:10px;font-weight:800}}
.topics .ttl{{display:block;font-size:15px;font-weight:800;line-height:1.5;letter-spacing:-.01em}}
.topics .sum{{display:block;margin:6px 0 0;font-size:12.5px;line-height:1.75;color:#4a5872}}
.topics .meta{{display:block;margin-top:auto;padding-top:12px;font-size:11px;color:var(--muted);font-weight:600}}
.topics .meta b{{color:var(--navy);font-size:12px}}
.topics .sep{{margin:0 6px;color:var(--line)}}
.stance-cap{{display:block;margin:12px 0 5px;font-size:10.5px;font-weight:800;color:var(--muted);letter-spacing:.01em}}
.stance-bar{{display:flex;height:9px;border-radius:5px;overflow:hidden;background:#eef2f9}}
.stance-bar i{{display:block;min-width:1px}}
.stance-num{{display:block;margin-top:6px;font-size:11px;font-weight:700;color:var(--navy)}}
.stance-leg{{margin:5px 0 0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:2px 10px}}
.stance-leg li{{font-size:10px;color:var(--muted);font-weight:600;line-height:1.6}}
.stance-leg i{{display:inline-block;width:7px;height:7px;border-radius:2px;margin-right:4px;vertical-align:middle}}
.recent{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:8px 22px;box-shadow:var(--shadow-sm)}}
.recent ul{{margin:0;padding:0;list-style:none}}
.recent li{{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px;padding:12px 0;border-bottom:1px solid var(--line);font-size:13px}}
.recent li:last-child{{border-bottom:none}}
.recent .when{{font-size:11px;color:var(--muted);font-weight:700;min-width:104px}}
.recent .what{{font-size:11px;color:var(--muted)}}
footer.site{{background:#07172f;color:rgba(255,255,255,.66);padding:30px 0 22px;font-size:12px}}
footer.site a{{color:rgba(255,255,255,.8)}}
footer.site .links{{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:14px}}
footer.site .copy{{padding-top:14px;border-top:1px solid rgba(255,255,255,.12);font-size:11px}}
@media(max-width:680px){{.topics{{grid-template-columns:1fr}}header.site .shell{{height:auto;padding-top:12px;padding-bottom:12px;flex-direction:column;align-items:flex-start}}header.site nav a{{margin:0 16px 0 0}}.recent .when{{min-width:0}}}}
</style>
</head>
<body>
<header class="site">
  <div class="shell">
    <a class="brand" href="/">Issue Stance Lab<span>意見が割れる争点を、理由から整理する</span></a>
    <nav>
      <a href="{map_base}">SNS反応まっぷ</a>
      <a href="{map_base}about.html#operator">運営者情報</a>
      <a href="{map_base}usage.html">使い方</a>
    </nav>
  </div>
</header>

<div class="hero">
  <div class="shell">
    <h1>賛成か反対かではなく、<br>「なぜそう考えるのか」を並べて読む。</h1>
    <p class="lead">Issue Stance Lab は、社会で意見が割れているテーマについて、SNS上の公開投稿を収集・分類し、どんな立場の人が何を理由にそう考えているのかを整理して公開している個人運営のプロジェクトです。制作しているサイト「SNS反応まっぷ」では、現在{theme_count}のテーマを公開しています。</p>
    <a class="cta" href="{map_base}">SNS反応まっぷを見る →</a>
    <ul class="facts">
      <li>公開中のテーマ<b>{theme_count}</b></li>
      <li>分類済み投稿<b>{total_count:,}件</b></li>
      <li>最終更新<b>{latest_date}</b></li>
    </ul>
  </div>
</div>

<main class="shell">

  <section>
    <div class="note">
      <strong>掲載内容の性質について</strong>
      掲載しているのは、収集したSNS公開投稿の<b>サンプル</b>を整理した結果であり、社会全体の世論調査ではありません。件数の比率をそのまま「世論の比率」として読むことはできません。各テーマページには、取得元・件数・分類方法を明記しています。
    </div>
  </section>

  <section>
    <h2>公開中のテーマ</h2>
    <p>バーは各テーマの<b>論点1</b>について、どの立場の投稿が何件あったかの内訳です。テーマページに出している数字をそのまま載せています。<a href="{map_base}about.html#numbers">数字の読み方</a>／<a href="{map_base}about.html#method">調査・編集方法</a></p>
    <ul class="topics">
{topic_cards}
    </ul>
  </section>

  <section>
    <h2>最近の更新</h2>
    <div class="recent">
      <ul>
{recent_updates}
      </ul>
    </div>
  </section>

  <section>
    <h2>運営者・お問い合わせ</h2>
    <p>本サイトはエンジニアではない個人が1人で運営しています。テーマの選定、収集・分類の仕組みづくり、ページ制作まで同じ1人が行っており、「SNS反応まっぷ編集部」は法人名ではなく個人プロジェクトの編集名義です。収集や分類の手順は<a href="{map_base}about.html#method">調査・編集方法</a>、運営者情報は<a href="{map_base}about.html#operator">運営者情報</a>に書いています。誤りのご指摘・削除依頼は<a href="{contact_url}" target="_blank" rel="noopener noreferrer">お問い合わせフォーム</a>へお寄せください。</p>
  </section>

</main>

<footer class="site">
  <div class="shell">
    <div class="links">
      <a href="{map_base}">SNS反応まっぷ</a>
      <a href="{map_base}about.html#operator">運営者情報</a>
      <a href="{map_base}about.html#method">調査・編集方法</a>
      <a href="{contact_url}" target="_blank" rel="noopener noreferrer">お問い合わせ・訂正依頼</a>
      <a href="{map_base}privacy.html">プライバシーポリシー</a>
      <a href="{map_base}disclaimer.html">免責事項</a>
      <a href="{map_base}image-policy.html">画像制作方針</a>
      <a href="{map_base}usage.html">使い方・FAQ</a>
    </div>
    <div class="copy">© Issue Stance Lab</div>
  </div>
</footer>
</body>
</html>
"""


def render() -> str:
    entries = collect_entries()
    latest = max(entry["modified"] for entry in entries)
    return PAGE.format(
        site_url=SITE_URL,
        map_base=MAP_BASE,
        contact_url=CONTACT_URL,
        theme_count=f"{len(entries)}",
        total_count=sum(entry["count"] for entry in entries),
        latest_date=format_date(latest),
        topic_cards=topic_cards(entries),
        recent_updates=recent_updates(entries),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="書き出し先（ルートリポジトリの index.html）",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き換えず、内容が一致しなければ exit 1",
    )
    args = parser.parse_args(argv)

    try:
        page = render()
    except BuildError as exc:
        print(f"NG {exc}")
        return 1

    if args.check:
        if not args.output.is_file():
            print(f"NG {args.output} がありません")
            return 1
        if args.output.read_text(encoding="utf-8") != page:
            print(f"NG {args.output} が正典から生成した内容と一致しません")
            return 1
        print(f"OK {args.output} は正典と一致しています")
        return 0

    args.output.write_text(page, encoding="utf-8")
    print(f"Generated {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
