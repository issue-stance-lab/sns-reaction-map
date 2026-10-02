(function () {
  'use strict';
  var root = document.getElementById('fukushuto-now');
  if (!root) return;

  var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-fuk-entry-tab]'));
  var panels = Array.prototype.slice.call(root.querySelectorAll('[data-fuk-entry-panel]'));

  function track(name, parameters) {
    if (typeof window.gtag !== 'function') return;
    window.gtag('event', name, parameters || {});
  }

  function selectTopic(key, options) {
    var selected = tabs.find(function (tab) { return tab.dataset.fukEntryTab === key; });
    if (!selected) return;
    tabs.forEach(function (tab) {
      var active = tab === selected;
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.tabIndex = active ? 0 : -1;
    });
    panels.forEach(function (panel) {
      panel.hidden = panel.dataset.fukEntryPanel !== key;
    });
    if (options && options.focus) selected.focus();
    if (!(options && options.silent)) {
      track('fukushuto_entry_topic_select', {
        topic: key,
        issue_id: selected.dataset.issueId
      });
    }
  }

  function openMountain(issueId) {
    var issueButton = document.getElementById('btn-' + issueId);
    var planet = document.getElementById('planet-block');
    if (!issueButton || !planet) return;
    issueButton.click();
    window.setTimeout(function () {
      planet.scrollIntoView({
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
        block: 'start'
      });
    }, 0);
    track('fukushuto_entry_mountain_open', { issue_id: issueId });
  }

  if (tabs.length && tabs.length === panels.length) {
    root.classList.add('is-ready');
    selectTopic(tabs[0].dataset.fukEntryTab, { silent: true });
    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () { selectTopic(tab.dataset.fukEntryTab); });
      tab.addEventListener('keydown', function (event) {
        var next = index;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
        else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + tabs.length) % tabs.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = tabs.length - 1;
        else return;
        event.preventDefault();
        selectTopic(tabs[next].dataset.fukEntryTab, { focus: true });
      });
    });
  }

  root.querySelectorAll('[data-fuk-mountain]').forEach(function (button) {
    button.addEventListener('click', function () { openMountain(button.dataset.fukMountain); });
  });

  root.querySelectorAll('[data-fuk-entry-link]').forEach(function (link) {
    link.addEventListener('click', function () {
      track('fukushuto_entry_navigate', { destination: link.dataset.fukEntryLink });
    });
  });
  root.querySelectorAll('[data-fuk-entry-faq]').forEach(function (details, index) {
    details.addEventListener('toggle', function () {
      if (details.open) track('fukushuto_entry_faq_open', { question_number: index + 1 });
    });
  });
})();
