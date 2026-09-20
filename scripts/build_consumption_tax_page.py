#!/usr/bin/env python3
"""消費税減税テーマページを分類済みデータから生成する。

既定では自分自身の公開ページ（docs/consumption-tax-cut-reaction-map.html）を
テンプレートに読み、データ由来のセクションだけを作り直す。

  python3 scripts/build_consumption_tax_page.py \\
      --input <stage>/cumulative-candidate.json \\
      --html-template docs/consumption-tax-cut-reaction-map.html \\
      --output-html <stage>/page-candidate.html

初版は副首都ページ（docs/fukushuto-reaction-map.html）をテンプレートに生成した。
副首都由来の文字列を置き換える処理はそのまま残してあり、既に置き換わっている
（＝自分自身をテンプレートにした）場合は何もしない。副首都ページはSEOスクリプトで
随時書き換わるため、テンプレートとして読み続けると他テーマの変更が漏れ込む。

--input を渡すと scripts/build_consumption_tax_arena.py を内部で実行して
アリーナ用データを作り直す。渡さない場合は既存の
social-samples/consumption-tax-cut_arena_data.json を読む。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from x_embed import embed_html  # noqa: E402
PAGE = ROOT / "docs" / "consumption-tax-cut-reaction-map.html"
# 既定のテンプレートは自分自身。副首都ページから作った初版だけ --html-template で指定した。
TEMPLATE = PAGE
OUTPUT = PAGE
DATA = ROOT / "social-samples" / "consumption-tax-cut_arena_data.json"
CANONICAL = ROOT / "social-samples" / "consumption-tax-cut_hermes_arena_classified.json"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / "consumption-tax-cut.json"
TOPIC_CONFIG = ROOT / "configs" / "topics" / "consumption-tax-cut.yaml"

PAGE_URL = "https://sns-reaction-map.jp/consumption-tax-cut-reaction-map.html"

# ヒーロー画像。topic-modern.css の .hero::before は --topic-hero-image 未指定だと
# ai-copyright-hero.webp にフォールバックするため、必ず値を入れる。
HERO_IMAGE = "url('images/topics/consumption-tax-cut/consumption-tax-cut-hero.webp')"

# SEO_META / ARTICLE_JSON_LD の中身。テーマを configs/theme-seo.json に登録したあとは
# scripts/seo/apply_theme_trust.py が同じブロックを上書き管理するので、値を揃えておく。
HEADLINE = "消費税減税は何が論点？食料品限定と一律の賛否"
DESCRIPTION = (
    "消費税減税について、対象範囲、財源と社会保障、価格への効果、給付付き税額控除との比較、"
    "事業者の実務負担、公約と政治不信の6論点とSNS上の賛否を整理します。"
)
OGP_IMAGE = "https://sns-reaction-map.jp/images/topics/consumption-tax-cut/consumption-tax-cut-hero.webp"
PUBLISHED_AT = "2026-07-28"
ORGANIZATION = {
    "@type": "Organization",
    "name": "SNS反応まっぷ編集部",
    "url": "https://sns-reaction-map.jp/about.html",
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

def query_lines() -> list[str]:
    """収集クエリは configs/topics/consumption-tax-cut.yaml が正典。

    ページに直書きすると検索語を足したときに古い一覧が残る（実際に他テーマで起きた）。
    4語ずつ 1 行にまとめて、初版と同じ見た目にする。
    """
    import yaml  # 収集設定を読むためだけに使うので、ここで読み込む

    queries = yaml.safe_load(TOPIC_CONFIG.read_text(encoding="utf-8"))["fetch_queries"]
    return [" / ".join(queries[i : i + 4]) for i in range(0, len(queries), 4)]


def collection_period(rows: list[dict]) -> str:
    """収集日の範囲。scripts/refresh_topic.py の sample_period と同じ導き方。"""
    values = sorted({str(row.get("fetched_at") or "")[:10] for row in rows})
    if not values or any(not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) for value in values):
        raise SystemExit("fetched_at から収集日を読み取れません")
    if values[0] == values[-1]:
        return f"{values[0]}に"
    return f"{values[0]}〜{values[-1]}に"


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
    "fukushuto-reaction-map.html": "fukushuto",
    "koshitsu-tenpakai-reaction-map.html": "koshitsu-tenpakai",
    "consumption-tax-cut-reaction-map.html": "consumption-tax-cut",
}
RELATED_THEMES = {
    "consumption-tax-cut": [
        ["fukushuto", "fukushuto-reaction-map.html", "images/topics/fukushuto/fukushuto-hero.webp",
         "副首都法案", "「物価対策より優先か」の声も出た争点。"],
        ["constitutional-amendment", "constitutional-amendment-reaction-map.html",
         "images/topics/constitutional-amendment/constitutional-hero.webp", "憲法改正論議", "制度変更への賛否と慎重論を整理する。"],
        ["koshitsu-tenpakai", "koshitsu-tenpakai-reaction-map.html",
         "images/topics/koshitsu-tenpakai/koshitsu-hero.webp", "皇室典範改正", "政策転換への賛否と慎重論を見る。"],
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


def research_conditions(html: str) -> str:
    """調査条件（取得元・期間・件数）を THEMES.yaml と累積正典から貼り直す。

    件数は正典の行数、取得期間は台帳の sample_period。どちらも昇格の途中で
    書き換わるため、候補ページを組み立てる時点では新しい値を入れられない。
    adapter の finalize（＝昇格後）から呼ぶ。
    """
    import yaml

    theme = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"][
        "consumption-tax-cut"
    ]
    sys.path.insert(0, str(ROOT / "scripts"))
    from x_embed import period_label  # noqa: E402

    count = len(json.loads(CANONICAL.read_text(encoding="utf-8")))
    period = period_label(str(theme.get("sample_period") or ""))
    source = str(theme.get("sample_source") or "Yahooリアルタイム検索")
    block = (
        "<!-- RESEARCH_CONDITIONS_START -->\n"
        '<aside class="research-conditions" aria-label="SNSデータの調査条件" '
        'style="padding:16px min(6vw,72px);background:#fff;border-bottom:1px solid var(--line);'
        'font-size:13px;line-height:1.8;color:var(--muted);">\n'
        '  <p style="max-width:1000px;margin:0 auto;"><strong style="color:var(--ink);">'
        f"このマップの元データ:</strong> {source}で取得した公開投稿 {count}件<br>\n"
        # 確認表示は <span class="review-note"> で囲む。scripts/seo/apply_review_note.py が
        # data/review-ledger.json に合わせて中身を書き分け、
        # verify_number_provenance.py がこの囲みだけを検査から外す。
        f'  （取得期間: {period}／<span class="review-note">AI分類。代表投稿は編集部が選定</span>）<br>\n'
        "  <strong>社会全体の世論調査ではありません。</strong></p>\n"
        "</aside>\n<!-- RESEARCH_CONDITIONS_END -->"
    )
    return re.sub(
        r"<!-- RESEARCH_CONDITIONS_START -->.*?<!-- RESEARCH_CONDITIONS_END -->",
        lambda _: block,
        html,
        count=1,
        flags=re.S,
    )


def pinned_issue_order(html: str, order: list[str]) -> list[str]:
    """公開済みページに入っている論点の並びを引き継ぐ。

    データ側の並びは件数の多い順で、データが増えると入れ替わる。ところが投票は
    「論点の番号×立場の番号」で保存されているため（saveVote の choiceIdx）、
    並びが変わると過去の投票の意味まで変わってしまう。公開後は並びを固定する。

    ページにまだ無い論点は、件数順のまま「その他」の直前へ足す。
    """
    published = re.search(r"var VOTE_ISSUES=\[(.*?)\];", html, re.DOTALL)
    if not published:
        return order
    short_to_name = {ISSUE_META[name]["short"]: name for name in order if name in ISSUE_META}
    pinned = [
        short_to_name[key]
        for key in re.findall(r"\bk:'([^']+)'", published.group(1))
        if key in short_to_name
    ]
    rest = [name for name in order if name not in pinned and name != "その他"]
    tail = ["その他"] if "その他" in order else []
    return [name for name in pinned if name != "その他"] + rest + tail


def existing_dates(html: str) -> tuple[str, str]:
    """テンプレートに入っている公開日・最終更新日を引き継ぐ。

    どちらも本来は scripts/seo/apply_theme_trust.py が configs/theme-seo.json から
    管理する値で、このスクリプトが初版の日付で塗り直すと更新日が巻き戻る。
    """
    published = re.search(r'"datePublished": "(\d{4}-\d{2}-\d{2})"', html)
    modified = re.search(r'"dateModified": "(\d{4}-\d{2}-\d{2})"', html)
    return (
        published.group(1) if published else PUBLISHED_AT,
        modified.group(1) if modified else PUBLISHED_AT,
    )


def japanese_date(value: str) -> str:
    year, month, day = value.split("-")
    return f"{int(year)}年{int(month)}月{int(day)}日"


ARTICLE_TRUST_START = "<!-- ARTICLE_TRUST_START -->"
ARTICLE_TRUST_END = "<!-- ARTICLE_TRUST_END -->"


def trust_block(total: int, relevant: int, opinions: int, published_at: str, modified_at: str) -> str:
    """他テーマと同じ「このページの作り方」ブロック。

    scripts/seo/apply_theme_trust.py が configs/theme-seo.json から生成するものと
    同じ構造・同じ文面にしてある。テーマを登録したあとは同スクリプトが上書き管理する。

    **「収集・分類で分かったこと」（article-trust-observations）はここに含めていない。**
    あれは configs/theme-seo.json の observations が出所で、apply_theme_trust.py が書く。
    このスクリプトを単体で流すと分析メモが消えるので、流したあとは必ず

        python3 scripts/seo/apply_theme_trust.py

    を実行して戻すこと。再生成可能性の検査（scripts/verify_builder_rebuildability.py）は
    consumption-tax-cut に build_consumption_tax_arena.py を使うため、ここは検査に出ない。
    """
    return f"""{ARTICLE_TRUST_START}
<aside class="article-trust" aria-labelledby="article-trust-title">
  <div class="article-trust-heading">
    <p class="article-trust-kicker">編集・分析情報</p>
    <h2 id="article-trust-title">このページの作り方</h2>
  </div>
  <dl class="article-trust-meta">
    <div><dt>公開日</dt><dd><time datetime="{published_at}">{japanese_date(published_at)}</time></dd></div>
    <div><dt>最終更新日</dt><dd><time datetime="{modified_at}">{japanese_date(modified_at)}</time></dd></div>
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
{ARTICLE_TRUST_END}"""


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def arena_data(classified: Path | None) -> tuple[dict, list[dict]]:
    """アリーナ用データと、元になった分類済み行を返す。

    --input が来たときは既存の social-samples/*_arena_data.json を書き換えず、
    一時ファイルへ作り直す（候補ページの生成が正典の隣を汚さないようにする）。
    """
    source = classified if classified is not None else CANONICAL
    with tempfile.TemporaryDirectory(prefix="consumption-tax-arena-") as directory:
        output = Path(directory) / "arena_data.json"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "build_consumption_tax_arena.py"),
                "--input", str(source),
                "--output", str(output),
            ],
            cwd=ROOT,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8")), json.loads(source.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 投稿の言い分と一次資料の突き合わせ（AdSense診断でExperienceだけがNGだったため、
# 誰が・いつ・何を確かめたかをページに残す。FACT_CHECK_GUIDE.md が正典）
# ---------------------------------------------------------------------------
CLAIM_POSTS = ROOT / "data" / "consumption-tax-cut_claim_posts.json"
CLAIM_START = "<!-- CLAIM_AUDIT_START -->"
CLAIM_END = "<!-- CLAIM_AUDIT_END -->"
# 差し込む位置（マーカーがまだ無い、テンプレート初回のときだけ使う）。
# 起承転結の再構成（課題69、fukushutoのFACT_CHECKと同型）で、山なみ図を
# 読んだ直後に置くよう変更した（以前は最後尾に近い「スタンス集計」の手前だった）。
CLAIM_ANCHOR = "<!-- PLANET_SECTION_END -->"
CHECKED_ON = "2026年8月19日"

# 判定の呼び名。他テーマと同じ言い方にしないこと（verify_page_originality.py が見る）。
VERDICT_LABEL = {
    "fact": "原典どおり",
    "gap": "原典とズレ",
    "miss": "原典に届かず",
}

# 件数は data/consumption-tax-cut_claim_posts.json の tweet_id から毎回数え直す。
# 直書きしないこと。キーワード一致の件数をそのまま出すと実際より多く出る。
CLAIM_AUDIT = [
    {
        "key": "rate10",
        "issues": ["減税の対象範囲"],
        "say": "2年たてば、食料品の消費税は10％に戻る",
        "source": (
            "首相官邸の会見録（令和8年7月30日）は、令和11年4月の「本格導入」に合わせて"
            "「『飲食料品の消費税率』は元の税率（８％）に戻」すとしている。"
            "飲食料品に今かかっているのは標準税率10％ではなく軽減税率8％"
            "（国分6.24％・地方分1.76％）で、戻り先も8％になる。"
        ),
        "note": (
            "戻る先は10％ではなく8％。1％との差は7ポイントで、"
            "投稿が前提にしている9ポイントではない。"
        ),
        "verdict": "gap",
        "links": [
            ("https://www.kantei.go.jp/jp/105/statement/2026/0730kaiken.html",
             "首相官邸「『飲食料品に係る消費税率の引下げ』及び『給付付き税額控除』についての会見」"),
            ("https://www.mof.go.jp/tax_policy/summary/consumption/122.pdf",
             "財務省「消費税の使途（令和8年度予算）」（PDF）"),
        ],
    },
    {
        "key": "register",
        "issues": ["事業者の実務負担"],
        "say": "ゼロではなく1％にしたのは、レジなどのシステム改修が理由だ",
        "source": (
            "同じ会見で、税率を1％とした理由について"
            "「１％であれば０％とするよりも事業者のシステム改修の期間を短縮でき、"
            "令和９年４月から実施可能である」と説明されている。"
        ),
        "note": (
            "理由の説明は会見の発言と重なる。ただし投稿によく出てくる"
            "「改修に1年かかる」という年数までは、この会見録からは確認できなかった。"
        ),
        "verdict": "fact",
        "links": [
            ("https://www.kantei.go.jp/jp/105/statement/2026/0730kaiken.html",
             "首相官邸「『飲食料品に係る消費税率の引下げ』及び『給付付き税額控除』についての会見」"),
        ],
    },
    {
        "key": "cost5cho",
        "issues": ["財源と社会保障"],
        "say": "食料品の消費税を下げると、年5兆円かかる",
        "source": (
            "片山さつき財務大臣は衆議院予算委員会（令和8年6月22日）で"
            "「軽減税率の対象、飲食料品の消費税率を一％にした場合」について"
            "「減収額が約四・三兆円になりますから、それを総人口約一・二億人で割りますと、"
            "一人、一年当たりの減税額は……約三万六千円」と答弁している。"
        ),
        "note": (
            "国会で政府が示した額は約4.3兆円。5兆円はそれより約7千億円大きい。"
            "桁は合っているが、答弁の数字ではない。"
        ),
        "verdict": "gap",
        "links": [
            ("https://kokkai.ndl.go.jp/txt/122105261X01520260622/110",
             "国会会議録検索システム 第219回国会 衆議院予算委員会（令和8年6月22日）片山財務大臣答弁"),
        ],
    },
    {
        "key": "welfare",
        "issues": ["財源と社会保障"],
        "say": "消費税は全額が社会保障に使われている／一般会計に入るのだから使われていない",
        "source": (
            "消費税法第1条第2項は、消費税の収入を「毎年度、制度として確立された年金、医療及び介護の"
            "社会保障給付並びに少子化に対処するための施策に要する経費に充てるものとする」と定める。"
            "財務省は「消費税収（国・地方）は、全て社会保障財源に充てることとされています。"
            "しかしながら、社会保障４経費の合計額には足りていません」と書いており、"
            "令和8年度予算では消費税収34.0兆円に対し社会保障4経費は48.9兆円。"
        ),
        "note": (
            "「全額を社会保障へ」は、法律と予算の建て付けとしては資料どおり。"
            "ただし4経費を消費税収でまかなえてはいない。"
            "逆に「一般会計に入るのだから社会保障には使われていない」という言い方も、"
            "条文と予算総則を見るかぎり成り立たない。どちらの言い分も、そのままでは資料と合わない。"
        ),
        "verdict": "gap",
        "links": [
            ("https://www.mof.go.jp/tax_policy/summary/consumption/d05.htm",
             "財務省「消費税の使途に関する資料」"),
            ("https://www.mof.go.jp/tax_policy/summary/consumption/d05_1.pdf",
             "財務省「消費税率の引上げと使途の明確化」（PDF、消費税法第1条第2項の条文）"),
        ],
    },
    {
        "key": "refund",
        "issues": ["財源と社会保障"],
        "say": "輸出企業には年11.7兆円（別の投稿では7兆円）の消費税が還付されている",
        "source": (
            "国税庁は「個人及び法人が提出した令和４（2022）年の消費税還付申告税額の合計額は"
            "７兆円を超えています」と公表している。ただしこれは還付申告全体の額で、"
            "輸出取引に係る分を区分した数字ではない。国税庁の公表資料にも政府統計の総合窓口にも、"
            "輸出企業向けの還付額だけを切り出した統計は見当たらなかった。"
        ),
        "note": (
            "輸出免税で仕入れにかかった税額が控除しきれず還付が生じる仕組み自体は、"
            "国税庁が説明している。確かめられなかったのは金額のほう。"
            "7兆円は還付申告全体の額に近いが、輸出分と限った公表値ではなく、"
            "11.7兆円に至っては対応する公表値を見つけられなかった。"
            "投稿が誤りだと判定したのではなく、公表資料では確認できなかった、という結果である。"
        ),
        "verdict": "miss",
        "links": [
            ("https://www.nta.go.jp/about/introduction/torikumi/report/2024/04_3.htm",
             "国税庁「令和6年度版 国税庁レポート 適正・公平な課税・徴収」"),
            ("https://www.nta.go.jp/taxes/shiraberu/taxanswer/shohi/6551.htm",
             "国税庁 タックスアンサー No.6551 輸出取引の免税"),
        ],
    },
    {
        "key": "firstcut",
        "issues": ["公約と政治不信"],
        "say": "消費税は導入されてから、一度も下げられたことがない",
        "source": (
            "財務省の説明では、税率3％の消費税が平成元年4月に導入され、平成9年に5％、"
            "平成26年に8％、令和元年10月に8％から10％へ引き上げられた。"
            "引下げにあたる記載はない。"
        ),
        "note": (
            "税率が下がった例は資料に見当たらない。"
            "ただし年数の言い方は投稿ごとに割れていて、平成元年4月からだと37年になる。"
            "「30年」「40年」はどちらも実際の期間とずれる。"
        ),
        "verdict": "fact",
        "links": [
            ("https://www.mof.go.jp/tax_information/qanda015.html",
             "財務省「日本の税の歴史を教えてください。」"),
        ],
    },
]

CLAIM_CSS = """<style>
.claim-audit .ca-lead{margin:0 0 18px;line-height:1.9}
.claim-audit .ca-list{display:grid;gap:14px}
.claim-audit .ca-item{border:1px solid var(--line,#dcdfe6);border-radius:12px;padding:16px 18px;background:var(--card,#fff)}
.claim-audit .ca-item[data-verdict="gap"]{border-left:5px solid #d1603d}
.claim-audit .ca-item[data-verdict="fact"]{border-left:5px solid #3f7d58}
.claim-audit .ca-item[data-verdict="miss"]{border-left:5px solid #8a8fa3;border-style:dashed;border-left-style:solid}
.claim-audit .ca-say{margin:0 0 10px;font-weight:700;font-size:1.02rem;line-height:1.7}
.claim-audit .ca-n{display:inline-block;margin-left:8px;padding:2px 9px;border-radius:999px;background:rgba(120,130,150,.14);font-size:.78rem;font-weight:600;white-space:nowrap;vertical-align:middle}
.claim-audit .ca-detail{margin:0;display:grid;grid-template-columns:8.4em 1fr;gap:6px 14px}
.claim-audit .ca-detail dt{font-size:.8rem;font-weight:700;opacity:.72;white-space:normal}
.claim-audit .ca-detail dd{margin:0;line-height:1.85;white-space:normal}
.claim-audit .ca-mark{display:inline-block;margin-right:.5em;padding:1px 8px;border-radius:5px;background:rgba(120,130,150,.16);font-size:.82rem}
.claim-audit .ca-item[data-verdict="gap"] .ca-mark{background:rgba(209,96,61,.16);color:#a34526}
.claim-audit .ca-item[data-verdict="fact"] .ca-mark{background:rgba(63,125,88,.16);color:#2f6144}
.claim-audit .ca-item[data-verdict="miss"] .ca-mark{background:rgba(138,143,163,.2)}
.claim-audit .ca-src{margin:10px 0 0;font-size:.82rem;line-height:1.8}
.claim-audit .ca-src a{word-break:break-word}
.claim-audit .ca-how{margin:18px 0 0;padding:12px 14px;border-radius:10px;background:rgba(120,130,150,.09);font-size:.86rem;line-height:1.85}
@media (max-width:640px){.claim-audit .ca-detail{grid-template-columns:1fr;gap:2px}
.claim-audit .ca-detail dt{margin-top:8px}}
</style>"""


def claim_audit(rows: list[dict]) -> str:
    """投稿の言い分と一次資料の突き合わせセクションを組み立てる。"""
    data = json.loads(CLAIM_POSTS.read_text(encoding="utf-8"))
    known = {row["tweet_id"] for row in rows}
    items = []
    total = 0
    for entry in CLAIM_AUDIT:
        ids = data["claims"][entry["key"]]
        missing = [i for i in ids if i not in known]
        if missing:
            raise SystemExit(f"{entry['key']}: 正典に無い tweet_id があります: {missing}")
        if len(set(ids)) != len(ids):
            raise SystemExit(f"{entry['key']}: tweet_id が重複しています")
        total += len(ids)
        links = " ／ ".join(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
            for url, label in entry["links"]
        )
        items.append(
            f'  <article class="ca-item" data-verdict="{entry["verdict"]}">\n'
            f'    <p class="ca-say">「{esc(entry["say"])}」'
            f'<span class="ca-n">該当した投稿 {len(ids)}件</span></p>\n'
            f'    <dl class="ca-detail">\n'
            f"      <dt>原典はこう書いている</dt><dd>{esc(entry['source'])}</dd>\n"
            f'      <dt>突き合わせた結果</dt><dd><b class="ca-mark">'
            f"{esc(VERDICT_LABEL[entry['verdict']])}</b>{esc(entry['note'])}</dd>\n"
            f"    </dl>\n"
            f'    <p class="ca-src">{links}</p>\n'
            f"  </article>"
        )
    body = "\n".join(items)
    return f"""{CLAIM_START}
<section class="panel claim-audit" id="claim-audit">
{CLAIM_CSS}
<div class="panel-title"><h2>その言い分、原典に当たるとどうなるか</h2><span>会見録・国会答弁・官庁統計で1件ずつ照合</span></div>
<p class="ca-lead">税の話は、数字を出したほうが強く見えます。だからこそ、その数字がどこから来たのかを見ておきたい。ここでは投稿にくり返し出てくる言い分のうち、公の記録で当否を判定できるものを6つ取り出し、首相官邸の会見録、国会の議事録、財務省と国税庁の公表資料に当たりました。照合したのは{CHECKED_ON}です。裏の取れなかった1件も、取れないまま置いてあります。</p>
<div class="ca-list">
{body}
</div>
<p class="ca-how">数え方について。検索で拾った候補をそのまま足すと、同じ語を別の意味で使っている投稿まで数に入ります。ここでは候補を一つずつ開き、その言い分を実際にしている投稿だけを残しました（合わせて{total}件）。減税に賛成か反対かは問うていません。この節では投稿の本文は載せず、件数と照合の結果だけを出しています。</p>
</section>
{CLAIM_END}"""


def write_claim_provenance(destination: Path | None = None) -> None:
    """ページに出る「N件」の出所を、1行1投稿の配列として書き出す。

    verify_number_provenance.py はレコードの配列しか出所にできないため、
    編集部が割り当てた件数はここを通す。中身は claim_posts の写しなので、
    候補ページを作るときに同じ内容を書いても差分は出ない。
    """
    data = json.loads(CLAIM_POSTS.read_text(encoding="utf-8"))
    records = [
        {"tweet_id": tid, "claim": key}
        for key, ids in data["claims"].items()
        for tid in ids
    ]
    out = destination or ROOT / "data" / "verification"
    out.mkdir(parents=True, exist_ok=True)
    (out / "consumption-tax-cut-claims.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# 論点ごとのX投稿
#
# 皇室典範（#issue-cards）と同じ位置（一次資料クイズの直後）・同じ簡潔な形。
# 要約文は付けない。皇室典範は2026-09-20にオーナー指示で要約(hermes-sample-summary)を
# 撤去済み（同じ文の反復が「質の低いコンテンツ」の兆候として審査対策上逆効果、と
# x_embed.pyにも明記されている）。ラベルは編集部が短く言い換えたもので、要約ではない。
# ---------------------------------------------------------------------------
ISSUE_CARDS_START = "<!-- ISSUE_CARDS_START -->"
ISSUE_CARDS_END = "<!-- ISSUE_CARDS_END -->"
# claim_audit の直後（起承転結の並びで、一次資料クイズの次）に置く。
ISSUE_CARDS_ANCHOR = CLAIM_END

# 各論点で、具体的に違う角度から語っている実際の投稿を2件ずつ選んだ
# （veins.json（地下水脈）と同じ基準＝要約だけで選ばず、本文を1件ずつ読んで選定。
# 他セクションで既に使っている投稿とは重複させていない）。2026-09-20選定。
ISSUE_CARDS_POSTS: dict[str, list[tuple[str, str]]] = {
    "consumption-tax-cut-scope": [
        ("https://x.com/siki2364/status/2084241343036219545", "一律減税でなければ意味がない"),
        ("https://x.com/148pv9yuZKv7Hox/status/2086203743704637530", "一律は非現実的、まず食料品から実現を"),
    ],
    "consumption-tax-cut-effect": [
        ("https://x.com/mina_713713/status/2091198301052055950", "対応が遅く物価高に追いつかない"),
        ("https://x.com/longtallsagi/status/2093939866065371202", "減税がなければ値上がりしていた分、恩恵はある"),
    ],
    "consumption-tax-cut-finance-welfare": [
        ("https://x.com/Culena0/status/2085897628005650517", "社会保障の削減が先ではないか"),
        ("https://x.com/Yan0321Asa/status/2086480295843504503", "財源論より歳出の使い道を議論すべき"),
    ],
    "consumption-tax-cut-alternatives": [
        ("https://x.com/fukmaru2020/status/2083093838630142393", "非課税の事業者には届かず給付の方が確実"),
        ("https://x.com/gasnukiaccount/status/2094004743136063806", "給付は一時的、減税は恒久的な効果"),
    ],
    "consumption-tax-cut-business-burden": [
        ("https://x.com/NobodyR01/status/2083849357380694468", "改修費の支援策がまだ議論されていない"),
        ("https://x.com/koto_cat_/status/2081981547775995905", "増税の時は問題にならなかった話"),
    ],
    "consumption-tax-cut-political-trust": [
        ("https://x.com/shigani_kisyain/status/2082021002566095151", "公約から実現までの遅さへの不満"),
        ("https://x.com/QVb7cvZhCKCLMqK/status/2084235686341992560", "党内議論の報道のされ方に疑問"),
    ],
    "consumption-tax-cut-other": [
        ("https://x.com/kawanashigaikot/status/2091675832569979076", "世論調査の聞き方が公平でないと指摘"),
        ("https://x.com/KayoRabbit/status/2084228125450482119", "制度の説明が分かりにくいと指摘"),
    ],
}

ISSUE_CARDS_CSS = """<style>
#issue-cards .ic{border-top:2px solid #0F1A3D;padding:22px 0 30px;scroll-margin-top:64px}
#issue-cards .ic:first-of-type{border-top:none;padding-top:0}
#issue-cards .ic:target .ic-head h3{color:var(--accent)}
#issue-cards .ic-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
#issue-cards .ic-head h3{margin:0;font-size:21px;font-weight:900;line-height:1.4;letter-spacing:.01em}
#issue-cards .ic-head .cnt{margin-left:auto;font-weight:900;font-size:26px;line-height:1;
  font-variant-numeric:tabular-nums;color:#0F1A3D}
#issue-cards .ic-head .cnt small{font-size:13px;font-weight:700;color:var(--muted);margin-left:2px}
#issue-cards .ic-back{display:inline-block;margin-top:16px;font-size:13px;font-weight:700}
#issue-cards .hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:6px}
#issue-cards .hermes-sample{min-width:0}
#issue-cards .hermes-sample-meta{font-weight:800;display:block;margin-bottom:8px;font-size:14.5px}
@media (max-width:640px){#issue-cards .hermes-samples{grid-template-columns:1fr}}
</style>"""


def issue_cards(public_theme: Path = PUBLIC_THEME) -> str:
    """「論点ごとのX投稿」セクションを組み立てる（皇室典範と同じ位置・同じ形）。"""
    data = json.loads(public_theme.read_text(encoding="utf-8"))
    if data.get("theme_id") != "consumption-tax-cut":
        raise ValueError(f"消費税減税の公開JSONではありません: {public_theme}")
    by_id = {issue["id"]: issue for issue in data["issues"]}
    missing = set(ISSUE_CARDS_POSTS) - set(by_id)
    if missing:
        raise ValueError(f"論点IDが公開JSONに無い: {missing}")

    cards = []
    for iid, posts in sorted(ISSUE_CARDS_POSTS.items(), key=lambda kv: -by_id[kv[0]]["count"]):
        issue = by_id[iid]
        samples = "".join(
            f'<div class="hermes-sample"><span class="hermes-sample-meta">{esc(label)}</span>'
            f'{embed_html(url)}</div>'
            for url, label in posts
        )
        cards.append(
            f'<article class="ic" id="issue-{esc(iid)}">'
            f'<div class="ic-head"><h3>{esc(issue["label"])}</h3>'
            f'<span class="cnt">{issue["count"]}<small>件</small></span></div>'
            f'<div class="hermes-samples">{samples}</div>'
            f'<a class="ic-back" href="#planet-block">↑ 地図へ戻る</a></article>'
        )
    return (
        f'{ISSUE_CARDS_START}\n'
        f'<section class="panel" id="issue-cards">{ISSUE_CARDS_CSS}'
        f'<div class="panel-title"><h2>論点ごとのX投稿</h2></div>'
        f'<p>それぞれの論点について、実際に投稿された2件を編集部が選んで載せています。'
        f'ここでの選び方は、その論点全体の賛否の比率を表すものではありません。'
        f'うまく表示されないときは、リンクからXで元の投稿を確認してください。</p>'
        + "".join(cards)
        + f'</section>\n{ISSUE_CARDS_END}'
    )


# ---------------------------------------------------------------------------
# 何が、どこまで進んでいるのか／決まったこととまだのこと
#
# 山なみ変換（4b973a4、2026-09-14）で「この争点の背景」が消えたまま、
# 2026-09-18に「山なみへ統合済み」と誤認され本文ごと削除された（54d4888、
# 課題69）。2026-09-19、オーナー指摘で発覚し書き直して復元したが、当初案は
# 独自形式（`issue-background`）だった。オーナーから「他のテーマのように」と
# 追加指摘があり、9テーマ共通の型（`#bukatsu-background`＋`#bukatsu-check`、
# 起承転結の再構成でfukushuto向けに作られ他8テーマへ複製済み）に作り直した。
# IDは他テーマと同じ `bukatsu-background`/`bukatsu-check` を使う（テーマをまたぐ
# 固有の命名ではなく、各テーマのHTMLファイル内で完結するローカルなID）。
#
# CLAIM_AUDITと同じ「後付けの補完処理」方式。山なみ図（PLANET_SECTION_START）の
# 直前に毎回そろえる（PLANET_SECTIONの再生成やCLAIM_AUDITの再構築では消えない）。
# ---------------------------------------------------------------------------
BACKGROUND_START = "<!-- BACKGROUND_CONTEXT_START -->"
BACKGROUND_END = "<!-- BACKGROUND_CONTEXT_END -->"
BACKGROUND_ANCHOR = "<!-- PLANET_SECTION_START -->"

# 他テーマ（bukatsu-chiiki・fukushuto等）の埋め込み<style>と同一（コピー）。
# セレクタがID指定のため、テーマごとにHTMLファイルが別なら衝突しない。
BACKGROUND_CSS = """<style>
#bukatsu-background .bg-def{font-size:17px;font-weight:700;line-height:1.85;margin:0 0 6px}
#bukatsu-background .bg-now{font-size:14px;color:var(--muted);margin:0 0 20px}
#bukatsu-background h3{font-size:15px;font-weight:900;margin:24px 0 8px;padding-left:10px;
  border-left:3px solid var(--accent);line-height:1.5}
#bukatsu-background p{font-size:14.5px;line-height:1.95;margin:0 0 .9em}
#bukatsu-background ol.bg-tl{list-style:none;margin:6px 0 0;padding:0}
#bukatsu-background ol.bg-tl li{display:grid;grid-template-columns:132px 1fr;gap:18px;
  padding:14px 0;border-top:1px solid var(--line)}
#bukatsu-background ol.bg-tl .when{font-size:13px;font-weight:900;color:var(--accent);line-height:1.6}
#bukatsu-background ol.bg-tl .when em{display:block;font-style:normal;font-size:11.5px;
  font-weight:400;color:var(--muted)}
#bukatsu-background ol.bg-tl .what{font-size:14.5px;line-height:1.9;margin:0}
#bukatsu-background ol.bg-tl .src{display:block;margin-top:6px;font-size:12px;line-height:1.7}
#bukatsu-background ol.bg-tl .src a{color:var(--muted)}
#bukatsu-background .bg-jump{margin:22px 0 0;font-size:14px;font-weight:700}
#bukatsu-check .ck{display:grid;grid-template-columns:150px 1fr;gap:0;
  border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:0 0 10px}
#bukatsu-check .ck .k{background:#F2F6FD;padding:14px 16px;border-right:1px solid var(--line)}
#bukatsu-check .ck .k b{display:block;font-size:15px;font-weight:900;line-height:1.5}
#bukatsu-check .ck .k span{display:block;margin-top:5px;font-size:12.5px;color:var(--muted);
  line-height:1.7}
#bukatsu-check .ck .v{padding:14px 18px;font-size:14.5px;line-height:1.9}
#bukatsu-check .ck .v .src{display:block;margin-top:7px;font-size:11.5px;line-height:1.7}
#bukatsu-check .ck .v .src a{color:var(--muted)}
#bukatsu-check .ck-note{margin:14px 0 0;padding:12px 15px;border-radius:10px;
  background:#FBF8EC;border-left:3px solid #C9971A;font-size:13.5px;line-height:1.85}
@media (max-width:560px){
  #bukatsu-check .ck{grid-template-columns:1fr}
  #bukatsu-check .ck .k{border-right:none;border-bottom:1px solid var(--line)}
}
@media (max-width:560px){
  #bukatsu-background ol.bg-tl li{grid-template-columns:1fr;gap:4px}
}
</style>"""

# 一次情報は quality/research/consumption-tax-cut-primary-sources.md で
# 確認済みの資料（H-2・N・O・P、確認日2026-09-17）から選んだ。新しい数字を
# ここで足さないこと（足す場合は先に一次資料メモへ確認日つきで記録する）。
BACKGROUND_TIMELINE = [
    (
        "2026年7月30日",
        "税率引下げと給付付き税額控除の検討を表明",
        "首相官邸の会見で、軽減税率対象の飲食料品について、税率引下げと給付付き税額控除の両方をあわせて検討していると説明されました。",
        [("https://www.kantei.go.jp/jp/105/statement/2026/0730kaiken.html",
          "首相官邸「『飲食料品に係る消費税率の引下げ』及び『給付付き税額控除』についての会見」（令和8年7月30日）")],
    ),
    (
        "2026年8月5日",
        "「1%・2年間」の方針を初めて閣議決定",
        "政府として、令和9年4月から2年間、軽減税率対象の飲食料品の消費税率を1%とする方針を正式に決定しました。財源は歳出・歳入の見直しで確保し、赤字国債には頼らないとしています。",
        [("https://www.kantei.go.jp/jp/kakugi/2026/kakugi-2026080501.html",
          "首相官邸「『給付付き税額控除』の制度導入の基本方針について」（令和8年8月5日閣議決定）")],
    ),
    (
        "2026年9月15日",
        "大綱を閣議決定、制度設計が確定",
        "税率引下げの期間（2027年4月〜2029年3月）、就業者負担軽減支援金の対象・支給額、事業者向けの経過措置など、法案のもとになる制度設計が固まりました。本ページ確認時点で、これが到達している最新の段階です。",
        [("https://www.cas.go.jp/jp/seisaku/shouhizei_zeigakukoujo/pdf/sankou4.pdf",
          "内閣「飲食料品消費税率の臨時的な引下げ及び就業者負担軽減支援金の導入に関する大綱」（令和8年9月15日閣議決定）")],
    ),
]

BACKGROUND_CHECKS = [
    (
        "対象範囲",
        "食料品だけか、広がるのか",
        "決まっています。現行の軽減税率が適用される飲食料品（酒類・外食を除く）のままで、対象を広げる決定はしていません。",
        [("https://www.cas.go.jp/jp/seisaku/shouhizei_zeigakukoujo/pdf/sankou4.pdf", "内閣「大綱」（令和8年9月15日閣議決定）第二")],
    ),
    (
        "税率と期間",
        "いつから、何%、いつまでか",
        "決まっています。2027年4月1日から2029年3月31日までの2年間、税率を1%（軽減税率8%から引下げ）とします。",
        [("https://www.cas.go.jp/jp/seisaku/shouhizei_zeigakukoujo/pdf/sankou4.pdf", "同大綱")],
    ),
    (
        "給付との関係",
        "減税と給付、どちらか一方か",
        "決まっています。両方を組み合わせる設計です。2027年4月から「就業者負担軽減支援金」を導入し、2029年度には「給付付き税額控除」として本格化させます。",
        [("https://www.cas.go.jp/jp/seisaku/shouhizei_zeigakukoujo/pdf/sankou4.pdf", "同大綱（就業者負担軽減支援金の制度設計）")],
    ),
    (
        "財源",
        "いくらかかり、どう賄うか",
        "方針だけ決まっています。「赤字国債に頼らない」という原則は閣議決定されましたが、具体的な金額の内訳は令和9年度の予算編成まで示されていません。",
        [("https://www.cas.go.jp/jp/seisaku/shouhizei_zeigakukoujo/pdf/sankou4.pdf", "同大綱")],
    ),
]


def _bg_sources(links: list[tuple[str, str]]) -> str:
    return " ／ ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{esc(label)}</a>' for url, label in links
    )


def background_context() -> str:
    """「何が、どこまで進んでいるのか」「決まったこと・まだのこと」を組み立てる。

    他9テーマ（fukushuto等）と同じ`#bukatsu-background`＋`#bukatsu-check`型
    （静的な編集部原稿）。
    """
    timeline = "\n".join(
        f'<li><div class="when">{esc(when)}<em>{esc(title)}</em></div>'
        f'<div><p class="what">{esc(body)}</p>'
        f'<span class="src">出典: {_bg_sources(links)}</span></div></li>'
        for when, title, body, links in BACKGROUND_TIMELINE
    )
    checks = "\n".join(
        f'<div class="ck"><div class="k"><b>{esc(key)}</b><span>{esc(question)}</span></div>'
        f'<div class="v">{esc(body)}<span class="src">出典: {_bg_sources(links)}</span></div></div>'
        for key, question, body, links in BACKGROUND_CHECKS
    )
    return f"""{BACKGROUND_START}
{BACKGROUND_CSS}
<section class="panel" id="bukatsu-background" aria-labelledby="bg-title">
<div class="panel-title"><h2 id="bg-title">何が、どこまで進んでいるのか</h2><span>官庁の資料で確かめた範囲</span></div>
<p class="bg-def">消費税減税（食料品分）は、物価高への対策として、飲食料品にかかる消費税率を時限的に引き下げる政策です。現在は標準税率10%、飲食料品などには軽減税率8%が適用されています。</p>
<p class="bg-now">法律はまだ成立していません。政府が決めたのは法案のもとになる方針（大綱）までで、これから法案を作り、臨時国会に提出して審議されます。</p>
<h3>なぜ始まったか</h3>
<p>物価高が続くなか、各党が消費税や物価対策としての減税・給付を公約や提言として掲げてきました。国民民主党は消費税の一律5%への引下げを、立憲民主党は食料品のゼロ税率化を提言するなど、政党によって対象・税率・実施方法は分かれていました。</p>
<p>2026年に入り、政府・与党内でも食料品に対象を絞った引下げの検討が進み、8月5日には政府として初めて「税率1%・2年間」という具体的な方針を閣議決定しました。9月15日には、この方針をもとにした大綱が閣議決定され、期間や支援金の制度設計が固まりました。</p>
<h3>これまでの経緯</h3>
<ol class="bg-tl">
{timeline}
</ol>
<p class="bg-jump"><a href="#planet-block">意見の分布のほうを先に見る →</a></p>
</section>
<section class="panel" id="bukatsu-check" aria-labelledby="ck-title">
<div class="panel-title"><h2 id="ck-title">「決まった」と「まだ」を分けて確かめる</h2><span>大綱と、これからの法案審議を見分ける</span></div>
<p>「消費税が下がる」と一言で言っても、対象・税率・期間・財源のうち、政府がすでに決めた部分と、これから決める部分があります。混同すると、賛否の理由がかみ合わなくなります。</p>
{checks}
<p class="ck-note"><b>このページで未確認のこと</b><br>決まっているのは政府の方針（大綱）までで、法律はまだ成立していません。臨時国会への法案提出時期や審議の見通しは報道に基づくもので、政府の公式発表として確認できた日程はありません（本ページ確認: 2026年9月19日）。</p>
</section>
{BACKGROUND_END}"""


def build(
    *,
    classified: Path | None = None,
    template: Path = TEMPLATE,
    output: Path = OUTPUT,
    verification_dest: Path | None = None,
) -> None:
    data, rows = arena_data(classified)
    period = collection_period(rows)
    html = template.read_text(encoding="utf-8")
    published_at, modified_at = existing_dates(html)

    opinions = data["opinions"]
    relevant = data["relevant"]
    total = data["total_classified"]
    order = pinned_issue_order(html, data["issue_order"])
    counts = data["issue_counts"]
    stance_counts = data["stance_counts"]
    stance_share = data["stance_share"]
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
            "datePublished": published_at,
            "dateModified": modified_at,
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
        "background:url('images/topics/fukushuto/fukushuto-hero.webp') center/cover no-repeat;opacity:.18}",
        "background:url('images/topics/consumption-tax-cut/consumption-tax-cut-hero.webp') center/cover no-repeat;opacity:.18}",
    )
    html = html.replace(
        "<body class=\"summary-on-light\" style=\"--topic-hero-image:url('images/topics/fukushuto/fukushuto-hero.webp')\">",
        f'<body class="summary-on-light" style="--topic-hero-image:{HERO_IMAGE}">',
    )

    # 「条件付き賛成」用の配色を追加（アリーナの橙と揃える）。既にあれば足さない
    if ".side.mid{" not in html:
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

    # --- 5. 潮目ウィジェットの位置をそろえる -------------------------------
    # 中身（前回の収集回×今回の収集回の比較）はこのスクリプトの管轄外で、
    # adapter（scripts/refresh_adapters/consumption_tax.py）が生成のたびに
    # 貼り直す。ここでは中身は作り直さず、既にあれば抜き出していったん外し、
    # bukatsu-chiikiと同じ位置（claim-audit＝一次資料クイズの直前）へ戻す
    # （オーナー指摘 2026-09-20。以前はexplainer-section跡地＝issue-cardsの後ろに
    # 居座っていた）。
    tide_marker = "<!-- TIDE_CARD_END --></section>"
    existing_tide = ""
    if '<section class="update-dashboard"' in html and tide_marker in html:
        tide_start = html.index('<section class="update-dashboard"')
        tide_end = html.index(tide_marker) + len(tide_marker)
        existing_tide = html[tide_start:tide_end]
        html = html[:tide_start] + html[tide_end:]
    # 潮目を外したあと・貼る前の空行を必ず2行に揃える。揃えないと、貼り直しのたびに
    # 空行が増えていき、adapterの冪等性検査（2回目で差分なし）が通らない。
    # 次に来るのは、テンプレートに「6つの論点」セクションが残っている初回だけ
    # explainer-section、削除済みなら拡大モーダルのdiv。
    html = re.sub(
        r'\n\s*\n+(<section class="panel" id="explainer-section">|<div class="explainer-modal" id="explainer-modal")',
        r"\n\n\1",
        html,
    )
    if existing_tide:
        if CLAIM_START not in html:
            raise SystemExit("潮目ウィジェットの貼り直し先（一次資料クイズのマーカー）が見つかりません")
        html = html.replace(CLAIM_START, existing_tide + "\n\n" + CLAIM_START, 1)
    # --- 6. 拡大モーダル（論点別図解は各論点パネルへ移設済み） -----------
    # 「6つの論点」解説カードは、山なみ図の各論点パネルと内容が重複するため
    # 起承転結の再構成（課題69）で削除した。画像は refresh_planet_section.py の
    # _inject_ctc_landing_images() が山なみ再生成のたびに各論点パネルへ差し戻す。
    # モーダル本体（拡大表示の器）とその開閉スクリプトはテンプレートのものを
    # そのまま使い、位置だけ投票セクションの直前へそろえる。
    vote_open = re.search(r'<section class="panel" id="vote-section"[^>]*>', html)
    if not vote_open:
        raise SystemExit("投票セクションが見つかりません")

    modal_start = html.index('<div class="explainer-modal" id="explainer-modal"')
    modal_end = vote_open.start()
    modal = html[modal_start:modal_end]

    # 「このテーマを読み解く、6つの論点」セクションがまだ残っているテンプレート
    # （初回のみ）はそこから、すでに削除済みのテンプレートはモーダル自身の位置から
    # 差し替える（冪等）。
    start = html.index(
        '<section class="panel" id="explainer-section">'
    ) if '<section class="panel" id="explainer-section">' in html else modal_start
    html = html[:start] + modal + html[modal_end:]
    vote_open_tag = vote_open.group(0)

    # --- 7. 投票セクション ---------------------------------------------
    # 「このページの作り方」(article-trust) は、皇室典範と同じく投票セクションの
    # 外（次のパネルの直前）に独立して置く。以前は投票への導入文に続けて
    # 投票セクションの中へ差し込んでいたため、「あなたが一番気になる論点は？」と
    # 「このページの作り方」が1つのパネルに同居していた（オーナー指摘 2026-09-20）。
    # 既存のarticle-trustをそのまま抜き出して移す（trust_block()で作り直すと、
    # apply_theme_trust.py が書き足す「収集・分類で分かったこと」が消える）。
    if ARTICLE_TRUST_START in html and ARTICLE_TRUST_END in html:
        ts = html.index(ARTICLE_TRUST_START)
        te = html.index(ARTICLE_TRUST_END) + len(ARTICLE_TRUST_END)
        existing_trust = html[ts:te]
        html = html[:ts] + html[te:]
    else:
        existing_trust = trust_block(total, relevant, opinions, published_at, modified_at)

    vote_intro = (
        f'{vote_open_tag}<div class="panel-title"><h2>あなたが一番気になる「減税の論点」は？</h2>'
        "<span>SNSの声を見る前に</span></div>"
        "<p>2026年7月、物価高対策として食料品に対象を絞った消費税減税の議論が大詰めを迎えました。"
        "「対象が限定的で中途半端だ」という不満に加え、財源や社会保障への影響を心配する声、"
        "値下げが実際の価格に反映されるのかを疑う声も上がっています。</p>"
    )
    start = html.index(vote_open_tag)
    end = html.index('<div id="vote-step1">')
    html = html[:start] + vote_intro + "\n" + html[end:]
    html = html.replace(
        '<span class="step-num">2</span>副首都構想への賛否は？',
        '<span class="step-num">2</span>消費税減税への立場は？',
    )

    # 投票セクションを閉じた直後（次のパネルの直前）に独立して置く。
    trust_anchor = html.index('<section class="panel" id="related-topics"')
    html = (
        html[:trust_anchor]
        + existing_trust
        + "\n\n"
        + html[trust_anchor:]
    )

    # --- 8. アリーナ見出し・凡例 ---------------------------------------
    html, map_heading_count = re.subn(
        r'<span>意見[\d,]+件 \| セクター=論点 / 中心に近いほど冷静 / 色=(?:賛否|立場) \| ホバーで詳細・クリックでXへ</span>',
        f'<span>意見{opinions}件 | セクター=論点 / 中心に近いほど冷静 / 色=立場 | ホバーで詳細・クリックでXへ</span>',
        html,
        count=1,
    )
    if map_heading_count != 1:
        raise ValueError(f"反応マップ見出しの置換が{map_heading_count}件です")
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
    # 凡例の先頭は初版（副首都）では「肯定的」、生成後は「減税推進」。どちらからでも作り直す。
    legend_start = next(
        (
            token
            for token in (
                '<span><i style="background:#059669"></i>肯定的</span>',
                '<span><i style="background:#059669"></i>減税推進</span>',
            )
            if token in html
        ),
        None,
    )
    if legend_start is None:
        raise SystemExit("アリーナの凡例が見つかりません")
    html = replace_between(
        html,
        legend_start,
        '<span style="color:#888">中心＝冷静 / 外周＝感情的</span>',
        legend,
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
        "encodeURIComponent('https://sns-reaction-map.jp/fukushuto-reaction-map.html')",
        f"encodeURIComponent('{PAGE_URL}')",
    )

    # --- 13. スタンス集計（削除済み） -------------------------------------
    # 「6つの論点とXの声」「この争点の背景」の2セクションは、2026-09-14の
    # 山なみ形式への切り替え（4b973a4）でページから無くなった。同じ内容は
    # 山なみの論点別パネル（一次資料との照合込み）と投票セクションの導入文に
    # 統合済みのため、ここでの再構築は行わない。
    # スタンス集計（数字が山なみの凡例と重複）自体も、起承転結の再構成（課題69、
    # fukushutoと同型）で削除した。テンプレートに古いセクションが残っていれば
    # ここで取り除く（冪等: 無ければ何もしない）。
    stance_summary_start = '<section class="panel conflict-panel"><div class="panel-title"><h2>スタンス集計</h2>'
    if stance_summary_start in html:
        start = html.index(stance_summary_start)
        end = html.index('<section class="panel" id="related-topics">')
        html = html[:start] + html[end:]

    # --- 14. 次に読むテーマ ----------------------------------------------
    related = (
        '<section class="panel" id="related-topics"><div class="panel-title"><h2>次に読むテーマ</h2>'
        '<span>他のテーマ</span></div><div class="related-grid">\n'
        '<a class="related-card" href="fukushuto-reaction-map.html"><img src="images/topics/fukushuto/fukushuto-hero.webp" alt="副首都法案" loading="lazy"><div><strong>副首都法案</strong><p>「物価対策どこ行った」の声も。</p></div></a>\n'
        '<a class="related-card" href="constitutional-amendment-reaction-map.html"><img src="images/topics/constitutional-amendment/constitutional-hero.webp" alt="憲法改正論議" loading="lazy"><div><strong>憲法改正論議</strong><p>統治の仕組みを変えるか、守るか。</p></div></a>\n'
        '<a class="related-card" href="koshitsu-tenpakai-reaction-map.html"><img src="images/topics/koshitsu-tenpakai/koshitsu-hero.webp" alt="皇室典範改正" loading="lazy"><div><strong>皇室典範改正</strong><p>政策転換への賛否と慎重論を見る。</p></div></a>\n'
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
    query_items = "".join(f"<li>{q}</li>" for q in query_lines())
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
        f"<li>{period}Yahooリアルタイム検索で{total}件を取得（重複除外後）。"
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
    # 他テーマページと同じく </footer> の直後に置く。既にあれば差し替える
    # （追記のままだと、自分自身をテンプレートに再生成したときに2枚出る）。
    block = related_block()
    if '<script id="related-theme-tracking">' in html:
        start = html.index('<script id="related-theme-tracking">')
        end = html.index("</script>", start) + len("</script>")
        html = html[:start] + block + html[end:]
    else:
        idx = html.index("</footer>") + len("</footer>")
        html = html[:idx] + "\n" + block + html[idx:]

    # --- 17. 投稿の言い分と一次資料の突き合わせ ---------------------------
    # マーカーごと、山なみ図を読んだ直後（PLANET_SECTION_ENDの直後）へ置く。
    # 既存のマーカーがどこにあっても（以前は最後尾に近い位置だった）毎回そこへ
    # 動かすことで、起承転結の再構成後は常に正しい位置にそろう（fukushutoの
    # FACT_CHECKと同じ「後付けの補完処理」方式、課題69）。
    audit = claim_audit(rows)
    if CLAIM_START in html and CLAIM_END in html:
        start = html.index(CLAIM_START)
        end = html.index(CLAIM_END) + len(CLAIM_END)
        html = html[:start] + html[end:]
    idx = html.index(CLAIM_ANCHOR) + len(CLAIM_ANCHOR)
    html = html[:idx] + "\n\n" + audit + html[idx:]
    write_claim_provenance(verification_dest)

    # --- 17.5. 論点ごとのX投稿 -------------------------------------------
    # CLAIM_AUDITと同じ「後付けの補完処理」。claim_auditの直後（CLAIM_END）に置く。
    if ISSUE_CARDS_START in html and ISSUE_CARDS_END in html:
        start = html.index(ISSUE_CARDS_START)
        end = html.index(ISSUE_CARDS_END) + len(ISSUE_CARDS_END)
        html = html[:start] + html[end:]
    idx = html.index(ISSUE_CARDS_ANCHOR) + len(ISSUE_CARDS_ANCHOR)
    html = html[:idx] + "\n\n" + issue_cards() + html[idx:]

    # --- 18. 何が、どこまで進んでいるのか／決まったこと・まだのこと ---------
    # CLAIM_AUDITと同じ「後付けの補完処理」。山なみ図（PLANET_SECTION_START）の
    # 直前に毎回そろえる。他9テーマと同じ`#bukatsu-background`＋`#bukatsu-check`型。
    if BACKGROUND_START in html and BACKGROUND_END in html:
        start = html.index(BACKGROUND_START)
        end = html.index(BACKGROUND_END) + len(BACKGROUND_END)
        html = html[:start] + html[end:]
    idx = html.index(BACKGROUND_ANCHOR)
    html = html[:idx] + background_context() + "\n\n" + html[idx:]

    verify(html, opinions)
    output.write_text(html, encoding="utf-8")
    print(f"wrote {output} ({len(html.splitlines())} lines)")
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

    if re.search(r"const SM_RAW = \[", html):
        problems.append(
            "SM_RAW（旧アリーナ形式の投稿別データ。山なみ形式には無い機能で"
            "2026-09-20に撤去済み）が復活している"
        )
    # 投票の保存先は supabase 直叩きから vote-store.js 経由へ移っている
    for token in ("G-K10S4YCZFH", "ca-pub-2542211932832864", "vote-store.js", "topic-modern.js"):
        if token not in html:
            problems.append(f"保護タグが失われている: {token}")
    if "--topic-hero-image:" not in html:
        problems.append("--topic-hero-image が未指定（他テーマの画像にフォールバックする）")

    # 参照している画像が実在するか（論点図解・ヒーロー）
    for src in sorted(set(re.findall(r'(?:src|data-img)="(images/[^"]+)"', html))):
        # 候補ページを stage に書くときも、画像の在り処は公開ディレクトリで見る
        if not (PAGE.parent / src).exists():
            problems.append(f"参照画像が存在しない: {src}")
    if '<div class="explainer-modal"' not in html:
        problems.append("図解の拡大モーダルが失われている")
    if '<aside class="article-trust"' not in html:
        problems.append("「このページの作り方」ブロックがない（他テーマと不揃いになる）")
    elif '<section class="panel" id="vote-section"' in html:
        # 皇室典範と同じく、投票セクション（あなたが一番気になる論点は？）の
        # 外に独立して置くこと（2026-09-20オーナー指摘の再発防止）。
        vote_start = html.index('<section class="panel" id="vote-section"')
        vote_end = html.index("</section>", vote_start) + len("</section>")
        trust_start = html.index('<aside class="article-trust"')
        if vote_start < trust_start < vote_end:
            problems.append(
                "「このページの作り方」が投票セクションの中に同居している"
                "（皇室典範と同じく、投票セクションの外に分けること）"
            )
    # 潮目ウィジェットがあるなら、bukatsu-chiikiと同じ位置（一次資料クイズの直前）か。
    if '<section class="update-dashboard"' in html and CLAIM_START in html:
        if html.index('<section class="update-dashboard"') > html.index(CLAIM_START):
            problems.append(
                "潮目ウィジェットが一次資料クイズより後ろにある"
                "（bukatsu-chiikiと同じく、その直前に置くこと）"
            )
    if 'id="related-theme-tracking"' not in html:
        problems.append("投票後の回遊カードのスクリプトがない")

    # 一次資料との突き合わせセクション。マーカー・判定3種・確認日・件数の出所が揃っているか。
    if html.count(CLAIM_START) != 1 or html.count(CLAIM_END) != 1:
        problems.append("突き合わせセクションのマーカーが1組でない")
    audits = len(re.findall(r'<article class="ca-item"', html))
    if audits != len(CLAIM_AUDIT):
        problems.append(f"突き合わせカードが{len(CLAIM_AUDIT)}枚でない: {audits}枚")
    for verdict in ("fact", "gap", "miss"):
        if f'data-verdict="{verdict}"' not in html:
            problems.append(f"突き合わせの判定 {verdict} のカードがない")
    if CHECKED_ON not in html:
        problems.append("突き合わせの照合日がページにない")
    claims_file = ROOT / "data" / "verification" / "consumption-tax-cut-claims.json"
    if not claims_file.exists():
        problems.append("件数の出所ファイル（consumption-tax-cut-claims.json）がない")
    else:
        records = json.loads(claims_file.read_text(encoding="utf-8"))
        shown = [
            int(n) for n in re.findall(r'<span class="ca-n">該当した投稿 (\d+)件</span>', html)
        ]
        expected = [
            sum(1 for r in records if r["claim"] == entry["key"]) for entry in CLAIM_AUDIT
        ]
        if shown != expected:
            problems.append(f"突き合わせの件数が出所ファイルと合わない: {shown} != {expected}")

    # 論点ごとのX投稿。マーカー1組・論点数分のカード・投稿2件ずつ・
    # 一次資料クイズ（claim-audit）の直後にあるかを検査する。
    if html.count(ISSUE_CARDS_START) != 1 or html.count(ISSUE_CARDS_END) != 1:
        problems.append("論点ごとのX投稿のマーカーが1組でない")
    ic_cards = len(re.findall(r'<article class="ic" id="issue-', html))
    if ic_cards != len(ISSUE_CARDS_POSTS):
        problems.append(f"論点ごとのX投稿のカードが{len(ISSUE_CARDS_POSTS)}枚でない: {ic_cards}枚")
    ic_samples = len(re.findall(r'<div class="hermes-sample">', html))
    expected_samples = sum(len(posts) for posts in ISSUE_CARDS_POSTS.values())
    if ic_samples != expected_samples:
        problems.append(f"論点ごとのX投稿の投稿数が{expected_samples}件でない: {ic_samples}件")
    for posts in ISSUE_CARDS_POSTS.values():
        for url, _label in posts:
            if f'href="{url}"' not in html:
                problems.append(f"論点ごとのX投稿: リンクが見つからない: {url}")
    if (
        ISSUE_CARDS_START in html
        and CLAIM_END in html
        and html.index(ISSUE_CARDS_START) < html.index(CLAIM_END)
    ):
        problems.append("論点ごとのX投稿が一次資料クイズより前にある（クイズの直後に置くこと）")

    # 何が、どこまで進んでいるのか／決まったこと・まだのこと。マーカー1組・
    # 見出し2つ・タイムライン・確認観点・出典が揃っているか（2026-09-18に
    # 「山なみへ統合済み」と誤認され削除された再発防止）。
    if html.count(BACKGROUND_START) != 1 or html.count(BACKGROUND_END) != 1:
        problems.append("背景セクションのマーカーが1組でない")
    if '<h2 id="bg-title">何が、どこまで進んでいるのか</h2>' not in html:
        problems.append("「何が、どこまで進んでいるのか」の見出しがページにない")
    if '<h2 id="ck-title">「決まった」と「まだ」を分けて確かめる</h2>' not in html:
        problems.append("「決まった」と「まだ」を分けて確かめるの見出しがページにない")
    timeline_items = len(re.findall(r'<ol class="bg-tl">(.*?)</ol>', html, re.S))
    if timeline_items != 1:
        problems.append("これまでの経緯のタイムラインが1つでない")
    if html.count('<div class="ck">') != len(BACKGROUND_CHECKS):
        problems.append(f"確かめる観点が{len(BACKGROUND_CHECKS)}件でない")
    for _when, _title, _body, links in BACKGROUND_TIMELINE:
        for url, _label in links:
            if f'href="{url}"' not in html:
                problems.append(f"これまでの経緯: 出典リンクが見つからない: {url}")
    for _key, _question, _body, links in BACKGROUND_CHECKS:
        for url, _label in links:
            if f'href="{url}"' not in html:
                problems.append(f"確かめる観点: 出典リンクが見つからない: {url}")
    # 位置も検査する。山なみ図（PLANET_SECTION_START）より後ろにあると、読者が
    # 地図・クイズ・照合コーナーを全部読み終えるまで経緯に出会えない
    # （2026-09-19にオーナー報告で発覚した位置の問題の再発防止）。
    if (
        BACKGROUND_START in html
        and BACKGROUND_ANCHOR in html
        and html.index(BACKGROUND_START) > html.index(BACKGROUND_ANCHOR)
    ):
        problems.append("背景セクションが山なみ図より後ろにある（地図より前に置くこと）")

    if problems:
        raise SystemExit("ビルド検証に失敗しました:\n  - " + "\n  - ".join(problems))


def _sync_issue_counts() -> None:
    """論点カードの件数を貼り直す。ここを外すと再ビルドで件数が消える。"""
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_issue_counts.py"), "consumption-tax-cut"],
        check=True,
    )


def apply_public_counts(html: str, public_theme: Path = PUBLIC_THEME) -> str:
    """公開JSONを正典として、ページ上部の管理対象数字を貼り直す。

    更新候補の生成時は、先に `build_public_registry.py` が候補JSONを作る。
    ここでは投稿本文を読まず、承認対象になる公開JSONだけから収集数・意見数・
    最大論点数を反映する。論点カードは直後の sync_issue_counts.py が同じJSONから同期する。
    """
    data = json.loads(public_theme.read_text(encoding="utf-8"))
    if data.get("theme_id") != "consumption-tax-cut":
        raise ValueError(f"消費税減税の公開JSONではありません: {public_theme}")
    collected = int(data["collected_count"])
    opinions = int(data["opinion_count"])
    named = [issue for issue in data["issues"] if issue["kind"] == "named"]
    if not named:
        raise ValueError("消費税減税の公開JSONに主要論点がありません")
    top_issue = max(named, key=lambda issue: int(issue["count"]))

    replacements = (
        (
            r'<p class="lead">収集したSNS投稿[\d,]+件のうち、分析対象となった意見[\d,]+件をAIが6つの論点に整理しました。',
            f'<p class="lead">収集したSNS投稿{collected}件のうち、分析対象となった意見{opinions}件をAIが6つの論点に整理しました。',
            "ヒーローの収集数・意見数",
        ),
        (
            r'(<div class="thirty-summary".*?<span class="conclusion-count"><b>)[\d,]+(</b>件</span>)',
            rf'\g<1>{int(top_issue["count"])}\2',
            "議論の中心の件数",
        ),
        (
            r'(<div class="panel-title"><h2>SNS反応マップ</h2><span>意見)[\d,]+(件 \|)',
            rf'\g<1>{opinions}\2',
            "反応マップの意見数",
        ),
        (
            r'(重複を除いた)[\d,]+(件を分類し、意見と判定した)[\d,]+(件を論点分析に使用しています。)',
            rf'\g<1>{collected:,}\g<2>{opinions:,}\g<3>',
            "作り方欄の収集数・意見数",
        ),
    )
    for pattern, replacement, label in replacements:
        html, count = re.subn(pattern, replacement, html, count=1, flags=re.S)
        if count != 1:
            raise ValueError(f"公開JSON件数の置換が{count}件です: {label}")
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None, help="分類済みJSON（既定: 累積正典）")
    parser.add_argument("--html-template", type=Path, default=TEMPLATE, help="作り直しの土台にするHTML")
    parser.add_argument("--output-html", type=Path, default=OUTPUT)
    parser.add_argument(
        "--verification-dest",
        type=Path,
        default=None,
        help="件数の出所ファイルの書き出し先（既定: data/verification）",
    )
    parser.add_argument(
        "--conditions-only",
        action="store_true",
        help="調査条件（取得元・期間・件数）だけを公開ページに貼り直す（昇格後に使う）",
    )
    parser.add_argument(
        "--public-counts-only",
        action="store_true",
        help="公開JSONから収集数・意見数・最大論点数だけを貼り直す",
    )
    parser.add_argument(
        "--claim-audit-only",
        action="store_true",
        help="一次資料との突き合わせセクションだけを貼り直す（潮目ウィジェットを落とさない）",
    )
    parser.add_argument(
        "--background-only",
        action="store_true",
        help="「何が、どこまで進んでいるのか」セクションだけを貼り直す（潮目ウィジェットを落とさない）",
    )
    parser.add_argument(
        "--issue-cards-only",
        action="store_true",
        help="「論点ごとのX投稿」セクションだけを貼り直す（潮目ウィジェットを落とさない）",
    )
    parser.add_argument(
        "--skip-issue-counts",
        action="store_true",
        help="sync_issue_counts.py を呼ばない（公開ページ以外へ書き出すときに使う）",
    )
    args = parser.parse_args()

    if args.claim_audit_only:
        page = args.output_html
        rows = json.loads((args.input or CANONICAL).read_text(encoding="utf-8"))
        html = page.read_text(encoding="utf-8")
        audit = claim_audit(rows)
        if CLAIM_START in html and CLAIM_END in html:
            start = html.index(CLAIM_START)
            end = html.index(CLAIM_END) + len(CLAIM_END)
            html = html[:start] + html[end:]
        idx = html.index(CLAIM_ANCHOR) + len(CLAIM_ANCHOR)
        html = html[:idx] + "\n\n" + audit + html[idx:]
        write_claim_provenance(args.verification_dest)
        page.write_text(html, encoding="utf-8")
        print(f"updated claim audit in {page}")
        return 0

    if args.background_only:
        page = args.output_html
        html = page.read_text(encoding="utf-8")
        if BACKGROUND_ANCHOR not in html:
            raise SystemExit("PLANET_SECTION_START が見つかりません（まだ山なみ形式ではない）")
        if BACKGROUND_START in html and BACKGROUND_END in html:
            start = html.index(BACKGROUND_START)
            end = html.index(BACKGROUND_END) + len(BACKGROUND_END)
            html = html[:start] + html[end:]
        idx = html.index(BACKGROUND_ANCHOR)
        html = html[:idx] + background_context() + "\n\n" + html[idx:]
        page.write_text(html, encoding="utf-8")
        print(f"updated background context in {page}")
        return 0

    if args.issue_cards_only:
        page = args.output_html
        html = page.read_text(encoding="utf-8")
        if ISSUE_CARDS_START in html and ISSUE_CARDS_END in html:
            start = html.index(ISSUE_CARDS_START)
            end = html.index(ISSUE_CARDS_END) + len(ISSUE_CARDS_END)
            html = html[:start] + html[end:]
        idx = html.index(ISSUE_CARDS_ANCHOR) + len(ISSUE_CARDS_ANCHOR)
        html = html[:idx] + "\n\n" + issue_cards() + html[idx:]
        page.write_text(html, encoding="utf-8")
        print(f"updated issue cards in {page}")
        return 0

    if args.conditions_only:
        page = args.output_html
        page.write_text(research_conditions(page.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"updated research conditions in {page}")
        return 0

    if args.public_counts_only:
        page = args.output_html
        page.write_text(apply_public_counts(page.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"updated public JSON counts in {page}")
        return 0

    build(
        classified=args.input,
        template=args.html_template,
        output=args.output_html,
        verification_dest=args.verification_dest,
    )
    if not args.skip_issue_counts:
        _sync_issue_counts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
