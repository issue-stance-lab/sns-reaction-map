/* 課題77・辺野古の中心配置。山、立場、読書面を一つの導線へ並べ替える。 */
(function(){
  'use strict';
  function ready(fn){ if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',fn,{once:true}); else fn(); }
  ready(function(){
    var node=document.getElementById('henoko-connected-data'), map=window.HenokoConnectedMap;
    if(!node||!map)return;
    var index; try{index=JSON.parse(node.textContent);}catch(_){return;}
    var data=window.PLANET_DATA, bar=document.getElementById('stance-glance'), planet=document.getElementById('planet-block'), panel=document.getElementById('panel');
    if(!data||data.theme_id!=='henoko-student-accident'||!bar||!planet||!panel)return;
    if(data.issues.some(function(it){return !document.getElementById('henoko-student-accident-reading-'+it.id);}))return;
    var fmt=function(n){return Number(n||0).toLocaleString('ja-JP');};
    var mountain=planet.closest('.planet-panel');
    if(mountain && bar.nextElementSibling!==mountain) bar.before(mountain);
    var modes=document.getElementById('modes');
    if(modes) modes.before(bar);
    var headline=bar.querySelector('.sg-headline'); if(headline)headline.hidden=true;
    var list=document.getElementById('list'), oldHeading=list&&list.previousElementSibling;
    if(oldHeading&&oldHeading.matches('h3.sec'))oldHeading.hidden=true;
    if(list){list.setAttribute('aria-label','論点を切り替える'); if(panel)panel.before(list);}
    if(modes) modes.querySelectorAll('button').forEach(function(button){
      var mode=data.modes.find(function(item){return item.id===button.dataset.m;}); if(!mode)return;
      var stance=data.stances.find(function(item){return item.key===mode.id;});
      button.replaceChildren();
      var label=document.createElement('span'); label.className='henoko-mode-name'; label.textContent=stance?stance.label:'すべての意見';
      var count=document.createElement('strong'); count.textContent=fmt(mode.total)+'件'; button.append(label,count);
      if(stance){button.classList.add('sg-pick-btn');button.style.setProperty('--henoko-stance-color',stance.color);}
      button.setAttribute('aria-label',mode.label+' '+fmt(mode.total)+'件');
    });
    var guesses=document.getElementById('guesses');
    if(guesses&&!guesses.closest('.henoko-guesses')){
      var details=document.createElement('details'); details.className='henoko-guesses'; details.innerHTML='<summary>予想してから読む · 2問</summary>';
      guesses.before(details); details.appendChild(guesses);
    }
    var hint=document.querySelector('#planet-block .chart-box .hint');
    if(hint)hint.textContent='山を押すと、その論点の理由・資料・一次資料クイズを読めます。';
    var meta=document.getElementById('meta');
    if(meta)meta.textContent='山ひとつが論点ひとつです。幅は選んだ立場の意見数、高さは強い表現の割合です。立場を選ぶと同じ色で山を見比べられます。';
    document.body.classList.add('henoko-connected');
    var section=document.getElementById('section');
    if(section){var box;try{box=section.getBBox();}catch(_){box=null;}if(box&&box.height){section.setAttribute('viewBox','0 '+Math.max(0,box.y-8)+' 900 '+(box.height+16));section.setAttribute('preserveAspectRatio','none');}}
    function openImage(event){
      var button=event.target.closest('[data-henoko-image]'); if(!button)return;
      var image=button.querySelector('img'); if(!image)return;
      var dialog=document.createElement('dialog'); dialog.className='henoko-image-dialog';
      dialog.innerHTML='<button type="button" class="henoko-dialog-close" aria-label="閉じる">×</button><img alt="">';
      dialog.querySelector('img').src=image.currentSrc||image.src; dialog.querySelector('img').alt=image.alt;
      dialog.addEventListener('click',function(e){if(e.target===dialog||e.target.classList.contains('henoko-dialog-close'))dialog.close();});
      document.body.appendChild(dialog); dialog.showModal(); dialog.addEventListener('close',function(){dialog.remove();},{once:true});
    }
    document.addEventListener('click',openImage);
    var observer=new MutationObserver(function(){mountPanel();});
    observer.observe(panel,{childList:true,subtree:true,attributes:true,attributeFilter:['data-henoko-issue-id']});
    function mountPanel(){
      var reading=panel.querySelector('.henoko-reading'), evidence=panel.querySelector('.henoko-evidence');
      if(!reading||!evidence)return;
      if(!evidence.querySelector('.henoko-evidence-tabs')){
        var tabs=document.createElement('div'); tabs.className='henoko-evidence-tabs'; tabs.setAttribute('role','tablist');
        tabs.innerHTML='<button type="button" data-henoko-tab="read" role="tab" aria-selected="true">資料を読む</button><button type="button" data-henoko-tab="discover" role="tab" aria-selected="false">X投稿で語られない話</button>'+((data.claims||[]).length?'<button type="button" data-henoko-tab="quiz" role="tab" aria-selected="false">一次資料クイズ</button>':'');
        evidence.insertBefore(tabs,evidence.querySelector('.henoko-reading-sources'));
        tabs.addEventListener('click',function(event){var button=event.target.closest('[data-henoko-tab]');if(button)setTab(evidence,button.dataset.henokoTab);});
      }
      if((data.claims||[]).length&&!evidence.querySelector('.henoko-quiz-panel')){
        var quiz=document.createElement('div');quiz.className='henoko-quiz-panel';quiz.hidden=true;evidence.appendChild(quiz);buildQuiz(quiz);
      }
      setTab(evidence,evidence.dataset.henokoTab||'read');
    }
    function setTab(evidence,tab){
      evidence.dataset.henokoTab=tab;
      evidence.querySelectorAll('[data-henoko-tab]').forEach(function(button){var active=button.dataset.henokoTab===tab;button.setAttribute('aria-selected',String(active));});
      var sourcesBox=evidence.querySelector('.henoko-reading-sources'), quiz=evidence.querySelector('.henoko-quiz-panel');
      if(sourcesBox)sourcesBox.hidden=tab==='quiz';
      if(sourcesBox&&tab==='discover')sourcesBox.classList.add('henoko-discover-mode');else if(sourcesBox)sourcesBox.classList.remove('henoko-discover-mode');
      if(quiz)quiz.hidden=tab!=='quiz';
      if(typeof window.gtag==='function'&&tab!=='read')window.gtag('event','henoko_material_tab',{tab:tab,issue_id:panel.dataset.henokoIssueId||null});
    }
    function buildQuiz(box){
      var claims=data.claims||[], verdicts=['fact','gap','miss'];
      if(!claims.length){box.remove();return;}
      var current=0,score=0;
      function paint(){
        if(current>=claims.length){box.innerHTML='<p class="henoko-quiz-score">'+score+' / '+claims.length+'問正解</p><p class="henoko-note">公開された一次資料を、投稿にあった主張と照合した結果です。</p>';return;}
        var claim=claims[current], fallback={fact:'資料どおり',gap:'少しずれる',miss:'裏が取れない'}, labels=verdicts.map(function(v){var same=claims.find(function(x){return x.verdict===v;});return same?(same.verdict_label||v):fallback[v];});
        box.innerHTML='<p class="henoko-quiz-progress">問 '+(current+1)+' / '+claims.length+'</p><p class="henoko-quiz-claim">「'+escapeHtml(claim.claim)+'」</p><div class="henoko-quiz-options">'+labels.map(function(label,i){return '<button type="button" data-answer="'+i+'">'+escapeHtml(label)+'</button>';}).join('')+'</div><div class="henoko-quiz-answer" hidden></div>';
        box.querySelectorAll('[data-answer]').forEach(function(button){button.addEventListener('click',function(){
          var pick=Number(button.dataset.answer), right=verdicts.indexOf(claim.verdict); if(pick===right)score++;
          box.querySelectorAll('[data-answer]').forEach(function(other,i){other.disabled=true;other.classList.toggle('is-right',i===right);other.classList.toggle('is-wrong',i===pick&&i!==right);});
          var answer=box.querySelector('.henoko-quiz-answer');answer.hidden=false;answer.innerHTML='<p><b>'+escapeHtml(claim.verdict_label||claim.verdict)+'</b>　'+escapeHtml(claim.finding)+'</p><div class="henoko-sources">'+(claim.sources||[]).map(function(src){return '<a href="'+escapeAttr(src.url)+'" target="_blank" rel="noopener nofollow">'+escapeHtml(src.name)+'</a>';}).join('')+'</div><button type="button" class="henoko-quiz-next">'+(current===claims.length-1?'結果を見る':'次の問題 →')+'</button>';
          var next=answer.querySelector('.henoko-quiz-next');next.addEventListener('click',function(){current++;paint();});
          var issue=(claim.issue_ids||[])[0];if(issue&&map.selectIssue)map.selectIssue(issue);
        });});
      }
      paint();
    }
    function escapeHtml(value){return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
    function escapeAttr(value){return escapeHtml(value).replace(/'/g,'&#39;');}
    var originalLand=map.selectIssue;
    window.addEventListener('keydown',function(event){if(event.key==='Escape'&&panel.dataset.henokoIssueId){event.preventDefault();originalLand(null);}});
    mountPanel();
    if(window.HenokoConnectedMap){
      var state=window.HenokoConnectedMap.getState(); if(state.issueId)map.selectIssue(state.issueId);
    }
  });
})();
