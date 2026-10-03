"""副首都ページの検索入口を、再生成後も同じ内容で差し戻す。"""

from __future__ import annotations

import html
import json
import re


START = "<!-- FUKUSHUTO_SEARCH_ENTRY_START -->"
END = "<!-- FUKUSHUTO_SEARCH_ENTRY_END -->"
CSS_HREF = "fukushuto-search-entry.css?v=4"
JS_SRC = "fukushuto-search-entry.js?v=2"
OPINION_START = "<!-- FUKUSHUTO_SEARCH_OPINIONS -->"
OPINION_END = "<!-- FUKUSHUTO_SEARCH_OPINIONS_END -->"


FAQS = [
    (
        "副首都法は、もう成立していますか？",
        "はい。2026年7月24日に成立し、7月31日に公布されました。2026年10月3日時点では施行前です。10月30日は施行予定日として示されています。",
    ),
    (
        "副首都は大阪に決まったのですか？",
        "いいえ。成立した法律は指定の仕組みを定めたもので、特定の道府県を副首都に指定していません。大阪が自動的に選ばれたわけではありません。",
    ),
    (
        "副首都は、いつ決まりますか？",
        "指定日は示されていません。2026年10月3日に指定要件の政令・規則案が公表されましたが、要件はまだ確定していません。道府県の申出と国の指定は今後の手続きです。",
    ),
    (
        "首都中枢機能代替地域と副首都は同じですか？",
        "別です。代替地域は首都中枢機能の一部を担います。副首都はその全部または大部分を代替し、経済圏の中核も担う道府県です。法律は両者を分けています。",
    ),
    (
        "大阪都構想と副首都法は同じ制度ですか？",
        "別です。大阪都構想は大阪市を廃止して特別区を設ける構想です。成立した副首都法には、道府県名を「都」へ変える規定はありません。",
    ),
    (
        "副首都の整備費は4兆〜7.5兆円ですか？",
        "確定した総額ではありません。4兆〜7.5兆円は過去の首都機能移転の試算として国会審議で引用された数字です。今回の制度の整備総額は、2026年10月3日時点で示されていません。",
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
        "fact": "2026年10月3日の現在地",
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


# 自治体の一次資料で確認できた動き。国の「公式候補地一覧」ではない。
CANDIDATE_REGIONS = [
    {
        "name": "大阪府・大阪市", "stage": "aiming", "label": "構想を公表",
        "detail": "府市が「大阪の副首都構想」を公表。国による指定はまだ。",
        "date": "2026年2月12日", "source": "大阪市", "url": "https://www.city.osaka.lg.jp/fukushutosuishin/page/0000679231.html",
    },
    {
        "name": "福岡県", "stage": "aiming", "label": "指定を目指す",
        "detail": "副知事を長とする検討チームを設置し、福岡市・北九州市と連携。",
        "date": "2026年8月7日", "source": "福岡県", "url": "https://www.pref.fukuoka.lg.jp/contents/fukuoka-fukusyuto.html",
    },
    {
        "name": "愛知県・名古屋市", "stage": "aiming", "label": "指定を目指す",
        "detail": "知事と市長が指定を目指すと表明。県市の連携協議会を開催。",
        "date": "2026年8月10日", "source": "愛知県", "url": "https://www.pref.aichi.jp/site/chiji/20260810.html",
    },
    {
        "name": "北海道・札幌市", "stage": "aiming", "label": "指定を目指す",
        "detail": "知事と市長が国に提案・要望し、指定に向けて準備。",
        "date": "2026年8月27日", "source": "北海道", "url": "https://www.pref.hokkaido.lg.jp/ss/ssa/270000.html",
    },
    {
        "name": "群馬県", "stage": "aiming", "label": "知事が意思表明",
        "detail": "知事が立候補の意思を表明。正式な申出には県議会の議決が必要。",
        "date": "2026年7月30日", "source": "群馬県", "url": "https://www.pref.gunma.jp/site/chiji/769457.html",
    },
    {
        "name": "広島県", "stage": "considering", "label": "申出を検討",
        "detail": "関係自治体と意見交換を開始。正式に申し出るかは今後判断。",
        "date": "2026年8月25日", "source": "広島県", "url": "https://www.pref.hiroshima.lg.jp/site/kishakaiken/gpc-20260825.html",
    },
    {
        "name": "宮城県・仙台市", "stage": "considering", "label": "要件を待って判断",
        "detail": "知事は政令の内容を見てから判断する考えを示した。",
        "date": "2026年8月26日", "source": "宮城県", "url": "https://www.pref.miyagi.jp/site/chiji-kaiken/kk-260826.html",
    },
    {
        "name": "京都府", "stage": "not_preparing", "label": "単独申出の準備なし",
        "detail": "知事は府単独で手を挙げる準備をしていないと説明。",
        "date": "2026年7月31日", "source": "京都府", "url": "https://www.pref.kyoto.jp/koho/kaiken/260731.html",
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
    candidate_rows = "\n".join(
        f'''        <article class="fuk-candidate__row" data-candidate-stage="{region["stage"]}">
          <div class="fuk-candidate__place"><h4>{html.escape(region["name"])}</h4><span class="fuk-candidate__stage fuk-candidate__stage--{region["stage"]}">{html.escape(region["label"])}</span></div>
          <p>{html.escape(region["detail"])}</p>
          <div class="fuk-candidate__source"><time>{html.escape(region["date"])}</time><a href="{html.escape(region["url"], quote=True)}" target="_blank" rel="noopener noreferrer" data-fuk-entry-link="candidate-{region["stage"]}">{html.escape(region["source"])}の資料を見る</a></div>
        </article>'''
        for region in CANDIDATE_REGIONS
    )
    stage_counts = {stage: sum(region["stage"] == stage for region in CANDIDATE_REGIONS) for stage in ("aiming", "considering", "not_preparing")}
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
        <p class="fuk-now__eyebrow"><span>2026年10月3日確認</span> 副首都法の現在地</p>
        <h2 id="fuk-now-title">副首都はいつ、どこに決まる？<br><em>大阪はまだ指定されていません。</em></h2>
      </div>
      <p>副首都法は2026年7月に成立しました。指定日は決まっておらず、大阪を含めて指定済みの道府県はありません。自治体の構想と国の指定を分けて確認できます。</p>
    </header>

    <ol class="fuk-status" aria-label="副首都法の進み具合">
      <li class="is-done"><span>1</span><small>2026年7月</small><strong>成立・公布</strong><p>法律の枠組みが決まった</p></li>
      <li class="is-current" aria-current="step"><span>2</span><small>2026年10月3日現在</small><strong>要件案を公表</strong><p>10月16日まで意見募集。施行前</p></li>
      <li><span>3</span><small>時期は未定</small><strong>指定前</strong><p>どの道府県かは未決定</p></li>
    </ol>
    <p class="fuk-now__policy-note">指定要件の政令・規則案が公表されました。要件と指定先はまだ確定していません。<a href="https://public-comment.e-gov.go.jp/pcm/detail?CLASSNAME=PCMMSTDETAIL&amp;Mode=0&amp;id=060261003" target="_blank" rel="noopener noreferrer" data-fuk-entry-link="decree-proposal">意見募集の資料を見る</a></p>

    <section class="fuk-candidate" id="fukushuto-candidates" aria-labelledby="fuk-candidate-title">
      <div class="fuk-candidate__heading"><div><p>指定状況を追う</p><h3 id="fuk-candidate-title">各地は、今どの段階？</h3></div><p>自治体の公表と国の指定を分けて見ます。最終確認は2026年10月3日です。</p></div>
      <div class="fuk-candidate__national"><div><span>国の指定</span><strong>0<small>道府県</small></strong></div><p>副首都法は10月30日施行予定。現在はどの道府県も指定されていません。</p><a href="https://laws.e-gov.go.jp/law/508AC1000000078" target="_blank" rel="noopener noreferrer" data-fuk-entry-link="candidate-law">法律の指定手続きを確認</a></div>
      <div class="fuk-candidate__toolbar" role="group" aria-label="各地の動きを絞り込む">
        <button type="button" data-fuk-candidate-filter="all" aria-pressed="true">すべて <span>{len(CANDIDATE_REGIONS)}</span></button>
        <button type="button" data-fuk-candidate-filter="aiming" aria-pressed="false">指定を目指す・意思表明 <span>{stage_counts["aiming"]}</span></button>
        <button type="button" data-fuk-candidate-filter="considering" aria-pressed="false">検討・要件待ち <span>{stage_counts["considering"]}</span></button>
        <button type="button" data-fuk-candidate-filter="not_preparing" aria-pressed="false">単独申出の準備なし <span>{stage_counts["not_preparing"]}</span></button>
      </div>
      <p class="fuk-candidate__result" aria-live="polite"><span id="fuk-candidate-visible-count">{len(CANDIDATE_REGIONS)}</span>地域を表示</p>
      <div class="fuk-candidate__rows">
{candidate_rows}
      </div>
      <p class="fuk-candidate__foot">掲載したのは一次資料で動きを確認した地域です。全国の網羅的な一覧や、国が認定した候補地一覧ではありません。次は意見募集の結果と、10月末に公布予定の政府令を確認します。</p>
    </section>

    <div class="fuk-topic-switcher" id="fuk-entry-switcher">
      <div class="fuk-topic-tabs" role="tablist" aria-label="知りたい論点を選ぶ">
{topic_tabs}
      </div>
      <div class="fuk-answer-panels" aria-live="polite">
{topic_panels}
      </div>
    </div>

    <section class="fuk-problems" id="fukushuto-problems" aria-labelledby="fuk-problems-title">
      <header><p>もう一つの入口</p><h2 id="fuk-problems-title">副首都法案の問題点は何？</h2><p>制度の目的と、なお確かめるべき点を論点ごとに並べました。</p></header>
      <div class="fuk-problems__list">
        <article><span>防災</span><h3>東京と同時に被災しないか</h3><p>首都機能の代替が目的です。候補地の災害リスクと、実際に機能を移せるかが問われます。</p><button type="button" data-fuk-mountain="fukushuto-disaster-preparedness">防災をめぐる意見を見る</button></article>
        <article><span>決め方</span><h3>大阪ありきで決まらないか</h3><p>法律は大阪を指定していません。道府県の申出と国の指定を、今後の手続きで確認する必要があります。</p><button type="button" data-fuk-mountain="fukushuto-location">候補地をめぐる意見を見る</button></article>
        <article><span>費用</span><h3>いくらかかり、何を優先するか</h3><p>今回の制度の整備総額は示されていません。4兆〜7.5兆円は過去の首都機能移転の試算です。</p><button type="button" data-fuk-mountain="fukushuto-finance">費用をめぐる意見を見る</button></article>
      </div>
      <div class="fuk-problems__sources"><a href="https://laws.e-gov.go.jp/law/508AC1000000078" target="_blank" rel="noopener noreferrer" data-fuk-entry-link="problem-law">副首都法の条文</a><a href="https://www.mlit.go.jp/kokudokeikaku/iten/relocation/qa/qa_step4_02_01.html" target="_blank" rel="noopener noreferrer" data-fuk-entry-link="problem-cost">過去の移転費用の試算</a><a href="#stance-glance" data-fuk-entry-link="stances">SNS {OPINION_START}{opinions:,}{OPINION_END}件の内訳</a></div>
      <p class="fuk-problems__note">SNSの件数は収集した公開投稿の分類結果で、世論調査ではありません。</p>
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
    source = re.sub(r'<link rel="stylesheet" href="fukushuto-search-entry\.css\?v=\d+">\n', "", source)
    source = re.sub(r'<script src="fukushuto-search-entry\.js\?v=\d+" defer></script>\n', "", source)
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
