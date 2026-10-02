(function () {
  'use strict';
  var root = document.getElementById('tax-brief');
  if (!root) return;

  var options = {
    food: { before: 8, after: 1, beforeLabel: '軽減税率', afterLabel: '2年間の政府案', note: '現行の軽減税率対象となる飲食料品は、1%とする大綱です。法律はまだ成立していません。' },
    takeout: { before: 8, after: 1, beforeLabel: '軽減税率', afterLabel: '2年間の政府案', note: 'テイクアウトは現行でも軽減税率の対象で、大綱でも1%の対象です。' },
    eatin: { before: 10, after: 10, beforeLabel: '標準税率', afterLabel: '変更なし', note: '店内飲食は外食にあたり、飲食料品の税率引下げ対象外です。' },
    alcohol: { before: 10, after: 10, beforeLabel: '標準税率', afterLabel: '変更なし', note: '酒類は現行の軽減税率対象外で、大綱でも税率引下げの対象外です。' }
  };
  var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-tax-tab]'));
  var routes = Array.prototype.slice.call(root.querySelectorAll('[data-tax-open]'));
  if (!tabs.length) return;

  function yen(number) { return number.toLocaleString('ja-JP') + '円'; }
  function setText(id, value) { var node = document.getElementById(id); if (node) node.textContent = value; }
  function select(key, focus) {
    var selected = tabs.find(function (tab) { return tab.dataset.taxTab === key; });
    var data = options[key];
    if (!selected || !data) return;
    tabs.forEach(function (tab) {
      var active = tab === selected;
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.tabIndex = active ? 0 : -1;
    });
    var panel = document.getElementById('tax-case-panel');
    if (panel) panel.setAttribute('aria-labelledby', selected.id);
    var beforePrice = 1000 * (1 + data.before / 100);
    var afterPrice = 1000 * (1 + data.after / 100);
    var difference = beforePrice - afterPrice;
    setText('tax-before-rate', data.before + '%');
    setText('tax-after-rate', data.after + '%');
    setText('tax-before-label', data.beforeLabel);
    setText('tax-after-label', data.afterLabel);
    setText('tax-before-price', yen(beforePrice));
    setText('tax-after-price', yen(afterPrice));
    setText('tax-price-delta', difference ? '−' + yen(difference) : '±0円');
    setText('tax-case-note', data.note);
    if (focus) selected.focus();
    try {
      if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        selected.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    } catch (_) {}
  }

  tabs.forEach(function (tab, index) {
    tab.addEventListener('click', function () { select(tab.dataset.taxTab); });
    tab.addEventListener('keydown', function (event) {
      var next = index;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      select(tabs[next].dataset.taxTab, true);
    });
  });
  routes.forEach(function (route) {
    route.addEventListener('click', function () {
      if (route.dataset.taxOpen) select(route.dataset.taxOpen);
    });
  });
  select('food');
})();
