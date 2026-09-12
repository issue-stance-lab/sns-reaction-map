"""Reader sections following the shared topic-page order."""
import base64
import html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIGURES={'定義・中身':'teigi','候補地':'kouhochi','都構想・維新':'tokoso','防災・災害':'bousai','費用・財源':'hiyou','優先順位':'yusen'}
DESCRIPTIONS={'定義・中身':'副首都にどの機能を持たせ、誰が何を決めるのか。制度の中身と進め方をめぐる論点です。','候補地':'どの地域が代わりを担えるのか。候補地ごとの条件や別の地域を選ぶ提案を扱います。','都構想・維新':'大阪都構想との関係や、政策を進める政党・政治姿勢への評価を扱います。','防災・災害':'東京と同時に被災しないか、災害時に機能を引き継げるかをめぐる論点です。','費用・財源':'整備と維持にかかる費用、国や地域の負担をめぐる論点です。','優先順位':'副首都の整備と、暮らしや他の政策のどちらを先に進めるかをめぐる論点です。','その他':'七つの区分のうち、ほかの六論点に収まらない意見をまとめています。'}
def render_sections(data):
 out=['<section class="panel" id="issue-cards"><div class="panel-title"><h2>論点ごとに、なかを見る</h2><span>図解で論点を確かめる</span></div>']
 for i,item in enumerate(data['issues']):
  name=item['name'];out.append(f'<article class="reader-issue" id="reader-issue-{i}"><h3>{html.escape(name)} <small>{item["after"]:,}件</small></h3><p>{DESCRIPTIONS[name]}</p>')
  if name in FIGURES:
   path=ROOT/'docs/images/topics/fukushuto'/f'fukushuto-infographic-wide-{FIGURES[name]}.webp'
   image='data:image/webp;base64,'+base64.b64encode(path.read_bytes()).decode()
   out.append(f'<button type="button" class="figure-open" aria-label="{html.escape(name)}の図解を拡大"><img src="{image}" alt="{html.escape(name)}の論点図解" loading="lazy"></button>')
  out.append('<a href="#planet-block">↑ 地図へ戻る</a></article>')
 out.append('</section><dialog id="figure-dialog"><button type="button" id="figure-close">閉じる</button><img alt=""></dialog>')
 out.append('<section class="panel" id="reader-method"><div class="panel-title"><h2>このページの作り方</h2></div><p>Yahoo!リアルタイム検索で収集した公開投稿を読み、意見の中心となる論点と、構想・法案や制度・候補地それぞれへの評価を整理しています。世論調査ではなく、収集したSNS投稿のサンプルです。</p><p>図解は論点を理解するための説明画像です。制度の現状は冒頭の出典、投稿の件数は各論点の表示をご覧ください。</p></section>')
 out.append('<section class="panel" id="related-topics"><div class="panel-title"><h2>次に見るテーマ</h2></div><div class="reader-related">')
 for slug,label in [('bukatsu-chiiki','部活動の地域移行'),('bike-blue-ticket','自転車の青切符'),('elderly-license-revocation','高齢者の免許返納')]:
  out.append(f'<a href="https://sns-reaction-map.jp/{slug}-reaction-map.html?utm_source=fukushuto&amp;utm_medium=related&amp;utm_campaign=topic">{label} →</a>')
 out.append('</div></section><section class="panel" id="detail-data"><h2>詳細データ</h2><details><summary>論点別の件数を見る</summary><table><thead><tr><th>論点</th><th>件数</th></tr></thead><tbody>')
 for x in data['issues']:out.append(f'<tr><td>{html.escape(x["name"])}</td><td>{x["after"]:,}</td></tr>')
 out.append('</tbody></table></details></section>')
 return ''.join(out)
