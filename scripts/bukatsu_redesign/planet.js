/* 部活動の地域移行・新デザインに載せた「前の対話式の山なみ」（元HTMLの #planet-block をそのまま写したもの）の橋渡し。
   生成AIと著作権（scripts/ai_copyright_redesign/planet.js）の写しに、部活動だけの事情（下の 6）を足したもの。
   山なみ本体のスクリプト（PLANET_SECTION 内、定期更新で元HTMLごと作り直される）は書き換えない。ここでは
   旧ページで docs/bukatsu-connected.js が担っていた見た目の組み替えのうち山なみの分だけと、
   新デザインの読書面へのつなぎだけを行う。
     1. 立場ボタン（#modes）を、立場名・件数・割合が読めるカードに作り直す（旧ページと同じ）。
     2. 論点ボタンの一覧（#list）を選択パネル（#panel）の直前へ移す（旧ページと同じ）。
     3. 山の SVG の viewBox を、実際に描いた範囲に切り直す（旧ページと同じ）。論点を選んでも図を100マスの背後へ移さない。
     4. 山を押したら、その論点の読書面（#issue-{論点ID}）を選んで、そこへ移る。
        山なみ側の選択（色・100マス・選択パネル）は、山なみ自身の hashchange の経路（画面を動かさない着地）で合わせる。
     5. docs/topic-modern.js は #issue-… のハッシュを見ると #btn-{論点ID} を押させて地図へ戻してしまう。
        新ページでは #issue-… は読書面の場所なので、スクリプトが押させたクリック（isTrusted=false）だけを止める。
     6. 部活動の読書面は、論点の欄そのものが素の論点ID（#bukatsu-chiiki-…）を持ち、app.js も素の論点IDの URL で
        読書面を切り替えてそこへ移る。山なみも論点を選ぶと URL を素の論点IDにするので、そのままだと
        論点ボタンを押しただけで画面が読書面へ飛ぶ。山なみが URL を書く間だけ欄の ID を外し、
        app.js には画面を動かさないよう伝える（BUKATSU_PLANET_QUIET）。読書面の論点の切り替えには山なみも合わせる。 */
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
      label.className = 'bk-mode-name';
      label.textContent = stance ? stance.label : 'すべて';
      const count = document.createElement('strong');
      count.textContent = fmt(mode.total) + '件';
      button.replaceChildren(label, count);
      if (stance) {
        button.classList.add('sg-pick-btn');
        button.style.setProperty('--bk-stance-color', stance.color);
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

  // 6. 山なみが URL（素の論点ID）を書く間だけ、同じ ID を持つ読書面の欄から ID を外し、app.js に画面を動かさないよう伝える。
  //    ブラウザがその URL の欄へ移る処理は少し遅れて走るので、ID を戻すのはその URL の hashchange を
  //    app.js・山なみが受け取った後（ここで足す受け手は最後に呼ばれる）、さらにページの読み込みが終わってから少し後。
  function quietly(id, write, after) {
    const section = document.getElementById(id);
    const owned = section && !block.contains(section) ? section : null;
    if (owned) owned.removeAttribute('id');
    window.BUKATSU_PLANET_QUIET = true;
    let heard = false, done = false;
    const restore = () => {
      if (done) return;
      done = true;
      if (owned) owned.id = id;
      window.BUKATSU_PLANET_QUIET = false;
    };
    const later = () => {
      if (document.readyState === 'complete') setTimeout(restore, 60);
      else addEventListener('load', () => setTimeout(restore, 60), { once: true });
    };
    const onHash = () => {
      if (heard) return;
      heard = true;
      removeEventListener('hashchange', onHash);
      if (after) after();
      later();
    };
    addEventListener('hashchange', onHash);
    try { write(); } finally { setTimeout(onHash, 400); }  // URL が変わらなかったときも戻す
  }
  const issueIds = D.issues.map(i => i.id);
  const currentId = () => { try { return decodeURIComponent(location.hash.slice(1)); } catch (_) { return ''; } };

  // 4. 山を押したら読書面へ
  function goReading(id) {
    if (!issueIds.includes(id)) return;
    const finish = () => { if (window.BukatsuReading) window.BukatsuReading.select(id, true); };
    if (currentId() !== id) {
      // 山なみ自身の hashchange（素の論点ID）で、画面を動かさずに山・100マス・選択パネルを合わせてから、読書面へ移る
      quietly(id, () => { location.hash = id; }, finish);
    } else {
      finish();
    }
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
    if (ev.isTrusted) {
      // 6. 人が論点ボタンを押したときは山なみの動きのまま（地図の中で切り替え、読書面も合わせる）。画面だけ読書面へ飛ばさない
      const b = ev.target.closest && ev.target.closest('#list button[id^="btn-"]');
      const id = b ? b.id.slice(4) : '';
      if (issueIds.includes(id) && currentId() !== id) quietly(id, () => {}, null);
      return;
    }
    const b = ev.target.closest && ev.target.closest('#list button');
    if (!b) return;
    ev.stopPropagation();
    ev.preventDefault();
  }, true);

  // 6. 読書面の論点ボタン（app.js、URL を素の論点IDにする）で切り替えたら、山なみもその論点に合わせる（画面は動かさない）
  document.addEventListener('click', ev => {
    if (!(ev.target.closest && ev.target.closest('button[data-select]'))) return;
    const id = currentId();
    if (!issueIds.includes(id)) return;
    // 山なみは論点を選ぶと選択パネルの見出しへフォーカスを移し、上の図の高さも変わる。
    // 読書面で押した人のフォーカスと、読書面の見えている位置はそのまま残す
    const active = document.activeElement;
    const reading = document.getElementById('reading');
    const before = reading ? reading.getBoundingClientRect().top : 0;
    quietly(id, () => dispatchEvent(new HashChangeEvent('hashchange')), null);
    if (active && active !== document.activeElement && active.focus) active.focus({ preventScroll: true });
    const shift = reading ? reading.getBoundingClientRect().top - before : 0;
    if (shift) window.scrollBy({ left: 0, top: shift, behavior: 'instant' });
  });

  // 7. 読み込み時の自動の選択（件数1位の論点）。URL が空だったときは build_bukatsu_redesign.py が仮に #map を置いて
  //    山なみ自身の自動の選択を止めているので、ここで画面を動かさずに同じ論点を選び直す。
  if (window.BUKATSU_LOAD_HASH === '' && location.hash === '#map') {
    const top = D.issues.reduce((a, b) => (b.count > a.count ? b : a));
    quietly(top.id, () => {
      history.replaceState(null, '', location.pathname + location.search + '#' + top.id);
      dispatchEvent(new HashChangeEvent('hashchange'));
    }, null);
  }
})();
