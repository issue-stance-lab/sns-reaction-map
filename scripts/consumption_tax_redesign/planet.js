/* 消費税減税・新デザインに載せた「前の対話式の山なみ」（元HTMLの #planet-block をそのまま写したもの）の橋渡し。
   辺野古の planet.js（あだ名禁止・高齢者・自転車と同じ）と同じ動き。山なみ本体のスクリプト（PLANET_SECTION 内、
   定期更新で元HTMLごと作り直される。消費税は連動表示の橋渡し TAX_CONNECTED_BRIDGE を中に持ち、window.ConsumptionTaxMap を出す）は書き換えない。
   連動表示の本体（docs/consumption-tax-connected.js）は読み込まないので、橋渡しは旧来の動き（activate されない）のまま働く。
   ここでは旧ページで docs/consumption-tax-connected.js・theme-design.css が担っていた見た目の組み替えのうち山なみの分だけと、
   新デザインの読書面へのつなぎだけを行う。
     1. 立場ボタン（#modes）を、立場名・件数・割合が読めるカードに作り直す。
     2. 論点ボタンの一覧（#list）を選択パネル（#panel）の直前へ移す。
     3. 山の SVG の viewBox を、実際に描いた範囲に切り直す。論点を選んでも図を100マスの背後へ移さない。
     4. 山を押したら、山なみ側をその論点に合わせ（ConsumptionTaxMap.selectIssue。URL・履歴は触らない）、
        読書面（#issue-{論点ID}）を選んで、そこへ移る。URL は #issue-{論点ID} に置き換える（履歴は増やさない）。
     5. docs/topic-modern.js は #issue-… のハッシュを見ると #btn-{論点ID} を押させて地図へ戻してしまう。
        新ページでは #issue-… は読書面の場所なので、スクリプトが押させたクリック（isTrusted=false）だけを止める。 */
(() => {
  'use strict';
  const D = window.PLANET_DATA;
  const block = document.getElementById('planet-block');
  const svg = document.getElementById('section');
  if (!D || !block || !svg) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = n => Number(n).toLocaleString('ja-JP');

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
  //     図は常に論点ボタンの上に置いたままにする（旧ページの連動表示と同じ並び）。
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
    if (!target) return;
    // 山なみ側（色・100マス・選択パネル）を合わせる。橋渡しの land は history:'none' なら URL に触れない
    if (window.ConsumptionTaxMap) window.ConsumptionTaxMap.selectIssue(id, { history: 'none' });
    if (window.ConsumptionTaxReading) window.ConsumptionTaxReading.select(id);
    history.replaceState(null, '', '#issue-' + id);
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

  // 5. topic-modern.js が押させる #btn-… のクリックを止める（人が押したときはそのまま）
  document.addEventListener('click', ev => {
    if (ev.isTrusted) return;
    const b = ev.target.closest && ev.target.closest('#list button');
    if (!b) return;
    ev.stopPropagation();
    ev.preventDefault();
  }, true);
})();
