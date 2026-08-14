#!/usr/bin/env python3
"""ルート（issue-stance-lab.github.io）のトップページを正典から生成する。

ルートは AdSense と検索エンジンがサイト全体を評価するときの入口だが、
2026-08-14 時点で Google に一度もクロールされていなかった（URL 検査の
「前回のクロール: 該当なし」）。中身がテーマ名の羅列だけだったため、
初回クロールで「クロール済み・インデックス未登録」になる恐れがあった。

このスクリプトはテーマの説明・件数・更新日を正典から読んで生成する。
ルート側に数字を手書きしないので、テーマ側と食い違うことがない。

正典
  THEMES.yaml            … テーマID・表示名・更新日
  configs/theme-seo.json … 説明文・ページURL・最終更新日
  docs/index.html        … 分類済み件数（sync_portal_stats.py が算出した値）

件数を docs/index.html から読むのは、算出元の social-samples/ が本文を含み
Git 管理外のため。ポータルの表示値をそのまま引き写すことで二重集計を避ける。

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
        entries.append(
            {
                "id": theme,
                "category": category,
                "title": themes[theme]["title"],
                "description": meta["description"],
                "url": MAP_BASE + meta["url"],
                "count": counts[theme],
                "modified": meta["dateModified"],
            }
        )
    return entries


def topic_cards(entries: list[dict]) -> str:
    rows = []
    for entry in entries:
        rows.append(
            "      <li><a href=\"{url}\">"
            "<span class=\"cat\">{category}</span>"
            "<span class=\"ttl\">{title}</span>"
            "<span class=\"sum\">{description}</span>"
            "<span class=\"meta\">分類済み <b>{count:,}</b>件"
            "<span class=\"sep\">/</span>最終更新 {modified}</span>"
            "</a></li>".format(
                url=html.escape(entry["url"]),
                category=html.escape(entry["category"]),
                title=html.escape(entry["title"]),
                description=html.escape(entry["description"]),
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
.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:0;padding:0;list-style:none}}
.steps li{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:var(--shadow-sm)}}
.steps .num{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#eef5ff;color:var(--blue);font-size:12px;font-weight:900;margin-bottom:10px}}
.steps p{{font-size:12px;color:var(--muted);margin:0}}
.topics{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:0;padding:0;list-style:none}}
.topics a{{display:block;height:100%;background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;text-decoration:none;color:var(--navy);box-shadow:var(--shadow-sm);transition:transform .2s,box-shadow .2s}}
.topics a:hover{{transform:translateY(-2px);box-shadow:var(--shadow)}}
.topics .cat{{display:inline-block;margin-bottom:6px;padding:3px 8px;border-radius:6px;background:#eef5ff;color:var(--blue);font-size:10px;font-weight:800}}
.topics .ttl{{display:block;font-size:15px;font-weight:800;line-height:1.5;letter-spacing:-.01em}}
.topics .sum{{display:block;margin:6px 0 10px;font-size:12.5px;line-height:1.75;color:#4a5872}}
.topics .meta{{display:block;font-size:11px;color:var(--muted);font-weight:600}}
.topics .meta b{{color:var(--navy);font-size:12px}}
.topics .sep{{margin:0 6px;color:var(--line)}}
.recent{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:8px 22px;box-shadow:var(--shadow-sm)}}
.recent ul{{margin:0;padding:0;list-style:none}}
.recent li{{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px;padding:12px 0;border-bottom:1px solid var(--line);font-size:13px}}
.recent li:last-child{{border-bottom:none}}
.recent .when{{font-size:11px;color:var(--muted);font-weight:700;min-width:104px}}
.recent .what{{font-size:11px;color:var(--muted)}}
.policy{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:var(--shadow-sm)}}
.policy ul{{margin:0;padding-left:20px;font-size:14px}}
.policy li{{margin-bottom:8px}}
footer.site{{background:#07172f;color:rgba(255,255,255,.66);padding:30px 0 22px;font-size:12px}}
footer.site a{{color:rgba(255,255,255,.8)}}
footer.site .links{{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:14px}}
footer.site .copy{{padding-top:14px;border-top:1px solid rgba(255,255,255,.12);font-size:11px}}
@media(max-width:680px){{.steps,.topics{{grid-template-columns:1fr}}header.site .shell{{height:auto;padding-top:12px;padding-bottom:12px;flex-direction:column;align-items:flex-start}}header.site nav a{{margin:0 16px 0 0}}.recent .when{{min-width:0}}}}
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
    <h2>何をしているか</h2>
    <p>ニュースやSNSで意見が割れる争点は、「賛成が多い／反対が多い」という数字だけを見ても、その裏にある理由までは分かりません。同じ「反対」でも、制度の中身に反対している人と、決め方の乱暴さに反対している人では、話がまったく噛み合いません。Issue Stance Lab は、そこを分けて読めるようにすることを目的にしています。</p>
    <p>そのため、各テーマでは投稿を「賛成／反対」だけで数えず、<b>何について語っているか（論点）</b>と<b>その論点に対する立場</b>の2つに分けて分類しています。たとえば消費税減税なら、財源をどうするかを論じている投稿と、生活の苦しさを訴えている投稿は、どちらも「賛成」でも読み方が変わります。論点ごとに賛否の内訳が見えると、賛成派・反対派の内部でも意見が割れている場所が分かります。</p>
    <ol class="steps">
      <li>
        <span class="num">1</span>
        <h3>収集</h3>
        <p>テーマごとに賛否双方の立場から検索語を決め、Yahoo!リアルタイム検索から公開投稿を収集します。取得期間と件数は記録し、ページ上に表示します。</p>
      </li>
      <li>
        <span class="num">2</span>
        <h3>分類</h3>
        <p>大規模言語モデルを使い、各投稿が意見を含むかを判定したうえで、どの論点について何を主張しているかを分類します。分類は論点整理の補助であり、事実認定ではありません。</p>
      </li>
      <li>
        <span class="num">3</span>
        <h3>編集と公開</h3>
        <p>分類結果を人が確認し、賛成・反対それぞれの主要な論拠と争点の背景、一次資料へのリンクを整理してページにまとめます。読者は自分の立場を投票できます。</p>
      </li>
    </ol>
  </section>

  <section>
    <h2>数字の読み方</h2>
    <p>各テーマに表示している「分類済み◯件」は、<b>収集した投稿のうち、意見を含むと判定され論点分類まで済んだ件数</b>です。収集した総数とは別の数字で、テーマページには両方を載せています。母数が何を指しているかを取り違えると読み方が変わるため、ページ内の数字には必ず母数の名前を付けています。</p>
    <p>この数字は<b>そのテーマに関心があり、かつSNSに書き込んだ人の中での分布</b>です。世の中の意見の比率ではありません。関心が高い人ほど投稿しやすく、検索語の選び方によっても集まる投稿は変わります。何を検索語にしたかは各テーマページの調査条件に明記しているので、偏りの方向を読者が判断できるようにしています。</p>
    <p>ページ内の投票は、この分類結果とは別に集計しています。読者の投票結果を投稿の分類件数に混ぜることはありません。</p>
  </section>

  <section>
    <h2>公開中のテーマ</h2>
    <p>各テーマのページでは、争点の背景と経緯、賛成・反対それぞれの理由、論点ごとの分類件数、取得期間と検索条件、参照した一次資料を確認できます。以下の件数と最終更新日は各テーマページの表示と同じ値です。</p>
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
    <h2>編集方針</h2>
    <div class="policy">
      <ul>
        <li><b>賛否のどちらかを推奨しません。</b>特定の政党・団体・候補者を支持または批判する目的でテーマを選定・編集することはありません。</li>
        <li><b>両側の理由を必ず載せます。</b>片方の立場の論拠だけを詳しく書き、もう片方を要約で済ませることはしません。</li>
        <li><b>数字の出所を明示します。</b>ページに出す件数は収集した投稿データから機械的に算出したものだけを使い、根拠のない概数は掲載しません。算出できない数字はページに出しません。</li>
        <li><b>投稿の扱いに配慮します。</b>個々の投稿は要約とリンク中心で扱い、一般個人が特定される形での転載は行いません。</li>
        <li><b>分かっていないことは、分かっていないと書きます。</b>収集したデータだけでは判断できない点は、各テーマの「収集・分類で分かったこと」に明記します。</li>
        <li><b>誤りは訂正します。</b>事実誤認のご指摘および掲載内容の削除依頼には、内容を確認のうえ対応します。</li>
      </ul>
    </div>
  </section>

  <section>
    <h2>運営者・お問い合わせ</h2>
    <p>本サイトは個人が運営しています。テーマの選定、データ収集・分類の仕組みの開発、ページ制作までを一貫して行っています。ページ内で使っている「SNS反応まっぷ編集部」は個人運営プロジェクトの編集名義であり、法人名ではありません。</p>
    <p>収集の方法、意見投稿と判定する基準、論点と立場の分類方法、代表投稿の選び方、AI分類の誤りをどう確認しているかは、<a href="{map_base}about.html#method">調査・編集方法</a>に手順として書いています。運営者情報は<a href="{map_base}about.html#operator">運営者情報</a>をご覧ください。</p>
    <p>内容の誤りのご指摘、引用の削除依頼、その他のお問い合わせは<a href="{contact_url}" target="_blank" rel="noopener noreferrer">お問い合わせフォーム</a>よりお寄せください。個人運営のため個別の返信は原則として行っておりませんが、事実誤認のご指摘と削除依頼には対応します。</p>
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
