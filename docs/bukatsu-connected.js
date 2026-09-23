/* 部活動の読書面・ページ配置（工程3・4後追い、2026-09-23）。
   バー↔山の状態共有・読書面そのものはscripts/templates/bukatsu_connected_bridge.jsが
   既に配線済み（工程2・3）。ここでは消費税のconsumption-tax-connected.jsに合わせて、
   山の直前へバーと#modesをまとめ、#modesの中身を件数・割合つきのグリッドボタンへ作り直し、
   #listを読書面の直前へ移動し、.bukatsu-connectedを付与してCSSを切り替える。
   window.BukatsuConnectedMapとdrawPanel/layout/renderの差し替えはbridge.js側の責務のため、
   ここでは触らない。 */
(function () {
  'use strict';
  var node = document.getElementById('bukatsu-connected-data');
  var map = window.BukatsuConnectedMap;
  if (!node || !map) return;
  var index;
  try { index = JSON.parse(node.textContent); } catch (_) { return; }
  var data = window.PLANET_DATA;
  var bar = document.getElementById('stance-glance');
  var planet = document.getElementById('planet-block');
  var panel = document.getElementById('panel');
  if (!data || data.theme_id !== 'bukatsu-chiiki' || !bar || !planet || !panel) return;
  if (data.issues.some(function (it) { return !document.getElementById('bukatsu-reading-' + it.id); })) return;

  var fmt = function (n) { return n.toLocaleString('ja-JP'); };
  var ratio = function (n, total) { return total ? (100 * n / total).toFixed(1) + '%' : '算出できません'; };

  // 見本（tax版）と同じく、バー・#modes・山・論点ボタン・読書面を一続きの読み順にまとめる。
  var mountain = planet.closest('.planet-panel');
  bar.before(mountain);
  var list = document.getElementById('list');
  var oldHeading = list.previousElementSibling;
  if (oldHeading && oldHeading.matches('h3.sec')) oldHeading.hidden = true;
  list.setAttribute('aria-label', '論点を切り替える');
  panel.before(list);

  // #modesの中身を、立場名・件数・割合が見える形へ作り直す（buildModes()自体は上書きしない。
  // #modesはbuildModes()実行後に呼ばれるこのIIFEより先に中身が入っている）。
  var modes = document.getElementById('modes');
  modes.querySelectorAll('button').forEach(function (button) {
    var mode = data.modes.find(function (m) { return m.id === button.dataset.m; });
    if (!mode) return;
    var stance = data.stances.find(function (s) { return s.key === mode.id; });
    button.replaceChildren();
    var label = document.createElement('span'); label.className = 'bkt-mode-name';
    label.textContent = stance ? stance.label : 'すべて';
    var count = document.createElement('strong'); count.textContent = fmt(mode.total) + '件';
    button.append(label, count);
    if (stance) {
      button.classList.add('sg-pick-btn');
      button.style.setProperty('--bkt-stance-color', stance.color);
      var share = document.createElement('small'); share.textContent = ratio(mode.total, data.totals.opinions);
      count.append(' ', share);
    }
    button.setAttribute('aria-label', mode.label + ' ' + fmt(mode.total) + '件');
  });

  // 予想2問は折りたたみ、既定は閉じたまま（山を先に読める）。
  var guesses = document.getElementById('guesses');
  if (guesses && !guesses.closest('.bkt-guesses')) {
    var guessDetails = document.createElement('details');
    guessDetails.className = 'bkt-guesses';
    guessDetails.innerHTML = '<summary>予想してから読む · 2問</summary>';
    guesses.before(guessDetails);
    guessDetails.appendChild(guesses);
  }

  document.querySelector('#planet-block .chart-box .hint').textContent = '山を押すと、その論点の理由・投稿・資料を読めます（面積＝強く語られた投稿の数）。';

  document.body.classList.add('bukatsu-connected');

  // 山のSVGは固定900×500のviewBoxのまま（海面下の演出をCSSで隠すだけ）なので、
  // CSSでheightだけ縮めると、山の描画（TOP〜SEA）は空いた下半分ごと一律に縮み、
  // 消費税より小さく見える。実際に描かれた範囲（getBBox）に合わせてviewBoxを切り直し、
  // 縦横比をCSSの表示枠に合わせて引き伸ばす（内部の描画処理そのものは変更しない）。
  // render()はsvg.innerHTMLだけを毎回作り直し、viewBox属性自体には触れない
  // （縦の描画範囲はTOP/SEAの定数で固定、立場・論点を変えても動かない）ため、
  // 最初の描画後に一度だけ切り直せば、以降のすべての再描画でも有効なまま残る。
  var section = document.getElementById('section');
  if (section) {
    var box;
    try { box = section.getBBox(); } catch (_) { box = null; }
    if (box && box.height) {
      var padTop = 6, padBottom = 6;
      section.setAttribute('viewBox', '0 ' + Math.max(0, box.y - padTop) + ' 900 ' + (box.height + padTop + padBottom));
      section.setAttribute('preserveAspectRatio', 'none');
    }
  }

  // ---------- 理由の立場別内訳（工程3後追い、2026-09-23、オーナー依頼） ----------
  // data-bkt-counts/pctsは論点ごとの読書面テンプレートに埋め込み済み（"all"は必ずある。
  // 立場idは生データにstanceが無い論点では省かれる＝その論点は「すべて」のまま変わらない）。
  function applyStanceToReasons() {
    var state = map.getState();
    var stance = data.stances.find(function (s) { return s.id === state.stanceId; });
    var modeKey = stance ? stance.key : 'all';
    panel.querySelectorAll('[data-bkt-counts]').forEach(function (li) {
      var counts, pcts;
      try {
        counts = JSON.parse(li.dataset.bktCounts);
        pcts = JSON.parse(li.dataset.bktPcts);
      } catch (_) { return; }
      var n = Object.prototype.hasOwnProperty.call(counts, modeKey) ? counts[modeKey] : counts.all;
      var pct = Object.prototype.hasOwnProperty.call(pcts, modeKey) ? pcts[modeKey] : pcts.all;
      var b = li.querySelector('.bkt-reason-row b');
      if (b) {
        b.textContent = fmt(n);
        var small = document.createElement('small'); small.textContent = '件';
        b.appendChild(small);
      }
      var track = li.querySelector('.bkt-reason-track i');
      if (track) track.style.width = pct + '%';
    });
  }
  new MutationObserver(applyStanceToReasons).observe(panel, { childList: true });
  applyStanceToReasons();

  // 開いた理由・投稿カードのXカードだけ読み込む。元の投稿リンクは常に残す。
  var embedSources = new WeakMap();
  function loadEmbeds() {
    if (!window.twttr || !window.twttr.widgets) return;
    panel.querySelectorAll('.bkt-embed[open]').forEach(function (holder) {
      if (!holder.getClientRects().length) return;
      function resetFailed() {
        var source = embedSources.get(holder);
        if (source) holder.replaceChildren(source.cloneNode(true));
        delete holder.dataset.bktWidgetRequested;
      }
      if (holder.dataset.bktWidgetRequested) {
        if (!holder.querySelector('blockquote.twitter-tweet-error')) return;
        resetFailed();
      }
      if (!embedSources.has(holder)) embedSources.set(holder, holder.cloneNode(true));
      if (!holder.querySelector('blockquote.twitter-tweet')) return;
      holder.dataset.bktWidgetRequested = 'true';
      try {
        Promise.resolve(window.twttr.widgets.load(holder)).then(function () {
          if (holder.querySelector('blockquote.twitter-tweet-error')) resetFailed();
        }).catch(resetFailed);
      } catch (_) { resetFailed(); }
    });
  }
  function twitterReady() {
    loadEmbeds();
    if (window.twttr && window.twttr.ready) window.twttr.ready(loadEmbeds);
  }
  document.querySelectorAll('script[src="https://platform.twitter.com/widgets.js"]').forEach(function (script) {
    script.addEventListener('load', twitterReady);
  });
  twitterReady();
  // renderReading()は論点切替のたびにpanelを丸ごと差し替えるため、開閉状態は残らない。
  // 開いた瞬間だけ読み込めばよく、bridge.js側に専用イベントを追加する必要はない。
  panel.addEventListener('toggle', function (event) {
    if (event.target.matches('.bkt-embed')) loadEmbeds();
  }, true);
}());
