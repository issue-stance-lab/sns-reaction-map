from bs4 import BeautifulSoup
from pathlib import Path
import json,re,html,datetime
from glance_chart import annotated_graph
E=lambda x:html.escape(str(x),quote=True)
def add_public_trends(markup,root,source_html):
 src=BeautifulSoup(source_html,'html.parser')
 card=src.select_one('.trend-card');script=card.select_one('script');js=script.string
 data=json.loads(re.search(r'const panels = (.*?);\n',js).group(1));d=data['issue'];rounds=d['rounds']
 script=card.select_one('script')
 js=js.replace('return {draw, finish, replay() { if (!pending) play(); }};','return {draw, finish, replay() { play(); }};')
 js=js.replace('  window.addEventListener("beforeprint",', '''  const disclosure = document.getElementById('trends');
  disclosure.querySelector(':scope > summary').addEventListener('click', (event) => {
    event.preventDefault(); disclosure.open=!disclosure.open;
    Object.keys(charts).forEach(k => charts[k].finish());
    if (disclosure.open) { const k=Object.keys(nodes).find(k=>!nodes[k].hidden); if(k){charts[k].draw();charts[k].replay();} }
  });
  document.querySelectorAll('.issue-glance-link').forEach(a=>a.addEventListener('click',event=>{event.preventDefault();disclosure.open=true;show('issue');disclosure.scrollIntoView({behavior:'instant'});}));
  window.addEventListener("beforeprint",''')
 js=js.replace('if (!nodes[k].hidden && charts[k]) charts[k].draw();','if (!nodes[k].hidden && charts[k]) { charts[k].draw(); if(disclosure.open) charts[k].replay(); }')
 script.string=js
 # Absolute URLs for any retained source links.
 for a in card.select('[href]'):
  if not a['href'].startswith(('http','#')):a['href']='https://sns-reaction-map.jp/'+a['href']
 s=BeautifulSoup(markup,'html.parser');rich=s.select_one('#trends > .rich-content');rich.clear();rich.append(card)
 css='\n'.join(x.get_text() for x in src.select('style'));css=css[css.index('.trend-card'):css.index('/* TREND_CARD_END */')]
 style=s.new_tag('style');style.string=css+'''\n#trends>.rich-content{padding:12px 0 24px;max-width:none}.trend-card{margin:0;padding:22px 0;border:0;box-shadow:none;border-radius:0}.trend-card h2{font-family:var(--sans);font-size:24px}.trend-card .trend-stage{max-width:100%}.issue-glance{margin:0 0 32px;padding:23px 26px;background:#f7faff;border-radius:0;display:grid;grid-template-columns:1fr 1.3fr;gap:12px 30px}.issue-glance .eyebrow{margin:0}.issue-glance h3{font-size:20px;margin:7px 0 14px}.glance-number{font-size:36px;font-weight:850;line-height:1.2;color:var(--topic)}.glance-number small{font-size:15px}.glance-number span{color:#a4b0be;font-size:24px;padding:0 12px}.issue-glance svg{width:100%;height:auto;color:var(--topic);align-self:center}.issue-glance .fine{grid-column:1/-1;margin:0}.issue-glance-link{font-size:12px;display:inline-block;margin-top:14px}.issue-glance text{font:12px var(--sans);fill:#59677c}@media(max-width:650px){.issue-glance{padding:20px 15px;grid-template-columns:1fr;gap:14px}.issue-glance h3{font-size:18px}.glance-number{font-size:30px}.trend-card h2{font-size:21px}.trend-card{padding:15px 0}.trend-card .trend-table-scroll{max-width:100%}}'''+'''
.issue-glance{display:block;background:#fff;border-top:1px solid #dce6ee;border-bottom:1px solid #dce6ee;padding:22px 0}.glance-head{display:flex;justify-content:space-between;align-items:baseline;gap:16px}.glance-head>.fine{white-space:nowrap}.issue-glance h3{margin-bottom:6px}.issue-glance .glance-chart-mobile{display:none}.issue-glance .gc-axis{font-size:12px;fill:#75869c}.issue-glance .gc-first{font-size:20px;font-weight:800;fill:var(--ink);paint-order:stroke;stroke:white;stroke-width:5px;stroke-linejoin:round}.issue-glance .gc-latest{font-size:30px;font-weight:850;fill:var(--ink)}.issue-glance .gc-count{font-size:14px;font-weight:400;fill:#75869c}.issue-glance .gc-name{font-size:13px;font-weight:700;fill:var(--ink)}.glance-source{display:flex;justify-content:space-between;align-items:center;gap:12px;border-top:1px solid #dce6ee;padding:9px 0 4px;font-size:12px}.glance-source .issue-glance-link{margin:0}.issue-glance>.fine{font-size:11px}@media(max-width:650px){.issue-glance .glance-chart-desktop{display:none}.issue-glance .glance-chart-mobile{display:block}.issue-glance{padding:18px 0}.issue-glance .gc-latest{font-size:27px}.glance-head{gap:8px}.glance-head>.fine{font-size:10px}.glance-source{font-size:11px}.glance-source .issue-glance-link{font-size:11px}}
''';s.head.append(style)
 reading=s.select_one('#reading');s.select_one('#map').insert_after(reading.extract())
 names=['教員の働き方','制度・移行プロセス','教育的意義・機会','受け皿・指導者','費用・家庭負担',None,'地域格差']
 dates=[datetime.date.fromisoformat(r['d']) for r in rounds]
 period=f'{dates[0].year}年{dates[0].month}月{dates[0].day}日〜{dates[-1].year}年{dates[-1].month}月{dates[-1].day}日'
 summary=s.select_one('#trends > summary')
 for node in list(summary.find_all(string=True)):
  if '回の収集' in str(node):node.replace_with(re.sub(r'\d+回の収集',str(len(data['stance']['rounds']))+'回の収集',str(node)))
 for i,name in enumerate(names):
  panel=s.select_one(f'.issue-panel[data-issue="{i}"]')
  if name is None:continue
  j=d['labels'].index(name)
  svg=annotated_graph(name,rounds,j)+annotated_graph(name,rounds,j,True)
  glance=f'<section class="issue-glance"><header class="glance-head"><div><p class="eyebrow">ひと目で見る、この論点の推移</p><h3>{E(name)}</h3></div><span class="fine">{len(rounds)}回の収集</span></header>{svg}<div class="glance-source"><strong>出典：SNS反応まっぷ</strong><a class="issue-glance-link" href="#trends">詳しいグラフを開く ↓</a></div><p class="fine">{period}。「その他」を除く意見の投稿に占める割合と件数です。世論全体の変化を示すものではありません。</p></section>'
  panel.select_one('.issue-heading').insert_after(BeautifulSoup(glance,'html.parser'))
 (root/'evidence/published-trends-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 return str(s)
