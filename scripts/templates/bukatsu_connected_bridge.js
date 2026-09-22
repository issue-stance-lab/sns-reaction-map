// バー↔山の立場共有。既存のrender/layout/land/morphToは上書きせず、
// STANCE_GLANCE・#modesの両方へ「もう一方も揃える」監視を追加するだけに留める
// （工程2の範囲。論点の理由・投稿例・資料の読書面は工程3以降）。
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
  // 「議論の中身」の文言はSTANCE_GLANCE自身のscript内に閉じている（DATA配列がここから
  // 見えない）ため、ここで作り直さず、対応するSTANCE_GLANCEボタン自体をクリックさせて
  // 既存の表示処理をそのまま使う（同じ文言が2通りに分かれるのを避ける）。
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

  window.BukatsuConnectedMap = Object.freeze({
    getState: function(){
      var stance = D.stances.find(function(s){ return s.key === st.mode; });
      return Object.freeze({
        stanceId: stance ? stance.id : 'all',
        issueId: st.landed === null ? null : issues[st.landed].id
      });
    },
    selectIssue: function(id){
      if (id === null){ orbit(); return true; }
      if (!Object.prototype.hasOwnProperty.call(idIndex, id)) return false;
      land(idIndex[id]);
      return true;
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
