/* 消費税の連動表示。状態は山の ConsumptionTaxMap に一元化する。 */
(function () {
  'use strict';
  var node = document.getElementById('tax-connected-data');
  var map = window.ConsumptionTaxMap;
  if (!node || !map || !document.documentElement.classList.contains('planet-live')) return;
  var index;
  try { index = JSON.parse(node.textContent); } catch (_) { return; }
  var data = window.PLANET_DATA;
  var bar = document.getElementById('stance-glance');
  if (!data || data.theme_id !== 'consumption-tax-cut' || !bar) return;
  var buttons = bar.querySelectorAll('.sg-pick-btn');
  var stanceIds = index.stances.map(function (s) { return s.id; });
  var buttonIds = Array.from(buttons, function (button) { return button.dataset.stanceId; });
  if (buttons.length !== stanceIds.length || new Set(buttonIds).size !== stanceIds.length ||
      buttonIds.some(function (id) { return !stanceIds.includes(id); })) return;

  function paint(state) {
    buttons.forEach(function (button) {
      button.setAttribute('aria-pressed', String(state.stanceId === button.dataset.stanceId));
    });
    var stance = data.stances.find(function (s) { return s.id === state.stanceId; });
    var result = document.getElementById('stance-glance-result');
    var text = document.getElementById('stance-glance-result-text');
    if (result && text) {
      result.style.display = stance ? 'block' : 'none';
      text.textContent = stance
        ? '「' + stance.label + '」の投稿' + stance.count.toLocaleString('ja-JP') + '件で山なみを表示しています。'
        : '';
    }
    var panel = document.getElementById('panel');
    if (!panel) return;
    panel.dataset.taxIssueId = state.issueId || '';
    panel.dataset.taxStanceId = state.stanceId;
    var note = document.getElementById('tax-content-scope');
    if (state.issueId && index.issues[state.issueId]) {
      if (!note) {
        note = document.createElement('p');
        note.id = 'tax-content-scope';
        var heading = panel.querySelector('h2');
        if (heading) heading.insertAdjacentElement('afterend', note);
        else panel.prepend(note);
      }
      note.textContent = index.scope_note;
    } else if (note) {
      note.remove();
    }
  }

  // 既存バーの独立したクリック処理をここで受け止め、山と同じ状態へ送る。
  // 古いインラインJSが残るテンプレートからの生成でも二重処理しない。
  bar.addEventListener('click', function (event) {
    var button = event.target.closest('.sg-pick-btn');
    if (!button || !bar.contains(button)) return;
    var stanceId = button.dataset.stanceId;
    if (!index.stances.some(function (s) { return s.id === stanceId; })) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    map.selectStance(stanceId);
  }, true);
  document.addEventListener('tax-map:render', function () { paint(map.getState()); });
  document.body.classList.add('tax-connected');
  var hint = bar.querySelector('.sg-pick-hint');
  if (hint) hint.textContent = 'その立場の意見で、山なみを表示します';
  paint(map.getState());
}());
