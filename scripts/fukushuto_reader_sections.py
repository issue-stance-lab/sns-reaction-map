"""Reader sections following the shared topic-page order."""
import base64
import html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIGURES={'定義・中身':'teigi','候補地':'kouhochi','都構想・維新':'tokoso','防災・災害':'bousai','費用・財源':'hiyou','優先順位':'yusen'}
DESCRIPTIONS={'定義・中身':'副首都にどの機能を持たせ、誰が何を決めるのか。制度の中身と進め方をめぐる論点です。','候補地':'どの地域が代わりを担えるのか。候補地ごとの条件や別の地域を選ぶ提案を扱います。','都構想・維新':'大阪都構想との関係や、政策を進める政党・政治姿勢への評価を扱います。','防災・災害':'東京と同時に被災しないか、災害時に機能を引き継げるかをめぐる論点です。','費用・財源':'整備と維持にかかる費用、国や地域の負担をめぐる論点です。','優先順位':'副首都の整備と、暮らしや他の政策のどちらを先に進めるかをめぐる論点です。','その他':'七つの区分のうち、ほかの六論点に収まらない意見をまとめています。'}

def render_overview(data):
    """The four small summary cards used by the other topic pages."""
    issues=sorted(data['issues'],key=lambda x:x['after'],reverse=True)
    concept=data['concept']
    cards=[('収集した公開投稿',f"{data['original_total']:,}件",'Yahoo!リアルタイム検索で取得した投稿'),
           ('分析対象の意見',f"{data['candidate_opinions']:,}件",'本文を確認して意見とした投稿'),
           ('最も語られた論点',f"{issues[0]['name']} {issues[0]['after']:,}件",'各投稿の中心となる論点を一つずつ集計'),
           ('構想への評価',f"肯定 {concept['肯定']:,}件",f"否定 {concept['否定']:,}件・未表明 {concept['未表明']:,}件")]
    out=['<section class="stats overview" aria-label="このテーマの注目ポイント">']
    for i,(label,value,note) in enumerate(cards):
        out.append(f'<article class="stat stat-{i}"><span>{label}</span><strong>{html.escape(value)}</strong><p>{html.escape(note)}</p><i aria-hidden="true"></i></article>')
    return ''.join(out)+'</section><aside class="research-conditions"><strong>このマップの元データ：</strong>公開投稿を収集したSNS反応サンプルです。世論調査ではありません。構想・法案や制度・候補地への評価は、同じ投稿でも別々に記録しています。</aside>'
def render_sections(data):
 out=['<section class="panel" id="issue-cards"><div class="panel-title"><h2>論点ごとに、なかを見る</h2><span>図解で論点を確かめる</span></div><p class="reader-lead">副首都の議論は、必要性・制度の中身・候補地・防災などに分かれています。山なみで気になった論点を、図解と説明で確かめてください。</p>']
 for i,item in enumerate(data['issues']):
  name=item['name'];out.append(f'<article class="reader-issue" id="reader-issue-{i}"><h3>{html.escape(name)} <small>{item["after"]:,}件</small></h3><p>{DESCRIPTIONS[name]}</p>')
  out.append(f'<div class="reader-share"><span style="width:{min(100,max(2,100*item["after"]/max(1,data["candidate_opinions"]))):.1f}%"></span></div>')
  if name in FIGURES:
   path=ROOT/'docs/images/topics/fukushuto'/f'fukushuto-infographic-wide-{FIGURES[name]}.webp'
   image='data:image/webp;base64,'+base64.b64encode(path.read_bytes()).decode()
   out.append(f'<button type="button" class="figure-open" aria-label="{html.escape(name)}の図解を拡大"><img src="{image}" alt="{html.escape(name)}の論点図解" loading="lazy"></button>')
  out.append('<a href="#planet-block">↑ 地図へ戻る</a></article>')
 out.append('</section><dialog id="figure-dialog"><button type="button" id="figure-close">閉じる</button><img alt=""></dialog>')
 out.append('<section class="panel vote-panel" id="vote-section" data-vote-topic="fukushuto-target-v1"><div class="panel-title"><h2>あなたが一番気になる「論点」は？</h2><span>ここまで読んだうえで</span></div><p class="vote-intro">副首都の必要性、制度の中身、候補地。あなたが気になる論点を一つ選び、次に考えを選んでください。</p><p class="vote-step"><b>1</b> 気になる論点を選ぶ</p><div class="vote-issues">')
 for i,item in enumerate(data['issues']):
  out.append(f'<button type="button" data-vote-issue="{i}">{html.escape(item["name"])}</button>')
 out.append('</div><div class="vote-step-two" hidden><p class="vote-step"><b>2</b> あなたの考えに近いもの</p><div class="vote-stances"><button type="button">肯定・推進</button><button type="button">条件付き・慎重</button><button type="button">否定・反対</button></div></div><p class="vote-status" role="status" aria-live="polite"></p><p class="note">この確認版では回答を送信せず、画面の動作だけを確認できます。</p></section>')
 out.append('<section class="panel" id="reader-method"><div class="panel-title"><h2>このページの作り方</h2><span>編集・分析情報</span></div><p>Yahoo!リアルタイム検索で収集した公開投稿を読み、意見の中心となる論点と、構想・法案や制度・候補地それぞれへの評価を整理しています。世論調査ではなく、収集したSNS投稿のサンプルです。</p><div class="method-grid"><div><h3>SNS投稿の収集方法</h3><p>副首都、候補地、防災、費用などの検索語で公開投稿を収集しました。</p></div><div><h3>AIを使用した工程</h3><p>関連性・意見性・論点の整理を補助に使い、本文を確認して表示対象を決めています。</p></div><div><h3>数字の読み方</h3><p>同じ投稿が複数の地域を評価する場合があります。地域別の件数を合計しません。</p></div></div><p class="reader-caution"><strong>注意：</strong>未表明は中立票ではありません。法案・制度への評価と候補地への評価を一つの賛否にまとめていません。</p></section>')
 out.append('<section class="panel" id="related-topics"><div class="panel-title"><h2>次に見るテーマ</h2><span>他のテーマ</span></div><div class="reader-related">')
 for slug,label in [('bukatsu-chiiki','部活動の地域移行'),('bike-blue-ticket','自転車の青切符'),('elderly-license-revocation','高齢者の免許返納')]:
  hero_name='bukatsu-hero.webp' if slug == 'bukatsu-chiiki' else f'{slug}-hero.webp'
  image=base64.b64encode((ROOT/'docs/images/topics'/slug/hero_name).read_bytes()).decode()
  out.append(f'<a class="related-card" href="https://sns-reaction-map.jp/{slug}-reaction-map.html?utm_source=fukushuto&amp;utm_medium=related&amp;utm_campaign=topic"><img src="data:image/webp;base64,{image}" alt="" loading="lazy"><span>{label} →</span></a>')
 out.append('</div></section><section class="panel" id="detail-data"><h2>詳細データ</h2><details><summary>論点別の件数を見る</summary><table><thead><tr><th>論点</th><th>件数</th></tr></thead><tbody>')
 for x in data['issues']:out.append(f'<tr><td>{html.escape(x["name"])}</td><td>{x["after"]:,}</td></tr>')
 out.append('</tbody></table></details></section>')
 return ''.join(out)
