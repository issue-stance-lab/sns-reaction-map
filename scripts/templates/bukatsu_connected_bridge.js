// バー↔山の立場共有（工程2）、論点を選んだときの読書面（工程3）、
// 立場を切り替えたときの山の滑らかな変化・初期表示の自動選択・予想2問②からの論点移動
// （工程3後追い、tax版の考え方を移植）、深いリンクの統一・クイズからの論点移動・
// 論点表示と出典操作の計測（工程4）。潮目カードへのリンクは消費税版・計画書のどちらにも
// 前例が無い独自追加と判明したため一度追加して削除した（オーナー指摘、2026-09-23）。
// land/orbit/buildGuesses/buildQuiz自体の中身は変えず、drawPanel・layout・render・morphToだけを差し替える。
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
  // ---------- 工程4: 論点表示・出典操作の計測 ----------
  // GA4本体（gtag）はGA_TAG_START〜ENDのshimが本番ホストでだけ動く前提のため、無い環境
  // （ローカル確認等）では何もしない。再描画のたびに送らないよう、直前に送った論点idと
  // 比較する（立場切替でdrawPanelが同じ論点を再描画しても送り直さない）。閲覧者が選んだ
  // 立場・自由記述は送らない。送るのはissue_idと、押した出典リンクの行き先URLだけ。
  var lastTrackedIssue = null;
  function trackIssueView(id){
    if (typeof window.gtag !== 'function' || id === lastTrackedIssue) return;
    lastTrackedIssue = id;
    window.gtag('event', 'issue_view', {issue_id: id});
  }
  var panelEl = document.getElementById('panel');
  if (panelEl){
    panelEl.addEventListener('click', function(e){
      var a = e.target.closest('a[target="_blank"]');
      if (!a || typeof window.gtag !== 'function') return;
      window.gtag('event', 'citation_click', {
        issue_id: st.landed === null ? null : issues[st.landed].id,
        outbound_url: a.href
      });
    });
  }
  drawPanel = function(){
    if (st.landed === null) { legacyDrawPanel(); return; }
    var id = issues[st.landed].id;
    trackIssueView(id);
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

  // ---------- 初期表示・深いリンクの統一（工程4） ----------
  // land()自体（クリック時に該当箇所へ画面を運ぶ、オーナー指摘2026-09-10/09-19で追加した
  // 動き）は変えない。画面を動かさず状態だけ変えたい場面（初期表示・issue-cardsや授業節の
  // 既存アンカー・ブラウザの戻る/進む）では、bringIntoView()を一時的に何もしない関数へ
  // 差し替えてland()を呼び、直後に戻す（land()の中身は複製しない）。
  function landSilently(i){
    var real = bringIntoView;
    bringIntoView = function(){};
    land(i);
    bringIntoView = real;
  }
  // land()が書くhashは論点の生id（例: #bukatsu-chiiki-kyoin）だが、issue-cards・授業節の
  // 既存リンクは別の名前空間（例: #issue-bukatsu-chiiki-kyoin、Xの投稿カード側のid）を
  // 使っている。両方を同じ論点選択へ正規化する。
  function issueIdFromHash(){
    var h = location.hash.slice(1);
    if (!h) return null;
    if (idIndex[h] !== undefined) return h;
    if (h.indexOf('issue-') === 0 && idIndex[h.slice(6)] !== undefined) return h.slice(6);
    return null;
  }
  // 読書面のtemplateはbody末尾にあり、このscript（PLANET_SECTION内）より後ろでパースされる。
  // setTimeout(0)は大きなページだとパース完了より先に発火することがあるため使わず、
  // DOMContentLoaded（このscript自体は常にその前に実行されるため、必ず後で発火する）を待つ。
  //
  // 素のhash付きURL（例: 前回訪問した論点をブラウザが覚えている再訪問）では、この関数を
  // 待たずに既存init（PLANET_SECTION末尾の同期処理）がすぐland()を呼ぶ。その時点ではまだ
  // templateが未パースのため、drawPanel()は「読書面が無い論点」と判定して旧描画（升目100個
  // 等）へ後退する。st.landedはその時点で決まってしまうため、以前はここで単純に
  // 「もう決まっているなら何もしない」としていたが、それでは旧描画のまま固定されて残る
  // （オーナー報告2026-09-23: 論点を押すまでマス目が消えない）。テンプレートが必ず揃っている
  // このタイミングで、読書面が実際に描けているかを確かめ、旧描画のままなら同じ論点へもう一度
  // 静かに着地し直す（land()の中身は複製せず、同じ論点idへの再呼び出しで済ませる）。
  function readingRenderedFor(i){
    return i !== null && !!document.getElementById('panel').querySelector('.bkt-selected-head');
  }
  function initialLand(){
    if (st.landed === null) {
      var id = issueIdFromHash();
      if (id !== null){ landSilently(idIndex[id]); }
      else if (!location.hash){
        var top = issues.reduce(function(a, b){ return b.count > a.count ? b : a; });
        landSilently(idIndex[top.id]);
      }
    }
    if (st.landed !== null && !readingRenderedFor(st.landed)) landSilently(st.landed);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialLand, {once: true});
  } else {
    initialLand();
  }
  // issue-cardsの戻りリンク・授業節の論点リンクも、ブラウザの戻る/進むも、最終的には
  // hashの変化として届く。1箇所で拾い、同じ論点選択へつなぐ。論点に無関係なhash
  // （#planet-block・#vote-section等）は無視して今の選択状態を保つ（issue-cardsの
  // 「↑ 地図へ戻る」を押しても、読んでいた論点の読書面が消えないように）。
  window.addEventListener('hashchange', function(){
    var h = location.hash.slice(1);
    if (!h){ if (st.landed !== null) orbit(); return; }
    var id = issueIdFromHash();
    if (id !== null && (st.landed === null || issues[st.landed].id !== id)) landSilently(idIndex[id]);
  });

  // ---------- 予想2問（②強い表現がいちばん多い論点）の答えから、該当の山へ移動 ----------
  // buildGuesses()自体は上書きしない（①②の文言・正誤判定は既存のまま）。#guesses
  // （buildModes()と同様、buildGuesses()実行前は空の入れ物）への委譲で、答えが開いた
  // 直後（＝buildGuesses()自身のclick listenerが先に走った後、bubbling で#guessesへ届く
  // 時点）にだけ動く。②の答えの論点名は「peak[0].it.label」だがbuildGuesses()の
  // クロージャ内にしか無いため、再計算せず、既に表示された答え文の「「論点名」」を
  // そのまま読み取る（tax版のx.issueIdと同じ対象、ボタン文言「この論点の山を見る ↓」も
  // tax版に合わせた）。
  var guessesBox = document.getElementById('guesses');
  if (guessesBox){
    guessesBox.addEventListener('click', function(e){
      if (!e.target.closest('.gopts button')) return;
      var card = e.target.closest('.guess');
      if (!card || card.dataset.k !== 'g2') return;
      var answerBox = card.querySelector('.gans');
      if (!answerBox || answerBox.querySelector('.bkt-guess-link')) return;
      var match = answerBox.innerHTML.match(/<b>「([^」]+)」/);
      var target = match && issues.find(function(it){ return it.label === match[1]; });
      if (!target) return;
      var link = document.createElement('button');
      link.type = 'button';
      link.className = 'bkt-guess-link';
      link.textContent = 'この論点の山を見る ↓';
      link.addEventListener('click', function(){ land(idIndex[target.id]); });
      answerBox.appendChild(link);
    });
  }

  // ---------- 予想クイズ・一次資料クイズの答えから、関係する論点の山へ移動 ----------
  // buildQuiz()自体は上書きしない。#quiz（buildQuiz()実行前は空の入れ物）への委譲で、
  // 答えが開いた直後（buildQuiz()自身のclick listenerが先に走った後、bubblingで#quizへ
  // 届く時点）にだけ動く。どの問題かはqi（buildQuiz()のクロージャ内）を再計算せず、
  // 既に表示された問題文「「主張」」をD.claims[].claimと照合してclaim idを求め、
  // issues[].claims[]にそのidを含む論点（0〜2件。例: national-fundingは制度・費用の2論点）
  // へリンクを作る。答え文自体には論点名が出ないため（予想クイズと違い）、リンクの文言に
  // 論点名を明示する。
  var quizBox = document.getElementById('quiz');
  if (quizBox){
    quizBox.addEventListener('click', function(e){
      if (!e.target.closest('.gopts button')) return;
      var qclaim = quizBox.querySelector('.qclaim');
      var qans = quizBox.querySelector('.qans');
      if (!qclaim || !qans || qans.querySelector('.bkt-quiz-link')) return;
      var m = qclaim.textContent.match(/「([\s\S]+)」/);
      var claim = m && D.claims.find(function(c){ return c.claim === m[1]; });
      if (!claim) return;
      issues.filter(function(it){
        return (it.claims || []).some(function(c){ return c.id === claim.id; });
      }).forEach(function(target){
        var link = document.createElement('button');
        link.type = 'button';
        link.className = 'bkt-guess-link bkt-quiz-link';
        link.textContent = 'この論点の山を見る：' + target.label + ' ↓';
        link.addEventListener('click', function(){ land(idIndex[target.id]); });
        qans.appendChild(link);
      });
    });
  }

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
