/* 部活動の地域移行・新デザイン（最新の型。scripts/build_bukatsu_redesign_v2.py）に載せた「前の対話式の山なみ」
   （元HTMLの #planet-block をそのまま写したもの）の橋渡し。消費税減税の planet.js と同じ動き。
   初期型の planet.js（素の論点IDの URL と読書面の欄の ID がぶつかるのを避ける細工）は使わない。新しい読書面の欄は
   #issue-{論点ID} なので、山なみの URL の書き込み（build_bukatsu_redesign_v2.py の PLANET_PATCHES で止めた）とはぶつからない。
   山なみ本体のスクリプト（PLANET_SECTION 内、定期更新で元HTMLごと作り直される。部活動は連動表示の橋渡し BUKATSU_CONNECTED_BRIDGE を
   中に持ち、window.BukatsuConnectedMap を出す）は、上の3か所のほかは書き換えない。
     1. 立場ボタン（#modes）を、立場名・件数・割合が読めるカードに作り直す。
     2. 論点ボタンの一覧（#list）を選択パネル（#panel）の直前へ移す。
     3. 山の SVG の viewBox を、実際に描いた範囲に切り直す。論点を選んでも図を100マスの背後へ移さない。
     4. 山を押したら、URL を #issue-{論点ID} に置き換え（履歴は増やさない）、山なみ自身の hashchange の経路（画面を動かさない着地）で
        山なみ側を合わせ、読書面（window.BukatsuReading.select）を選んで、その欄へ移る。見出しにフォーカスする。
     5. 人が論点ボタン（#list）を押したときは、山なみの中で切り替える（山なみの元の動き）。読書面もその論点に合わせ、URL を置き換える。
     6. docs/topic-modern.js は #issue-… のハッシュを見ると #btn-{論点ID} を押させて地図へ戻してしまう。
        新ページでは #issue-… は読書面の場所なので、スクリプトが押させたクリック（isTrusted=false）だけを止める。 */
(() => {
  'use strict';
  const D = window.PLANET_DATA;
  const block = document.getElementById('planet-block');
  const svg = document.getElementById('section');
  if (!D || !block || !svg) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = n => Number(n).toLocaleString('ja-JP');
  const issueIds = D.issues.map(i => i.id);

  // 1. 立場ボタン
  const modes = document.getElementById('modes');
  if (modes) {
    modes.querySelectorAll('button[data-m]').forEach(button => {
      const mode = D.modes.find(m => m.id === button.dataset.m);
      if (!mode) return;
      const stance = D.stances.find(s => s.key === mode.id);
      const label = document.createElement('span');
      label.className = 'cap-mode-name';
      label.textContent = stance ? stance.label : 'すべて';
      const count = document.createElement('strong');
      count.textContent = fmt(mode.total) + '件';
      button.replaceChildren(label, count);
      if (stance) {
        button.classList.add('sg-pick-btn');
        button.style.setProperty('--cap-stance-color', stance.color);
        const share = document.createElement('small');
        const total = D.totals.opinions;
        share.textContent = total ? (100 * mode.total / total).toFixed(1) + '%' : '';
        count.append(' ', share);
      }
      button.setAttribute('aria-label', mode.label + ' ' + fmt(mode.total) + '件');
    });
  }

  // 2. 論点ボタンの一覧
  const list = document.getElementById('list');
  const panel = document.getElementById('panel');
  if (list && panel) {
    const heading = list.previousElementSibling;
    if (heading && heading.matches('h3.sec')) heading.hidden = true;
    list.setAttribute('aria-label', '論点を切り替える');
    panel.before(list);
  }

  // 3. viewBox を描いた範囲に合わせる（海面下の演出は CSS で隠してあるので測る範囲に入らない）
  try {
    const box = svg.getBBox();
    if (box && box.height) {
      svg.setAttribute('viewBox', '0 ' + Math.max(0, box.y - 6) + ' 900 ' + (box.height + 12));
      svg.setAttribute('preserveAspectRatio', 'none');
    }
  } catch (_) { /* 測れない環境では元の viewBox のまま */ }

  // 3b. 山なみは論点を選ぶと図を100マスの背後へ薄く敷く（押せなくなる）。新ページでは山を押して読書面へ移るので、
  //     図は常に論点ボタンの上に置いたままにする。
  const stage = block.querySelector('.stage');
  const chartBox = block.querySelector('.chart-box');
  if (stage && chartBox && typeof MutationObserver === 'function') {
    const keep = () => {
      if (chartBox.parentElement === stage && stage.firstElementChild === chartBox) return;
      chartBox.classList.remove('as-backdrop');
      stage.insertBefore(chartBox, stage.firstChild);
    };
    new MutationObserver(keep).observe(stage, { childList: true, subtree: true });
    keep();
  }

  // 4. 山を押したら読書面へ
  function goReading(id) {
    const target = document.getElementById('issue-' + id);
    if (!target || !issueIds.includes(id)) return;
    // URL を読書面の場所に置き換え、山なみ（連動表示の橋渡しの hashchange → 画面を動かさない着地）と読書面を合わせる
    history.replaceState(null, '', '#issue-' + id);
    dispatchEvent(new HashChangeEvent('hashchange'));
    if (window.BukatsuReading) window.BukatsuReading.select(id, false);
    target.scrollIntoView({ block: 'start', behavior: reduce ? 'auto' : 'smooth' });
    // なめらかなスクロールは、山なみの選択パネルの描き直しと重なると途中で止まることがある（Chromium で確認）。
    // 止まった位置で欄の上端が画面の上の方に来ていなければ、一度だけ寄せ直す
    const settle = () => {
      const top = target.getBoundingClientRect().top;
      if (top < -4 || top > 240) target.scrollIntoView({ block: 'start' });
    };
    if (!reduce) {
      if ('onscrollend' in window) addEventListener('scrollend', settle, { once: true });
      else setTimeout(settle, 900);
    }
    const h = document.getElementById('fr-h-' + id);
    if (h) h.focus({ preventScroll: true });
  }
  function hillFrom(ev) {
    const g = ev.target.closest && ev.target.closest('.hill');
    if (!g || !svg.contains(g)) return null;
    const issue = D.issues[Number(g.dataset.i)];
    return issue ? issue.id : null;
  }
  svg.addEventListener('click', ev => {
    const id = hillFrom(ev);
    if (!id) return;
    ev.stopPropagation();
    ev.preventDefault();
    goReading(id);
  }, true);
  svg.addEventListener('keydown', ev => {
    if (ev.key !== 'Enter' && ev.key !== ' ') return;
    const id = hillFrom(ev);
    if (!id) return;
    ev.stopPropagation();
    ev.preventDefault();
    goReading(id);
  }, true);

  document.addEventListener('click', ev => {
    const b = ev.target.closest && ev.target.closest('#list button');
    if (!b) return;
    // 6. topic-modern.js が押させる #btn-… のクリックを止める
    if (!ev.isTrusted) {
      ev.stopPropagation();
      ev.preventDefault();
      return;
    }
    // 5. 人が押したときは山なみの元の動き（地図の中で切り替え）のまま、読書面と URL を合わせる（履歴は増やさない）
    const id = b.id && b.id.startsWith('btn-') ? b.id.slice(4) : '';
    if (!issueIds.includes(id)) return;
    setTimeout(() => {
      if (window.BukatsuReading) window.BukatsuReading.select(id, false);
      history.replaceState(null, '', '#issue-' + id);
    }, 0);
  }, true);
})();
