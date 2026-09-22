// バー↔山の立場共有（工程2）、論点を選んだときの読書面（工程3）、
// 立場を切り替えたときの山の滑らかな変化（工程3後追い、tax版の考え方を移植）。
// land/orbitは変えず、drawPanel・layout・render・morphToだけを差し替える。
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

  // ---------- 工程3: 論点を選んだときの読書面（理由・投稿・資料）への差し替え ----------
  // drawPanel()だけを差し替える。land()/orbit()/morphTo()は全てdrawPanel()を呼ぶため、
  // ここ1箇所で全ての入口をまとめて拾える。読書面が無い論点（テンプレート未生成）や
  // 「すべての論点」表示（st.landed===null）では、既存の描画をそのまま使う。
  var legacyDrawPanel = drawPanel;
  function readingTemplateFor(id){
    return document.getElementById('bukatsu-reading-' + id);
  }
  function fillMetrics(root, issue){
    var m = modeById[st.mode], n = m.counts[issue.id] || 0;
    var count = root.querySelector('[data-bkt-count]');
    var mode = root.querySelector('[data-bkt-mode]');
    var ratio = root.querySelector('[data-bkt-ratio]');
    var zero = root.querySelector('[data-bkt-zero]');
    if (count) count.textContent = n.toLocaleString('ja-JP');
    if (mode) mode.textContent = '件 / ' + m.label + m.total.toLocaleString('ja-JP') + '件中';
    if (n && m.total){
      if (ratio){ ratio.textContent = (100*n/m.total).toFixed(1) + '%　高さ：強い表現 ' + (m.high_pct[issue.id]||0) + '%'; ratio.hidden = false; }
      if (zero) zero.hidden = true;
    } else {
      if (ratio) ratio.hidden = true;
      if (zero){ zero.textContent = 'この立場では0件です。'; zero.hidden = false; }
    }
  }
  function renderReading(id){
    var tpl = readingTemplateFor(id);
    var panel = document.getElementById('panel');
    panel.innerHTML = '';
    panel.appendChild(tpl.content.cloneNode(true));
    fillMetrics(panel, issues[idIndex[id]]);
    var back = document.createElement('button');
    back.type = 'button'; back.className = 'back'; back.id = 'back';
    back.textContent = '← 論点の一覧へ戻る（Esc）';
    back.addEventListener('click', orbit);
    panel.appendChild(back);
    // 図解の拡大は、既存のdocument委譲ハンドラ（.explainer-card[data-img]監視）が
    // そのまま拾う。ここで別のlistenerを足す必要はない。
  }
  drawPanel = function(){
    if (st.landed === null) { legacyDrawPanel(); return; }
    var id = issues[st.landed].id;
    if (!readingTemplateFor(id)) { legacyDrawPanel(); return; }
    renderReading(id);
  };

  // ---------- 立場を切り替えたときの山の変化を滑らかにする ----------
  // consumption-tax-cutのtaxAnimate/taxLayoutと同じ考え方（tax版
  // scripts/templates/consumption_tax_connected_bridge.jsを参照して移植）。
  // bukatsu-chiikiのlayout()/render()はtax版と違い画面幅に応じた再計算を持たず
  // 固定900幅のviewBoxのため、render()自体は書き換えずに済む。layout()だけを
  // 差し替え、render()が内部で呼ぶlayout(st.mode)が補間後の形を返すようにする。
  var bktVisual = null, bktAnimation = 0;
  var legacyLayout = layout;
  layout = function(modeId){ return bktVisual && modeId === st.mode ? bktVisual : legacyLayout(modeId); };

  // アニメーション中は毎フレームsvg.innerHTMLを作り直す（render()自体の仕様）ため、
  // キーボード操作中の山（.hill）へのフォーカスが毎回外れる。呼び出し前後で復元する。
  var legacyRender = render;
  render = function(){
    var focused = document.activeElement;
    var focusId = focused && focused.classList && focused.classList.contains('hill') ? focused.dataset.i : null;
    legacyRender();
    if (focusId !== null){
      var el = svg.querySelector('.hill[data-i="' + focusId + '"]');
      if (el) el.focus({preventScroll: true});
    }
  };

  function bktAnimate(from, to){
    cancelAnimationFrame(bktAnimation);
    if (reduce){ bktVisual = null; render(); return; }
    var start = performance.now();
    var byId = function(list){ var m = new Map(); list.forEach(function(v){ m.set(v.it.id, v); }); return m; };
    var a = byId(from.live), b = byId(to.live);
    var keys = issues.map(function(it){ return it.id; }).filter(function(id){ return a.has(id) || b.has(id); });
    function zero(v){ return Object.assign({}, v, {x0: v.cx, x1: v.cx, w: 0, top: SEA, n: 0, hi: 0, rate: 0, share: 0}); }
    function frame(now){
      var t = Math.min(1, (now - start) / 480), f = 1 - Math.pow(1 - t, 3);
      bktVisual = Object.assign({}, to, {live: keys.map(function(id){
        var end = b.get(id), begin = a.get(id);
        var left = begin || zero(end), right = end || zero(begin), value = Object.assign({}, right);
        ['x0', 'x1', 'cx', 'w', 'top', 'n', 'hi', 'rate', 'share'].forEach(function(key){
          value[key] = left[key] + (right[key] - left[key]) * f;
        });
        value.n = Math.round(value.n); value.hi = Math.round(value.hi);
        value.clipped = value.rate > Y_MAX;
        return value;
      })});
      render();
      if (t < 1) bktAnimation = requestAnimationFrame(frame);
      else { bktVisual = null; bktAnimation = 0; render(); }
    }
    bktAnimation = requestAnimationFrame(frame);
  }

  // 連打時、前のアニメーションの最新の形（bktVisual）から次の目的地へつなぐため、
  // 常に最後に押した立場へ収束する（前のアニメーションへ戻らない）。
  var legacyMorph = morphTo;
  morphTo = function(toMode){
    if (!modeById[toMode] || toMode === st.mode) return;
    var from = bktVisual || legacyLayout(st.mode);
    st.prevRank = ranksOf(st.mode);
    st.mode = toMode;
    if (st.landed !== null && modeById[toMode].counts[issues[st.landed].id] === 0){
      st.landed = null;
      if (location.hash) history.replaceState(null, "", location.pathname);
    }
    evacuateChart();
    drawPanel(); syncList(); placeChart();
    bktAnimate(from, legacyLayout(toMode));
    if (window.innerWidth < 820) bringIntoView(document.querySelector("#panel h2") || document.getElementById("panel"));
  };

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
