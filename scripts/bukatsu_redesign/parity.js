
(()=>{
 const record=(name,params={})=>{
  if(typeof window.gtag==='function')window.gtag('event',name,{theme:'bukatsu-chiiki',...params});
  else{window.dataLayer=window.dataLayer||[];window.dataLayer.push({event:name,theme:'bukatsu-chiiki',...params,preview:true});}
 };
 document.querySelector('[data-copy-questions]')?.addEventListener('click',async()=>{
  const rows=[...document.querySelectorAll('.local-question-list dl>div')];
  const text=rows.map(x=>x.querySelector('dt').textContent+'\n'+x.querySelector('dd').textContent).join('\n\n');
  const status=document.querySelector('[data-copy-status]');
  try{await navigator.clipboard.writeText(text);status.textContent='確認事項をコピーしました。'}
  catch(e){status.textContent='コピーできませんでした。確認事項の本文を選択してコピーしてください。'}
  record('bukatsu_local_questions_copy');
 });
 document.addEventListener('click',e=>{
  const node=e.target.closest('a,button,[data-index]');if(!node)return;
  if(node.matches('[data-index]'))record('issue_view',{issue_index:node.dataset.index});
  if(node.matches('[data-select]'))record('topic_select',{issue:node.dataset.select});
  if(node.matches('[data-reason]'))record('reason_select',{reason:node.dataset.reason});
  if(node.matches('a[href^="https://x.com/intent/"]'))record('share_x');
  if(node.matches('a[href]')&&node.closest('.source-reading'))record('citation_click',{url:node.href});
  if(node.matches('[data-trend-download],[data-trend-copy]'))record('trend_asset_use',{variant:node.dataset.variant});
 });
 document.querySelector('.classroom-print-btn')?.addEventListener('click',()=>record('classroom_print_view'));
 document.querySelectorAll('#trends,#faq-guide,.issue-examples,.original-posts').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)record('detail_open',{section:d.id||d.className})}));
 function revealHash(){
  let id;try{id=decodeURIComponent(location.hash.slice(1))}catch(e){return}
  const aliases={'bukatsu-background':'background','detail-data':'method','ocean':'source-only','editorial':'editorial-notes','issue-cards':'reading','stance-map-section':'map','classroom-title':'classroom'};
  const target=document.getElementById(aliases[id]||id);if(!target)return;
  for(let p=target;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true}
 }
 window.addEventListener('hashchange',revealHash);revealHash();
})();

