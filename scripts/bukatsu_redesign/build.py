from pathlib import Path
from bs4 import BeautifulSoup
import json,html,hashlib,collections
import os
R=Path(os.environ['BUKATSU_BUILD_ROOT'])
B=R.parent
MAIN=Path(os.environ['BUKATSU_REPO_ROOT'])
from refresh_inputs import load_inputs
D,source_html,output_path=load_inputs(R,MAIN)
S=BeautifulSoup((R/'.build/editorial-source.html').read_text(),'html.parser')
e=lambda x:html.escape(str(x),quote=True)
def read(n):return json.loads((MAIN/n).read_text())
teacher=read('data/bukatsu-chiiki_teacher-reread.json')
cost=read('data/bukatsu-chiiki_cost-receiver-reread.json')
child=read('data/verification/bukatsu-chiiki-plan-child-subissues.json')
groups=[teacher,child['plan_side'],child['child_side'],cost['receiver_side'],cost['cost_side'],None,None]
short=['教員の働き方','制度・移行','教育の機会','受け皿・指導者','費用・家庭負担','その他','地域格差']
titles=['教員の働き方の意見','制度・移行の意見','教育の機会の意見','受け皿・指導者の意見','費用・家庭負担の意見','その他の論点の意見','地域格差の意見']
subtitles=['部活動の指導や休日対応を減らし、教員が授業や私生活に使える時間を取り戻してほしいという意見です。専門指導者への期待がある一方、地域へ移しても教員の負担は残るのではないかという懸念もあります。給与や勤務時間の制度を見直すべきだという声も含みます。', '地域移行をいつ、どのような手順で進めるのかをめぐる意見です。自治体の計画や日程に触れる投稿のほか、まだ決まっていない条件や、移行が進まない理由を指摘する声があります。移行期にいる子どもや家庭への影響、活動の選択肢への期待も語られています。', '子どもが活動を始める機会や、学校での居場所がどう変わるかをめぐる意見です。選べる活動が増えることへの期待と、気軽に参加できる入口が失われることへの懸念があります。部活動にどんな教育的な意味があるのか、その役割自体を問い直す声も含みます。', '学校に代わって誰が活動を運営し、子どもを指導するのかをめぐる意見です。担い手の不足や報酬の低さに加え、安全管理や指導の質、責任の所在への不安が語られています。地域で受け皿ができたという報告もあり、活動を続けられる条件に注目する論点です。', '会費や送迎などの負担を、家庭・自治体・指導者の間でどう分担するかをめぐる意見です。家庭の支出が増えることや、お金を理由に参加を諦める子どもが出ることへの懸念があります。いまの低い費用は誰かの無償労働に支えられているとして、財源の見直しを求める声も含みます。', 'ほかの6つの論点に分けられなかった意見の欄です。部活動そのものの存廃や、地域の別の課題と結び付けた意見など、異なる話題を含みます。ひとつの立場を表すまとまりではないため、個々の投稿が何について述べているかを確かめながら読む欄です。', '住む地域によって、選べる活動や通える場所に差が出ることをめぐる意見です。地方での担い手や施設の不足、長距離の移動や保護者の送迎、文化系の活動を続けられるかが懸念されています。参加の機会を確保するため、行政の支援や移行前の制度設計を求める声もあります。']
copy={
'B':['制度と待遇を見直してほしい','移行よりも、教員の給与や勤務時間の制度を見直してほしいという意見です。'],
'G':['専門指導者への期待','外部への委託や専門の指導者に期待する声です。指導の質が高まることへの期待も含みます。'],
'H':['教員の時間を取り戻したい','部活動にかかる教員の負担を減らし、本来の仕事や私生活の時間を取り戻したいという意見です。'],
'A':['移しても負担は減らない','地域に移しても教員の負担は減らず、むしろ増えるのではないかという意見です。']
}
panels=[];audit=[];public_links={}
for ix,it in enumerate(D['issues']):
 items=it['sub'].get('items',[]);group=groups[ix]
 for item in items:
  matches=[p for p in (group or {}).get('items',[]) if p.get('bucket')==item['id']]
  if group and not item.get('unread'):
   assert len(matches)==item['count'],(it['id'],item['id'],len(matches),item['count'])
  urls=list(dict.fromkeys(p.get('url') or 'https://x.com/i/web/status/'+str(p['tweet_id']) for p in matches))
  item['posts']=urls[:2]
  public_links[it['id']+'/'+item['id']]=urls[:2]
  audit.append({'issue':it['id'],'reason':item['id'],'count':item['count'],'matched':len(matches),'links':len(urls[:2])})
  item['title'],item['description']=(copy[item['id']] if ix==0 and item['id'] in copy else [item['label'],''])
  if item.get('unread'):item['description']='この分は、理由の分類をまだ読み直していません。ほかの理由の件数に振り分けず、分けて表示しています。'
 default='G' if ix==0 else (items[0]['id'] if items else None)
 featured=['B','G','H','A'] if ix==0 else [a['id'] for a in items[:4]]
 nav=[];more=[];bodies=[]
 for item in items:
  active=item['id']==default
  key=it['id']+'--'+item['id']
  btn=f'<button class="reason-choice" data-reason="{e(item["id"])}" aria-pressed="{str(active).lower()}" aria-controls="{key}"><span>{e(item["title"])}</span><b>{item["count"]}<small>件</small></b></button>'
  (nav if item['id'] in featured else more).append(btn)
  posts=''.join(f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">分類した投稿 {j+1} をXで読む ↗</a>' for j,url in enumerate(item['posts']))
  if posts:posts='<details class="original-posts"><summary>この理由に分類した元の投稿を読む</summary><p class="fine">分類記録で対応を確認した投稿例です。引用本文は表示していません。</p><div class="post-links">'+posts+'</div></details>'
  else:posts='<p class="fine">この理由に対応する投稿例は、この試作には掲載していません。</p>'
  alt=None
  if ix==0 and item['id'] in ['G','A']:alt=next(x for x in items if x['id']==('A' if item['id']=='G' else 'G'))
  elif len(items)>1:alt=next((x for x in items if x['id']!=item['id'] and not x.get('unread')),None)
  alt_html=f'<div class="another"><span class="eyebrow">この論点の別の理由</span><h4>{e(alt["title"] if "title" in alt else alt["label"])}</h4><button class="text-button" data-reason="{e(alt["id"])}">この理由も読む →</button></div>' if alt else ''
  desc=f'<p class="reason-copy">{e(item["description"])}</p>' if item['description'] else '<p class="fine">公開中の理由分類の見出しを表示しています。</p>'
  bodies.append(f'<article id="{key}" class="reason-detail" data-detail="{e(item["id"])}" {"" if active else "hidden"}><span class="eyebrow">選んだ理由 · {item["count"]}件</span><h3 tabindex="-1">{e(item["title"])}</h3>{desc}{posts}{alt_html}</article>')
 coverage=f'<p class="fine">理由の再読済み {it["sub"]["reread_count"]}件 ／ 未再読 {it["sub"]["unread_count"]}件。件数はこの論点内の投稿数です。</p>' if items else ''
 if not items:
  nav=['<p class="fine">この論点の理由別分類は、まだ掲載していません。</p>']
  bodies=['<article class="reason-detail"><h3>投稿例と関連資料から読む</h3><p>現在は論点全体の集計を掲載しています。細かな理由分類は今後の確認対象です。</p></article>']
 claims=S.select_one('#'+it['id']+' .sources-pane')
 if claims:
  claims.select_one('h3').string='この論点の投稿と一次資料'
  claims.select_one('.source-intro p').string='「'+it['label']+'」に関する投稿の主張を、公表された資料と照らし合わせます。'
 postexamples=S.select('#'+it['id']+' .post-link')
 stances=''.join(f'<span><i style="background:{e(s["color"])}"></i>{e(s["label"])} <b>{it["stances"][s["key"]]}件</b></span>' for s in D['stances'])
 morehtml=f'<details class="all-reasons"><summary>ほかの理由も読む（残り{len(more)}分類）</summary>{"".join(more)}</details>' if more else ''
 panels.append(f'<section class="issue-panel" id="{it["id"]}" data-issue="{ix}" data-default="{default or ""}" {"" if ix==0 else "hidden"} aria-labelledby="heading-{ix}"><div class="issue-heading"><div><span class="eyebrow">選択中の論点 · {it["count"]}件</span><h2 id="heading-{ix}" tabindex="-1">{titles[ix]}</h2><p class="issue-subtitle">{subtitles[ix]}</p></div><a href="#map">全体図へ戻る ↑</a></div><div class="reason-layout"><aside class="reason-index"><details class="reason-menu" open><summary>この論点の理由一覧（{len(items)}分類）</summary><h3>この論点に寄せられた意見</h3><p class="fine">意見を選ぶと、その理由と投稿例が開きます。</p>{"".join(nav)}{morehtml}{coverage}<details class="stance-detail"><summary>この論点の立場別集計</summary><div class="issue-stances">{stances}</div></details></details></aside><div class="reason-reading">{"".join(bodies)}<div class="source-reading" id="sources-{ix}">{claims.decode_contents() if claims else ""}</div><details class="issue-examples"><summary>この論点の投稿例も読む</summary><p class="fine">論点全体から選んだ例です。上の個別理由に対応する投稿とは別です。</p>{"".join(str(p) for p in postexamples)}</details></div></div><div class="issue-next"><a href="#map">7つの論点を見渡す ↑</a><button class="text-button" data-select="{(ix+1)%7}">次の論点：{short[(ix+1)%7]} →</button></div></section>')
# Preserve the already extracted source/background/trend/classroom text exactly.
deep=S.select_one('.deep-read')
deep.select_one('h2').string='さらに、背景から確かめる'
newdetail=BeautifulSoup('<details id="local"><summary>地域ごとに異なる条件</summary><div class="rich-content"><p>開始時期、参加費、活動場所、送迎方法、指導の責任主体、大会の参加条件は、地域や活動によって異なります。</p><p>学校や自治体の案内で、希望する活動の条件を確かめてください。</p><a href="https://sns-reaction-map.jp/bukatsu-chiiki-reaction-map.html#bukatsu-check" target="_blank" rel="noopener noreferrer">現行ページの確認事項を読む ↗</a></div></details>','html.parser')
deep.insert(4,newdetail)
mapdata={'issues':[{k:i[k] for k in ['id','label','count','high_pct']} for i in D['issues']],'modes':D['modes'],'stances':D['stances'],'totals':D['totals']}
template=(R/'.build/template.html').read_text()
template=template.replace('__DATA_DATE__',D['updated_at'].replace('-','.'))
template=template.replace('__OPINION_TOTAL__',format(D['totals']['opinions'],',')).replace('__PANELS__',''.join(panels)).replace('__DEEP__',str(deep)).replace('__DATA__',json.dumps(mapdata,ensure_ascii=False).replace('</','<\\/')).replace('__JS__',(R/'.build/app.js').read_text())
from lower_design import decorate
template=decorate(template,(R/'.build/app.js').read_text())
from public_trends import add_public_trends
template=add_public_trends(template,R,source_html)
from x_embeds import add_x_embeds
template=add_x_embeds(template)
from parity import add_parity
template=add_parity(template,R,source_html,MAIN,D)
from site_chrome import add_site_chrome
template=add_site_chrome(template,R)
temporary=output_path.with_suffix('.tmp')
temporary.write_text(template)
temporary.replace(output_path)
(R/'evidence').mkdir(exist_ok=True)
(R/'evidence/reason-links.json').write_text(json.dumps(public_links,ensure_ascii=False,indent=2))
(R/'evidence/data-check.json').write_text(json.dumps({'snapshot':D['snapshot_id'],'opinions':D['totals']['opinions'],'issues':len(D['issues']),'reasons':audit},ensure_ascii=False,indent=2))
(R/'.build/new-copy.html').write_text('<html><body>'+''.join('<p>'+e(c)+'</p>' for v in copy.values() for c in v)+''.join('<p>'+e(x)+'</p>' for x in titles)+str(newdetail)+'</body></html>')
print('Built',len(template),'characters;',sum(a['links'] for a in audit),'verified reason-source links')

