// 閲覧状態は既存の st だけに持つ。投票・資料クイズ・潮目の状態は独立。
let taxConnectedReady = false;
// 工程3の o: は既存の s: と同じ地点。古い記録を統合し、未知の地点を数えない。
const taxSpots = new Set(['g1','g2', ...issues.map(i=>'i:'+i.id), ...D.claims.map(c=>'c:'+c.id),
  ...D.ocean.sunk_continents.map(s=>'s:'+s.id), ...D.ocean.veins.map(v=>'v:'+v.id)]);
const taxSaved = [...seen];
seen.clear();
taxSaved.forEach(id=>{const key=String(id).replace(/^o:/,'s:');if(taxSpots.has(key))seen.add(key);});
if (JSON.stringify(taxSaved)!==JSON.stringify([...seen])) {
  try {localStorage.setItem('isa-seen-'+D.theme_id,JSON.stringify([...seen]));} catch(_){}
}
const taxLegacyVisit = visit;
visit = function(id){const key=String(id).replace(/^o:/,'s:');if(taxSpots.has(key))taxLegacyVisit(key);};
function taxState(){
  const stance = D.stances.find(s => s.key === st.mode);
  return Object.freeze({stanceId: stance ? stance.id : "all", issueId: st.landed === null ? null : issues[st.landed].id});
}
let taxLastState = "";
function taxPublish(){
  const state = taxState();
  document.querySelectorAll("#modes [data-m]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.m === st.mode)));
  document.dispatchEvent(new CustomEvent("tax-map:render", {detail: state}));
  const key = JSON.stringify(state);
  if (key !== taxLastState) {
    taxLastState = key;
    document.dispatchEvent(new CustomEvent("tax-map:change", {detail: state}));
  }
}
const taxLegacyPanel = drawPanel;
drawPanel = function(){ if (!taxConnectedReady) taxLegacyPanel(); else taxPublish(); };
const taxLegacyPlace = placeChart;
placeChart = function(){ if (!taxConnectedReady) taxLegacyPlace(); else evacuateChart(); };

// 最後に描いた形から補間する。連打で前のアニメーションに戻らない。
const taxLegacyLayout = layout;
function taxLayout(mode){
  if (!taxConnectedReady) return taxLegacyLayout(mode);
  const width=svg.clientWidth || 900, height=width<450?180:210, sea=height-26, top=26;
  const left=34, right=width-6, gap=width<450?3:6, minimum=width<450?13:25;
  const m=modeById[mode], live=[], floored=[];
  issues.forEach((it,i)=>{if(m.counts[it.id])live.push({i,it,n:m.counts[it.id],hi:m.high_counts[it.id],rate:m.high_pct[it.id],share:m.width_pct[it.id]});});
  const usable=right-left-gap*Math.max(0,live.length-1), sum=live.reduce((n,v)=>n+v.n,0);
  live.forEach(v=>{v.w=usable*v.n/sum;if(v.w<minimum){v.w=minimum;floored.push(v.it.label);}});
  const excess=live.reduce((n,v)=>n+v.w,0)-usable;
  const spare=live.reduce((n,v)=>n+Math.max(0,v.w-minimum),0);
  if(excess>0&&spare>0)live.forEach(v=>{v.w-=excess*Math.max(0,v.w-minimum)/spare;});
  let x=left;
  live.forEach(v=>{v.x0=x;v.x1=x+v.w;v.cx=x+v.w/2;v.top=sea-(sea-top)*v.rate/100;x=v.x1+gap;});
  return {live,total:m.total,floored,width,height,sea,top,left,right};
}
let taxVisual = null, taxAnimation = 0;
layout = function(mode){ return taxVisual && mode === st.mode ? taxVisual : taxLayout(mode); };
const taxLegacyRender = render;
render = function(){
  if(!taxConnectedReady){taxLegacyRender();return;}
  const focused = document.activeElement;
  const focusId = focused && focused.matches('#section .hill') ? focused.dataset.i : null;
  const L=layout(st.mode), selected=L.live.find(v=>v.i===st.landed);
  const color=D.stances.find(s=>s.key===st.mode)?.color || '#075ef2';
  const p=[], shortNames={'political-trust':'公約','scope':'範囲','effect':'効果','finance-welfare':'財源','alternatives':'給付','business-burden':'実務','other':'他'};
  svg.setAttribute('viewBox','0 0 '+L.width+' '+L.height);
  svg.style.height=L.height+'px';
  [0,50,100].forEach(value=>{
    const y=L.sea-(L.sea-L.top)*value/100;
    p.push('<line x1="'+L.left+'" x2="'+L.right+'" y1="'+y+'" y2="'+y+'" stroke="#dce5f0"/><text x="'+(L.left-6)+'" y="'+(y+4)+'" text-anchor="end" font-size="10" fill="#53647d">'+value+'%</text>');
  });
  L.live.forEach(v=>{
    const active=v.i===st.landed, k=v.w*.32, hitTop=Math.min(v.top,L.sea-44);
    const d='M'+v.x0+','+L.sea+' C'+(v.x0+k)+','+L.sea+' '+(v.x0+k*.9)+','+v.top+' '+v.cx+','+v.top+' C'+(v.x1-k*.9)+','+v.top+' '+(v.x1-k)+','+L.sea+' '+v.x1+','+L.sea+' Z';
    p.push('<g class="hill" tabindex="0" role="button" data-i="'+v.i+'" aria-pressed="'+active+'" aria-label="'+esc(v.it.label)+' '+v.n+'件 強い表現'+v.rate.toFixed(1)+'%">'
      +'<rect class="hill-hit" x="'+v.x0+'" y="'+hitTop+'" width="'+v.w+'" height="'+(L.sea-hitTop+4)+'" fill="transparent" pointer-events="all"/>'
      +'<path d="'+d+'" fill="'+color+'" opacity="'+(st.landed === null ? 0.6 : active ? 0.9 : 0.23)+'"/>'
      +(v.rate===0?'<circle class="zero-mark" cx="'+v.cx+'" cy="'+L.sea+'" r="3" fill="'+color+'"/>':'')
      +(L.width>560?'<text x="'+v.cx+'" y="'+(L.sea+17)+'" text-anchor="middle" font-size="10" fill="#53647d">'+esc(shortNames[v.it.id.replace(/^consumption-tax-cut-/,'')]||v.it.label)+'</text>':'')+'</g>');
  });
  if(selected)p.push('<text class="tax-selected-label" x="'+Math.max(L.left+58,Math.min(L.right-58,selected.cx))+'" y="'+Math.max(14,selected.top-10)+'" text-anchor="middle" font-size="11" font-weight="700" fill="#071a3d" pointer-events="none">'+selected.n.toLocaleString('ja-JP')+'件 · '+selected.rate.toFixed(1)+'%</text>');
  svg.innerHTML=p.join('');
  svg.querySelectorAll('.hill').forEach(g=>{
    g.onclick=()=>land(+g.dataset.i);
    g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();land(+g.dataset.i);}};
  });
  document.getElementById('chartdesc').textContent='論点別の山なみ。'+modeById[st.mode].label+'。'+L.live.map(v=>v.it.label+' '+v.n+'件、強い表現'+v.rate.toFixed(1)+'%').join('。');
  document.getElementById('floor-note').textContent=(L.floored.length?'小さい山は選びやすい幅に補正しています。正確な件数は下のボタンで確認できます。':'')
    +(L.live.some(v=>v.rate===0)?' 強い表現が0%の論点は、基準線上の点を押せます。':'');
  if (focusId !== null) svg.querySelector('.hill[data-i="'+focusId+'"]')?.focus({preventScroll:true});
};
const taxLegacySyncList=syncList;
syncList=function(){
  if(!taxConnectedReady){taxLegacySyncList();return;}
  issues.forEach((it,i)=>{
    const button=document.getElementById('btn-'+it.id), n=modeById[st.mode].counts[it.id];
    button.innerHTML='<span>'+esc(it.label)+'</span><span class="m">'+n.toLocaleString('ja-JP')+'件</span>';
    button.style.opacity=1;
    button.setAttribute('aria-pressed',String(i===st.landed));
  });
};
function taxAnimate(from, to){
  cancelAnimationFrame(taxAnimation);
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { taxVisual = null; render(); return; }
  const start = performance.now();
  const byId = list => new Map(list.map(v => [v.it.id, v]));
  const a = byId(from.live), b = byId(to.live);
  const keys = issues.map(it=>it.id).filter(id=>a.has(id)||b.has(id));
  function frame(now){
    const t = Math.min(1, (now-start)/480), f = 1-Math.pow(1-t,3);
    taxVisual = {...to, live:keys.map(id=>{
      const end = b.get(id), begin = a.get(id);
      const zero = v => ({...v, x0:v.cx, x1:v.cx, w:0, top:to.sea, n:0, hi:0, rate:0, share:0});
      const left = begin || zero(end), right = end || zero(begin), value = {...right};
      for (const key of ['x0','x1','cx','w','top','n','hi','rate','share']) value[key]=left[key]+(right[key]-left[key])*f;
      value.n=Math.round(value.n); value.hi=Math.round(value.hi);
      return value;
    })};
    render();
    if (t<1) taxAnimation=requestAnimationFrame(frame);
    else { taxVisual=null; taxAnimation=0; render(); }
  }
  taxAnimation=requestAnimationFrame(frame);
}
function taxHistory(options={}) {
  if(options.history==='none')return;
  const state=taxState(), url=new URL(location.href);
  if(!options.preserveHash)url.hash=state.issueId||'';
  const previous=history.state && history.state.taxMap;
  const next={...history.state,taxMap:state};
  const replace=!taxConnectedReady || options.history==='replace' ||
    (previous && previous.issueId===state.issueId && previous.stanceId===state.stanceId && url.href===location.href);
  history[replace?'replaceState':'pushState'](next,'',url);
}
land = function(i, options={}){
  if (!Number.isInteger(i) || !issues[i]) return;
  st.landed=i;
  visit('i:'+issues[i].id);
  taxHistory(options);
  evacuateChart(); syncList(); drawPanel(); render(); placeChart(); taxPublish();
};
const taxLegacyMorph = morphTo;
morphTo = function(mode, options={}){
  if (!modeById[mode]) return;
  if (!taxConnectedReady) { taxLegacyMorph(mode); taxPublish(); return; }
  if (mode===st.mode) return;
  const from=taxVisual || taxLayout(st.mode);
  st.prevRank=ranksOf(st.mode); st.mode=mode;
  taxHistory(options);
  // 選択中の論点が0件でも、理由・資料への入口を残す。
  syncList(); drawPanel(); taxPublish(); taxAnimate(from, taxLayout(mode));
};
orbit = function(options={}){
  if (document.querySelector('#explainer-modal.open')) return;
  st.landed=null;
  taxHistory(options);
  evacuateChart(); syncList(); drawPanel(); render(); taxPublish();
};
function taxRestore(){
  if(!taxConnectedReady)return;
  const hash=location.hash.slice(1).replace(/^(issue-|fb-)/,''), saved=history.state && history.state.taxMap;
  const issueId=Object.prototype.hasOwnProperty.call(idIndex,hash)?hash:saved?.issueId;
  if(saved){const stance=D.stances.find(s=>s.id===saved.stanceId);morphTo(stance?stance.key:'all',{history:'none'});}
  if(issueId && Object.prototype.hasOwnProperty.call(idIndex,issueId))land(idIndex[issueId],{history:'none'});
  else if(issueId===null)orbit({history:'none'});
  // 共通の旧hashchange処理が同じ論点をもう一度クリックしないよう正規化する。
  taxHistory({history:'replace',preserveHash:!Object.prototype.hasOwnProperty.call(idIndex,hash)});
}
addEventListener('popstate',taxRestore);
addEventListener('hashchange',taxRestore);

// 既存の予想2問。全意見の実数で判定し、丸め前の同率も正解として扱う。
buildGuesses = function(){
  const box=document.getElementById('guesses');
  if (!D.totals.opinions) { box.innerHTML='<p class="tax-empty">意見が0件のため、予想の答えを比較できません。</p>'; return; }
  const ordered=D.stances.slice().sort((a,b)=>b.count-a.count), a=ordered[0], b=ordered[1];
  const peak=issues.filter(it=>it.count>0).sort((a,b)=>b.intensity.high/b.count-a.intensity.high/a.count);
  const fmt=n=>n.toLocaleString('ja-JP');
  const q=[{
    key:'g1', title:'「'+a.label+'」と「'+b.label+'」、どちらが多いと思いますか？',
    opts:['「'+a.label+'」のほうが多い','「'+b.label+'」のほうが多い','同じ件数'],
    correct:[a.count===b.count?2:0],
    answer:a.count===b.count?'どちらも'+fmt(a.count)+'件で、同じ件数でした。'
      :'「'+a.label+'」'+fmt(a.count)+'件に対し、「'+b.label+'」'+fmt(b.count)+'件。「'+a.label+'」が'+fmt(a.count-b.count)+'件多く集まりました。'
  }];
  if (peak.length) {
    const options=[peak[peak.length-1], peak[Math.min(1,peak.length-1)],peak[0]].filter((x,i,all)=>all.indexOf(x)===i);
    const top=peak[0], rate=100*top.intensity.high/top.count;
    q.push({key:'g2',title:'「強い表現」の割合が最も高い論点はどれだと思いますか？',
      opts:options.map(it=>it.label),
      correct:options.map((it,i)=>it.intensity.high*top.count===top.intensity.high*it.count?i:-1).filter(i=>i>=0),
      answer:'「'+top.label+'」は'+fmt(top.count)+'件中'+fmt(top.intensity.high)+'件、'+rate.toFixed(1)+'%です。山の高さは、強い表現に分類された投稿の割合を示します。',
      issueId:top.id});
  }
  box.innerHTML=q.map(x=>'<div class="guess" data-k="'+x.key+'"><h3>'+esc(x.title)+'</h3><div class="gopts">'
    +x.opts.map((o,i)=>'<button type="button" data-i="'+i+'">'+esc(o)+'</button>').join('')
    +'</div><div class="gans" hidden></div></div>').join('');
  q.forEach(x=>{
    const card=box.querySelector('[data-k="'+x.key+'"]'), buttons=card.querySelectorAll('.gopts button');
    buttons.forEach(button=>button.addEventListener('click',()=>{
      const pick=+button.dataset.i;
      buttons.forEach((b,i)=>{b.disabled=true; b.className=x.correct.includes(i)?'hit':i===pick?'miss':'';});
      const answer=card.querySelector('.gans');
      answer.innerHTML='<p class="lead">'+(x.correct.includes(pick)?'正解':'集計では、こうなりました')+'</p><p>'+esc(x.answer)+'</p>'
        +'<button class="tax-answer-link" type="button">'+(x.issueId?'この論点の山を見る ↓':'全体の内訳を山で見る ↓')+'</button>';
      answer.hidden=false; visit(x.key);
      answer.querySelector('button').onclick=()=>{
        morphTo('all'); if(x.issueId) land(idIndex[x.issueId]);
        document.getElementById('modes').scrollIntoView({block:'start',behavior:reduce?'auto':'smooth'});
      };
    }));
  });
};
window.ConsumptionTaxMap = Object.freeze({
  getState:taxState,
  activate:function(){
    taxConnectedReady=true; evacuateChart(); dotBox.hidden=true; taxPublish();
    let width=svg.clientWidth, resizeFrame=0;
    new ResizeObserver(()=>{
      if(width===svg.clientWidth)return;
      width=svg.clientWidth;cancelAnimationFrame(taxAnimation);taxAnimation=0;taxVisual=null;
      // 監視callback内で高さを変更するとWebKitが循環通知と扱う。次の描画へ送る。
      cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>render());
    }).observe(svg);
  },
  selectIssue:function(id,options){
    if(id===null){orbit(options);return true;}
    if(!Object.prototype.hasOwnProperty.call(idIndex,id))return false;
    land(idIndex[id],options);return true;
  },
  selectStance:function(id){
    const stance=D.stances.find(s=>s.id===id);
    if(id!=='all'&&!stance)return false;
    morphTo(id==='all'?'all':stance.key);return true;
  },
  visit:visit
});
