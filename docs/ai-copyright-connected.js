/* 生成AIと著作権の読書面・中心部分の配置（工程3、2026-09-23）。
   バー↔山の状態共有・読書面そのものはscripts/templates/ai_copyright_connected_bridge.jsが
   既に配線済み。ここではbukatsu-chiikiのbukatsu-connected.jsに合わせて、山の直前へバーと
   #modesをまとめ、#modesの中身を件数・割合つきのグリッドボタンへ作り直し、#listを読書面の
   直前へ移動し、.ai-copyright-connectedを付与してCSSを切り替える。
   window.AiCopyrightConnectedMapとdrawPanel/layout/renderの差し替えはbridge.js側の責務の
   ため、ここでは触らない。理由別X投稿・資料3タブ・年表統合・旧セクションの隠蔽（V07〜V10）は
   ページ全体の再配置を扱う工程4で追加する。 */
(function () {
  'use strict';
  var node = document.getElementById('ai-copyright-connected-data');
  var map = window.AiCopyrightConnectedMap;
  if (!node || !map) return;
  var index;
  try { index = JSON.parse(node.textContent); } catch (_) { return; }
  var data = window.PLANET_DATA;
  var bar = document.getElementById('stance-glance');
  var planet = document.getElementById('planet-block');
  var panel = document.getElementById('panel');
  if (!data || data.theme_id !== 'ai-copyright' || !bar || !planet || !panel) return;
  if (data.issues.some(function (it) { return !document.getElementById('ai-copyright-reading-' + it.id); })) return;

  var fmt = function (n) { return n.toLocaleString('ja-JP'); };
  var ratio = function (n, total) { return total ? (100 * n / total).toFixed(1) + '%' : '算出できません'; };

  // バー・#modes・山・論点ボタン・読書面を一続きの読み順にまとめる（V02）。
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
    var label = document.createElement('span'); label.className = 'aic-mode-name';
    label.textContent = stance ? stance.label : 'すべて';
    var count = document.createElement('strong'); count.textContent = fmt(mode.total) + '件';
    button.append(label, count);
    if (stance) {
      button.classList.add('sg-pick-btn');
      button.style.setProperty('--aic-stance-color', stance.color);
      var share = document.createElement('small'); share.textContent = ratio(mode.total, data.totals.opinions);
      count.append(' ', share);
    }
    button.setAttribute('aria-label', mode.label + ' ' + fmt(mode.total) + '件');
  });

  // 予想2問は折りたたみ、既定は閉じたまま（山を先に読める）。
  var guesses = document.getElementById('guesses');
  if (guesses && !guesses.closest('.aic-guesses')) {
    var guessDetails = document.createElement('details');
    guessDetails.className = 'aic-guesses';
    guessDetails.innerHTML = '<summary>予想してから読む · 2問</summary>';
    guesses.before(guessDetails);
    guessDetails.appendChild(guesses);
  }

  var hint = document.querySelector('#planet-block .chart-box .hint');
  if (hint) hint.textContent = '山を押すと、その論点の理由・投稿・資料を読めます（面積＝強く語られた投稿の数）。';

  document.body.classList.add('ai-copyright-connected');

  // 山のSVGは固定viewBoxのまま（余白がその分だけ残る）なので、CSSで高さだけ縮めると
  // 山の描画自体が縮んで小さく見える。実際に描かれた範囲（getBBox）に合わせてviewBoxを
  // 切り直し、縦横比をCSSの表示枠に合わせて引き伸ばす（内部の描画処理自体は変更しない、V03）。
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

  // 開いた投稿カードのXカードだけ読み込む。元の投稿リンクは常に残す。
  var embedSources = new WeakMap();
  function loadEmbeds() {
    if (!window.twttr || !window.twttr.widgets) return;
    panel.querySelectorAll('.aic-embed[open]').forEach(function (holder) {
      if (!holder.getClientRects().length) return;
      function resetFailed() {
        var source = embedSources.get(holder);
        if (source) holder.replaceChildren(source.cloneNode(true));
        delete holder.dataset.aicWidgetRequested;
      }
      if (holder.dataset.aicWidgetRequested) {
        if (!holder.querySelector('blockquote.twitter-tweet-error')) return;
        resetFailed();
      }
      if (!embedSources.has(holder)) embedSources.set(holder, holder.cloneNode(true));
      if (!holder.querySelector('blockquote.twitter-tweet')) return;
      holder.dataset.aicWidgetRequested = 'true';
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
    if (event.target.matches('.aic-embed')) loadEmbeds();
  }, true);
}());
