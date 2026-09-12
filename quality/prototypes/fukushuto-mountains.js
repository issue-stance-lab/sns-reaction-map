/* Target-specific counts only: height does not encode unreviewed intensity. */
let mountainSelection=null;
function drawMountains(rows,total,targetLabel){
 const box=$('target-issues');box.replaceChildren();
 const note=document.createElement('p');note.className='note';note.textContent='山の幅は投稿の件数を表します。高さはすべて同じです。山または論点名を押すと、件数と割合を見られます。';box.append(note);
 const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 900 200');svg.setAttribute('class','mountains');svg.setAttribute('role','group');svg.setAttribute('aria-label',targetLabel+'の議論の山なみ');
 const active=rows.filter(x=>x.count>0);let left=0;
 const colors=['#38698b','#7d5ba6','#2f8f83','#a46d32','#5163a0','#916678','#64777b'];
 const buttons=document.createElement('div');buttons.className='mountain-keys';
 rows.forEach((r,i)=>{
 const color=colors[i];const b=document.createElement('button');b.type='button';b.textContent=`${r.name} ${fmt(r.count)}件`;b.style.borderLeft='5px solid '+color;b.setAttribute('aria-pressed',String(mountainSelection===r.name));b.onclick=()=>select(r.name);buttons.append(b);
 if(!r.count||!total)return;
 const width=900*r.count/total;const path=document.createElementNS(ns,'path');path.setAttribute('d',`M${left},180 Q${left+width*.2},180 ${left+width*.4},40 Q${left+width*.5},5 ${left+width*.6},40 Q${left+width*.8},180 ${left+width},180 Z`);path.setAttribute('fill',color);path.setAttribute('tabindex','0');path.setAttribute('role','button');path.setAttribute('aria-label',`${r.name} ${r.count}件`);path.setAttribute('aria-pressed',String(mountainSelection===r.name));path.onclick=()=>select(r.name);path.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(r.name)}};svg.append(path);left+=width;
 });
 box.append(svg,buttons);
 const panel=document.createElement('div');panel.id='mountain-detail';panel.className='mountain-detail';panel.hidden=mountainSelection===null;box.append(panel);
 function select(name){mountainSelection=name;update();panel.querySelector('h3').scrollIntoView({block:'nearest',behavior:'auto'});}
 function update(){
 if(mountainSelection===null)return;
 const r=rows.find(x=>x.name===mountainSelection);if(!r)return;
 panel.hidden=false;panel.replaceChildren();
 buttons.querySelectorAll('button').forEach((b,i)=>b.setAttribute('aria-pressed',String(rows[i].name===r.name)));
 svg.querySelectorAll('path').forEach((p,i)=>p.setAttribute('aria-pressed',String(active[i].name===r.name)));
 const h=document.createElement('h3');h.textContent=r.name;panel.append(h);
 const pct=total?100*r.count/total:0;const description=document.createElement('p');description.id='matrix-description';description.textContent=`${targetLabel}：${fmt(total)}件のうち、${r.name}は${fmt(r.count)}件（${pct.toFixed(1)}%）。`;panel.append(description);
 const grid=document.createElement('div');grid.className='waffle';grid.setAttribute('aria-hidden','true');const lit=Math.round(pct);for(let i=0;i<100;i++){const cell=document.createElement('span');if(i<lit)cell.style.background=colors[rows.indexOf(r)];grid.append(cell)}panel.append(grid);
 const caption=document.createElement('p');caption.className='note';caption.textContent=total?'100マスが選択中の投稿全体、色つきがこの論点です。1マス＝約1%。端数は四捨五入しています。':'選択中の投稿は0件です。割合を計算できないため、色つきのマスはありません。';panel.append(caption);
 const baseline=D.issues.find(x=>x.name===r.name);const stats=document.createElement('div');stats.className='matrix-stats';
 for(const [label,value] of [['選択中の件数',`${fmt(r.count)}件`],['選択中での割合',total?`${pct.toFixed(1)}%`:'—'],['全意見での件数',`${fmt(baseline.after)}件`],['全意見での割合',`${(100*baseline.after/D.candidate_opinions).toFixed(1)}%`]]){const card=document.createElement('div');const l=document.createElement('span');l.textContent=label;const v=document.createElement('strong');v.textContent=value;card.append(l,v);stats.append(card)}panel.append(stats);const link=document.createElement("a");link.href="#reader-issue-"+D.issues.findIndex(x=>x.name===r.name);link.textContent="この論点の図解を見る →";panel.append(link);
 }
 update();
}
