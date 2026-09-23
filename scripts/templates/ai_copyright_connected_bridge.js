// バー↔山の立場共有（工程2）。論点を選んだときの読書面はまだ無く、drawPanel()は
// 工程3まで無変更のまま（bukatsu-chiiki版と同じ設計、扱う立場が3つな点だけが違う）。
(function(){
  // この橋渡しは buildModes() より前（/* ---------- 初期化 ---------- */の直前）に
  // 挿し込まれる。#modes の中身はまだ空なので、個々のボタンへ直接listenerを付けると
  // 何も登録されない。#modes 自体（常に存在する入れ物）への委譲で、後から生まれる
  // ボタンにも効くようにする。STANCE_GLANCE側は静的HTMLで最初から存在するため、
  // 個別付与のままでよい。
  var glanceButtons = document.querySelectorAll('#stance-glance-buttons .sg-pick-btn');
  var modesBox = document.getElementById('modes');

  function stanceAt(i){ return D.stances[i] || null; }

  function syncGlance(modeId){
    glanceButtons.forEach(function(btn, i){
      var s = stanceAt(i);
      btn.setAttribute('aria-pressed', String(!!s && s.key === modeId));
    });
  }
  function syncModes(modeId){
    if (!modesBox) return;
    modesBox.querySelectorAll('[data-m]').forEach(function(btn){
      btn.setAttribute('aria-pressed', String(btn.dataset.m === modeId));
    });
  }

  // STANCE_GLANCEは表示だけの装置として作られている（自分の中だけで完結する）。
  // 山を動かす呼び出しをここで追加する。既存のonclickは残したまま、別のlistenerを足す。
  glanceButtons.forEach(function(btn, i){
    btn.addEventListener('click', function(){
      var s = stanceAt(i);
      if (!s || !modeById[s.key]) return;
      morphTo(s.key);
      syncModes(s.key);
    });
  });
  // #modesは既存のonclickでmorphTo()を直接呼ぶ。STANCE_GLANCE側の見た目をここで揃える。
  // 「すべて」はSTANCE_GLANCE側に対応ボタンが無いため、押下状態だけを揃える。
  if (modesBox){
    modesBox.addEventListener('click', function(e){
      var btn = e.target.closest('[data-m]');
      if (!btn) return;
      var i = D.stances.findIndex(function(s){ return s.key === btn.dataset.m; });
      if (i >= 0 && glanceButtons[i]) glanceButtons[i].click();
      else syncGlance(btn.dataset.m);
    });
  }
  syncGlance(st.mode);
  syncModes(st.mode);

  window.AiCopyrightConnectedMap = Object.freeze({
    getState: function(){
      var stance = D.stances.find(function(s){ return s.key === st.mode; });
      return Object.freeze({
        stanceId: stance ? stance.id : 'all',
        issueId: st.landed === null ? null : issues[st.landed].id
      });
    },
    selectStance: function(id){
      if (id === 'all'){ morphTo('all'); syncGlance('all'); syncModes('all'); return true; }
      var stance = D.stances.find(function(s){ return s.id === id; });
      if (!stance) return false;
      morphTo(stance.key);
      syncGlance(stance.key);
      syncModes(stance.key);
      return true;
    }
  });
})();
