from bs4 import BeautifulSoup
import re

def add_x_embeds(markup):
 s=BeautifulSoup(markup,'html.parser')
 for section in s.select('.original-posts,.issue-examples'):
  links=[]
  for a in section.select('a[href]'):
   url=a['href'];m=re.search(r'https://(?:www\.)?(?:x|twitter)\.com/[^\s]+/status/(\d+)',url)
   if m and m.group(1) not in [i for i,u in links]:links.append((m.group(1),url))
  if not links:continue
  summary=section.select_one('summary').extract();section.clear();section.append(summary)
  note=s.new_tag('p',attrs={'class':'fine'});note.string='元のX投稿を最大2件表示します。';section.append(note)
  for i,url in links[:2]:
   entry=s.new_tag('div',attrs={'class':'x-embed','data-tweet-id':i})
   host=s.new_tag('div',attrs={'class':'x-embed-host'});entry.append(host)
   status=s.new_tag('p',attrs={'class':'fine x-embed-status','role':'status'});status.string='投稿を開くと、埋め込みを読み込みます。';entry.append(status)
   a=s.new_tag('a',href=url,target='_blank',rel='noopener noreferrer',attrs={'class':'x-original-link'});a.string='元の投稿をXで開く ↗';entry.append(a);section.append(entry)
 style=s.new_tag('style');style.string='.x-embed{margin:20px 0;padding:0 0 18px;border-bottom:1px solid #dce6ee;min-width:0}.x-embed-host{max-width:550px;width:100%;margin:auto}.x-embed-host iframe{max-width:100%!important}.x-original-link{display:inline-block;font-size:12px;min-height:32px}.x-embed-status{margin:8px 0}.x-embed-host .twitter-tweet{margin:0 auto!important}'
 s.head.append(style)
 script=s.new_tag('script');script.string=r"""
(()=>{
 let loader;
 function widgets(){
  if(window.twttr?.widgets)return Promise.resolve(window.twttr.widgets);
  if(loader)return loader;
  loader=new Promise((resolve,reject)=>{
   const script=document.createElement('script');script.src='https://platform.twitter.com/widgets.js';script.async=true;
   const timer=setTimeout(()=>reject(new Error('timeout')),15000);
   script.onload=()=>{clearTimeout(timer);window.twttr?.widgets?resolve(window.twttr.widgets):reject(new Error('unavailable'))};
   script.onerror=()=>{clearTimeout(timer);reject(new Error('load'))};document.head.append(script);
  }).catch(e=>{loader=null;throw e});return loader;
 }
 async function render(section){
  if(!section.open||!section.closest('.issue-panel')||section.closest('.issue-panel').hidden)return;
  for(const item of section.querySelectorAll('.x-embed')){
   if(item.dataset.started)continue;
   item.dataset.started='true';const status=item.querySelector('.x-embed-status');status.textContent='Xの投稿を読み込んでいます。';
   try{
    const api=await widgets();
    const result=await Promise.race([api.createTweet(item.dataset.tweetId,item.querySelector('.x-embed-host'),{lang:'ja',dnt:true,conversation:'none',align:'center'}),new Promise((_,reject)=>setTimeout(()=>reject(new Error('timeout')),15000))]);
    if(!result)throw new Error('unavailable');status.hidden=true;item.dataset.state='loaded';
   }catch(e){item.dataset.state='fallback';status.textContent='埋め込みを表示できません。下のリンクから元の投稿を開けます。'}
  }
 }
 document.querySelectorAll('.original-posts,.issue-examples').forEach(d=>{
  d.addEventListener('toggle',()=>render(d));
  d.querySelector('summary').addEventListener('click',()=>requestAnimationFrame(()=>render(d)));
 });
})();
"""
 s.body.append(script)
 return str(s)
