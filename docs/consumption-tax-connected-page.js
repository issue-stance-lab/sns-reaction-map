/* 連動表示のページ全体。原稿は既存DOMとPLANET_DATA、回答状態は閲覧・投票から独立。 */
(function () {
  'use strict';
  if (!document.body.classList.contains('tax-connected')) return;
  const map = window.ConsumptionTaxMap, data = window.PLANET_DATA;
  const index = JSON.parse(document.getElementById('tax-connected-data').textContent);
  const panel = document.getElementById('panel');
  const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const esc = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  function moveTo(element) {
    if (!element) return;
    element.scrollIntoView({block:'start', behavior:reduce()?'auto':'smooth'});
    element.tabIndex = -1; element.focus({preventScroll:true});
  }

  // 読む前に必要な現状だけを残し、長い年表は山と読書面の後へ移す。
  const mountain = document.getElementById('planet-block').closest('.planet-panel');
  const background = document.getElementById('bukatsu-background');
  const status = document.createElement('aside');
  status.className = 'tax-status';
  status.innerHTML = '<p class="tax-eyebrow">制度の確認時点 '+esc(index.background_checked_on)+'</p><p>'
    +esc(background.querySelector('.bg-now').textContent)+'</p><a href="#bg-title">制度の経緯を確かめる ↓</a>';
  mountain.before(status); mountain.after(background);
  const timeline = background.querySelector('.bg-tl');
  const intro = document.createElement('details'); intro.className = 'tax-background-intro';
  intro.innerHTML = '<summary>政策の背景を読む</summary>';
  for (const child of [...background.children]) {
    if (child === timeline) break;
    if (!child.classList.contains('panel-title')) intro.appendChild(child);
  }
  // 年表の直前の見出しは操作の見出しで代わりに示す。
  if (intro.lastElementChild?.matches('h3')) intro.lastElementChild.remove();
  background.querySelector('.panel-title').after(intro);
  const timelineNav = document.createElement('div');
  timelineNav.className = 'tax-timeline-nav'; timelineNav.setAttribute('role','tablist');
  timelineNav.setAttribute('aria-label','制度の経緯の日付'); timeline.before(timelineNav);
  const events = [...timeline.querySelectorAll('[data-timeline-id]')];
  function selectDate(selected, focus) {
    events.forEach((event, i) => {
      const active = selected === i, button = timelineNav.children[i];
      event.hidden = !active; button.setAttribute('aria-selected',String(active)); button.tabIndex=active?0:-1;
    });
    if(focus) timelineNav.children[selected].focus();
  }
  events.forEach((event, i) => {
    const button = document.createElement('button'); button.type='button'; button.id='tax-date-'+i;
    button.textContent=[...event.querySelector('.when').childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();
    button.setAttribute('role','tab'); event.id='tax-'+event.dataset.timelineId;
    button.setAttribute('aria-controls',event.id); event.setAttribute('role','tabpanel'); event.setAttribute('aria-labelledby',button.id);
    button.onclick=()=>selectDate(i,false);
    button.onkeydown=event=>{
      const next=event.key==='ArrowRight'?(i+1)%events.length:event.key==='ArrowLeft'?(i+events.length-1)%events.length:event.key==='Home'?0:event.key==='End'?events.length-1:null;
      if(next!==null){event.preventDefault();selectDate(next,true);}
    };
    timelineNav.appendChild(button);
  });
  selectDate(events.length-1,false);
  background.querySelector('.bg-jump a').textContent='選んだ論点に戻る ↑';
  const tide = document.getElementById('consumption-tax-cut-tide-widget');
  if (tide) {
    const heading=document.createElement('h2');heading.textContent='収集した投稿の変化';tide.prepend(heading);
    const note=document.createElement('p');note.className='tax-comparison-note';
    note.textContent='制度の経緯と、投稿サンプルの比較は別の情報です。この差だけで、制度決定の影響や同じ人の意見の変化は判断できません。';
    tide.appendChild(note);
  }
  function fold(element, label) {
    if(!element)return;
    const details=document.createElement('details');details.className='tax-fold';
    const summary=document.createElement('summary');summary.textContent=label;
    element.before(details);details.append(summary,element);
  }
  fold(document.getElementById('editorial'),'編集部の横断整理を読む');
  const meta=document.getElementById('meta');if(meta?.previousElementSibling?.matches('h3'))meta.previousElementSibling.hidden=true;
  fold(meta,'図の見かたを確かめる');

  // 元のクイズ6問を資料欄へ移す。本文の資料と同じclaimを参照し、進捗IDも共用する。
  const quizRoot=document.getElementById('quiz');
  if(quizRoot.previousElementSibling?.matches('h3'))quizRoot.previousElementSibling.hidden=true;
  quizRoot.remove();
  const quiz={active:false,position:0,answers:new Map()}, verdicts=['fact','gap','miss'];
  let selectingForQuiz=false;
  const claimIssue=claim=>data.issues.find(i=>i.claims.some(c=>c.id===claim.id)).id;
  const verdictLabel=value=>data.claims.find(c=>c.verdict===value)?.verdict_label||({fact:'資料どおり',gap:'少しずれる',miss:'裏が取れない'}[value]);
  function mount() {
    const aside=panel.querySelector('.tax-evidence');
    if(!aside){quiz.active=false;quizRoot.remove();return;}
    const claim=data.claims[quiz.position];
    if(quiz.active && claim && !selectingForQuiz && map.getState().issueId!==claimIssue(claim))quiz.active=false;
    if(!aside.querySelector('.tax-evidence-controls')){
      const reading=document.createElement('div');reading.className='tax-reading-sources';
      reading.append(...aside.childNodes);
      const controls=document.createElement('div');controls.className='tax-evidence-controls';controls.setAttribute('aria-label','資料の読み方');
      controls.innerHTML='<button type="button" data-tax-read>資料を読む</button><button type="button" data-tax-quiz>一次資料クイズ · '+data.claims.length+'問</button>';
      controls.querySelector('[data-tax-read]').onclick=()=>{quiz.active=false;mount();};
      controls.querySelector('[data-tax-quiz]').onclick=()=>{quiz.active=true;showQuestion(quiz.position);};
      aside.append(controls,reading);
    }
    aside.querySelector('.tax-reading-sources').hidden=quiz.active;
    aside.querySelector('[data-tax-read]').setAttribute('aria-pressed',String(!quiz.active));
    aside.querySelector('[data-tax-quiz]').setAttribute('aria-pressed',String(quiz.active));
    quizRoot.hidden=!quiz.active;aside.appendChild(quizRoot);
    if(!panel.querySelector('.tax-evidence-jump')){
      const jump=document.createElement('button');jump.type='button';jump.className='tax-evidence-jump';jump.textContent='この論点の制度・資料へ ↓';
      jump.onclick=()=>moveTo(aside);panel.querySelector('.tax-scope-note').after(jump);
    }
  }
  function renderQuiz() {
    const claim=data.claims[quiz.position];
    if(!claim){
      const score=data.claims.filter(c=>quiz.answers.get(c.id)===c.verdict).length;
      quizRoot.innerHTML='<h3>資料クイズの結果</h3><p class="tax-quiz-score">'+score+' / '+data.claims.length+'問正解</p><p>回答済み '+quiz.answers.size+'問。本文の資料と同じ内容で照合しています。</p><button type="button" data-tax-restart>最初の問題へ</button><button type="button" data-tax-finish>資料に戻る</button>';
      quizRoot.querySelector('[data-tax-restart]').onclick=()=>showQuestion(0);
      quizRoot.querySelector('[data-tax-finish]').onclick=()=>{quiz.active=false;mount();};return;
    }
    const answer=quiz.answers.get(claim.id);
    quizRoot.innerHTML='<div class="qh" tabindex="-1"><span>問 '+(quiz.position+1)+' / '+data.claims.length+'</span><span>資料照合 '+esc(data.ocean.checked_on)+'</span></div>'
      +'<p class="tax-quiz-note">収集した投稿から選んだ主張です。掲載した投稿例2件への判定ではありません。</p>'
      +'<p class="qclaim">「'+esc(claim.claim)+'」</p><div class="gopts">'+verdicts.map(v=>'<button type="button" data-verdict="'+v+'" '+(answer?'disabled':'')+' class="'+(answer?(v===claim.verdict?'hit':v===answer?'miss':''):'')+'">'+esc(verdictLabel(v))+'</button>').join('')+'</div>'
      +'<div class="qans" '+(answer?'':'hidden')+'><p class="tax-verdict">'+esc(claim.verdict_label)+'</p><p>'+esc(claim.finding)+'</p><div class="tax-quiz-sources">'+claim.sources.map(s=>'<p><a href="'+esc(s.url)+'" target="_blank" rel="noopener noreferrer">'+esc(s.name)+'</a></p>').join('')+'</div><button type="button" class="qnext">'+(quiz.position===data.claims.length-1?'結果を見る':'次の問題 →')+'</button></div>';
    quizRoot.dataset.claimId=claim.id;
    quizRoot.querySelectorAll('[data-verdict]').forEach(button=>button.onclick=()=>{
      if(quiz.answers.has(claim.id))return;
      quiz.answers.set(claim.id,button.dataset.verdict);map.visit('c:'+claim.id);renderQuiz();
      quizRoot.querySelector('.qans').tabIndex=-1;quizRoot.querySelector('.qans').focus({preventScroll:true});
    });
    quizRoot.querySelector('.qnext').onclick=()=>showQuestion(quiz.position+1);
  }
  function showQuestion(position) {
    quiz.position=position;quiz.active=true;selectingForQuiz=true;
    const claim=data.claims[position];if(claim)map.selectIssue(claimIssue(claim));
    selectingForQuiz=false;renderQuiz();mount();
    const head=quizRoot.querySelector('.qh,h3');
    const bounds=head.getBoundingClientRect();if(bounds.top<110 || bounds.bottom>innerHeight)moveTo(head);else head.focus({preventScroll:true});
  }
  document.addEventListener('tax-map:render',mount);
  mount();

  // 離れた節から明示的に来たときだけ、本文へ移動する。既存のクリック計測は止めない。
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href^="#"]');if(!link)return;
    const hash=link.getAttribute('href').slice(1), issueId=hash.replace(/^(issue-|fb-)/,'');
    if(!index.issues[issueId])return;
    event.preventDefault();map.selectIssue(issueId);moveTo(panel.querySelector('h2'));
  },true);
  const vote=document.getElementById('vote-section');
  vote.querySelector('.panel-title > span').textContent='閲覧の切替とは別の、任意の投票';
  vote.querySelector(':scope > p').textContent='ページを読んで、いま最も気になる論点と、消費税減税への立場を選んでください。上の表示を切り替えただけでは投票されません。';

  // 授業ボタンは節のみ、ブラウザからの印刷は全本文。閉じた詳細も印刷中だけ展開する。
  // 非表示の一覧にある図解も先に読み込み、通常の印刷で選択外の画像が欠けるのを防ぐ。
  document.querySelectorAll('#fallback img').forEach(img=>{img.loading='eager';});
  // 旧一覧にない再読理由も同じ本文テンプレートから補う。印刷だけの別原稿は持たない。
  data.issues.forEach(issue=>{
    const reasons=document.getElementById('tax-reading-'+issue.id).content.querySelector('.tax-opinions').cloneNode(true);
    reasons.className='tax-print-reasons';reasons.setAttribute('aria-label','意見の理由');
    reasons.querySelector('.tax-posts').remove();
    reasons.querySelectorAll('[id]').forEach(element=>element.removeAttribute('id'));
    document.querySelector('#fb-'+issue.id+' .note').after(reasons);
  });
  const fallbackHeading=document.querySelector('#fallback > h3');
  const fallbackLabel=fallbackHeading.textContent;
  let printDetails=[];
  document.addEventListener('click',event=>{
    if(event.target.closest('.classroom-print-btn'))document.body.classList.add('tax-print-classroom');
  },true);
  addEventListener('beforeprint',()=>{
    document.body.classList.add('tax-printing');
    fallbackHeading.textContent='全'+data.issues.length+'論点の内容';
    printDetails=[...document.querySelectorAll('details:not([open])')];printDetails.forEach(d=>d.open=true);
  });
  addEventListener('afterprint',()=>{
    fallbackHeading.textContent=fallbackLabel;
    printDetails.forEach(d=>d.open=false);printDetails=[];document.body.classList.remove('tax-print-classroom','tax-printing');
  });
  // 過去のクイズ固定リンクも、現在の資料欄に到達させる。
  if(location.hash==='#quiz')showQuestion(0);
}());
