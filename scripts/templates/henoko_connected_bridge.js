// 山の立場フィルター、論点パネル、選択色、480msの変形、固定リンクを一つの状態へ結ぶ。
(function(){
  var glanceButtons = document.querySelectorAll('#stance-glance-buttons .sg-pick-btn');
  var modesBox = document.getElementById('modes');
  function stanceAt(i){ return D.stances[i] || null; }
  function syncGlance(modeId){
    glanceButtons.forEach(function(btn, i){
      var stance = stanceAt(i);
      btn.setAttribute('aria-pressed', String(!!stance && stance.key === modeId));
    });
  }
  function syncModes(modeId){
    if (!modesBox) return;
    modesBox.querySelectorAll('[data-m]').forEach(function(btn){
      btn.setAttribute('aria-pressed', String(btn.dataset.m === modeId));
    });
  }
  glanceButtons.forEach(function(btn, i){
    btn.addEventListener('click', function(){
      var stance = stanceAt(i);
      if (!stance || !modeById[stance.key]) return;
      morphTo(stance.key); syncModes(stance.key);
    });
  });
  if (modesBox) modesBox.addEventListener('click', function(event){
    var btn = event.target.closest('[data-m]');
    if (!btn) return;
    var i = D.stances.findIndex(function(s){ return s.key === btn.dataset.m; });
    if (i >= 0 && glanceButtons[i]) glanceButtons[i].click();
    else if (btn.dataset.m === 'all') morphTo('all');
  });

  var legacyDrawPanel = drawPanel;
  function readingTemplateFor(id){ return document.getElementById('henoko-student-accident-reading-' + id); }
  function fillMetrics(root, issue){
    var mode = modeById[st.mode], n = mode.counts[issue.id] || 0;
    var count = root.querySelector('[data-henoko-count]');
    var label = root.querySelector('[data-henoko-mode]');
    var ratio = root.querySelector('[data-henoko-ratio]');
    var zero = root.querySelector('[data-henoko-zero]');
    if (count) count.textContent = n.toLocaleString('ja-JP');
    if (label) label.textContent = '件 / ' + mode.label + mode.total.toLocaleString('ja-JP') + '件中';
    if (n && mode.total){
      if (ratio){ ratio.textContent = (100*n/mode.total).toFixed(1) + '%　高さ：強い表現 ' + (mode.high_pct[issue.id] || 0) + '%'; ratio.hidden = false; }
      if (zero) zero.hidden = true;
    } else {
      if (ratio) ratio.hidden = true;
      if (zero){ zero.textContent = 'この立場では0件です。'; zero.hidden = false; }
    }
  }
  function renderReading(id){
    var tpl = readingTemplateFor(id), panel = document.getElementById('panel');
    if (!tpl || !panel) return;
    panel.setAttribute('data-henoko-issue-id', id);
    panel.innerHTML = '';
    panel.appendChild(tpl.content.cloneNode(true));
    fillMetrics(panel, issues[idIndex[id]]);
    var back = document.createElement('button');
    back.type = 'button'; back.className = 'back'; back.id = 'back';
    back.textContent = '← 論点の一覧へ戻る（Esc）';
    back.addEventListener('click', orbit); panel.appendChild(back);
  }
  drawPanel = function(){
    if (st.landed === null){
      document.getElementById('panel').removeAttribute('data-henoko-issue-id');
      legacyDrawPanel(); return;
    }
    var id = issues[st.landed].id;
    if (!readingTemplateFor(id)){ legacyDrawPanel(); return; }
    renderReading(id);
  };

  var henokoVisual = null, henokoAnimation = 0, legacyLayout = layout;
  layout = function(modeId){ return henokoVisual && modeId === st.mode ? henokoVisual : legacyLayout(modeId); };
  function recolorHills(){
    var stance = D.stances.find(function(s){ return s.key === st.mode; });
    var color = stance ? stance.color : '#075ef2';
    svg.querySelectorAll('.hill').forEach(function(group){
      var path = group.querySelector('path'); if (!path) return;
      var landed = st.landed !== null && Number(group.dataset.i) === st.landed;
      path.setAttribute('fill', color);
      path.setAttribute('opacity', String(st.landed === null ? 0.6 : (landed ? 0.9 : 0.23)));
      if (landed){ path.setAttribute('stroke', '#f2f6fa'); path.setAttribute('stroke-width', '1.8'); path.removeAttribute('stroke-dasharray'); }
      else if (path.getAttribute('stroke-dasharray')) path.setAttribute('stroke', color);
      else path.removeAttribute('stroke');
      var zero = group.querySelector('.zero-mark'); if (zero) zero.setAttribute('fill', color);
    });
  }
  var legacyRender = render;
  render = function(){
    var focused = document.activeElement, focusId = focused && focused.classList && focused.classList.contains('hill') ? focused.dataset.i : null;
    legacyRender(); recolorHills();
    if (focusId !== null){
      var next = svg.querySelector('.hill[data-i="' + focusId + '"]');
      if (next) next.focus({preventScroll:true});
    }
  };
  function animate(from, to){
    cancelAnimationFrame(henokoAnimation);
    if (reduce){ henokoVisual = null; render(); return; }
    var start = performance.now();
    var byId = function(list){ var map = new Map(); list.forEach(function(value){ map.set(value.it.id, value); }); return map; };
    var a = byId(from.live), b = byId(to.live);
    var keys = issues.map(function(issue){ return issue.id; }).filter(function(id){ return a.has(id) || b.has(id); });
    function zero(value){ return Object.assign({}, value, {x0:value.cx,x1:value.cx,w:0,top:SEA,n:0,hi:0,rate:0,share:0}); }
    function frame(now){
      var t = Math.min(1, (now-start)/480), f = 1-Math.pow(1-t,3);
      henokoVisual = Object.assign({}, to, {live:keys.map(function(id){
        var end=b.get(id), begin=a.get(id), left=begin||zero(end), right=end||zero(begin), value=Object.assign({},right);
        ['x0','x1','cx','w','top','n','hi','rate','share'].forEach(function(key){ value[key]=left[key]+(right[key]-left[key])*f; });
        value.n=Math.round(value.n); value.hi=Math.round(value.hi); value.clipped=value.rate>Y_MAX; return value;
      })});
      render();
      if (t<1) henokoAnimation=requestAnimationFrame(frame); else { henokoVisual=null; henokoAnimation=0; render(); }
    }
    henokoAnimation=requestAnimationFrame(frame);
  }
  morphTo = function(toMode){
    if (!modeById[toMode] || toMode === st.mode) return;
    var from=henokoVisual||legacyLayout(st.mode);
    st.prevRank=ranksOf(st.mode); st.mode=toMode;
    if (st.landed!==null && modeById[toMode].counts[issues[st.landed].id]===0){
      st.landed=null; if (location.hash) history.replaceState(null,'',location.pathname);
    }
    evacuateChart(); drawPanel(); syncList(); placeChart(); animate(from,legacyLayout(toMode));
    syncGlance(toMode); syncModes(toMode);
    if (window.innerWidth<820) bringIntoView(document.querySelector('#panel h2')||document.getElementById('panel'));
  };
  function landSilently(i){ var real=bringIntoView; bringIntoView=function(){}; land(i); bringIntoView=real; }
  function issueIdFromHash(){
    var hash=location.hash.slice(1);
    if (Object.prototype.hasOwnProperty.call(idIndex,hash)) return hash;
    for (var prefix of ['issue-','fb-']) if (hash.indexOf(prefix)===0 && Object.prototype.hasOwnProperty.call(idIndex,hash.slice(prefix.length))) return hash.slice(prefix.length);
    return null;
  }
  function initialLand(){
    var id=issueIdFromHash();
    if (id!==null) landSilently(idIndex[id]);
    else if (!location.hash && st.landed===null){
      var top=issues.reduce(function(a,b){ return b.count>a.count?b:a; }); landSilently(idIndex[top.id]);
    }
    if (st.landed!==null && !document.getElementById('panel').querySelector('.henoko-selected-head')) landSilently(st.landed);
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',initialLand,{once:true}); else initialLand();
  window.addEventListener('hashchange',function(){
    var id=issueIdFromHash();
    if (id!==null && (st.landed===null || issues[st.landed].id!==id)) landSilently(idIndex[id]);
    else if (!location.hash && st.landed!==null) orbit();
  });
  var lastTrackedIssue=null;
  function trackIssueView(id){ if(typeof window.gtag!=='function'||id===lastTrackedIssue)return; lastTrackedIssue=id; window.gtag('event','issue_view',{issue_id:id}); }
  var trackedDraw=drawPanel;
  drawPanel=function(){ trackedDraw(); if(st.landed!==null) trackIssueView(issues[st.landed].id); };
  var panelForTracking=document.getElementById('panel');
  if(panelForTracking) panelForTracking.addEventListener('click',function(event){
    var link=event.target.closest('a[target="_blank"]');
    if(!link||typeof window.gtag!=='function')return;
    window.gtag('event','citation_click',{issue_id:st.landed===null?null:issues[st.landed].id,outbound_url:link.href});
  });
  window.HenokoConnectedMap=Object.freeze({
    getState:function(){ var stance=D.stances.find(function(s){return s.key===st.mode;}); return {stanceId:stance?stance.id:'all',issueId:st.landed===null?null:issues[st.landed].id}; },
    selectIssue:function(id){ if(id===null){orbit();return true;} if(!Object.prototype.hasOwnProperty.call(idIndex,id))return false; land(idIndex[id]);return true; },
    selectStance:function(id){ if(id==='all'){morphTo('all');return true;} var stance=D.stances.find(function(s){return s.id===id;}); if(!stance)return false; morphTo(stance.key);return true; }
  });
  syncGlance(st.mode); syncModes(st.mode);
})();
