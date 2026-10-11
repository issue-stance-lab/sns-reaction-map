/* 皇室典範改正・山なみと論点の読書面の試作。
   山か論点名を押すと、下の読書面だけを切り替える（公開ページの山なみは元HTMLの対話式の図で、planet.js が
   window.KoshitsuReading.select を呼ぶ）。ページは動かさない（scrollY を変えない）。
   JavaScriptが無いときは、全論点の読書面が縦に並び、リンクはその論点へ移動する。 */
(() => {
  'use strict';
  const root = document.getElementById('koshitsu-reading');
  if (!root) return;
  const panels = [...root.querySelectorAll('[data-issue-panel]')];
  const ids = panels.map(p => p.dataset.issuePanel);
  const live = document.getElementById('kr-live');
  const fromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1)).replace(/^issue-/, '');
    return ids.includes(id) ? id : null;
  };

  function select(id, announce) {
    panels.forEach(p => p.toggleAttribute('data-selected', p.dataset.issuePanel === id));
    root.querySelectorAll('.kr-hill').forEach(h => h.classList.toggle('is-on', h.dataset.issueId === id));
    root.querySelectorAll('.kr-chip').forEach(c => {
      if (c.dataset.issueId === id) c.setAttribute('aria-current', 'true');
      else c.removeAttribute('aria-current');
    });
    if (announce && live) {
      const h = root.querySelector('#kr-h-' + CSS.escape(id));
      live.textContent = (h ? h.textContent : '') + 'の読書面に切り替えました。';
    }
  }

  root.classList.add('kr-js');
  select(fromHash() || root.dataset.defaultIssue, false);

  // 山と論点名：その場で切り替える。位置は動かさず、フォーカスも押した所に残す。
  root.addEventListener('click', ev => {
    const a = ev.target.closest('[data-issue-id]');
    if (!a || !root.contains(a)) return;
    ev.preventDefault();
    const id = a.dataset.issueId;
    select(id, true);
    history.replaceState(null, '', '#issue-' + id);
    if (a.classList.contains('kr-chip')) a.focus({ preventScroll: true });
  });

  // 冒頭の論点リンク（#issue-…）：選んだうえで、ブラウザの通常の移動に任せる。
  document.addEventListener('click', ev => {
    const a = ev.target.closest('a[href^="#issue-"]');
    if (!a || root.contains(a)) return;
    const id = a.getAttribute('href').slice('#issue-'.length);
    if (ids.includes(id)) select(id, true);
  });

  addEventListener('hashchange', () => { const id = fromHash(); if (id) select(id, true); });

  // 山なみ（元HTMLから写した対話式の図、planet.js）から論点を選ぶための入口。
  window.KoshitsuReading = Object.freeze({
    select(id) { if (!ids.includes(id)) return false; select(id, true); return true; }
  });
})();
