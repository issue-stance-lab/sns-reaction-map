/* 消費税の読書面。選択は ConsumptionTaxMap の一か所から読む。 */
(function () {
  'use strict';
  var node = document.getElementById('tax-connected-data');
  var map = window.ConsumptionTaxMap;
  if (!node) return;
  // 山の初期化より前に例外が起きても、先に隠した静的本文を読める状態へ戻す。
  function fallback() { document.documentElement.classList.remove('planet-live'); }
  if (!map || !document.documentElement.classList.contains('planet-live')) return fallback();
  var index;
  try { index = JSON.parse(node.textContent); } catch (_) { return fallback(); }
  var data = window.PLANET_DATA;
  var bar = document.getElementById('stance-glance');
  var panel = document.getElementById('panel');
  if (!data || data.theme_id !== 'consumption-tax-cut' || !bar || !panel) return fallback();
  var buttons = bar.querySelectorAll('.sg-pick-btn');
  var stanceIds = index.stances.map(function (s) { return s.id; });
  var buttonIds = Array.from(buttons, function (b) { return b.dataset.stanceId; });
  if (buttons.length !== stanceIds.length || new Set(buttonIds).size !== stanceIds.length ||
      buttonIds.some(function (id) { return !stanceIds.includes(id); })) return fallback();
  if (data.issues.some(function (it) { return !document.getElementById('tax-reading-' + it.id); })) return fallback();

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
    var mode = data.modes.find(function (m) { return m.id === (stance ? stance.key : 'all'); });
    var result = document.getElementById('stance-glance-result');
    var text = document.getElementById('stance-glance-result-text');
    result.style.display = 'block';
    // 論点だけを選んだ時は、操作中の最多論点ボタンを作り直して焦点を失わせない。
    if (result.dataset.taxStanceId !== state.stanceId) {
      result.dataset.taxStanceId = state.stanceId;
      var max = Math.max.apply(null, data.issues.map(function (it) { return mode.counts[it.id]; }));
      var leaders = data.issues.filter(function (it) { return max > 0 && mode.counts[it.id] === max; });
      text.textContent = (stance ? '「' + index.stances.find(function (s) { return s.id === stance.id; }).short_label + '」' : '全体') + 'の' + fmt(mode.total) + '件では、';
      leaders.forEach(function (it, i) {
        if (i) text.append('・');
        var link = document.createElement('button'); link.type = 'button'; link.className = 'tax-leading-issue';
        link.textContent = it.label; link.onclick = function () { map.selectIssue(it.id); };
        text.appendChild(link);
      });
      text.append(leaders.length ? 'が最多（' + fmt(max) + '件' + (leaders.length > 1 ? 'ずつ' : '') + '）。' : '比較できる投稿がありません。');
    }
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
  // 見本と同じく、既存のバー・選択ボタン・山を一つの読み順にまとめる。
  var planet = document.getElementById('planet-block');
  var mountain = planet.closest('.planet-panel');
  bar.before(mountain);
  var modes = document.getElementById('modes');
  var oldButtons = document.getElementById('stance-glance-buttons');
  oldButtons.replaceWith(modes);
  planet.querySelector('.stage').before(bar);
  planet.querySelector('.panel-title h2').textContent = '意見は、どこで分かれている？';
  planet.querySelector('.panel-title > span').textContent = '立場を選ぶ → 山を選ぶ → 理由と資料を読む';
  bar.querySelector('.sg-note').textContent = 'ここでの選択は表示の切替です。投票には集計されません。';
  document.querySelectorAll('#modes button').forEach(function (button) {
    var mode = data.modes.find(function (m) { return m.id === button.dataset.m; });
    var stance = index.stances.find(function (s) { return s.mode_id === mode.id; });
    button.replaceChildren();
    var label = document.createElement('span'); label.className = 'tax-mode-name';
    label.textContent = stance ? stance.short_label : 'すべて';
    var count = document.createElement('strong'); count.textContent = fmt(mode.total) + '件';
    button.append(label, count);
    if (stance) {
      button.classList.add('sg-pick-btn'); button.dataset.stanceId = stance.id;
      var color = data.stances.find(function (s) { return s.id === stance.id; }).color;
      button.style.setProperty('--tax-stance-color', color);
      var share = document.createElement('small'); share.textContent = ratio(mode.total, data.totals.opinions);
      count.append(' ', share);
    }
    button.setAttribute('aria-label', mode.label + ' ' + fmt(mode.total) + '件');
  });
  buttons = bar.querySelectorAll('.sg-pick-btn');

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
  document.querySelector('#planet-block .chart-box .hint').textContent = '幅＝意見の数 ／ 高さ＝強い表現の割合。濃い山が選択中の論点です。';
  var meta = document.getElementById('meta');
  meta.textContent = '山ひとつが論点ひとつです。幅は選んだ立場の意見数、高さはその中で強い表現に分類された投稿の割合です。全体表示は青、立場を選ぶとバーと同じ色になります。濃い山が選択中の論点です。左右の並び順は固定し、順位を示しません。件数の少ない論点は高さが揺れやすいため、下のボタンで件数を確認してください。';
  planet.querySelector('.panel-title').after(document.getElementById('caution'));
  document.body.classList.add('tax-connected');
  map.activate();
  var hash = location.hash.slice(1).replace(/^(issue-|fb-)/, '');
  var initial = index.issues[hash] ? hash : (map.getState().issueId || index.default_issue_id);
  map.selectIssue(initial, {history:'replace', preserveHash:!!location.hash && !index.issues[hash]});

  // 理由を開くまでは投稿カードをDOMへ出さず、外部の読み込みを始めない。
  var reasonEmbedSources = new WeakMap();
  function loadReasonEmbeds() {
    if (!window.twttr || !window.twttr.widgets || document.body.classList.contains('tax-printing')) return;
    panel.querySelectorAll('.tax-reason-detail[open] .tax-reason-embed').forEach(function (holder) {
      if (!holder.getClientRects().length) return;
      function resetFailedEmbed() {
        // Xが失敗した要素に付ける処理済み属性も除き、次回は未処理の入口から始める。
        var source = reasonEmbedSources.get(holder);
        if (source) holder.replaceChildren(source.cloneNode(true));
        delete holder.dataset.taxWidgetRequested;
      }
      if (holder.dataset.taxWidgetRequested) {
        // 自動走査が後から失敗した場合も、開き直した時に再試行する。
        if (!holder.querySelector('blockquote.twitter-tweet-error')) return;
        resetFailedEmbed();
      }
      // APIが到着するまではtemplateのまま保つ。
      var template = holder.querySelector('template.tax-reason-embed-template');
      if (template) {
        reasonEmbedSources.set(holder, template.content.cloneNode(true));
        template.replaceWith(template.content.cloneNode(true));
      }
      if (!holder.querySelector('blockquote.twitter-tweet')) return;
      holder.dataset.taxWidgetRequested = 'true';
      try {
        Promise.resolve(window.twttr.widgets.load(holder)).then(function () {
          // 自動走査が先に取得すると手動loadは対象0件で完了する。
          // 元要素が残るだけでは失敗ではないため、描画中のDOMを保持する。
          if (holder.querySelector('blockquote.twitter-tweet-error')) resetFailedEmbed();
        }).catch(resetFailedEmbed);
      } catch (_) { resetFailedEmbed(); }
    });
  }
  function twitterReady() {
    loadReasonEmbeds();
    if (window.twttr && window.twttr.ready) window.twttr.ready(loadReasonEmbeds);
  }
  document.querySelectorAll('script[src="https://platform.twitter.com/widgets.js"]').forEach(function (script) {
    script.addEventListener('load', twitterReady);
  });
  twitterReady();
  document.addEventListener('tax-map:render', loadReasonEmbeds);
  var openedReasons = new WeakSet();
  panel.addEventListener('click', function (event) {
    var summary = event.target.closest('.tax-reason-detail > summary');
    if (!summary || !event.isTrusted) return;
    var details = summary.parentElement;
    if (!details.open && !openedReasons.has(details)) {
      openedReasons.add(details);
      // 閲覧した理由・立場・投稿URLは分析イベントへ渡さない。
      if (typeof window.gtag === 'function') window.gtag('event', 'reason_post_open', {topic_id:data.theme_id});
    }
  });

  // 必要な投稿だけ公式埋め込みを読み込む。元の投稿リンクは常に残す。
  panel.addEventListener('toggle', function (event) {
    var details = event.target;
    if (!details.open || !details.getClientRects().length || document.body.classList.contains('tax-printing')) return;
    if (details.matches('.tax-reason-detail')) {
      loadReasonEmbeds();
    }
    if (details.matches('.tax-embed') && window.twttr && window.twttr.widgets) window.twttr.widgets.load(details);
    var visit = details.dataset.taxClaim ? 'c:' + details.dataset.taxClaim
      : details.dataset.taxConcern ? 'v:' + details.dataset.taxConcern
      : details.dataset.taxSourceOnly ? 's:' + details.dataset.taxSourceOnly : null;
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
