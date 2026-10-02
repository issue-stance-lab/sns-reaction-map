(function () {
  'use strict';
  var root = document.getElementById('change-lens');
  if (!root) return;

  var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-lens-tab]'));
  var panels = Array.prototype.slice.call(root.querySelectorAll('[data-lens-panel]'));
  var routes = Array.prototype.slice.call(root.querySelectorAll('[data-lens-open]'));
  if (!tabs.length || tabs.length !== panels.length) return;

  function select(key, options) {
    var selected = tabs.find(function (tab) { return tab.dataset.lensTab === key; });
    if (!selected) return;
    tabs.forEach(function (tab) {
      var active = tab === selected;
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.tabIndex = active ? 0 : -1;
    });
    panels.forEach(function (panel) {
      panel.hidden = panel.dataset.lensPanel !== key;
    });
    if (options && options.focus) selected.focus({ preventScroll: true });
  }

  root.classList.add('is-ready');
  select('article9');
  tabs.forEach(function (tab, index) {
    tab.addEventListener('click', function () { select(tab.dataset.lensTab); });
    tab.addEventListener('keydown', function (event) {
      var next = index;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      select(tabs[next].dataset.lensTab, { focus: true });
    });
  });
  routes.forEach(function (route) {
    route.addEventListener('click', function () { select(route.dataset.lensOpen); });
  });
})();
