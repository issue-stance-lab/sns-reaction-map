/* 高齢者免許返納・論点ごとの読書面の試作（正本。scripts/elderly_reading.py が試作フォルダーへ写す）。
   自転車の青切符の reading.js（憲法改正論議の部活動型の圧縮済みの型、理由IDの前方一致の直しを含む）と同じ動き。
   論点タブを押すと、下の読書面だけを切り替える。ページは動かさない（scrollY を変えない）。
   公開ページでは手順7で元HTMLの対話式の山なみを上に写し、その橋渡しが window.ElderlyReading.select を呼ぶ。
   理由一覧の行（data-reason-pick）を押すと、その論点の中で選んだ理由の説明（.fr-reason-detail）だけを見せる。
   JavaScriptが無いときは、全論点の読書面と全理由の説明が縦に並び、リンクはその場所へ移動する。 */
(() => {
  'use strict';
  const root = document.getElementById('elderly-license-revocation-reading');
  if (!root) return;
  const panels = [...root.querySelectorAll('[data-issue-panel]')];
  const ids = panels.map(p => p.dataset.issuePanel);
  const live = document.getElementById('fr-live');
  const fromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1)).replace(/^issue-/, '');
    return ids.includes(id) ? id : null;
  };

  function select(id, announce) {
    panels.forEach(p => p.toggleAttribute('data-selected', p.dataset.issuePanel === id));
    root.querySelectorAll('.fr-tab').forEach(c => {
      if (c.dataset.issueId === id) c.setAttribute('aria-current', 'true');
      else c.removeAttribute('aria-current');
    });
    if (announce && live) {
      const h = root.querySelector('#fr-h-' + CSS.escape(id));
      live.textContent = (h ? h.textContent : '') + 'の読書面に切り替えました。';
    }
  }

  // 理由の説明を1つだけ見せる（一覧の行と「この論点の別の理由」）。位置は、説明が画面の外にあるときだけ寄せる。
  function pickReason(panel, bid, scroll) {
    const details = [...panel.querySelectorAll('.fr-reason-detail')];
    const target = details.find(a => a.dataset.reason === bid);
    if (!target) return false;
    details.forEach(a => a.toggleAttribute('data-on', a === target));
    panel.querySelectorAll('.fr-reason-pick').forEach(a => {
      if (a.dataset.reasonPick === bid) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
    if (scroll) {
      const r = target.getBoundingClientRect();
      if (r.top < 0 || r.top > innerHeight - 80) target.scrollIntoView({ block: 'start' });
    }
    return true;
  }
  // 論点IDにも理由区分のIDにもハイフン・下線が入りうる（憲法の手順7で直した不具合）ので、論点IDの前方一致で分ける
  function reasonFromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!h.startsWith('fr-r-')) return false;
    const id = ids.find(x => h.startsWith('fr-r-' + x + '-'));
    if (!id) return false;
    select(id, false);
    const panel = panels.find(p => p.dataset.issuePanel === id);
    return pickReason(panel, h.slice(('fr-r-' + id + '-').length), true);
  }

  // 外の記事から指定された論点を覚え、旧地図の初期化後に読書面へ移る。
  const initialIssue = fromHash();
  function restoreInitialIssue() {
    if (!initialIssue) return;
    select(initialIssue, false);
    history.replaceState(null, '', '#issue-' + initialIssue);
    const target = document.getElementById('issue-' + initialIssue);
    if (!target) return;
    const heading = target.querySelector('h3');
    if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
    target.scrollIntoView({ block: 'start', behavior: 'instant' });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restoreInitialIssue, { once: true });
  } else restoreInitialIssue();

  root.classList.add('fr-js');
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

  // 論点タブ：その場で切り替える。位置は動かさず、フォーカスも押した所に残す。
  root.addEventListener('click', ev => {
    const a = ev.target.closest('[data-issue-id]');
    if (!a || !root.contains(a)) return;
    ev.preventDefault();
    const id = a.dataset.issueId;
    select(id, true);
    history.replaceState(null, '', '#issue-' + id);
    if (a.classList.contains('fr-tab')) a.focus({ preventScroll: true });
  });

  // 冒頭の論点リンク（#issue-…）：選んだうえで、ブラウザの通常の移動に任せる。
  document.addEventListener('click', ev => {
    const a = ev.target.closest('a[href^="#issue-"]');
    if (!a || root.contains(a)) return;
    const id = a.getAttribute('href').slice('#issue-'.length);
    if (ids.includes(id)) select(id, true);
  });

  addEventListener('hashchange', () => { const id = fromHash(); if (id) select(id, true); else reasonFromHash(); });

  // 山なみ（手順7で元HTMLから写す対話式の図）から論点を選ぶための入口。
  window.ElderlyReading = Object.freeze({
    select(id) { if (!ids.includes(id)) return false; select(id, true); return true; }
  });
})();
