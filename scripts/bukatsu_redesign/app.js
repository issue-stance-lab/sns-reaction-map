(()=>{'use strict';
const D=JSON.parse(document.getElementById('public-data').textContent),$=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)],esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const short=['教員の働き方','制度・移行','教育の機会','受け皿・指導者','費用・家庭負担','その他','地域格差'];
const topicColors=['#008b92','#dc6256','#2177be','#aa7500','#008d86','#7650b4','#1e79c6'];
const topicPales=['#cceeed','#ffdbd6','#d8eaff','#fff0b8','#ccede8','#e5dcf6','#d8ecfa'];
const topicIcons=["<svg class=\"picto\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><rect x=\"10\" y=\"3\" width=\"12\" height=\"11\" rx=\"1\"/><circle cx=\"5\" cy=\"8\" r=\"2\"/><path d=\"M2 21v-8h5l4-4M5 13v8M16 14v6\"/></svg>", "<svg class=\"picto\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"5\" cy=\"12\" r=\"3\"/><circle cx=\"19\" cy=\"5\" r=\"3\"/><circle cx=\"19\" cy=\"19\" r=\"3\"/><path d=\"m8 10 8-4M8 14l8 4\"/></svg>", "<svg class=\"picto\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M12 6C8 3 4 3 2 4v15c4-1 7 0 10 2 3-2 6-3 10-2V4c-4-1-7 0-10 2v15\"/></svg>", "<svg class=\"picto\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M3 12a7 7 0 1 0 13 3l6-3V6H11l-4 6Z\"/><circle cx=\"9\" cy=\"15\" r=\"2\"/><path d=\"M17 2v2M22 2l-2 2\"/></svg>", "<svg class=\"picto\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><rect x=\"3\" y=\"6\" width=\"18\" height=\"15\" rx=\"2\"/><path d=\"m4 6 13-3v3M16 11h6v6h-6Z\"/><circle cx=\"18\" cy=\"14\" r=\".5\"/></svg>", "<svg class=\"picto\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M3 4h18v13H9l-6 4Z\"/><circle cx=\"7\" cy=\"10\" r=\".5\"/><circle cx=\"12\" cy=\"10\" r=\".5\"/><circle cx=\"17\" cy=\"10\" r=\".5\"/></svg>", "<svg class=\"picto\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M12 22s8-9 8-14a8 8 0 0 0-16 0c0 5 8 14 8 14Z\"/><circle cx=\"12\" cy=\"8\" r=\"3\"/></svg>"];
let selected=0,mode='all';
$('#global-stances').innerHTML=D.stances.map(s=>'<div><span><i style="background:'+s.color+'"></i>'+esc(s.label.replace('・改善要求','').replace('・情報',''))+'</span><strong>'+((s.count/D.totals.opinions)*100).toFixed(1)+'<small>%</small></strong></div>').join('');
$('#map-filters').innerHTML=D.modes.map(m=>'<button data-mode="'+esc(m.id)+'" aria-pressed="'+(m.id===mode)+'">'+esc(m.label)+'</button>').join('');
$('#issue-tabs').innerHTML=D.issues.map((i,j)=>'<button style="--topic:'+topicColors[j]+';--topic-pale:'+topicPales[j]+'" data-select="'+j+'" aria-pressed="'+(j===selected)+'">'+topicIcons[j]+short[j]+'</button>').join('');
function draw(){
 const mobile=matchMedia('(max-width:650px)').matches,m=D.modes.find(x=>x.id===mode),W=1100,B=mobile?260:230,T=20,MAX=Math.max(40,Math.ceil(Math.max(...Object.values(m.high_pct))/20)*20),MIN=mobile?84:70,GAP=10,L=38,usable=W-L-10-GAP*6;
 // The labeled axis fits the active data. Minimum hit widths are disclosed.
 const raw=D.issues.map(i=>usable*m.counts[i.id]/m.total), widths=raw.map(x=>Math.max(MIN,x));
 let over=widths.reduce((a,b)=>a+b,0)-usable,slack=widths.reduce((a,b)=>a+Math.max(0,b-MIN),0);
 widths.forEach((w,j)=>{if(w>MIN)widths[j]-=over*(w-MIN)/slack});
 let x=L,svg='<defs><linearGradient id="hill-light" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#b5a0d2"/><stop offset="1" stop-color="#e2d8ee"/></linearGradient><linearGradient id="hill-selected" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#7958a5"/><stop offset="1" stop-color="#bca7d3"/></linearGradient></defs>';
 for(let v=0;v<=MAX;v+=20){let y=B-(B-T)*v/MAX;svg+='<line x1="'+L+'" x2="1090" y1="'+y+'" y2="'+y+'" stroke="#e8e6ef" stroke-dasharray="'+(v?'3 7':'0')+'"/><text x="27" y="'+(y+4)+'" font-size="10" text-anchor="end" fill="#69758a">'+v+'%</text>'}
 D.issues.forEach((i,j)=>{let w=widths[j],cx=x+w/2,rate=m.high_pct[i.id]||0,top=B-(B-T)*rate/MAX,k=w*.32;
 const path='M '+x+' '+B+' L '+(x+w*.24)+' '+(top+(B-top)*.52)+' L '+(x+w*.34)+' '+(top+(B-top)*.6)+' L '+cx+' '+top+' L '+(x+w*.72)+' '+(top+(B-top)*.45)+' L '+(x+w*.8)+' '+(top+(B-top)*.4)+' L '+(x+w)+' '+B+' Z';
 svg+='<g class="hill" style="--hill-color:'+topicColors[j]+';--hill-pale:'+topicPales[j]+'" role="button" tabindex="0" data-index="'+j+'" aria-pressed="'+(j===selected)+'" aria-label="'+esc(i.label)+'、'+m.counts[i.id]+'件、強い表現'+rate+'パーセント"><rect class="hit" x="'+x+'" y="12" width="'+w+'" height="'+(B+54)+'" fill="transparent" rx="3"/><path class="silhouette" d="'+path+'"/><text x="'+cx+'" y="'+(top-13)+'" text-anchor="middle" font-size="'+(mobile?35:19)+'">'+m.counts[i.id]+'<tspan font-size="'+(mobile?19:11)+'">件</tspan></text>';

 svg+='</g>';x+=w+GAP});
 $('#mountains').setAttribute('viewBox','0 0 1100 '+(mobile?280:250));$('#mountains').innerHTML=svg;
 $('#mobile-issues').innerHTML=D.issues.map((i,j)=>'<button style="--topic:'+topicColors[j]+';--topic-pale:'+topicPales[j]+'" data-select="'+j+'" aria-pressed="'+(j===selected)+'">'+topicIcons[j]+'<span>'+short[j]+'</span><b>'+m.counts[i.id]+'件</b></button>').join('');
 $('#map-status').textContent=m.label+' '+m.total.toLocaleString('ja-JP')+'件を表示';
 $('#map-values').innerHTML=D.issues.map(i=>'<tr><th>'+esc(i.label)+'</th><td>'+m.counts[i.id]+'件</td><td>'+m.high_pct[i.id].toFixed(1)+'%</td></tr>').join('');
 $$('#issue-tabs button').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.select===selected)));
}
function choose(index,scroll=true,save=true){
 selected=index;$$('.issue-panel').forEach((p,j)=>p.hidden=j!==index);const panel=$('.issue-panel[data-issue="'+index+'"]');if(panel.dataset.default)reason(panel,panel.dataset.default,false,false);draw();
 $('#reading-announcement').textContent=D.issues[index].label+'の意見と推移に切り替えました。';
 if(save)history.pushState(null,'','#'+D.issues[index].id);
 if(scroll){$('#reading').scrollIntoView({behavior:'instant'});$('#heading-'+index).focus({preventScroll:true})}
}
function reason(panel,id,scroll=true,save=true){
 const found=[...panel.querySelectorAll('.reason-detail')].find(x=>x.dataset.detail===id);if(!found)return;
 panel.querySelectorAll('.reason-detail').forEach(x=>x.hidden=x!==found);
 panel.querySelectorAll('.reason-choice').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.reason===id)));
 const active=[...panel.querySelectorAll('.reason-choice')].find(x=>x.dataset.reason===id);const more=active?.closest('.all-reasons');if(more)more.open=true;
 if(save)history.pushState(null,'','#'+found.id);
 if(scroll){if(matchMedia('(max-width:650px)').matches)panel.querySelector('.reason-menu').open=false;found.scrollIntoView({behavior:'instant',block:'start'});found.querySelector('h3').focus({preventScroll:true})}
}
document.addEventListener('click',ev=>{
 const select=ev.target.closest('button[data-select]');if(select){const local=select.closest('#mobile-issues,#issue-tabs');choose(+select.dataset.select,!local);if(local)document.querySelector('#'+local.id+' button[data-select="'+select.dataset.select+'"]').focus({preventScroll:true});return}
 const r=ev.target.closest('button[data-reason]');if(r){reason(r.closest('.issue-panel'),r.dataset.reason);return}
 const a=ev.target.closest('a[href^="#"]');if(a){const el=document.getElementById(a.hash.slice(1));if(el){for(let p=el;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;if(a.classList.contains('trend-detail-link')){ev.preventDefault();history.pushState(null,'',a.hash);el.scrollIntoView({behavior:'instant',block:'start'});}}}
});
$('#mountains').addEventListener('click',e=>{const b=e.target.closest('[data-index]');if(b){choose(+b.dataset.index,false);$('#mountains [data-index="'+b.dataset.index+'"]').focus({preventScroll:true})}});
$('#mountains').addEventListener('keydown',e=>{const b=e.target.closest('[data-index]');if(!b)return;if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(+b.dataset.index,false);$('#mountains [data-index="'+b.dataset.index+'"]').focus({preventScroll:true})}
 else if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const j=(+b.dataset.index+(e.key==='ArrowRight'?1:6))%7;$('#mountains [data-index="'+j+'"]').focus()}});
$('#map-filters').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;mode=b.dataset.mode;$$('#map-filters button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));draw()});
$('#explain-toggle').addEventListener('click',()=>{const open=$('#explain-toggle').getAttribute('aria-expanded')==='true';$('#explain-toggle').setAttribute('aria-expanded',String(!open));$('#map-explain').hidden=open});
function route(scroll=false){
 const hash=decodeURIComponent(location.hash.slice(1)),parts=hash.split('--'),j=D.issues.findIndex(i=>i.id===parts[0]);
 if(j>=0){choose(j,false,false);if(parts[1])reason($('.issue-panel[data-issue="'+j+'"]'),parts[1],scroll,false);else if(scroll)$('#reading').scrollIntoView({behavior:'instant'});}
 else{const el=document.getElementById(hash);if(el){for(let p=el;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;if(scroll)el.scrollIntoView({behavior:'instant'})}}
}
function adapt(){const mobile=matchMedia('(max-width:650px)').matches;$$('.reason-menu').forEach(x=>x.open=true);draw()}
adapt();route(true);addEventListener('popstate',()=>route(true));addEventListener('hashchange',()=>route(true));
matchMedia('(max-width:650px)').addEventListener('change',adapt);
})();
