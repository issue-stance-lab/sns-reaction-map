#!/usr/bin/env python3
"""消費税減税テーマページを副首都ページのv3レイアウトから生成する。

docs/fukushuto-reaction-map.html をテンプレートとして読み、
社会実装済みの構造（CSS・投票UI・論点アリーナ・フッター）を保ったまま、
消費税減税のコンテンツとHermes分類データへ差し替える。

前提: scripts/build_consumption_tax_arena.py を先に実行して
      social-samples/consumption-tax-cut_arena_data.json を作っておく。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "docs" / "fukushuto-reaction-map.html"
OUTPUT = ROOT / "docs" / "consumption-tax-cut-reaction-map.html"
DATA = ROOT / "social-samples" / "consumption-tax-cut_arena_data.json"

PAGE_URL = "https://issue-stance-lab.github.io/sns-reaction-map/consumption-tax-cut-reaction-map.html"

# ヒーロー画像。topic-modern.css の .hero::before は --topic-hero-image 未指定だと
# ai-copyright-hero.webp にフォールバックするため、必ず値を入れる。
HERO_IMAGE = "url('images/consumption-tax-cut-hero.webp')"

# SEO_META / ARTICLE_JSON_LD の中身。テーマを configs/theme-seo.json に登録したあとは
# scripts/seo/apply_theme_trust.py が同じブロックを上書き管理するので、値を揃えておく。
HEADLINE = "消費税減税は何が論点？食料品限定と一律の賛否"
DESCRIPTION = (
    "消費税減税について、対象範囲、財源と社会保障、価格への効果、給付付き税額控除との比較、"
    "事業者の実務負担、公約と政治不信の6論点とSNS上の賛否を整理します。"
)
OGP_IMAGE = "https://issue-stance-lab.github.io/sns-reaction-map/images/consumption-tax-cut-hero.webp"
PUBLISHED_AT = "2026-07-28"
ORGANIZATION = {
    "@type": "Organization",
    "name": "SNS反応まっぷ編集部",
    "url": "https://issue-stance-lab.github.io/sns-reaction-map/about.html",
}

# 論点キー → ページ上の表示情報
ISSUE_META = {
    "減税の対象範囲": {
        "slug": "taishou",
        "bar_stances": {
            "減税推進": "一律・廃止まで下げる",
            "条件付き賛成・政府案に不満": "食料品限定では不十分",
            "減税反対・慎重": "これ以上広げるべきでない",
            "中立・情報": "範囲に言及なし",
        },
        "bar_label": "どこまで下げるか",
        "icon": "🧾",
        "short": "対象範囲",
        "focus": "「食料品だけ」「期限付き」の政府案に対し、一律・恒久を求める不満が集まりました。",
        "headline": "食料品だけか、一律か",
        "desc": "政府案は食料品に対象を絞った限定的な減税。「中途半端」「一律5%か廃止まで踏み込め」という不満と、「まず実現することが先」という現実論がぶつかる論点。",
        "args": {
            "減税推進": "食料品限定・期限付きでは生活実感に届かない。一律5%か廃止まで踏み込むべきだ",
            "条件付き賛成・政府案に不満": "減税自体は歓迎だが、対象と期限を絞った政府案では中途半端だ",
            "減税反対・慎重": "対象を広げるほど税収の穴が大きくなり、線引きも複雑になる",
        },
    },
    "財源と社会保障": {
        "slug": "zaigen",
        "bar_stances": {
            "減税推進": "歳出の組み替えで賄える",
            "条件付き賛成・政府案に不満": "財源の説明がほしい",
            "減税反対・慎重": "社会保障の財源が細る",
            "中立・情報": "立場を示さず論点を共有",
        },
        "bar_label": "財源をどう埋めるか",
        "icon": "🏛️",
        "short": "財源・社会保障",
        "focus": "減税分を何で埋めるのか。社会保障の財源をめぐる不安と、財源論そのものへの不信が交差します。",
        "headline": "減った分は誰が払うのか",
        "desc": "消費税は社会保障の財源とされてきた。減税分を国債・歳出削減・別の増税のどれで埋めるのか、そもそも財源論は増税側の方便なのか、で評価が割れる。",
        "args": {
            "減税推進": "財源論は増税のための口実。歳出の組み替えと国債で対応できる",
            "条件付き賛成・政府案に不満": "減税には賛成だが、財源の説明がないまま進めるのは不安だ",
            "減税反対・慎重": "年金・医療の財源が細る。財源を示さない減税は無責任だ",
        },
    },
    "減税の効果": {
        "slug": "kouka",
        "bar_stances": {
            "減税推進": "物価高に効く",
            "条件付き賛成・政府案に不満": "効くが規模が足りない",
            "減税反対・慎重": "効かない・副作用が大きい",
            "中立・情報": "実施して検証すべき",
        },
        "bar_label": "生活に効くと考えるか",
        "icon": "📉",
        "short": "減税の効果",
        "focus": "値下げに反映されるのか、インフレを加速させないか。効果の見立てで評価が割れます。",
        "headline": "本当に生活は楽になるのか",
        "desc": "減税分が価格に転嫁されず事業者の利益になる、需要を刺激してインフレを加速させる、という懐疑と、物価高の直撃を和らげる即効性を評価する声が対立する。",
        "args": {
            "減税推進": "物価高対策として最も早く広く効く。可処分所得が直接増える",
            "条件付き賛成・政府案に不満": "効果は認めるが、この規模と期間では生活実感まで届かない",
            "減税反対・慎重": "値下げに反映されず企業に吸収される。供給不足の中ではインフレを悪化させる",
        },
    },
    "給付など他策との比較": {
        "slug": "kyufu",
        "bar_stances": {
            "減税推進": "減税を推す",
            "条件付き賛成・政府案に不満": "減税と給付の併用を",
            "減税反対・慎重": "給付・税額控除を推す",
            "中立・情報": "手段を比較するのみ",
        },
        "bar_label": "減税と他の手段のどちらを推すか",
        "icon": "💴",
        "short": "給付との比較",
        "focus": "給付付き税額控除や現金給付と比べて、どちらが望ましいかが問われました。",
        "headline": "減税か、給付付き税額控除か",
        "desc": "給付付き税額控除・現金給付・所得税や住民税の減税など、他の手段と比べてどれが望ましいか。低所得層への効果と、実行までのスピードが論点になる。",
        "args": {
            "減税推進": "給付は一度きりで手続きも重い。減税なら全員に継続して効く",
            "条件付き賛成・政府案に不満": "減税と給付を組み合わせなければ、低所得層には届かない",
            "減税反対・慎重": "逆進性の是正が目的なら、給付付き税額控除の方が的を絞れる",
        },
    },
    "事業者の実務負担": {
        "slug": "jigyousha",
        "bar_stances": {
            "減税推進": "実務は見送る理由にならない",
            "条件付き賛成・政府案に不満": "準備期間があれば回る",
            "減税反対・慎重": "現場の負担が大きすぎる",
            "中立・情報": "対応状況を共有",
        },
        "bar_label": "現場が対応できると考えるか",
        "icon": "🏪",
        "short": "事業者の負担",
        "focus": "レジ改修やインボイス対応など、税率を動かす現場のコストが論点になりました。",
        "headline": "レジ改修とインボイスの現場",
        "desc": "税率を動かすたびに発生するレジ・システム改修、インボイス対応、税率変更のタイミング。現場の負担を理由にした慎重論と、それを言い訳とみる立場が対立する。",
        "args": {
            "減税推進": "システム改修は減税をやらない言い訳にされている",
            "条件付き賛成・政府案に不満": "減税は必要だが、現場が対応できる準備期間を確保すべきだ",
            "減税反対・慎重": "レジ改修の負担が中小事業者に集中する。短期の税率変更は現場が回らない",
        },
    },
    "公約と政治不信": {
        "slug": "kouyaku",
        "bar_stances": {
            "減税推進": "公約どおり実行すべき",
            "条件付き賛成・政府案に不満": "実行したとは言えない",
            "減税反対・慎重": "公約に縛られるべきでない",
            "中立・情報": "経緯の共有・立場不明",
        },
        "bar_label": "公約の実行を求めるか",
        "icon": "🗳️",
        "short": "公約・政治不信",
        "focus": "選挙で減税を掲げた政党が採決でどう動いたか。税制の中身より政治の姿勢が問われました。",
        "headline": "公約はどこへ行ったのか",
        "desc": "選挙で減税を掲げた政党が採決でどう動いたか、政権はどこまで踏み込むのか、財務省の影響力をどう見るか。税制の中身より政治の姿勢を問う声が集まる論点。",
        "args": {
            "減税推進": "公約に掲げた減税を実行しない政党は信用できない。先送りの言い訳が続いている",
            "条件付き賛成・政府案に不満": "公約どおりとは言えない中身で決着させ、やった形だけを作っている",
            "減税反対・慎重": "選挙目当ての減税公約に振り回されるべきではない。反対した側にも財政上の理由がある",
        },
    },
    "その他": {
        "slug": "sonota",
        "bar_stances": {
            "減税推進": "減税に前向き",
            "条件付き賛成・政府案に不満": "条件付きで前向き",
            "減税反対・慎重": "減税に慎重",
            "中立・情報": "立場不明",
        },
        "bar_label": "立場の内訳",
        "icon": "💬",
        "short": "その他",
        "focus": "上記の論点に収まらない声。",
        "headline": "その他・分類しきれない声",
        "desc": "上記の論点に収まらない投稿、税制全般への一般論、論点が特定できない意見。",
        "args": {
            "減税推進": "",
            "条件付き賛成・政府案に不満": "",
            "減税反対・慎重": "",
        },
    },
}

STANCE_META = {
    "減税推進": {
        "color": "#059669",
        "bg": "#ecfdf5",
        "shadow": "rgba(5,150,105,.22)",
        "icon": "✓",
        "desc": "一律減税や廃止まで踏み込むべきだ",
        "label": "推進",
    },
    "条件付き賛成・政府案に不満": {
        "color": "#f59e0b",
        "bg": "#fffbeb",
        "shadow": "rgba(245,158,11,.22)",
        "icon": "△",
        "desc": "減税は賛成、でも今の案では足りない",
        "label": "条件付き",
    },
    "減税反対・慎重": {
        "color": "#dc2626",
        "bg": "#fef2f2",
        "shadow": "rgba(220,38,38,.22)",
        "icon": "!",
        "desc": "財源や効果を考えると慎重であるべきだ",
        "label": "反対・慎重",
    },
    "中立・情報": {
        "color": "#64748b",
        "bg": "#f8fafc",
        "shadow": "rgba(100,116,139,.22)",
        "icon": "?",
        "desc": "もう少し情報を見てから判断したい",
        "label": "中立",
    },
}
STANCE_ORDER = ["減税推進", "条件付き賛成・政府案に不満", "減税反対・慎重", "中立・情報"]
# 投票UIで見せるスタンス（中立を含めた4択）
VOTE_STANCE_ORDER = STANCE_ORDER

QUERIES = [
    "消費税減税 賛成 / 消費税減税 反対 / 消費税 廃止 すべき / 消費税減税 財源 どうする",
    "消費税減税 意味ない / 消費税減税 期待 / 消費税 減税 社会保障 削減 / 消費税減税 効果",
    "食料品 消費税 ゼロ / 消費税減税 高市 / 給付付き税額控除 消費税 / 消費税 減税 恒久",
    "消費税減税 レジ 改修 / 消費税 減税 物価高 生活 / 消費税 増税 財務省 / 消費税 一律 減税 5% / 消費税減税 法案 採決 / 消費税減税 インボイス 事業者 / 消費税減税 おかしい OR やるべき",
]


def replace_between(html: str, start: str, end: str, new: str, *, keep_markers: bool = False) -> str:
    """start と end に挟まれた領域を new で置き換える。"""
    i = html.index(start)
    j = html.index(end, i) + len(end)
    if keep_markers:
        return html[:i] + start + new + end + html[j:]
    return html[:i] + new + html[j:]



# 投票後の回遊カード。他テーマページに同じ形で入っている
# <script id="related-theme-tracking"> ブロックを、消費税減税向けに組み立てる。
RELATED_TOPIC_BY_PATH = {
    "ai-copyright-reaction-map.html": "ai-copyright",
    "bike-blue-ticket-reaction-map.html": "bike-blue-ticket",
    "bukatsu-chiiki-reaction-map.html": "bukatsu-chiiki",
    "constitutional-amendment-reaction-map.html": "constitutional-amendment",
    "elderly-license-revocation-reaction-map.html": "elderly-license-revocation",
    "school-nickname-ban-reaction-map.html": "school-nickname-ban",
    "henoko-student-accident-reaction-map.html": "henoko-student-accident",
    "takaichi-reaction-map-standard.html": "takaichi",
    "fukushuto-reaction-map.html": "fukushuto",
    "koshitsu-tenpakai-reaction-map.html": "koshitsu-tenpakai",
    "consumption-tax-cut-reaction-map.html": "consumption-tax-cut",
}
RELATED_THEMES = {
    "consumption-tax-cut": [
        ["fukushuto", "fukushuto-reaction-map.html", "images/fukushuto-hero.webp",
         "副首都法案", "「物価対策より優先か」の声も出た争点。"],
        ["takaichi", "takaichi-reaction-map-standard.html", "images/takaichi-hero.webp",
         "高市文春問題", "政権への評価と説明責任を見比べる。"],
        ["constitutional-amendment", "constitutional-amendment-reaction-map.html",
         "images/constitutional-hero.webp", "憲法改正論議", "制度変更への賛否と慎重論を整理する。"],
    ],
}
RELATED_FUNCS = """  function currentTopic(){return topicByPath[(location.pathname.split("/").pop()||"")]||"unknown";}
  function track(target,placement){
    if(typeof window.gtag==="function"){
      window.gtag("event","related_theme_click",{source_topic:currentTopic(),target_topic:target,placement:placement});
    }
  }
  function cardHtml(item,placement){
    return "<a class=\\"related-card\\" href=\\""+item[1]+"\\" data-related-target=\\""+item[0]+"\\" data-related-placement=\\""+placement+"\\"><img src=\\""+item[2]+"\\" alt=\\""+item[3]+"\\" loading=\\"lazy\\"><div><strong>"+item[3]+"</strong><p>"+item[4]+"</p></div></a>";
  }
  function renderVoteRelated(){
    if(document.getElementById("vote-related-themes"))return;
    var items=relatedThemes[currentTopic()]||[];
    if(!items.length)return;
    var block=document.createElement("div");
    block.id="vote-related-themes";
    block.style.cssText="margin:18px 0 16px;";
    block.innerHTML="<div style=\\"font-size:14px;font-weight:900;margin-bottom:10px;\\">次に投票するテーマ</div><div class=\\"related-grid\\">"+items.slice(0,3).map(function(item){return cardHtml(item,"vote_result");}).join("")+"</div>";
    var anchor=document.getElementById("detail-data")||document.getElementById("related-topics");
    if(anchor){anchor.parentNode.insertBefore(block,anchor.nextSibling);}
    else{(document.querySelector("main")||document.body).appendChild(block);}
  }
  function bindTracking(){
    document.querySelectorAll("#related-topics .related-card").forEach(function(card){
      if(!card.dataset.relatedPlacement)card.dataset.relatedPlacement="page_bottom";
      if(!card.dataset.relatedTarget){
        var href=(card.getAttribute("href")||"").split("/").pop();
        card.dataset.relatedTarget=topicByPath[href]||href.replace(/-reaction-map\\.html|\\.html/g,"");
      }
    });
    document.addEventListener("click",function(ev){
      var card=ev.target.closest&&ev.target.closest(".related-card[data-related-target]");
      if(!card)return;
      track(card.dataset.relatedTarget,card.dataset.relatedPlacement||"page_bottom");
    },true);
  }
  document.addEventListener("DOMContentLoaded",function(){bindTracking();});
  document.addEventListener("vote2d:revealed",function(){renderVoteRelated();});
})();
</script>"""


def related_block() -> str:
    """投票後の回遊カードのスクリプト（他テーマページと同じ実装）。"""
    paths = ",\n    ".join(f'"{k}":"{v}"' for k, v in RELATED_TOPIC_BY_PATH.items())
    themes = ",\n    ".join(
        f'"{k}":[\n      '
        + ",\n      ".join(json.dumps(item, ensure_ascii=False) for item in v)
        + "\n    ]"
        for k, v in RELATED_THEMES.items()
    )
    return (
        '<script id="related-theme-tracking">\n(function(){\n'
        f"  var topicByPath={{\n    {paths}\n  }};\n"
        f"  var relatedThemes={{\n    {themes}\n  }};\n"
        f"{RELATED_FUNCS}"
    )


def trust_block(total: int, relevant: int, opinions: int) -> str:
    """他テーマと同じ「このページの作り方」ブロック。

    scripts/seo/apply_theme_trust.py が configs/theme-seo.json から生成するものと
    同じ構造・同じ文面にしてある。テーマを登録したあとは同スクリプトが上書き管理する。
    """
    published = "2026年7月28日"
    return f"""<!-- ARTICLE_TRUST_START -->
<aside class="article-trust" aria-labelledby="article-trust-title">
  <div class="article-trust-heading">
    <p class="article-trust-kicker">編集・分析情報</p>
    <h2 id="article-trust-title">このページの作り方</h2>
  </div>
  <dl class="article-trust-meta">
    <div><dt>公開日</dt><dd><time datetime="{PUBLISHED_AT}">{published}</time></dd></div>
    <div><dt>最終更新日</dt><dd><time datetime="{PUBLISHED_AT}">{published}</time></dd></div>
    <div><dt>編集・分析</dt><dd><a href="about.html">SNS反応まっぷ編集部</a></dd></div>
  </dl>
  <div class="article-trust-method">
    <h3>SNS投稿の収集方法</h3>
    <p>Yahoo!リアルタイム検索で「消費税減税 賛成」「消費税減税 反対」「消費税 廃止 すべき」「消費税減税 財源 どうする」など賛否双方の検索語20件を使い、公開されているX投稿を収集しました。重複を除いた{total}件を分類し、意見と判定した{opinions}件を論点分析に使用しています。</p>
    <h3>AIを使用した工程</h3>
    <p>収集後の投稿について、AIを関連性・意見性の判定、論点・立場・表現強度の分類、要旨作成の補助に使用しています。ページ内にAI生成の図解・漫画がある場合は、その制作補助にも使用しています。AIによる分類には誤りや偏りが含まれる可能性があります。</p>
  </div>
  <p class="article-trust-caution"><strong>データの読み方:</strong> このページは世論調査ではなく、検索語と収集時点に基づくSNS投稿サンプルの分類結果です。社会全体の意見割合や事実認定を示すものではありません。</p>
  <p class="article-trust-contact">内容の訂正、引用の削除依頼、調査方法への問い合わせは、<a href="about.html#corrections">運営者情報・訂正窓口</a>をご確認ください。</p>
</aside>
<!-- ARTICLE_TRUST_END -->"""


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def build() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    html = TEMPLATE.read_text(encoding="utf-8")

    opinions = data["opinions"]
    relevant = data["relevant"]
    total = data["total_classified"]
    order = data["issue_order"]
    counts = data["issue_counts"]
    stance_counts = data["stance_counts"]
    stance_share = data["stance_share"]
    per_issue = data["per_issue_stance"]
    named = [k for k in order if k != "その他"]

    top_issue = named[0]
    top_stance = max(stance_counts, key=lambda k: stance_counts[k])

    # --- 1. head / SEO -------------------------------------------------
    # SEO_META / ARTICLE_JSON_LD / ARTICLE_TRUST は scripts/seo/apply_theme_trust.py が
    # configs/theme-seo.json から管理するブロック。公開登録前でもテンプレート元テーマの
    # 内容が残らないよう、ここで消費税減税向けに埋めておく。
    html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{HEADLINE}｜SNS反応まっぷ</title>", html, count=1, flags=re.S)
    seo = f"""
  <meta name="description" content="{DESCRIPTION}">
  <link rel="canonical" href="{PAGE_URL}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="SNS反応まっぷ">
  <meta property="og:title" content="{HEADLINE}">
  <meta property="og:description" content="{DESCRIPTION}">
  <meta property="og:url" content="{PAGE_URL}">
  <meta property="og:image" content="{OGP_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{HEADLINE}">
  <meta name="twitter:description" content="{DESCRIPTION}">
  <meta name="twitter:image" content="{OGP_IMAGE}">
"""
    html = replace_between(html, "<!-- SEO_META_START -->", "<!-- SEO_META_END -->", seo, keep_markers=True)

    jsonld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": HEADLINE,
            "description": DESCRIPTION,
            "image": [OGP_IMAGE],
            "mainEntityOfPage": {"@type": "WebPage", "@id": PAGE_URL},
            "datePublished": PUBLISHED_AT,
            "dateModified": PUBLISHED_AT,
            "author": ORGANIZATION,
            "publisher": ORGANIZATION,
        },
        ensure_ascii=False,
        indent=2,
    ).replace("</", "<\\/")
    html = replace_between(
        html,
        "<!-- ARTICLE_JSON_LD_START -->",
        "<!-- ARTICLE_JSON_LD_END -->",
        f'\n  <script type="application/ld+json">\n{jsonld}\n  </script>\n',
        keep_markers=True,
    )

    # --- 2. hero 画像（未生成のためグラデーションのみ） -----------------
    html = html.replace(
        "background:url('images/fukushuto-hero.webp') center/cover no-repeat;opacity:.18}",
        "background:url('images/consumption-tax-cut-hero.webp') center/cover no-repeat;opacity:.18}",
    )
    html = html.replace(
        "<body class=\"summary-on-light\" style=\"--topic-hero-image:url('images/fukushuto-hero.webp')\">",
        f'<body class="summary-on-light" style="--topic-hero-image:{HERO_IMAGE}">',
    )

    # 「条件付き賛成」用の配色を追加（アリーナの橙と揃える）
    html = html.replace(
        ".side.pos{background:#ecfdf5;border-left:4px solid #059669}.side.pos strong{color:#065f46}",
        ".side.pos{background:#ecfdf5;border-left:4px solid #059669}.side.pos strong{color:#065f46}\n"
        "    .side.mid{background:#fffbeb;border-left:4px solid #f59e0b}.side.mid strong{color:#92400e}",
    )

    # --- 3. hero -------------------------------------------------------
    hero = (
        '<section class="hero"><div class="hero-inner"><nav class="top-nav"><a href="index.html">トップ</a></nav>'
        # h1 は apply_theme_trust.py が HEADLINE で上書きするので、最初から揃えておく
        f'<span class="badge">税・財政</span><h1>{HEADLINE}</h1>'
        '<p class="question-line">食料品だけの減税で足りる？ 財源はどうする？</p>'
        f'<p class="lead">収集したSNS投稿{total}件のうち、分析対象となった意見{opinions}件をAIが6つの論点に整理しました。'
        '世論調査ではなく、SNS反応サンプルの論点比較です。</p>'
        '<div class="thirty-summary" aria-label="議論の中心"><header class="thirty-summary-title"><h2>議論の中心</h2></header>'
        f'<ul><li class="conclusion-focus"><span class="conclusion-count"><b>{counts[top_issue]}</b>件</span>'
        f'<strong>{ISSUE_META[top_issue]["headline"]}</strong>'
        f'<span class="conclusion-detail">{ISSUE_META[top_issue]["focus"]}</span></li></ul></div></div></section>'
    )
    html = re.sub(r'<section class="hero">.*?</section>', lambda _: hero, html, count=1, flags=re.S)

    # --- 4. insight-stats ---------------------------------------------
    top_share = stance_share[top_stance]
    second_issue = named[1]
    pro = stance_counts.get("減税推進", 0) + stance_counts.get("条件付き賛成・政府案に不満", 0)
    con = stance_counts.get("減税反対・慎重", 0)
    stats = f"""<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">
  <article class="stat insight-stat">
    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span><span class="insight-label">分析対象の意見</span></div>
    <strong class="insight-value">{opinions}<small>件</small></strong>
    <p class="insight-note">対象範囲、財源、効果、公約を6論点で比較</p>
    <div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div>
  </article>
  <article class="stat insight-stat" data-tone="debate">
    <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚖️</span><span class="insight-label">最も多い立場</span></div>
    <strong class="insight-value">{STANCE_META[top_stance]["label"]} {top_share:.0f}%</strong>
    <p class="insight-note">意見{opinions}件中{stance_counts[top_stance]}件</p>
    <div class="insight-meter" aria-hidden="true"><i style="width:{top_share:.0f}%"></i></div>
  </article>
  <article class="stat insight-stat" data-tone="topic">
    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span><span class="insight-label">最も話された論点</span></div>
    <strong class="insight-value">{ISSUE_META[top_issue]["short"]} {counts[top_issue]}<small>件</small></strong>
    <p class="insight-note">次点は{ISSUE_META[second_issue]["short"]}の{counts[second_issue]}件</p>
    <div class="insight-meter" aria-hidden="true"><i style="width:{counts[top_issue] / opinions * 100:.0f}%"></i></div>
  </article>
  <article class="stat insight-stat" data-tone="insight">
    <div class="insight-head"><span class="insight-icon" aria-hidden="true">📊</span><span class="insight-label">減税に前向き vs 慎重</span></div>
    <span class="insight-chip">{abs(pro - con)}件差</span>
    <div class="insight-versus"><span>前向き<b>{pro}</b></span><em>VS</em><span>反対・慎重<b>{con}</b></span></div>
    <div class="insight-split" aria-hidden="true"><i style="width:{pro / max(pro + con, 1) * 100:.0f}%"></i><i style="width:{con / max(pro + con, 1) * 100:.0f}%"></i></div>
  </article>
</section>"""
    html = re.sub(
        r'<section class="stats insight-stats".*?</section>\n',
        lambda _: stats + "\n",
        html,
        count=1,
        flags=re.S,
    )

    # --- 5. 潮目ウィジェットは比較対象がないため削除 ---------------------
    start = html.index('<section class="update-dashboard"')
    end = html.index("<!-- TIDE_CARD_END --></section>") + len("<!-- TIDE_CARD_END --></section>")
    html = html[:start] + html[end:]

    # --- 6. explainer（論点別インフォグラフィック＋拡大モーダル） --------
    circled = "①②③④⑤⑥⑦"
    cards = []
    for n, name in enumerate(named, 1):
        meta = ISSUE_META[name]
        img = f"images/consumption-tax-cut-infographic-wide-{meta['slug']}.webp"
        cards.append(
            f'  <article class="explainer-card" data-img="{img}" data-alt="{meta["short"]}">\n'
            f'    <div class="explainer-card-label">\n'
            f'      <span class="explainer-num">論点{circled[n - 1]}</span>\n'
            f"      <div>\n"
            f'        <p class="explainer-card-title">{meta["short"]} — {meta["headline"]}</p>\n'
            f'        <p class="explainer-card-desc">{meta["desc"]}</p>\n'
            f'        <div class="explainer-sides">\n'
            f'          <span class="explainer-side con">反対・慎重：{meta["args"]["減税反対・慎重"]}</span>\n'
            f'          <span class="explainer-side pro">推進：{meta["args"]["減税推進"]}</span>\n'
            f"        </div>\n"
            f"      </div>\n"
            f"    </div>\n"
            f'    <img src="{img}" alt="論点{circled[n - 1]} {meta["short"]}" loading="lazy">\n'
            f"  </article>"
        )
    explainer = (
        '<section class="panel" id="explainer-section">\n'
        '<div class="panel-title"><h2>このテーマを読み解く、6つの論点</h2><span>図解で全論点をチェック</span></div>\n'
        '<p class="explainer-lead">消費税減税の議論は「賛成か反対か」だけではありません。'
        "対象は食料品だけでいいのか、財源はどうするのか、そもそも生活に効くのか——"
        "6つの論点を図解で把握してから投票に進んでください。画像はタップで拡大できます。</p>\n"
        '<div class="explainer-grid">\n' + "\n".join(cards) + "\n</div>\n"
        '<p class="explainer-note"><strong>使い方:</strong> 6つの論点を図解で確認してから、'
        "次の投票で「自分が一番気になる論点」を選んでください。</p>\n"
        "</section>"
    )
    # モーダルと開閉スクリプトはテンプレート（副首都）のものをそのまま使う
    modal_start = html.index('<div class="explainer-modal" id="explainer-modal"')
    modal_end = html.index('<section class="panel" id="vote-section">')
    modal = html[modal_start:modal_end]

    start = html.index('<section class="panel" id="explainer-section">')
    html = html[:start] + explainer + "\n\n" + modal + html[modal_end:]

    # --- 7. 投票セクション ---------------------------------------------
    vote_intro = (
        '<section class="panel" id="vote-section"><div class="panel-title"><h2>あなたが一番気になる「減税の論点」は？</h2>'
        "<span>SNSの声を見る前に</span></div>"
        "<p>2026年7月、物価高対策として食料品に対象を絞った消費税減税の議論が大詰めを迎えました。"
        "「限定的で中途半端」という不満、「財源と社会保障はどうするのか」という懸念、"
        "「そもそも値下げに反映されるのか」という疑問が同時に噴き出しています。</p>"
        + trust_block(total, relevant, opinions)
    )
    start = html.index('<section class="panel" id="vote-section">')
    end = html.index('<div id="vote-step1">')
    html = html[:start] + vote_intro + "\n" + html[end:]
    html = html.replace(
        '<span class="step-num">2</span>副首都構想への賛否は？',
        '<span class="step-num">2</span>消費税減税への立場は？',
    )

    # --- 8. アリーナ見出し・凡例 ---------------------------------------
    html = html.replace(
        '<span>意見227件 | セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細・クリックでXへ</span>',
        f'<span>意見{opinions}件 | セクター=論点 / 中心に近いほど冷静 / 色=立場 | ホバーで詳細・クリックでXへ</span>',
    )
    html = html.replace(
        '中心の「副首都法案」を6つの論点セクターが囲みます。扇の大きさは投稿数、中心からの距離は感情の熱量（外側ほど激しい）、点の色はスタンス（緑=肯定的 / 赤=否定的 / 灰=中立）。点をクリックすると元のXポストを開きます。',
        '中心の「消費税減税」を7つの論点セクターが囲みます。扇の大きさは投稿数、中心からの距離は感情の熱量（外側ほど激しい）、点の色は立場（緑=減税推進 / 橙=条件付き賛成 / 赤=反対・慎重 / 灰=中立）。点をクリックすると元のXポストを開きます。',
    )
    legend = (
        '<span><i style="background:#059669"></i>減税推進</span>\n'
        '    <span><i style="background:#f59e0b"></i>条件付き賛成</span>\n'
        '    <span><i style="background:#dc2626"></i>反対・慎重</span>\n'
        '    <span><i style="background:#64748b"></i>中立</span>\n'
        '    <span style="color:#888">中心＝冷静 / 外周＝感情的</span>'
    )
    html = replace_between(
        html,
        '<span><i style="background:#059669"></i>肯定的</span>',
        '<span style="color:#888">中心＝冷静 / 外周＝感情的</span>',
        legend,
    )

    # --- 9. SM_RAW / ISSUES / colorOf ----------------------------------
    html = re.sub(r"const SM_RAW = \[.*?\n\];", lambda _: data["sm_raw_js"], html, count=1, flags=re.S)
    html = re.sub(r"const ISSUES = \[.*?\n  \];", lambda _: data["issues_js"], html, count=1, flags=re.S)
    html = html.replace(
        "function colorOf(p){return p.x>=0.5?'#059669':(p.x<=-0.5?'#dc2626':'#64748b');}",
        "const STANCE_COLORS=['#059669','#f59e0b','#dc2626','#64748b'];\n"
        "  function colorOf(p){return STANCE_COLORS[p.st]||'#64748b';}",
    )
    html = html.replace("ctx.fillText('副首都',CX,CY-9);\n    ctx.fillText('法案',CX,CY+11);", "ctx.fillText('消費税',CX,CY-9);\n    ctx.fillText('減税',CX,CY+11);")

    # 論点名が副首都テーマより長く、右端のラベルが640px幅からはみ出すため
    # ラベル半径と文字サイズを詰める。加えて、扇が細い論点（その他・事業者の負担）は
    # ラベルが重なるので半径を交互にずらす。
    html = html.replace("R_MAX=214, R_HOLE=56, R_LBL=242;", "R_MAX=214, R_HOLE=56, R_LBL=224;")
    html = html.replace(
        "ctx.font='900 13px \"Noto Sans JP\",sans-serif';\n    ISSUES.forEach((iss,i)=>{\n"
        "      const rad=iss.mid*Math.PI/180;\n"
        "      const lx=CX+R_LBL*Math.cos(rad), ly=CY+R_LBL*Math.sin(rad);",
        "ctx.font='900 12px \"Noto Sans JP\",sans-serif';\n    let narrowSeen=0;\n    ISSUES.forEach((iss,i)=>{\n"
        "      const rad=iss.mid*Math.PI/180;\n"
        "      const rl=R_LBL+((iss.a1-iss.a0)<14?(narrowSeen++%2?36:14):0);\n"
        "      const lx=CX+rl*Math.cos(rad), ly=CY+rl*Math.sin(rad);",
    )

    # --- 10. 投票UIのJSデータ ------------------------------------------
    vote_issues = ",\n    ".join(
        f'{{k:\'{ISSUE_META[name]["short"]}\', icon:\'{ISSUE_META[name]["icon"]}\', desc:\'{ISSUE_META[name]["headline"]}\'}}'
        for name in order
    )
    html = re.sub(
        r"var VOTE_ISSUES=\[.*?\n  \];",
        lambda _: f"var VOTE_ISSUES=[\n    {vote_issues}\n  ];",
        html,
        count=1,
        flags=re.S,
    )
    # 投票の並び＝アリーナの並びなので恒等写像
    html = re.sub(
        r"  // VOTE_ISSUES index → ISSUES array index.*?\n  var V2I=\[[0-9,]*\];",
        lambda _: "  // VOTE_ISSUES の並びは ISSUES と同一（論点の多い順）\n  var V2I=["
        + ",".join(str(i) for i in range(len(order)))
        + "];",
        html,
        count=1,
        flags=re.S,
    )
    stances_js = ",\n    ".join(
        f'{{k:\'{STANCE_META[s]["label"]}\', color:\'{STANCE_META[s]["color"]}\', bg:\'{STANCE_META[s]["bg"]}\','
        f' shadow:\'{STANCE_META[s]["shadow"]}\', icon:\'{STANCE_META[s]["icon"]}\', desc:\'{STANCE_META[s]["desc"]}\'}}'
        for s in VOTE_STANCE_ORDER
    )
    html = re.sub(
        r"var STANCES=\[.*?\n  \];",
        lambda _: f"var STANCES=[\n    {stances_js}\n  ];",
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace("var TOPIC='fukushuto-issue-stance-v1';", "var TOPIC='consumption-tax-cut-issue-stance-v1';")
    html = html.replace(
        "var shareText='副首都法案、私が最も気になる論点は「'+iss.k+'」。'+st.k+'の立場です。';",
        "var shareText='消費税減税、私が最も気になる論点は「'+iss.k+'」。'+st.k+'の立場です。';",
    )
    html = html.replace(
        "encodeURIComponent('https://issue-stance-lab.github.io/sns-reaction-map/fukushuto-reaction-map.html')",
        f"encodeURIComponent('{PAGE_URL}')",
    )

    # --- 11. 論点とXの声 ------------------------------------------------
    blocks = []
    nav = []
    for n, name in enumerate(named, 1):
        meta = ISSUE_META[name]
        breakdown = per_issue.get(name, {})
        nav.append(f'<a href="#issue-{meta["slug"]}">{meta["short"]} {counts[name]}</a>')
        # 中立を除く3スタンスのうち件数上位2つを、その立場の論拠とともに表示する
        ranked = sorted(
            (s for s in STANCE_ORDER if s != "中立・情報" and breakdown.get(s)),
            key=lambda s: breakdown[s],
            reverse=True,
        )[:2]
        # 反対側を左（neg）、前向き側を右（pos）に置く
        ranked.sort(key=lambda s: STANCE_ORDER.index(s), reverse=True)
        side_class = {"減税反対・慎重": "neg", "条件付き賛成・政府案に不満": "mid", "減税推進": "pos"}
        sides = [
            f'<div class="side {side_class[stance]}">'
            f'<strong>{meta["bar_stances"][stance]}（{breakdown[stance]}件）</strong>{meta["args"][stance]}</div>'
            for stance in ranked
        ]
        cards = []
        for stance in STANCE_ORDER:
            for sample in data["samples"][name][stance][:1]:
                cards.append(
                    f'<div class="sample-card"><div class="meta">{meta["bar_stances"][stance]} / conf {sample["confidence"]}</div>'
                    f'<p>{esc(sample["summary"])}</p>'
                    f'<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
                    f'<a href="{sample["url"]}"></a></blockquote></div>'
                )
            if len(cards) >= 4:
                break
        # 論点内の立場構成バー（他テーマの .temp-bar と同じ形。CSSは topic-modern.css）
        seg_class = {
            "減税推進": "process",
            "条件付き賛成・政府案に不満": "mid",
            "減税反対・慎重": "con",
            "中立・情報": "neutral",
        }
        present = [s for s in STANCE_ORDER if breakdown.get(s)]
        segs = []
        legend = []
        for stance in present:
            share = breakdown[stance] / counts[name] * 100
            # 幅が狭いセグメントに数字を入れると潰れて読めなくなる
            text = f"{share:.0f}%" if share >= 9 else ""
            segs.append(
                f'<div class="temp-seg {seg_class[stance]}" style="width:{share:.1f}%">{text}</div>'
            )
            legend.append(
                f'<span><i class="{seg_class[stance]}"></i>{meta["bar_stances"][stance]} {breakdown[stance]}件</span>'
            )
        # 論点固有の文言は長いので、右肩は最多の立場だけを出す
        top = max(present, key=lambda s: breakdown[s])
        counts_text = f'最多は「{meta["bar_stances"][top]}」{breakdown[top]}件'
        temp_bar = (
            '<div class="temp-bar-wrap">\n'
            f'<div class="temp-bar-label"><span>{meta["bar_label"]}</span><span>{counts_text}</span></div>\n'
            f'<div class="temp-bar">{"".join(segs)}</div>\n'
            f'<div class="temp-bar-legend">{"".join(legend)}</div>\n'
            "</div>"
        )
        blocks.append(
            f'<article class="issue-block" id="issue-{meta["slug"]}">\n'
            f'<div class="issue-head"><span class="axis-kicker">論点{n}</span>'
            f'<h3>{meta["short"]} — {meta["headline"]}<span class="issue-count">{counts[name]}件</span></h3>\n'
            f"{temp_bar}\n"
            f'<p class="issue-desc">{meta["desc"]}</p>\n'
            f'<div class="issue-sides">{"".join(sides)}</div>\n'
            f"</div>\n"
            f'<div class="sample-grid">\n' + "\n".join(cards) + "\n</div>\n</article>"
        )
    voices = (
        '<section class="panel conflict-panel"><div class="panel-title"><h2>6つの論点とXの声</h2>'
        "<span>論点ごとに立場の違う投稿を読む</span></div>\n"
        f'<nav class="quadrant-nav">{"".join(nav)}</nav>\n\n' + "\n\n".join(blocks) + "\n</section>"
    )
    start = html.index('<section class="panel conflict-panel"><div class="panel-title"><h2>6つの論点とXの声</h2>')
    end = html.index('<section class="panel background-panel">')
    html = html[:start] + voices + "\n\n" + html[end:]

    # --- 12. 背景 -------------------------------------------------------
    p = 'style="font-size:14px;line-height:1.9;color:var(--ink);margin:0 0 14px;"'
    background = (
        '<section class="panel background-panel"><div class="panel-title"><h2>この争点の背景</h2>'
        "<span>なにが起きていて、なぜ意見が割れるのか</span></div>\n"
        f"<p {p}>消費税は税率10%（食料品などは軽減税率8%）で、社会保障の主要財源とされてきました。"
        "物価高が続くなかで各党が減税を掲げ、2026年7月には食料品に対象を絞った減税をめぐる調整が大詰めを迎えています。"
        "対象範囲・税率・実施時期・恒久化の有無が、いずれも決着の焦点になっています。</p>\n"
        f"<p {p}>推進する立場からは「物価高対策として最も早く広く効く」「可処分所得が直接増える」という主張があります。"
        "慎重な立場からは「社会保障の財源が細る」「値下げに反映されず事業者の利益になる」"
        "「供給が追いつかないなかで需要を刺激すればインフレが加速する」という反論が出ています。</p>\n"
        f"<p {p}>SNS上では減税に前向きな声が多数ですが、その中身は一枚岩ではありません。"
        "「一律・恒久でなければ意味がない」という不満、「財源を示さない減税は無責任」という批判、"
        "「公約を掲げた政党が採決でどう動いたか」という政治不信が、論点ごとに別々の対立軸をつくっています。</p>\n"
        "</section>"
    )
    start = html.index('<section class="panel background-panel">')
    end = html.index('<section class="panel conflict-panel"><div class="panel-title"><h2>スタンス集計</h2>')
    html = html[:start] + background + "\n\n" + html[end:]

    # --- 13. スタンス集計 ------------------------------------------------
    hottest = max(named, key=lambda k: counts[k])
    summary = (
        '<section class="panel conflict-panel"><div class="panel-title"><h2>スタンス集計</h2>'
        "<span>Hermes分類のサマリー</span></div><div class=\"axis-grid\">\n"
        f'<article class="axis-card"><div class="axis-kicker">減税への態度</div><h3>{STANCE_META[top_stance]["label"]}が最多</h3>'
        f'<div class="axis-count">{stance_counts[top_stance]}</div>'
        f'<p>意見{opinions}件の内訳は、減税推進{stance_counts.get("減税推進", 0)}件・'
        f'条件付き賛成{stance_counts.get("条件付き賛成・政府案に不満", 0)}件・'
        f'反対・慎重{stance_counts.get("減税反対・慎重", 0)}件・中立{stance_counts.get("中立・情報", 0)}件。</p></article>\n'
        f'<article class="axis-card"><div class="axis-kicker">前向き vs 慎重</div><h3>前向きが{pro / max(pro + con, 1) * 100:.0f}%</h3>'
        f'<div class="axis-count">{pro}</div>'
        f"<p>減税推進と条件付き賛成を合わせると{pro}件。反対・慎重は{con}件で、"
        "前向きな声が多数を占めます。ただし前向きの中身は一律派と限定容認派に割れています。</p></article>\n"
        f'<article class="axis-card"><div class="axis-kicker">論点の集中</div><h3>{ISSUE_META[hottest]["short"]}が中心</h3>'
        f'<div class="axis-count">{counts[hottest]}</div>'
        f'<p>{ISSUE_META[hottest]["short"]}が{counts[hottest]}件で最多。'
        f'次いで{ISSUE_META[named[1]]["short"]}{counts[named[1]]}件、{ISSUE_META[named[2]]["short"]}{counts[named[2]]}件と続きます。</p></article>\n'
        "</div></section>"
    )
    start = html.index('<section class="panel conflict-panel"><div class="panel-title"><h2>スタンス集計</h2>')
    end = html.index('<section class="panel" id="related-topics">')
    html = html[:start] + summary + "\n\n" + html[end:]

    # --- 14. 次に読むテーマ ----------------------------------------------
    related = (
        '<section class="panel" id="related-topics"><div class="panel-title"><h2>次に読むテーマ</h2>'
        '<span>他のテーマ</span></div><div class="related-grid">\n'
        '<a class="related-card" href="fukushuto-reaction-map.html"><img src="images/fukushuto-hero.webp" alt="副首都法案" loading="lazy"><div><strong>副首都法案</strong><p>「物価対策どこ行った」の声も。</p></div></a>\n'
        '<a class="related-card" href="takaichi-reaction-map-standard.html"><img src="images/takaichi-hero.webp" alt="高市文春問題" loading="lazy"><div><strong>高市文春問題</strong><p>中傷動画疑惑、説明責任はあるのか。</p></div></a>\n'
        '<a class="related-card" href="constitutional-amendment-reaction-map.html"><img src="images/constitutional-hero.webp" alt="憲法改正論議" loading="lazy"><div><strong>憲法改正論議</strong><p>統治の仕組みを変えるか、守るか。</p></div></a>\n'
        "</div></section>"
    )
    start = html.index('<section class="panel" id="related-topics">')
    end = html.index('<section class="panel details-panel" id="detail-data">')
    html = html[:start] + related + "\n\n" + html[end:]

    # --- 15. 詳細データ --------------------------------------------------
    issue_rows = "".join(f"<tr><th>{name}</th><td>{counts[name]}</td></tr>" for name in order)
    stance_rows = "".join(
        f"<tr><th>{s}</th><td>{stance_counts.get(s, 0)}</td></tr>" for s in STANCE_ORDER
    )
    intensity_rows = "".join(
        f"<tr><th>{k}</th><td>{data['intensity_counts'].get(k, 0)}</td></tr>"
        for k in ("high", "medium", "low")
    )
    marker_rows = "".join(
        f"<tr><td>{ISSUE_META[name]['short']}</td><td>{ISSUE_META[name]['short']}</td>"
        + ('<td rowspan="%d">選んだ立場の色</td>' % len(order) if i == 0 else "")
        + "</tr>"
        for i, name in enumerate(order)
    )
    query_items = "".join(f"<li>{q}</li>" for q in QUERIES)
    details = (
        '<section class="panel details-panel" id="detail-data"><div class="panel-title"><h2>詳細データ</h2>'
        "<span>折りたたみ</span></div>\n"
        f'<details open><summary>論点別件数（main_issue・意見{opinions}件）</summary>'
        f'<div class="table-wrap"><table><tbody>{issue_rows}</tbody></table></div></details>\n'
        f"<details><summary>立場別件数（stance・意見{opinions}件）</summary>"
        f'<div class="table-wrap"><table><tbody>{stance_rows}</tbody></table></div></details>\n'
        f"<details><summary>感情の強さ（intensity）</summary>"
        f'<div class="table-wrap"><table><tbody>{intensity_rows}</tbody></table></div></details>\n'
        "<details><summary>投票の選択とアリーナ上の位置</summary>"
        f'<div class="table-wrap"><table><thead><tr><th>選んだ論点</th><th>マーカーが置かれるセクター</th><th>マーカーの色</th></tr></thead>'
        f"<tbody>{marker_rows}</tbody></table></div></details>\n"
        f"<details><summary>収集クエリ</summary><ul>{query_items}"
        f"<li>2026-07-28にYahooリアルタイム検索で{total}件を取得（重複除外後）。"
        f"うちHermes（kimi-k2.6）が関連{relevant}件・意見{opinions}件と判定。</li></ul></details>\n"
        "<details><summary>注意</summary><ul>"
        "<li>これは世論調査ではなく、Yahooリアルタイム検索で取得した投稿サンプルの反応整理です。</li>"
        "<li>収集時点が食料品限定の減税案の決着直前のため、政府案への評価に反応が偏りやすいバイアスがあります。</li>"
        "<li>検索語に「賛成」「反対」など意見誘発語を含むため、意見投稿の比率が実際のSNS全体より高く出ます。</li>"
        "</ul></details>\n</section>"
    )
    start = html.index('<section class="panel details-panel" id="detail-data">')
    end = html.index("</main>")
    html = html[:start] + details + "\n" + html[end:]

    # --- 16. 投票後の回遊カード -------------------------------------------
    # 他テーマページと同じく </footer> の直後に置く
    anchor = "</footer>"
    idx = html.index(anchor) + len(anchor)
    html = html[:idx] + "\n" + related_block() + html[idx:]

    verify(html, opinions)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(html.splitlines())} lines)")
    print(f"意見{opinions}件 / 論点順: {order}")


def verify(html: str, opinions: int) -> None:
    """テンプレート（副首都ページ）が更新されて置換が空振りしていないか検査する。

    副首都ページはSEOスクリプトなどで随時書き換わるため、置換対象の文字列が
    変わると気付かないまま元テーマの内容が残る。ビルド時に落とす。
    """
    head = html[: html.index("</head>")]
    problems: list[str] = []

    for label, text in (("title", re.search(r"<title>(.*?)</title>", html, re.S).group(1)),
                        ("h1", re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1))):
        if text != (f"{HEADLINE}｜SNS反応まっぷ" if label == "title" else HEADLINE):
            problems.append(f"{label} が差し替わっていない: {text!r}")

    if "副首都" in head or "fukushuto" in head:
        problems.append("head にテンプレート元テーマ（副首都）の記述が残っている")
    if PAGE_URL not in head:
        problems.append("canonical/OGP が消費税減税のURLになっていない")

    # 本文側: 「次に読むテーマ」カード以外に副首都ページへの参照が残っていないか
    body_wo_related = re.sub(
        r'<section class="panel" id="related-topics">.*?</section>', "", html, flags=re.S
    )
    strays = re.findall(r'(?:src|href)="([^"]*fukushuto[^"]*)"', body_wo_related)
    if strays:
        problems.append(f"副首都テーマの画像・リンクが残っている: {strays}")
    if ".hero:before" in html and "fukushuto" in re.search(r"\.hero:before\{[^}]*\}", html).group(0):
        problems.append(".hero:before が副首都のヒーロー画像を参照している")

    if html.count("{x:") - 2 != opinions:
        problems.append("SM_RAW の件数が意見件数と一致しない")
    for token in ("G-K10S4YCZFH", "ca-pub-2542211932832864", "supabase", "topic-modern.js"):
        if token not in html:
            problems.append(f"保護タグが失われている: {token}")
    if "--topic-hero-image:" not in html:
        problems.append("--topic-hero-image が未指定（他テーマの画像にフォールバックする）")

    # 参照している画像が実在するか（論点図解・ヒーロー）
    for src in sorted(set(re.findall(r'(?:src|data-img)="(images/[^"]+)"', html))):
        if not (OUTPUT.parent / src).exists():
            problems.append(f"参照画像が存在しない: {src}")
    cards = len(re.findall(r'<article class="explainer-card"', html))
    if cards != 6:
        problems.append(f"論点解説カードが6枚でない: {cards}枚")
    if '<div class="explainer-modal"' not in html:
        problems.append("図解の拡大モーダルが失われている")
    if '<aside class="article-trust"' not in html:
        problems.append("「このページの作り方」ブロックがない（他テーマと不揃いになる）")
    if 'id="related-theme-tracking"' not in html:
        problems.append("投票後の回遊カードのスクリプトがない")
    bars = len(re.findall(r'<div class="temp-bar-wrap">', html))
    if bars != 6:
        problems.append(f"論点別の立場構成バーが6本でない: {bars}本")
    for m in re.finditer(r'<div class="temp-bar-wrap">(.*?)<div class="temp-bar-legend"', html, re.S):
        widths = [float(w) for w in re.findall(r'temp-seg [a-z]+" style="width:([\d.]+)%', m.group(1))]
        if not widths:
            problems.append("立場構成バーにセグメントがない")
        elif abs(sum(widths) - 100) > 0.5:
            problems.append(f"立場構成バーの合計が100%でない: {sum(widths):.1f}%")

    if problems:
        raise SystemExit("ビルド検証に失敗しました:\n  - " + "\n  - ".join(problems))


if __name__ == "__main__":
    build()
