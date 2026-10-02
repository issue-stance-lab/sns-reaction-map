/* 生成AIと著作権の連動表示・ページ全体の再配置（工程4、2026-09-23）。
   bukatsu-chiikiのbukatsu-connected-page.jsに合わせ、背景（#bukatsu-background）を山の
   後段へ移して日付タブ化し、編集部整理・凡例・判断の入口を折りたたみ、資料欄を「資料を読む／
   x投稿で語られない話／一次資料クイズ」の3タブへ統合する。理由からX投稿を開く機能は、
   ai-copyrightのissue-cardsが論点全体の投稿2件のみでbukatsu-chiiki同様の理由別内訳を
   持たないため実装しない（工程1内容確定書の方針どおり）。年表の論点連動・出典計測は
   scripts/templates/ai_copyright_connected_bridge.jsが配線済み（工程4）のため、ここでは
   触らない。bukatsu-check（制度確認4項目）・claim-audit・issue-cards・oceanは読書面へ
   統合済みのため通常画面で非表示にする。 */
(function () {
  'use strict';
  if (!document.body.classList.contains('ai-copyright-connected')) return;
  var map = window.AiCopyrightConnectedMap, data = window.PLANET_DATA;
  var index = JSON.parse(document.getElementById('ai-copyright-connected-data').textContent);
  var panel = document.getElementById('panel');
  var reduce = function () { return matchMedia('(prefers-reduced-motion: reduce)').matches; };
  var esc = function (value) { return String(value).replace(/[&<>"']/g, function (ch) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]; }); };

  // 短い現状だけを冒頭に残し、経緯の詳細は山・読書面の後段へ移す。
  var mountain = document.getElementById('planet-block').closest('.planet-panel');
  var background = document.getElementById('bukatsu-background');
  if (mountain && background) {
    var status = document.createElement('aside');
    status.className = 'aic-status';
    var now = background.querySelector('.bg-now');
    status.innerHTML = '<p class="aic-eyebrow">制度の確認時点 ' + esc(index.background_checked_on) + '</p><p>'
      + esc(now ? now.textContent : '') + '</p><a href="#bg-title">制度の経緯を確かめる ↓</a>';
    mountain.before(status);
    mountain.after(background);

    var timeline = background.querySelector('.bg-tl');
    if (timeline) {
      var intro = document.createElement('details'); intro.className = 'aic-background-intro';
      intro.innerHTML = '<summary>背景を読む</summary>';
      Array.prototype.slice.call(background.children).forEach(function (child) {
        if (child === timeline || child.classList.contains('panel-title') || child === status) return;
        if (child.compareDocumentPosition(timeline) & Node.DOCUMENT_POSITION_FOLLOWING) intro.appendChild(child);
      });
      var titleEl = background.querySelector('.panel-title');
      if (titleEl) titleEl.after(intro); else background.prepend(intro);

      var events = Array.prototype.slice.call(timeline.children);
      var nav = document.createElement('div');
      nav.className = 'aic-timeline-nav'; nav.setAttribute('role', 'tablist');
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
        event.dataset.aicTimelineI = String(i);
        var when = event.querySelector('.when');
        var button = document.createElement('button');
        button.type = 'button'; button.id = 'aic-date-' + i;
        button.textContent = when ? Array.prototype.filter.call(when.childNodes, function (n) { return n.nodeType === 3; }).map(function (n) { return n.textContent; }).join('').trim() : String(i + 1);
        button.setAttribute('role', 'tab');
        event.id = 'aic-timeline-' + i;
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

  var tide = document.getElementById('ai-copyright-tide-widget');
  if (tide && !tide.querySelector('.aic-comparison-note')) {
    var heading = document.createElement('h2'); heading.textContent = '収集した投稿の変化';
    tide.prepend(heading);
    var note = document.createElement('p'); note.className = 'aic-comparison-note';
    note.textContent = '制度の経緯と、投稿サンプルの比較は別の情報です。この差だけで、制度決定の影響や同じ人の意見の変化は判断できません。';
    tide.appendChild(note);
  }

  function fold(element, label) {
    if (!element || element.closest('.aic-fold')) return;
    var details = document.createElement('details'); details.className = 'aic-fold';
    var summary = document.createElement('summary'); summary.textContent = label;
    element.before(details);
    details.append(summary, element);
  }
  var editorial = document.getElementById('editorial');
  fold(editorial, '編集部の横断整理を読む');
  var meta = document.getElementById('meta');
  if (meta && meta.previousElementSibling && meta.previousElementSibling.matches('h3')) meta.previousElementSibling.hidden = true;
  fold(meta, '図の見かたを確かめる');
  // 判断の入口（学習・出力・公開の3段階）はai-copyright独自で、特定の1論点に対応しない
  // 横断的な内容のため論点へ統合しない（工程1内容確定書の方針）。他の折りたたみと同様、
  // 必要な人が開けるようにする。
  fold(document.getElementById('copyright-entry'), '判断の入口（学習・出力・公開）を読む');

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
  data.issues.forEach(function (issue) {
    var tpl = document.getElementById('ai-copyright-reading-' + issue.id);
    if (!tpl) return;
    tpl.content.querySelectorAll('[data-aic-source-only]').forEach(function (item) {
      if (!sourceItems.has(item.dataset.aicSourceOnly)) sourceItems.set(item.dataset.aicSourceOnly, item);
    });
  });
  var discoveryRoot = document.createElement('div'); discoveryRoot.className = 'aic-source-stories'; discoveryRoot.hidden = true;
  discoveryRoot.innerHTML = '<h3>x投稿で語られない話</h3><p class="aic-note">生成AIと著作権テーマ全体の' + data.ocean.sunk_continents.length + '項目です。一次資料に記載があり、今回収集した投稿では言及が見つからなかった内容をまとめています。</p>';
  data.ocean.sunk_continents.forEach(function (item) {
    var src = sourceItems.get(item.id);
    if (!src) return;
    var entry = src.cloneNode(true);
    entry.dataset.aicDiscovery = item.id; delete entry.dataset.aicSourceOnly;
    entry.querySelectorAll('[id]').forEach(function (n) { n.id = 'aic-discovery-' + n.id; });
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
    var head = panel.querySelector('[data-aic-read]');
    if (head) head.focus({ preventScroll: true });
  }
  function mount() {
    var aside = panel.querySelector('.aic-evidence');
    if (!aside) { quiz.active = false; discoveryActive = false; quizRoot.remove(); discoveryRoot.remove(); return; }
    var claim = data.claims[quiz.position];
    if (quiz.active && claim && !selectingForQuiz && map.getState().issueId !== claimIssue(claim)) quiz.active = false;
    if (!aside.querySelector('.aic-evidence-controls')) {
      var reading = document.createElement('div'); reading.className = 'aic-reading-sources';
      reading.append.apply(reading, aside.childNodes);
      var controls = document.createElement('div'); controls.className = 'aic-evidence-controls'; controls.setAttribute('aria-label', '資料の読み方');
      controls.innerHTML = '<button type="button" data-aic-read>資料を読む</button><button type="button" data-aic-discover>x投稿で語られない話</button><button type="button" data-aic-quiz>一次資料クイズ · ' + data.claims.length + '問</button>';
      controls.querySelector('[data-aic-read]').onclick = returnToReading;
      controls.querySelector('[data-aic-discover]').onclick = function (event) {
        var opening = !discoveryActive;
        quiz.active = false; discoveryActive = true; mount();
        if (opening && event.isTrusted && typeof window.gtag === 'function') window.gtag('event', 'source_only_tab_open', { topic_id: data.theme_id });
      };
      controls.querySelector('[data-aic-quiz]').onclick = function () { quiz.active = true; showQuestion(quiz.position); };
      aside.append(controls, reading);
    }
    aside.querySelector('.aic-reading-sources').hidden = quiz.active || discoveryActive;
    aside.querySelector('[data-aic-read]').setAttribute('aria-pressed', String(!quiz.active && !discoveryActive));
    aside.querySelector('[data-aic-discover]').setAttribute('aria-pressed', String(discoveryActive));
    aside.querySelector('[data-aic-quiz]').setAttribute('aria-pressed', String(quiz.active));
    discoveryRoot.hidden = !discoveryActive; quizRoot.hidden = !quiz.active;
    aside.append(discoveryRoot, quizRoot);
    if (!panel.querySelector('.aic-evidence-jump')) {
      var evidenceJump = document.createElement('button');
      evidenceJump.type = 'button'; evidenceJump.className = 'aic-evidence-jump'; evidenceJump.textContent = 'この論点の制度・資料へ ↓';
      evidenceJump.onclick = function () { aside.scrollIntoView({ block: 'start', behavior: reduce() ? 'auto' : 'smooth' }); };
      var scopeNote = panel.querySelector('.aic-scope-note');
      if (scopeNote) scopeNote.after(evidenceJump);
    }
  }
  function renderQuiz() {
    var claim = data.claims[quiz.position];
    if (!claim) {
      var score = data.claims.filter(function (c) { return quiz.answers.get(c.id) === c.verdict; }).length;
      quizRoot.innerHTML = '<h3>資料クイズの結果</h3><p class="aic-quiz-score">' + score + ' / ' + data.claims.length + '問正解</p>'
        + '<p>回答済み ' + quiz.answers.size + '問。本文の資料と同じ内容で照合しています。</p>'
        + '<button type="button" data-aic-restart>最初の問題へ</button><button type="button" data-aic-finish>資料に戻る</button>';
      quizRoot.querySelector('[data-aic-restart]').onclick = function () { showQuestion(0); };
      quizRoot.querySelector('[data-aic-finish]').onclick = returnToReading;
      return;
    }
    var answer = quiz.answers.get(claim.id);
    quizRoot.innerHTML = '<div class="qh" tabindex="-1"><span>問 ' + (quiz.position + 1) + ' / ' + data.claims.length + '</span><span>資料照合 ' + esc(data.ocean.checked_on) + '</span></div>'
      + '<p class="aic-quiz-note">収集した投稿から選んだ主張です。掲載した投稿例そのものへの判定ではありません。</p>'
      + '<p class="qclaim">「' + esc(claim.claim) + '」</p><div class="aic-qopts">' + verdicts.map(function (v) {
        return '<button type="button" data-verdict="' + v + '" ' + (answer ? 'disabled' : '') + ' class="' + (answer ? (v === claim.verdict ? 'hit' : v === answer ? 'miss' : '') : '') + '">' + esc(verdictLabel(v)) + '</button>';
      }).join('') + '</div>'
      + '<div class="qans" ' + (answer ? '' : 'hidden') + '><p class="aic-verdict">' + esc(claim.verdict_label) + '</p><p>' + esc(claim.finding) + '</p>'
      + '<div class="aic-quiz-sources">' + claim.sources.map(function (s) { return '<p><a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">' + esc(s.name) + '</a></p>'; }).join('') + '</div>'
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

  // ---------- 表紙直下の検索入口（課題100） ----------
  // 検索疑問は一次資料の要点へ、最後のリンクは実データの論点選択へ接続する。
  var searchEntry = document.getElementById('aic-search-entry');
  if (searchEntry) {
    var searchTopics = {
      learning: {
        mapIssue: 'ai-copyright-learning-data',
        title: '📚 学習データ・無断利用', kicker: '詳しい論点 01 / 学習・データ',
        questions: [
          {id:'illegal', text:'無断学習は違法？', kind:'fact', label:'資料で確認できること', title:'「無断」だけで、違法かどうかは決まりません。', body:'著作権法30条の4の条件に当てはまるか、利用の目的や方法などを分けて確認します。文化庁は2024年3月公表の考え方で、その時点では関連する判例・裁判例の蓄積がないとして整理しています。', source:'https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html', sourceText:'文化庁の資料を確認 ↗'},
          {id:'article30', text:'30条の4とは？', kind:'fact', label:'制度の説明', title:'「享受を目的としない利用」などの権利制限規定です。', body:'情報解析など一定の目的では、必要な範囲で権利者の許諾なく利用できる場合があります。AI学習を一律に許可する規定ではなく、目的・方法・ただし書などの確認が必要です。', source:'https://laws.e-gov.go.jp/law/345AC0000000048', sourceText:'e-Govで条文を確認 ↗'},
          {id:'disclosure', text:'学習データは開示される？', kind:'case', label:'制度の最新状況', title:'内閣府が2026年8月に非拘束のコードを公表しました。', body:'コードを受け入れた事業者が対象で、学習データ等の概要開示や、条件を満たす照会への回答を求める枠組みです。受入れ事業者の届出は2026年10月26日開始予定です。このコード自体が、法律による全データの一律公開義務を定めるものではありません。', source:'https://www.cas.go.jp/jp/seisakukaigi/titeki2/ai_principle_code/index.html', sourceText:'内閣府のコードを確認 ↗'}
        ]
      },
      generation: {
        mapIssue: 'ai-copyright-generated-work-rights',
        title: '✨ AI生成物の権利・創作性', kicker: '詳しい論点 02 / 生成物・権利',
        questions: [
          {id:'has-rights', text:'AI生成物に著作権はある？', kind:'case', label:'個別判断が残る点', title:'AIを使った事実だけでは、一律に決まりません。', body:'人の創作意図や、表現への創作的な関わり方などが論点です。文化庁の資料も、生成AIと著作権に関する考え方を示しながら、具体的な作品ごとの判断が必要であることを前提としています。', source:'https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html', sourceText:'文化庁の考え方を確認 ↗'},
          {id:'commercial', text:'AI画像を商用利用できる？', kind:'case', label:'確認すること', title:'著作権だけでなく、複数の条件を確認します。', body:'既存作品との類似性・依拠性のほか、使ったサービスの利用規約や、商標・肖像など他の権利も確認対象です。サービスや生成物ごとの条件を確認してください。', source:'https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html', sourceText:'文化庁の資料を確認 ↗'}
        ]
      },
      creator: {
        mapIssue: 'ai-copyright-creator-rights',
        title: '🎨 クリエイター保護・権利', kicker: '詳しい論点 03 / 作者・権利',
        questions: [
          {id:'style', text:'作風が似ると著作権侵害？', kind:'case', label:'個別判断が残る点', title:'作風そのものと、作品の具体的な表現は分けて考えます。', body:'文化庁の考え方では、作風が共通するだけでは直ちに侵害とはならず、生成物に元作品の創作的表現が感じ取れるかなどを個別に検討します。', source:'https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/hoseido/r05_07/pdf/94021801_03.pdf', sourceText:'文化庁の資料を確認 ↗'},
          {id:'opt-out', text:'自分の作品を学習から守れる？', kind:'case', label:'確認できる対策と限界', title:'拒否の表示だけで、すべての収集を止められるとは限りません。', body:'利用規約への明示、技術的な設定、作品の転載経路などを分けて確認します。使える手段や限界は、サービスと収集方法によって異なります。', source:'https://www.bunka.go.jp/seisaku/chosakuken/pdf/94097701_01.pdf', sourceText:'文化庁のチェックリストを確認 ↗'}
        ]
      }
    };
    var searchTabs = Array.prototype.slice.call(searchEntry.querySelectorAll('[data-aic-search-topic]'));
    var searchQuestionList = searchEntry.querySelector('#aic-search-question-list');
    var searchAnswer = searchEntry.querySelector('#aic-search-answer');
    var activeSearchTopic = null;
    function showSearchQuestion(question) {
      searchQuestionList.querySelectorAll('[data-aic-search-question]').forEach(function (button) {
        button.setAttribute('aria-pressed', String(button.dataset.aicSearchQuestion === question.id));
      });
      searchAnswer.dataset.kind = question.kind;
      searchEntry.querySelector('#aic-search-answer-label').textContent = question.label;
      searchEntry.querySelector('#aic-search-answer-title').textContent = question.title;
      searchEntry.querySelector('#aic-search-answer-text').textContent = question.body;
      var sourceLink = searchEntry.querySelector('#aic-search-source');
      sourceLink.href = question.source;
      sourceLink.textContent = question.sourceText;
    }
    function selectSearchTopic(key, focus) {
      var topic = searchTopics[key];
      if (!topic) return;
      activeSearchTopic = key;
      searchTabs.forEach(function (tab, index) {
        var selected = tab.dataset.aicSearchTopic === key;
        tab.setAttribute('aria-selected', String(selected));
        tab.tabIndex = selected ? 0 : -1;
        if (selected) searchEntry.querySelector('#aic-search-panel').setAttribute('aria-labelledby', tab.id);
      });
      searchEntry.querySelector('#aic-search-kicker').textContent = topic.kicker;
      searchEntry.querySelector('#aic-search-issue-title').textContent = topic.title;
      searchQuestionList.replaceChildren.apply(searchQuestionList, topic.questions.map(function (question, index) {
        var button = document.createElement('button');
        button.type = 'button'; button.dataset.aicSearchQuestion = question.id;
        button.setAttribute('aria-pressed', String(index === 0)); button.textContent = question.text;
        button.addEventListener('click', function () { showSearchQuestion(question); });
        return button;
      }));
      showSearchQuestion(topic.questions[0]);
      if (focus) searchTabs.filter(function (tab) { return tab.dataset.aicSearchTopic === key; })[0].focus();
    }
    searchTabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () { selectSearchTopic(tab.dataset.aicSearchTopic, false); });
      tab.addEventListener('keydown', function (event) {
        var next = index;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % searchTabs.length;
        else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index + searchTabs.length - 1) % searchTabs.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = searchTabs.length - 1;
        else return;
        event.preventDefault();
        selectSearchTopic(searchTabs[next].dataset.aicSearchTopic, true);
      });
    });
    searchEntry.querySelectorAll('[data-aic-search-question]').forEach(function (button) {
      button.addEventListener('click', function () {
        var topic = searchTopics[activeSearchTopic || 'learning'];
        var question = topic.questions.find(function (item) { return item.id === button.dataset.aicSearchQuestion; });
        if (question) showSearchQuestion(question);
      });
    });
    searchEntry.querySelector('[data-aic-search-map]').addEventListener('click', function (event) {
      event.preventDefault();
      var topic = searchTopics[activeSearchTopic || 'learning'];
      if (map && topic) map.selectIssue(topic.mapIssue);
      var target = document.getElementById('planet-block');
      if (target) target.scrollIntoView({ block:'start', behavior:reduce() ? 'auto' : 'smooth' });
    });
    selectSearchTopic('learning', false);
  }

  // ---------- 授業印刷は節のみ、通常印刷は全本文。閉じた詳細も印刷中だけ展開する。 ----------
  document.querySelectorAll('#fallback img').forEach(function (img) { img.loading = 'eager'; });
  var fallbackHeading = document.querySelector('#fallback > h3');
  var fallbackLabel = fallbackHeading ? fallbackHeading.textContent : '';
  var printDetails = [];
  document.addEventListener('click', function (event) {
    if (event.target.closest('.classroom-print-btn')) document.body.classList.add('aic-print-classroom');
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
    document.body.classList.remove('aic-print-classroom');
  });
}());
