/* 課題77・副首都の中心配置。立場→山→論点→読書面を一続きにする。 */
(function(){
  'use strict';
  var node=document.getElementById('fukushuto-connected-data'),map=window.FukushutoConnectedMap;
  if(!node||!map)return;
  var index,data=window.PLANET_DATA,bar=document.getElementById('stance-glance'),planet=document.getElementById('planet-block'),panel=document.getElementById('panel');
  try{index=JSON.parse(node.textContent);}catch(_){return;}
  if(!data||data.theme_id!=='fukushuto'||!bar||!planet||!panel)return;
  if(data.issues.some(function(it){return !document.getElementById('fukushuto-reading-'+it.id);}))return;
  var fmt=function(n){return n.toLocaleString('ja-JP');},ratio=function(n,total){return total?(100*n/total).toFixed(1)+'%':'算出できません';};
  var mountain=planet.closest('.planet-panel'); if(mountain)bar.before(mountain);
  var modes=document.getElementById('modes'); if(modes)modes.before(bar);
  var headline=bar.querySelector('.sg-headline');if(headline)headline.hidden=true;
  var list=document.getElementById('list'),oldHeading=list&&list.previousElementSibling;
  if(oldHeading&&oldHeading.matches('h3.sec'))oldHeading.hidden=true;
  if(list){list.setAttribute('aria-label','論点を切り替える');panel.before(list);}
  if(modes)modes.querySelectorAll('button').forEach(function(button){
    var mode=data.modes.find(function(item){return item.id===button.dataset.m;});if(!mode)return;
    var stance=data.stances.find(function(item){return item.key===mode.id;});button.replaceChildren();
    var label=document.createElement('span');label.className='fuk-mode-name';label.textContent=stance?stance.label:'すべて';
    var count=document.createElement('strong');count.textContent=fmt(mode.total)+'件';button.append(label,count);
    if(stance){button.classList.add('sg-pick-btn');button.style.setProperty('--fuk-stance-color',stance.color);var share=document.createElement('small');share.textContent=ratio(mode.total,data.totals.opinions);count.append(' ',share);}
    button.setAttribute('aria-label',mode.label+' '+fmt(mode.total)+'件');
  });
  var guesses=document.getElementById('guesses');if(guesses&&!guesses.closest('.fuk-guesses')){var details=document.createElement('details');details.className='fuk-guesses';details.innerHTML='<summary>予想してから読む · 2問</summary>';guesses.before(details);details.appendChild(guesses);}
  var hint=document.querySelector('#planet-block .chart-box .hint');if(hint)hint.textContent='山を押すと、その論点の理由・投稿・資料を読めます（面積＝強く語られた投稿の数）。';
  var meta=document.getElementById('meta');if(meta)meta.textContent='山ひとつが論点ひとつです。幅は選んだ立場の意見数、高さはその中で強い表現に分類された投稿の割合です。立場を選ぶと同じ色で山を見比べられます。左右の並び順は固定で、順位を示しません。';
  document.body.classList.add('fukushuto-connected');
  var section=document.getElementById('section');if(section){var box;try{box=section.getBBox();}catch(_){box=null;}if(box&&box.height){section.setAttribute('viewBox','0 '+Math.max(0,box.y-6)+' 900 '+(box.height+12));section.setAttribute('preserveAspectRatio','none');}}
  var embedSources=new WeakMap();function loadEmbeds(){if(!window.twttr||!window.twttr.widgets)return;panel.querySelectorAll('.fuk-embed[open]').forEach(function(holder){if(!holder.getClientRects().length)return;if(holder.dataset.fukWidgetRequested&&!holder.querySelector('blockquote.twitter-tweet-error'))return;if(!holder.dataset.fukWidgetRequested){embedSources.set(holder,holder.cloneNode(true));holder.dataset.fukWidgetRequested='true';}try{Promise.resolve(window.twttr.widgets.load(holder)).then(function(){if(holder.querySelector('blockquote.twitter-tweet-error')){var src=embedSources.get(holder);if(src)holder.replaceChildren(src.cloneNode(true));delete holder.dataset.fukWidgetRequested;}}).catch(function(){});}catch(_){}});}
  function twitterReady(){loadEmbeds();if(window.twttr&&window.twttr.ready)window.twttr.ready(loadEmbeds);}document.querySelectorAll('script[src="https://platform.twitter.com/widgets.js"]').forEach(function(script){script.addEventListener('load',twitterReady);});twitterReady();
  panel.addEventListener('toggle',function(event){if(event.target.matches('.fuk-embed'))loadEmbeds();},true);
})();
