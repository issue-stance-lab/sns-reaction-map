"""Carry existing article content and functions into the redesigned prototype."""
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json,re,shutil,html
BASE='https://sns-reaction-map.jp/'
E=lambda value:html.escape(str(value),quote=True)
def add_parity(markup,root,source_html,main,data):
 s=BeautifulSoup(markup,'html.parser');src=BeautifulSoup(source_html,'html.parser')
 added=[]
 def fragment(text):return BeautifulSoup(text,'html.parser')
 def clone(node):return fragment(str(node)).find()
 def disclosure(id,title,content):
  el=fragment('<details id="'+id+'"><summary>'+title+'</summary><div class="rich-content"></div></details>').details
  el.div.append(content);return el
 # FAQ: exact source wording and citations, presented beside the schedule.
 faq=fragment('<section class="parity-faq" id="faq"><h2>部活動の地域展開で、よくある疑問</h2></section>').section
 for node in src.select('.bukatsu-search-faq__grid > details'):
  item=clone(node)
  if '「地域移行」と「地域展開」は同じですか？' in item.summary.get_text():item.p.string=item.p.get_text().replace('同じ改革を指す文脈で使われます。','同じ改革を指す文脈で使われる呼び方です。')
  faq.append(item)
 source=src.select_one('.bukatsu-search-entry')
 for p in source.select('p'):
  if '制度の出典' in p.get_text():faq.append(clone(p))
 s.select_one('#schedule').insert_after(disclosure('faq-guide','対象・費用・送迎のよくある疑問',faq))
 added.append(str(faq))
 # Preserve questions as a readable reference, without the rejected checkbox flow.
 check=clone(src.select_one('#bukatsu-check'))
 for node in check.select('style,script,.local-check-tool'):node.decompose()
 question_script=next(x.get_text() for x in src.select('script') if 'const questions=[' in x.get_text())
 questions=json.loads(re.search(r'const questions=(\[.*?\]);',question_script,re.S).group(1))
 table='<div class="local-question-list"><h3>学校や自治体に確認する6つのこと</h3><dl>'
 for q in questions:table+='<div><dt>'+E(q['label'])+'</dt><dd>'+E(q['question'])+'</dd></div>'
 table+='</dl><button type="button" data-copy-questions>確認事項をまとめてコピー</button><span role="status" data-copy-status></span></div>'
 check.select_one('h3').insert_before(fragment(table))
 s.select_one('#local .rich-content').clear();s.select_one('#local .rich-content').append(check)
 added.append(str(check))
 # Existing cross-issue editorial context has its own date, separate from collection date.
 s.select_one('.deep-read').append(disclosure('editorial-notes','論点をまたいで分かること',clone(src.select_one('#editorial'))))
 # Article provenance; mark historical observations as such instead of implying latest waves.
 trust=clone(src.select_one('.article-trust'))
 obs=trust.select_one('.article-trust-observations')
 if obs:
  obs.find_previous_sibling('h3').string='過去の収集で確認したこと'
  obs.insert_before(fragment('<p class="fine">以下は記載された収集回についての記録です。最新までの変化は推移グラフで確認できます。</p>'))
 s.select_one('#method .rich-content').insert(0,trust)
 # Restore source illustrations below the source discussion, not ahead of the reasons.
 illustrations=src.select('.landing-panel img')
 for panel,img in zip(s.select('.issue-panel'),illustrations):
  pic=clone(img);pic['loading']='lazy'
  fig=fragment('<figure class="issue-illustration"><a target="_blank" rel="noopener"></a><figcaption>現行ページの論点図解。画像を押すと拡大して読めます。</figcaption></figure>').figure
  fig.a['href']=pic['src'];fig.a.append(pic)
  panel.select_one('.source-reading').append(disclosure('illustration-'+panel['id'],'この論点を図解で見る',fig))
 # Sharing images and illustrations are local copies so downloads work on localhost.
 for node in s.select('img[src],a[href]'):
  attr='src' if node.name=='img' else 'href';value=node.get(attr,'')
  relative=value.removeprefix(BASE)
  if relative.startswith('images/'):
   path=main/'docs'/relative
   if not path.is_file():raise ValueError('Missing source image '+relative)
   dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);node[attr]=relative
 # Existing related themes, replace unproven personalized recommendation wording.
 related=clone(src.select_one('#related-topics'))
 label=related.select_one('.panel-title span')
 if label:label.string='関連する論点も読む'
 s.main.append(related)
 # Existing vote identifiers and choice ordering stay unchanged.
 vote=clone(src.select_one('#vote-section'));vote['class']=['parity-vote']
 vote.select_one('.vote-storage-note').string='試作では、この端末に選択内容を保存します。本番の投票集計には送信しません。'
 s.select_one('.deep-read').insert_before(vote)
 assets=root/'assets';assets.mkdir(exist_ok=True)
 shutil.copy2(main/'docs/vote-store.js',assets/'vote-store.js')
 vote_script=next(x.get_text() for x in src.select('script') if "var VOTE_ISSUES=[" in x.get_text())
 vote_script=vote_script.replace("var STORAGE_KEY='sns_vote_'+TOPIC+'_my';","var STORAGE_KEY='sns_vote_preview_'+TOPIC+'_my';")
 vote_script=vote_script.replace("btn.innerHTML='<span class=\"vote-issue-icon\">'+iss.icon+'</span><span class=\"vote-issue-title\">'+iss.k+'</span>';","btn.innerHTML='<span class=\"vote-issue-title\">'+iss.k+'</span>';")
 # No remote config is loaded in the prototype. VoteStore's existing local mode is used.
 script=s.new_tag('script',src='assets/vote-store.js');s.body.append(script)
 helpers=next(x.get_text() for x in src.select('script') if 'window.voteMsg = function' in x.get_text())
 script=s.new_tag('script');script.string=helpers+vote_script;s.body.append(script)
 # Production metadata is retained while the local preview remains excluded from indexing.
 for node in src.head.select('meta[name="description"],meta[property^="og:"],meta[name^="twitter:"],link[rel="canonical"],script[type="application/ld+json"]'):
  s.head.append(clone(node))
 if not s.select_one('meta[name="robots"]'):s.head.append(s.new_tag('meta',attrs={'name':'robots','content':'noindex,nofollow'}))
 # Preserve production integrations for deployment review, not execution in the local preview.
 protected=[x for x in src.select('script') if 'allowedHosts' in x.get_text() or 'adsbygoogle' in x.get('src','')]
 (root/'.build/production-integrations.html').write_text('\n'.join(str(x) for x in protected))
 shutil.copy2(main/'docs/vote-config.js',root/'.build/production-vote-config.js')
 # Footer: policy, correction and operator links remain reachable.
 footer=clone(src.select_one('footer'));footer['class']=['parity-footer']
 for node in [footer,*footer.select('[style]')]:node.attrs.pop('style',None)
 s.footer.replace_with(footer)
 for img in related.select('img[src]'):
  relative=img['src'];dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(main/'docs'/relative,dest)
 # Relative document links resolve to the production site. Local deep links map to redesigned content.
 aliases={'bukatsu-background':'background','detail-data':'method','ocean':'source-only','editorial':'editorial-notes','issue-cards':'reading','stance-map-section':'map','planet':'map','classroom-title':'classroom','bukatsu-chiiki-audit':'reading'}
 aliases.update({'fb-'+i['id']:i['id'] for i in data['issues']})
 aliases.update({'issue-'+i['id']:i['id'] for i in data['issues']})
 for a in s.select('a[href]'):
  href=a['href']
  if href.startswith('#'):a['href']='#'+aliases.get(href[1:],href[1:])
  elif href.startswith(BASE+'bukatsu-chiiki-reaction-map.html#'):
   target=href.split('#',1)[1];target=aliases.get(target,target)
   if target!='quiz' and s.find(id=target):a['href']='#'+target;a.attrs.pop('target',None)
  elif not href.startswith(('http','#','images/','mailto:')):a['href']=urljoin(BASE,href)
 for a in list(s.select('a[href$="#quiz"]')):
  # No quiz exists in the source page. Replace the old broken link with actual print action.
  a.decompose()
 classroom=clone(s.select_one('#classroom .rich-content'))
 for a in classroom.select('a[href^="#"]'):a['href']='index.html'+a['href']
 print_html='<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>部活動の地域展開 — 授業用資料</title><style>body{font-family:system-ui,sans-serif;color:#10274c;max-width:850px;margin:32px auto;padding:0 24px;line-height:1.9}h1{font-size:26px}h2,h3{break-after:avoid}a{color:#005dde}li,p{orphans:3;widows:3}button{padding:12px 22px;cursor:pointer}@media print{.print-tools{display:none}body{margin:0;font-size:11pt}a{color:inherit}}</style><div class="print-tools"><a href="index.html#classroom">本文へ戻る</a> <button onclick="window.print()">印刷 / PDFに保存</button></div><h1>部活動の地域展開 — 授業用資料</h1>'+str(classroom)+'</html>'
 (root/'classroom-print.html').write_text(print_html)
 button=fragment('<a href="classroom-print.html" target="_blank" rel="noopener" class="classroom-print-btn">授業用の印刷画面を開く ↗</a>').a
 s.select_one('#classroom .rich-content').append(button)
 # Plain HTML remains usable without JavaScript; all topics and reasons become visible.
 no=s.new_tag('noscript');no.append(fragment('<style>.issue-panel[hidden],.reason-detail[hidden]{display:block!important}#reading .reason-menu{display:block}.reading-progress,#mountains,#map-filters,#mobile-issues,#issue-tabs,#vote-section{display:none!important}</style><p class="wrap">JavaScriptが無効のため、全論点と理由を続けて表示しています。</p>'));s.body.insert(0,no)
 style=s.new_tag('style');style.string=(root/'.build/parity.css').read_text();s.head.append(style)
 script=s.new_tag('script');script.string=(root/'.build/parity.js').read_text();s.body.append(script)
 (root/'.build/parity-imported-copy.html').write_text('<html><body>'+''.join(added)+'</body></html>')
 return str(s)

