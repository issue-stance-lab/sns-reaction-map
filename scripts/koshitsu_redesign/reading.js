/* 皇室典範改正・山なみと論点の読書面の試作。
   山か論点名を押すと、下の読書面だけを切り替える（公開ページの山なみは元HTMLの対話式の図で、planet.js が
   window.KoshitsuReading.select を呼ぶ）。ページは動かさない（scrollY を変えない）。
   JavaScriptが無いときは、全論点の読書面が縦に並び、リンクはその論点へ移動する。
   2026-10-12（部活動型の圧縮）：論点タブ（.kr-tab）も同じく切り替える。理由一覧の行（data-reason-pick）を押すと、
   その論点の中で選んだ理由の説明（.kr-reason-detail）だけを見せる。JavaScriptが無いときは全理由の説明が並ぶ。 */
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
    root.querySelectorAll('.kr-chip, .kr-tab').forEach(c => {
      if (c.dataset.issueId === id) c.setAttribute('aria-current', 'true');
      else c.removeAttribute('aria-current');
    });
    if (announce && live) {
      const h = root.querySelector('#kr-h-' + CSS.escape(id));
      live.textContent = (h ? h.textContent : '') + 'の読書面に切り替えました。';
    }
  }

  // 理由の説明を1つだけ見せる（一覧の行と「この論点の別の理由」）。位置は、説明が画面の外にあるときだけ寄せる。
  function pickReason(panel, bid, scroll) {
    const details = [...panel.querySelectorAll('.kr-reason-detail')];
    const target = details.find(a => a.dataset.reason === bid);
    if (!target) return false;
    details.forEach(a => a.toggleAttribute('data-on', a === target));
    panel.querySelectorAll('.kr-reason-pick').forEach(a => {
      if (a.dataset.reasonPick === bid) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
    if (scroll) {
      const r = target.getBoundingClientRect();
      if (r.top < 0 || r.top > innerHeight - 80) target.scrollIntoView({ block: 'start' });
    }
    return true;
  }
  // 皇室の理由区分の名前には「other-evaluation」のようにハイフンが入るので、論点IDの長い順に頭から当てる
  function reasonFromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    const id = [...ids].sort((a, b) => b.length - a.length).find(x => h.startsWith('kr-r-' + x + '-'));
    if (!id) return false;
    select(id, false);
    const panel = panels.find(p => p.dataset.issuePanel === id);
    return pickReason(panel, h.slice(('kr-r-' + id + '-').length), true);
  }

  root.classList.add('kr-js');
  select(fromHash() || root.dataset.defaultIssue, false);
  reasonFromHash();

  root.addEventListener('click', ev => {
    const a = ev.target.closest('[data-reason-pick]');
    if (!a || !root.contains(a)) return;
    const panel = a.closest('[data-issue-panel]');
    if (!panel || !pickReason(panel, a.dataset.reasonPick, true)) return;
    ev.preventDefault();
    ev.stopPropagation();
  }, true);

  // 山と論点名：その場で切り替える。位置は動かさず、フォーカスも押した所に残す。
  root.addEventListener('click', ev => {
    const a = ev.target.closest('[data-issue-id]');
    if (!a || !root.contains(a)) return;
    ev.preventDefault();
    const id = a.dataset.issueId;
    select(id, true);
    history.replaceState(null, '', '#issue-' + id);
    if (a.classList.contains('kr-chip') || a.classList.contains('kr-tab')) a.focus({ preventScroll: true });
  });

  // 冒頭の論点リンク（#issue-…）：選んだうえで、ブラウザの通常の移動に任せる。
  document.addEventListener('click', ev => {
    const a = ev.target.closest('a[href^="#issue-"]');
    if (!a || root.contains(a)) return;
    const id = a.getAttribute('href').slice('#issue-'.length);
    if (ids.includes(id)) select(id, true);
  });

  addEventListener('hashchange', () => { const id = fromHash(); if (id) select(id, true); else reasonFromHash(); });

  // 山なみ（元HTMLから写した対話式の図、planet.js）から論点を選ぶための入口。
  window.KoshitsuReading = Object.freeze({
    select(id) { if (!ids.includes(id)) return false; select(id, true); return true; }
  });
})();
