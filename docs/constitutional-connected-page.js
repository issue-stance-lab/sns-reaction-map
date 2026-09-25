/* 憲法改正論議の連動表示・ページ全体の再配置（工程4、2026-09-26）。
   bukatsu-chiikiのbukatsu-connected-page.jsに合わせ、背景（#bukatsu-background）を山の
   後段へ移して日付タブ化し、編集部整理・凡例・判断の入口を折りたたみ、資料欄を「資料を読む／
   x投稿で語られない話／一次資料クイズ」の3タブへ統合する。理由からX投稿を開く機能は、
   constitutional-amendmentの旧代表投稿が論点全体の投稿2件のみでbukatsu-chiiki同様の理由別内訳を
   持たないため実装しない（工程1内容確定書の方針どおり）。年表の論点連動・出典計測は
   scripts/templates/constitutional_connected_bridge.jsが配線済み（工程4）のため、ここでは
   触らない。bukatsu-check（制度確認4項目）・旧代表投稿・oceanは読書面へ
   統合済みのため通常画面で非表示にする。 */
(function () {
  'use strict';
  if (!document.body.classList.contains('constitutional-connected')) return;
  var map = window.ConstitutionalConnectedMap, data = window.PLANET_DATA;
  var index = JSON.parse(document.getElementById('constitutional-connected-data').textContent);
  var panel = document.getElementById('panel');
  var reduce = function () { return matchMedia('(prefers-reduced-motion: reduce)').matches; };
  var esc = function (value) { return String(value).replace(/[&<>"']/g, function (ch) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]; }); };

  // 短い現状だけを冒頭に残し、経緯の詳細は山・読書面の後段へ移す。
  var mountain = document.getElementById('planet-block').closest('.planet-panel');
  var background = document.getElementById('bukatsu-background');
  if (mountain && background) {
    var status = document.createElement('aside');
    status.className = 'ca-status';
    var now = background.querySelector('.bg-now');
    status.innerHTML = '<p class="ca-eyebrow">制度の確認時点 ' + esc(index.background_checked_on) + '</p><p>'
      + esc(now ? now.textContent : '') + '</p><a href="#bg-title">制度の経緯を確かめる ↓</a>';
    mountain.before(status);
    mountain.after(background);

    var timeline = background.querySelector('.bg-tl');
    if (timeline) {
      var intro = document.createElement('details'); intro.className = 'ca-background-intro';
      intro.innerHTML = '<summary>背景を読む</summary>';
      Array.prototype.slice.call(background.children).forEach(function (child) {
        if (child === timeline || child.classList.contains('panel-title') || child === status) return;
        if (child.compareDocumentPosition(timeline) & Node.DOCUMENT_POSITION_FOLLOWING) intro.appendChild(child);
      });
      var titleEl = background.querySelector('.panel-title');
      if (titleEl) titleEl.after(intro); else background.prepend(intro);

      var events = Array.prototype.slice.call(timeline.children);
      var nav = document.createElement('div');
      nav.className = 'ca-timeline-nav'; nav.setAttribute('role', 'tablist');
      nav.setAttribute('aria-label', '背景の経緯の日付');
      timeline.before(nav);
      function selectDate(selected, focus) {
        events.forEach(function (event, i) {
          var active = selected === i, button = nav.children[i];
          event.hidden = !active;
          button.setAttribute('aria-selected', String(active));
          button.tabIndex = active ? 0 : -1;
        });
        if (focus) nav.children[selected].focus();
      }
      events.forEach(function (event, i) {
        event.dataset.caTimelineI = String(i);
        var when = event.querySelector('.when');
        var button = document.createElement('button');
        button.type = 'button'; button.id = 'ca-date-' + i;
        button.textContent = when ? Array.prototype.filter.call(when.childNodes, function (n) { return n.nodeType === 3; }).map(function (n) { return n.textContent; }).join('').trim() : String(i + 1);
        button.setAttribute('role', 'tab');
        event.id = 'ca-timeline-' + i;
        button.setAttribute('aria-controls', event.id);
        event.setAttribute('role', 'tabpanel');
        event.setAttribute('aria-labelledby', button.id);
        button.onclick = function () { selectDate(i, false); };
        button.onkeydown = function (evt) {
          var next = evt.key === 'ArrowRight' ? (i + 1) % events.length
            : evt.key === 'ArrowLeft' ? (i + events.length - 1) % events.length
            : evt.key === 'Home' ? 0 : evt.key === 'End' ? events.length - 1 : null;
          if (next !== null) { evt.preventDefault(); selectDate(next, true); }
        };
        nav.appendChild(button);
      });
      if (events.length) selectDate(events.length - 1, false);
    }
    var jump = background.querySelector('.bg-jump a');
    if (jump) jump.textContent = '選んだ論点に戻る ↑';
  }

  var tide = document.getElementById('constitutional-tide-widget');
  if (tide && !tide.querySelector('.ca-comparison-note')) {
    var heading = document.createElement('h2'); heading.textContent = '収集した投稿の変化';
    tide.prepend(heading);
    var note = document.createElement('p'); note.className = 'ca-comparison-note';
    note.textContent = '制度の経緯と、投稿サンプルの比較は別の情報です。この差だけで、制度決定の影響や同じ人の意見の変化は判断できません。';
    tide.appendChild(note);
  }

  function fold(element, label) {
    if (!element || element.closest('.ca-fold')) return;
    var details = document.createElement('details'); details.className = 'ca-fold';
    var summary = document.createElement('summary'); summary.textContent = label;
    element.before(details);
    details.append(summary, element);
  }
  var editorial = document.getElementById('editorial');
  fold(editorial, '編集部の横断整理を読む');
  var meta = document.getElementById('meta');
  if (meta && meta.previousElementSibling && meta.previousElementSibling.matches('h3')) meta.previousElementSibling.hidden = true;
  fold(meta, '図の見かたを確かめる');
  // 編集・分析情報は横断的な内容なので、山と読書面の後段で必要な人だけ開ける。
  fold(document.getElementById('article-trust'), '編集・分析情報を読む');

  // ---------- 資料欄の3タブ化: 資料を読む / x投稿で語られない話 / 一次資料クイズ ----------
  var quizRoot = document.getElementById('quiz');
  var quizHeading = quizRoot && quizRoot.previousElementSibling;
  if (quizHeading && quizHeading.matches('h3')) quizHeading.hidden = true;
  if (quizRoot) quizRoot.remove();
  var quiz = { active: false, position: 0, answers: new Map() };
  var verdicts = ['fact', 'gap', 'miss'];
  var discoveryActive = false;
  var selectingForQuiz = false;

  var sourceItems = new Map();
  // nearest_issue_idが無い2件も、論点へ推測で割り当てず、テーマ全体の資料タブへ残す。
  // 旧#oceanの並びはPLANET_DATAのsunk_continentsと同じ生成順なので、位置で対応させる。
  Array.prototype.forEach.call(document.querySelectorAll('#ocean .sunk'), function (item, i) {
    var source = data.ocean.sunk_continents[i];
    if (source) sourceItems.set(source.id, item);
  });
  var discoveryRoot = document.createElement('div'); discoveryRoot.className = 'ca-source-stories'; discoveryRoot.hidden = true;
  discoveryRoot.innerHTML = '<h3>x投稿で語られない話</h3><p class="ca-note">憲法改正論議テーマ全体の' + data.ocean.sunk_continents.length + '項目です。一次資料に記載があり、今回収集した投稿では言及が見つからなかった内容をまとめています。</p>';
  data.ocean.sunk_continents.forEach(function (item) {
    var src = sourceItems.get(item.id);
    if (!src) return;
    var entry = src.cloneNode(true);
    entry.dataset.caDiscovery = item.id;
    entry.querySelectorAll('[id]').forEach(function (n) { n.id = 'ca-discovery-' + n.id; });
    discoveryRoot.appendChild(entry);
  });

  var claimIssue = function (claim) {
    var owner = data.issues.find(function (i) { return (i.claims || []).some(function (c) { return c.id === claim.id; }); });
    return owner ? owner.id : null;
  };
  var verdictLabel = function (value) {
    var found = data.claims.find(function (c) { return c.verdict === value; });
    return found ? found.verdict_label : ({ fact: '資料どおり', gap: '少しずれる', miss: '裏が取れない' })[value];
  };
  function returnToReading() {
    quiz.active = false; discoveryActive = false; mount();
    var head = panel.querySelector('[data-ca-read]');
    if (head) head.focus({ preventScroll: true });
  }
  function mount() {
    var aside = panel.querySelector('.ca-evidence');
    if (!aside) { quiz.active = false; discoveryActive = false; quizRoot.remove(); discoveryRoot.remove(); return; }
    var claim = data.claims[quiz.position];
    if (quiz.active && claim && !selectingForQuiz && map.getState().issueId !== claimIssue(claim)) quiz.active = false;
    if (!aside.querySelector('.ca-evidence-controls')) {
      var reading = document.createElement('div'); reading.className = 'ca-reading-sources';
      reading.append.apply(reading, aside.childNodes);
      var controls = document.createElement('div'); controls.className = 'ca-evidence-controls'; controls.setAttribute('aria-label', '資料の読み方');
      controls.innerHTML = '<button type="button" data-ca-read>資料を読む</button><button type="button" data-ca-discover>x投稿で語られない話</button><button type="button" data-ca-quiz>一次資料クイズ · ' + data.claims.length + '問</button>';
      controls.querySelector('[data-ca-read]').onclick = returnToReading;
      controls.querySelector('[data-ca-discover]').onclick = function (event) {
        var opening = !discoveryActive;
        quiz.active = false; discoveryActive = true; mount();
        if (opening && event.isTrusted && typeof window.gtag === 'function') window.gtag('event', 'source_only_tab_open', { topic_id: data.theme_id });
      };
      controls.querySelector('[data-ca-quiz]').onclick = function () { quiz.active = true; showQuestion(quiz.position); };
      aside.append(controls, reading);
    }
    aside.querySelector('.ca-reading-sources').hidden = quiz.active || discoveryActive;
    aside.querySelector('[data-ca-read]').setAttribute('aria-pressed', String(!quiz.active && !discoveryActive));
    aside.querySelector('[data-ca-discover]').setAttribute('aria-pressed', String(discoveryActive));
    aside.querySelector('[data-ca-quiz]').setAttribute('aria-pressed', String(quiz.active));
    discoveryRoot.hidden = !discoveryActive; quizRoot.hidden = !quiz.active;
    aside.append(discoveryRoot, quizRoot);
    if (!panel.querySelector('.ca-evidence-jump')) {
      var evidenceJump = document.createElement('button');
      evidenceJump.type = 'button'; evidenceJump.className = 'ca-evidence-jump'; evidenceJump.textContent = 'この論点の制度・資料へ ↓';
      evidenceJump.onclick = function () { aside.scrollIntoView({ block: 'start', behavior: reduce() ? 'auto' : 'smooth' }); };
      var scopeNote = panel.querySelector('.ca-scope-note');
      if (scopeNote) scopeNote.after(evidenceJump);
    }
  }
  function renderQuiz() {
    var claim = data.claims[quiz.position];
    if (!claim) {
      var score = data.claims.filter(function (c) { return quiz.answers.get(c.id) === c.verdict; }).length;
      quizRoot.innerHTML = '<h3>資料クイズの結果</h3><p class="ca-quiz-score">' + score + ' / ' + data.claims.length + '問正解</p>'
        + '<p>回答済み ' + quiz.answers.size + '問。本文の資料と同じ内容で照合しています。</p>'
        + '<button type="button" data-ca-restart>最初の問題へ</button><button type="button" data-ca-finish>資料に戻る</button>';
      quizRoot.querySelector('[data-ca-restart]').onclick = function () { showQuestion(0); };
      quizRoot.querySelector('[data-ca-finish]').onclick = returnToReading;
      return;
    }
    var answer = quiz.answers.get(claim.id);
    quizRoot.innerHTML = '<div class="qh" tabindex="-1"><span>問 ' + (quiz.position + 1) + ' / ' + data.claims.length + '</span><span>資料照合 ' + esc(data.ocean.checked_on) + '</span></div>'
      + '<p class="ca-quiz-note">収集した投稿から選んだ主張です。掲載した投稿例そのものへの判定ではありません。</p>'
      + '<p class="qclaim">「' + esc(claim.claim) + '」</p><div class="ca-qopts">' + verdicts.map(function (v) {
        return '<button type="button" data-verdict="' + v + '" ' + (answer ? 'disabled' : '') + ' class="' + (answer ? (v === claim.verdict ? 'hit' : v === answer ? 'miss' : '') : '') + '">' + esc(verdictLabel(v)) + '</button>';
      }).join('') + '</div>'
      + '<div class="qans" ' + (answer ? '' : 'hidden') + '><p class="ca-verdict">' + esc(claim.verdict_label) + '</p><p>' + esc(claim.finding) + '</p>'
      + '<div class="ca-quiz-sources">' + claim.sources.map(function (s) { return '<p><a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">' + esc(s.name) + '</a></p>'; }).join('') + '</div>'
      + '<button type="button" class="qnext">' + (quiz.position === data.claims.length - 1 ? '結果を見る' : '次の問題 →') + '</button></div>';
    quizRoot.dataset.claimId = claim.id;
    quizRoot.querySelectorAll('[data-verdict]').forEach(function (button) {
      button.onclick = function () {
        if (quiz.answers.has(claim.id)) return;
        quiz.answers.set(claim.id, button.dataset.verdict);
        renderQuiz();
        var ans = quizRoot.querySelector('.qans');
        ans.tabIndex = -1; ans.focus({ preventScroll: true });
      };
    });
    quizRoot.querySelector('.qnext').onclick = function () { showQuestion(quiz.position + 1); };
  }
  function showQuestion(position) {
    quiz.position = position; quiz.active = true; discoveryActive = false; selectingForQuiz = true;
    var claim = data.claims[position];
    var issueId = claim ? claimIssue(claim) : null;
    if (issueId) map.selectIssue(issueId);
    selectingForQuiz = false;
    renderQuiz(); mount();
    var head = quizRoot.querySelector('.qh, h3');
    if (!head) return;
    head.tabIndex = -1;
    var bounds = head.getBoundingClientRect();
    if (bounds.top < 110 || bounds.bottom > innerHeight) head.scrollIntoView({ block: 'start', behavior: reduce() ? 'auto' : 'smooth' });
    else head.focus({ preventScroll: true });
  }
  new MutationObserver(mount).observe(panel, { childList: true });
  mount();
  if (location.hash === '#quiz') showQuestion(0);

  // ---------- 授業印刷は節のみ、通常印刷は全本文。閉じた詳細も印刷中だけ展開する。 ----------
  document.querySelectorAll('#fallback img').forEach(function (img) { img.loading = 'eager'; });
  var fallbackHeading = document.querySelector('#fallback > h3');
  var fallbackLabel = fallbackHeading ? fallbackHeading.textContent : '';
  var printDetails = [];
  document.addEventListener('click', function (event) {
    if (event.target.closest('.classroom-print-btn')) document.body.classList.add('ca-print-classroom');
  }, true);
  addEventListener('beforeprint', function () {
    if (fallbackHeading) fallbackHeading.textContent = '全' + data.issues.length + '論点の内容';
    printDetails = Array.prototype.slice.call(document.querySelectorAll('details:not([open])'));
    printDetails.forEach(function (d) { d.open = true; });
  });
  addEventListener('afterprint', function () {
    if (fallbackHeading) fallbackHeading.textContent = fallbackLabel;
    printDetails.forEach(function (d) { d.open = false; });
    printDetails = [];
    document.body.classList.remove('ca-print-classroom');
  });
}());
