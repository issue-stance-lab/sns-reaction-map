"""副首都ページの検索入口を、再生成後も同じ内容で差し戻す。"""

from __future__ import annotations

import json
import re


START = "<!-- FUKUSHUTO_SEARCH_ENTRY_START -->"
END = "<!-- FUKUSHUTO_SEARCH_ENTRY_END -->"
CSS_HREF = "fukushuto-search-entry.css?v=1"
JS_SRC = "fukushuto-search-entry.js?v=1"
OPINION_START = "<!-- FUKUSHUTO_SEARCH_OPINIONS -->"
OPINION_END = "<!-- FUKUSHUTO_SEARCH_OPINIONS_END -->"


FAQS = [
    (
        "副首都法は、もう成立していますか？",
        "はい。2026年7月24日に成立し、7月31日に公布されました。2026年10月1日時点では施行前で、施行日は10月30日です。",
    ),
    (
        "副首都は大阪に決まったのですか？",
        "いいえ。成立した法律は指定の仕組みを定めたもので、特定の道府県を副首都に指定していません。大阪が自動的に選ばれたわけではありません。",
    ),
    (
        "副首都は、いつ決まりますか？",
        "具体的な指定日は示されていません。施行後、政府が基本方針や指定要件を定め、道府県が議会の議決を経て申し出た後に、指定の手続きが進みます。",
    ),
    (
        "首都中枢機能代替地域と副首都は同じですか？",
        "別です。代替地域は首都中枢機能の一部を担う地域、副首都は全部または大部分を代替し、経済圏の中核も担う道府県です。法律は両者を分けています。",
    ),
    (
        "大阪都構想と副首都法は同じ制度ですか？",
        "別です。大阪都構想は大阪市を廃止して特別区を設ける構想です。成立した副首都法には、道府県名を「都」へ変える規定はありません。",
    ),
    (
        "副首都の整備費は4兆〜7.5兆円ですか？",
        "確定した総額ではありません。4兆〜7.5兆円は過去の首都機能移転の試算として国会審議で引用された数字です。今回の制度の整備総額は、2026年10月1日時点で示されていません。",
    ),
]

ENTRY_TOPICS = [
    {
        "key": "definition",
        "issue_id": "fukushuto-definition",
        "label": "制度・中身",
        "question": "何が変わる？",
        "headline": "国が基本方針を作り、道府県を指定する制度が始まる",
        "body": "災害時の中枢機能の代替と、平時の経済拠点づくりを進めます。法律の成立だけで、首都機能の移転が始まるわけではありません。",
        "fact": "法律で決まったこと",
        "points": ["副首都の指定手続き", "基本方針と整備方針", "国の推進本部の設置"],
        "cta": "「制度・中身」の山を開く",
    },
    {
        "key": "location",
        "issue_id": "fukushuto-location",
        "label": "候補地",
        "question": "候補地は？",
        "headline": "大阪を含め、正式な指定はまだない",
        "body": "対象は都市ではなく道府県です。道府県の申出には議会の議決が必要で、国が要件に照らして指定します。",
        "fact": "2026年10月1日の現在地",
        "points": ["指定済みの道府県はない", "大阪への決定規定はない", "具体的な指定時期も未定"],
        "cta": "「候補地」の山を開く",
    },
    {
        "key": "osaka",
        "issue_id": "fukushuto-osaka-restoration",
        "label": "大阪都構想",
        "question": "都構想との関係は？",
        "headline": "副首都法と大阪都構想は別の制度",
        "body": "成立法に「大阪を副首都にする」「道府県名を都へ変える」という規定はありません。大阪市の特別区設置とも分けて確認します。",
        "fact": "混ぜずに見ること",
        "points": ["副首都法は国の制度", "都構想は特別区設置の構想", "住民投票は副首都法への投票ではない"],
        "cta": "「都構想・維新」の山を開く",
    },
    {
        "key": "finance",
        "issue_id": "fukushuto-finance",
        "label": "費用・財源",
        "question": "費用はいくら？",
        "headline": "今回の整備総額は、まだ示されていない",
        "body": "4兆〜7.5兆円は過去の首都機能移転の試算です。大阪府の既存予算とも分けて読む必要があります。",
        "fact": "数字の読み分け",
        "points": ["今回の公式総額は未提示", "過去の移転試算とは別", "大阪府予算は内訳を確認"],
        "cta": "「費用・財源」の山を開く",
    },
]


def faq_json_ld() -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in FAQS
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).replace("</", "<\\/")


def render(opinions: int) -> str:
    faq_html = "\n".join(
        f"""        <details data-fuk-entry-faq><summary>{question}<span aria-hidden=\"true\"></span></summary><div><p>{answer}</p></div></details>"""
        for question, answer in FAQS
    )
    topic_tabs = "\n".join(
        f'''      <button type="button" role="tab" id="fuk-entry-tab-{topic["key"]}" aria-controls="fuk-entry-panel-{topic["key"]}" aria-selected="{str(index == 0).lower()}" tabindex="{0 if index == 0 else -1}" data-fuk-entry-tab="{topic["key"]}" data-issue-id="{topic["issue_id"]}"><span>{topic["question"]}</span><b>{topic["label"]}</b><small>選んで確認</small></button>'''
        for index, topic in enumerate(ENTRY_TOPICS)
    )
    topic_panels = "\n".join(
        f'''      <article class="fuk-answer" role="tabpanel" id="fuk-entry-panel-{topic["key"]}" aria-labelledby="fuk-entry-tab-{topic["key"]}" data-fuk-entry-panel="{topic["key"]}" data-issue-id="{topic["issue_id"]}">
        <div class="fuk-answer__copy"><p>{topic["question"]}</p><h3>{topic["headline"]}</h3><p>{topic["body"]}</p></div>
        <div class="fuk-answer__facts"><b>{topic["fact"]}</b><ul>{''.join(f'<li>{point}</li>' for point in topic["points"])}</ul></div>
        <footer><button type="button" data-fuk-mountain="{topic["issue_id"]}"><span aria-hidden="true">⌁</span>{topic["cta"]}<small>理由・投稿・一次資料まで移動</small></button></footer>
      </article>'''
        for topic in ENTRY_TOPICS
    )
    return f"""{START}
<script id="fukushuto-faq-json-ld" type="application/ld+json">
{faq_json_ld()}
</script>
<section id="fukushuto-now" class="fuk-now" aria-labelledby="fuk-now-title">
  <div class="fuk-now__inner">
    <header class="fuk-now__header">
      <div>
        <p class="fuk-now__eyebrow"><span>3分で分かる</span> 副首都法の現在地</p>
        <h2 id="fuk-now-title">法律は成立。<br><em>大阪への指定は、まだ。</em></h2>
      </div>
      <p>成立したのは「副首都を選び、整備するための仕組み」です。首都が移ったわけでも、候補地が決まったわけでもありません。まず制度・場所・費用を分けて見ます。</p>
    </header>

    <ol class="fuk-status" aria-label="副首都法の進み具合">
      <li class="is-done"><span>1</span><small>2026年7月</small><strong>成立・公布</strong><p>法律の枠組みが決まった</p></li>
      <li class="is-current" aria-current="step"><span>2</span><small>2026年10月1日現在</small><strong>施行前</strong><p>10月30日に施行</p></li>
      <li><span>3</span><small>時期は未定</small><strong>指定前</strong><p>どの道府県かは未決定</p></li>
    </ol>

    <div class="fuk-topic-switcher" id="fuk-entry-switcher">
      <div class="fuk-topic-tabs" role="tablist" aria-label="知りたい論点を選ぶ">
{topic_tabs}
      </div>
      <div class="fuk-answer-panels" aria-live="polite">
{topic_panels}
      </div>
    </div>

    <section class="fuk-tradeoffs" aria-labelledby="fuk-tradeoffs-title">
      <header><p>メリット・デメリット</p><h3 id="fuk-tradeoffs-title">期待と懸念は、同じ基準で比べる</h3></header>
      <div class="fuk-tradeoffs__grid">
        <div><b>期待されること</b><ul><li>大災害でも政治・行政・経済の機能を続ける</li><li>東京への人口・経済機能の集中を分散する</li></ul></div>
        <div><b>指摘される懸念</b><ul><li>候補地との同時被災や、実際の代替能力</li><li>整備費・維持費、政策の優先順位</li></ul></div>
      </div>
      <nav aria-label="メリットと懸念の詳しい論点"><button type="button" data-fuk-mountain="fukushuto-disaster-preparedness">防災・同時被災の山を開く</button><button type="button" data-fuk-mountain="fukushuto-priority">政策の優先順位の山を開く</button><a href="#stance-glance" data-fuk-entry-link="stances">SNS {OPINION_START}{opinions:,}{OPINION_END}件の内訳を見る</a></nav>
      <p class="fuk-now__note">このページのSNS件数は、検索語と収集時点に基づく公開投稿の分類です。社会全体の世論調査ではありません。</p>
    </section>

    <section class="fuk-faq" id="fukushuto-faq" aria-labelledby="fuk-faq-title">
      <header><p>よくある質問</p><h3 id="fuk-faq-title">短い答えで確認する</h3></header>
      <div class="fuk-faq__list">
{faq_html}
      </div>
      <p class="fuk-faq__sources"><a href="https://laws.e-gov.go.jp/law/508AC1000000078" target="_blank" rel="noopener noreferrer">成立した法律（e-Gov）</a><a href="https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/keika/1DE2ACE.htm" target="_blank" rel="noopener noreferrer">審議経過（衆議院）</a></p>
    </section>
  </div>
</section>
{END}"""


def apply(source: str, opinions: int) -> str:
    """入口を挿入または更新する。何度呼んでも同じ結果になる。"""
    css = f'<link rel="stylesheet" href="{CSS_HREF}">'
    script = f'<script src="{JS_SRC}" defer></script>'
    source = source.replace(css + "\n", "").replace(script + "\n", "")
    if source.count("</head>") != 1:
        raise ValueError("副首都の検索入口アセットを置くhead要素が1つではありません")
    source = source.replace("</head>", css + "\n" + script + "\n</head>", 1)
    block = render(opinions)
    if START in source or END in source:
        if source.count(START) != 1 or source.count(END) != 1:
            raise ValueError("副首都の検索入口マーカーが1組ではありません")
        return re.sub(re.escape(START) + r".*?" + re.escape(END), block, source, count=1, flags=re.S)
    anchor = "<main>"
    if source.count(anchor) != 1:
        raise ValueError("副首都の検索入口を置くmain要素が1つではありません")
    return source.replace(anchor, anchor + "\n\n" + block, 1)
