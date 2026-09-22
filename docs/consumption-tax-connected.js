/* 消費税の読書面。選択は ConsumptionTaxMap の一か所から読む。 */
(function () {
  'use strict';
  var node = document.getElementById('tax-connected-data');
  var map = window.ConsumptionTaxMap;
  if (!node || !map || !document.documentElement.classList.contains('planet-live')) return;
  var index;
  try { index = JSON.parse(node.textContent); } catch (_) { return; }
  var data = window.PLANET_DATA;
  var bar = document.getElementById('stance-glance');
  var panel = document.getElementById('panel');
  if (!data || data.theme_id !== 'consumption-tax-cut' || !bar || !panel) return;
  var buttons = bar.querySelectorAll('.sg-pick-btn');
  var stanceIds = index.stances.map(function (s) { return s.id; });
  var buttonIds = Array.from(buttons, function (b) { return b.dataset.stanceId; });
  if (buttons.length !== stanceIds.length || new Set(buttonIds).size !== stanceIds.length ||
      buttonIds.some(function (id) { return !stanceIds.includes(id); })) return;
  if (data.issues.some(function (it) { return !document.getElementById('tax-reading-' + it.id); })) return;

  var views = new Map(); // 展開した詳細・埋め込みのDOMを再利用する。閲覧状態のコピーではない。
  var fmt = function (n) { return n.toLocaleString('ja-JP'); };
  var ratio = function (n, total) { return total ? (100 * n / total).toFixed(1) + '%' : '算出できません'; };
  function paint(state) {
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(state.stanceId === b.dataset.stanceId)); });
    bar.querySelectorAll('.temp-seg, .temp-bar-legend > span').forEach(function (item) {
      item.classList.toggle('tax-selected-stance', item.dataset.stanceId === state.stanceId);
      item.classList.toggle('tax-other-stance', state.stanceId !== 'all' && item.dataset.stanceId !== state.stanceId);
    });
    var stance = data.stances.find(function (s) { return s.id === state.stanceId; });
    var result = document.getElementById('stance-glance-result');
    var text = document.getElementById('stance-glance-result-text');
    result.style.display = stance ? 'block' : 'none';
    text.textContent = stance ? '「' + stance.label + '」の投稿' + fmt(stance.count) + '件で山なみを表示しています。' : '';
    var changed = panel.dataset.taxIssueId !== (state.issueId || '');
    panel.dataset.taxIssueId = state.issueId || '';
    panel.dataset.taxStanceId = state.stanceId;
    if (!state.issueId) {
      if (changed || !panel.querySelector('.tax-overview')) panel.innerHTML = '<div class="tax-overview"><h2>消費税減税の7つの論点</h2><p>上の山や論点名を選ぶと、理由・投稿・制度・資料を一緒に読めます。</p></div>';
      return;
    }
    var issue = data.issues.find(function (it) { return it.id === state.issueId; });
    if (!issue) return;
    if (!views.has(issue.id)) {
      var view = document.createElement('div');
      view.className = 'tax-reading';
      view.appendChild(document.getElementById('tax-reading-' + issue.id).content.cloneNode(true));
      view.querySelector('.tax-scope-note').id = 'tax-content-scope';
      view.style.setProperty('--tax-issue-color', data.stances.find(function (s) { return s.key === issue.top_stance; }).color);
      views.set(issue.id, view);
    }
    var current = views.get(issue.id);
    if (panel.firstElementChild !== current) {
      panel.replaceChildren(current);
      if (!matchMedia('(prefers-reduced-motion: reduce)').matches) current.animate([{opacity:0.4, transform:'translateY(5px)'},{opacity:1, transform:'none'}], {duration:180});
    }
    var mode = data.modes.find(function (m) { return m.id === (stance ? stance.key : 'all'); });
    var count = mode.counts[issue.id];
    current.querySelector('[data-tax-count]').textContent = fmt(count) + '件';
    current.querySelector('[data-tax-mode]').textContent = ' ／ ' + mode.label;
    current.querySelector('[data-tax-ratio]').textContent = (mode.id === 'all' ? '意見全体' : 'この立場の意見') + fmt(mode.total) + '件に占める割合 ' + ratio(count, mode.total)
      + '　強い表現の割合 ' + ratio(mode.high_counts[issue.id], count);
    var zero = current.querySelector('[data-tax-zero]');
    zero.hidden = count !== 0;
    zero.textContent = '今回収集した投稿では、この論点に該当する選択中の立場の投稿は0件です。';
  }

  bar.addEventListener('click', function (event) {
    var button = event.target.closest('.sg-pick-btn');
    if (!button || !bar.contains(button) || !stanceIds.includes(button.dataset.stanceId)) return;
    event.preventDefault(); event.stopImmediatePropagation();
    map.selectStance(button.dataset.stanceId);
  }, true);
  document.addEventListener('tax-map:render', function () { paint(map.getState()); });
  var jump = document.createElement('a');
  jump.className = 'tax-map-jump'; jump.href = '#modes'; jump.textContent = '選んだ立場の山なみを見る ↓';
  document.getElementById('stance-glance-result').appendChild(jump);
  bar.querySelector('.sg-pick-hint').textContent = 'その立場の意見で、山なみを表示します';
  document.querySelectorAll('#modes button').forEach(function (button) {
    var mode = data.modes.find(function (m) { return m.id === button.dataset.m; });
    var stance = index.stances.find(function (s) { return s.mode_id === mode.id; });
    button.textContent = (stance ? stance.short_label : 'すべて') + ' ' + fmt(mode.total);
    button.setAttribute('aria-label', mode.label + ' ' + fmt(mode.total) + '件');
  });

  var list = document.getElementById('list');
  var guesses = document.getElementById('guesses');
  var guessDetails = document.createElement('details');
  guessDetails.className = 'tax-guesses';
  guessDetails.innerHTML = '<summary>予想してから読む · 2問</summary>';
  guesses.before(guessDetails); guessDetails.appendChild(guesses);
  var oldHeading = list.previousElementSibling;
  if (oldHeading && oldHeading.matches('h3.sec-live')) oldHeading.hidden = true;
  list.setAttribute('aria-label', '論点を切り替える');
  panel.before(list);
  document.getElementById('section').setAttribute('viewBox', '0 0 900 328');
  document.querySelector('#planet-block .tap-hint').textContent = '山や論点名を選ぶと、その論点の意見と資料が切り替わります';
  document.querySelector('#planet-block .chart-box .hint').textContent = '幅＝意見の数 ／ 高さ＝強い表現の割合。色は論点全体で最も多い立場です。';
  document.body.classList.add('tax-connected');
  map.activate();
  var hash = location.hash.slice(1).replace(/^(issue-|fb-)/, '');
  var initial = index.issues[hash] ? hash : (map.getState().issueId || index.default_issue_id);
  map.selectIssue(initial);

  // 必要な投稿だけ公式埋め込みを読み込む。元の投稿リンクは常に残す。
  panel.addEventListener('toggle', function (event) {
    var details = event.target;
    if (!details.open) return;
    if (details.matches('.tax-embed') && window.twttr && window.twttr.widgets) window.twttr.widgets.load(details);
    var visit = details.dataset.taxClaim ? 'c:' + details.dataset.taxClaim
      : details.dataset.taxConcern ? 'v:' + details.dataset.taxConcern
      : details.dataset.taxSourceOnly ? 'o:' + details.dataset.taxSourceOnly : null;
    if (visit) map.visit(visit);
  }, true);

  // 図解は既存の拡大窓を使用し、キーボードでも開閉できる。
  var modal = document.getElementById('explainer-modal');
  var close = document.getElementById('explainer-modal-close');
  var opener = null;
  modal.setAttribute('role', 'dialog'); modal.setAttribute('aria-modal', 'true'); modal.setAttribute('aria-label', '論点の図解');
  panel.addEventListener('click', function (event) {
    var button = event.target.closest('.tax-image-action');
    if (!button) return;
    opener = button;
    setTimeout(function () { close.focus({preventScroll:true}); }, 0);
  });
  close.addEventListener('click', function () { if (opener && opener.isConnected) opener.focus({preventScroll:true}); });
  document.addEventListener('keydown', function (event) {
    if (!modal.classList.contains('open')) return;
    if (event.key === 'Tab') { event.preventDefault(); close.focus(); }
    if (event.key === 'Escape') {
      event.preventDefault(); event.stopImmediatePropagation();
      modal.classList.remove('open');
      if (opener && opener.isConnected) opener.focus({preventScroll:true});
    }
  }, true);
}());
