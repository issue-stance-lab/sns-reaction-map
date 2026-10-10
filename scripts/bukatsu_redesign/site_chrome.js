(()=>{
 const chrome=document.querySelector('.site-chrome');
 const bar=document.getElementById('reading-progress');
 const panels=[...document.querySelectorAll('.issue-panel')];
 const details=[...document.querySelectorAll('#schedule,#faq-guide,.deep-read>details[id]')];
 const ids=[...panels,...details].map(x=>x.id);
 const key=window.SNS_REDESIGN_PRODUCTION?'isa-reading-bukatsu-chiiki-v2':'sns-map-prototype-reading-v1';
 let stored=[];try{stored=JSON.parse(localStorage.getItem(key)||'[]')}catch(e){}
 const seen=new Set(Array.isArray(stored)?stored.filter(x=>ids.includes(x)):[]);
 // Migrate only equivalent topic visits; old quizzes/claims have no matching new section.
 if(window.SNS_REDESIGN_PRODUCTION){
  try{const old=JSON.parse(localStorage.getItem('isa-seen-bukatsu-chiiki')||'[]');
   if(Array.isArray(old))old.forEach(x=>{if(typeof x==='string'&&x.startsWith('i:')&&ids.includes(x.slice(2)))seen.add(x.slice(2))});
   localStorage.setItem(key,JSON.stringify([...seen]));
  }catch(e){}
 }
 const segments=bar.querySelector('.reading-segments');
 ids.forEach(()=>segments.appendChild(document.createElement('i')));
 function paint(){
  [...segments.children].forEach((x,i)=>x.classList.toggle('on',seen.has(ids[i])));
  bar.querySelector('.reading-count').textContent=seen.size+' / '+ids.length;
  bar.classList.toggle('started',seen.size>0);
  bar.title='論点'+panels.length+'か所と資料'+details.length+'か所のうち、開いた項目の数です。同じ項目は一度だけ数えます。';
 }
 function visit(id){if(document.body.classList.contains("is-printing"))return;if(!ids.includes(id)||seen.has(id))return;seen.add(id);try{localStorage.setItem(key,JSON.stringify([...seen]))}catch(e){}paint()}
 // Count topic descriptions only after they actually appear on screen, including deep links.
 const observer=new IntersectionObserver(entries=>entries.forEach(e=>{
  if(e.isIntersecting&&e.intersectionRatio>=0.5&&!e.target.closest('[hidden]'))visit(e.target.closest('.issue-panel').id);
 }),{threshold:0.5});
 panels.forEach(p=>observer.observe(p.querySelector('.issue-subtitle')));
 details.forEach(d=>d.addEventListener('toggle',()=>{if(d.open)visit(d.id)}));
 const resize=new ResizeObserver(()=>document.documentElement.style.setProperty('--chrome-height',chrome.getBoundingClientRect().height+'px'));resize.observe(chrome);
 document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelector('.global-mobile').open=false});
 document.addEventListener('click',e=>{const menu=document.querySelector('.global-mobile');if(!menu.contains(e.target))menu.open=false});
 paint();
})();
