/* 辺野古ページの「読み始める前に」を、山なみと同じ6論点で切り替える。
   内容は一次資料で確認できること／未決定事項／収集したSNS反応を混ぜない。 */
(function () {
  'use strict';

  var root = document.getElementById('henoko-entry');
  var data = window.PLANET_DATA;
  if (!root || !data) return;

  var copy = {
    'henoko-student-accident-safety': {
      facts: ['文科省資料は、旅行計画・船の選定・引率体制・事前説明を検証', '転覆時、生徒が乗る船に引率教員が同行していなかったと記載', '国交省は、両船による運送が事業登録を受けていなかったと公表'],
      pending: ['事故原因の最終結論', '個人ごとの刑事責任や法的責任', '指摘された各要素が事故へ与えた影響の大きさ'],
      note: '安全管理上の指摘と、事故原因の最終的な認定を同じものとして扱いません。',
      voices: '船の選定、学校の引率、事故後の説明など、何が事故を防げなかったのかを問う意見です。',
      sourceLabel: '安全管理の年表と資料を見る'
    },
    'henoko-student-accident-base-politics': {
      facts: ['事故は辺野古移設工事への抗議活動を含む研修旅行中に発生', '文科省は安全管理と教育活動の両面について見解を公表', '事故の検証と基地問題への立場は、別々に確認できる事項'],
      pending: ['個々の関係者が持っていた政治的な意図', '事故と基地問題を結びつける評価の妥当性', '投稿から推測した「世論全体」の考え'],
      note: '事故の事実確認と、基地政策・政治活動への評価を一つの結論にまとめません。',
      voices: '事故を政治利用すべきでないという声と、基地問題の文脈を切り離せないという声が含まれます。',
      sourceLabel: '事故の経緯と公表資料を見る'
    },
    'henoko-student-accident-public-response': {
      facts: ['文科省・国交省・沖縄県などが事故後に見解や確認結果を公表', '国会では安全管理と教育活動の検証範囲が取り上げられた', 'このページは公表日と内容を年表で分けて記録'],
      pending: ['報道量が適切だったかという価値判断', '報道が社会の受け止めへ与えた影響', '今後の捜査・行政対応の最終結果'],
      note: '「報道が少ない」という投稿は収集しましたが、放送時間や記事総数を実測した結論ではありません。',
      voices: '報道の量や取り上げ方、行政・政党の説明、会見や遺族の記録への受け止めが語られました。',
      sourceLabel: '行政対応の年表を見る'
    },
    'henoko-student-accident-victim-dignity': {
      facts: ['高校生が亡くなった事故であり、学校・行政から公表資料が出ている', '事故後の会見や追悼の動きが記録されている', '公開資料と公開投稿だけを対象に整理'],
      pending: ['遺族や生徒一人ひとりの受け止め', '追悼のあり方についての唯一の正解', '公開されていない個人情報や心情'],
      note: '被害者名や未公開の心情を推測せず、公開された範囲を越えて扱いません。',
      voices: '犠牲者への配慮を先にしてほしい、慰霊の場と政治的抗議を分けたい、といった意見です。',
      sourceLabel: '事故後の経緯を確認する'
    },
    'henoko-student-accident-neutrality': {
      facts: ['文科省は当時把握した情報を基に、教育基本法との関係について判断を公表', '教育基本法は政治的教養を学ぶこと自体を否定していない', '判断が公表された事実と、その判断への賛否は別'],
      pending: ['すべての学習場面での政治的中立性', '国が教育内容へ関わる適切な範囲', '個々の授業や説明を公開資料だけで評価した結論'],
      note: '法令と公表見解を確認した上で、教育への評価は立場ごとに分けて読みます。',
      voices: '政治活動と学校教育の境界、国の介入、一貫した基準を求める意見が集まりました。',
      sourceLabel: '教育活動の資料を見る'
    },
    'henoko-student-accident-peace-education': {
      facts: ['文科省見解は安全管理だけでなく教育活動の内容も対象', '一方で、平和学習そのものを否定した文書ではない', '多様な見解を通じて生徒が判断する指導も求められている'],
      pending: ['全国の平和学習へ及んだ影響の大きさ', '現場で学習機会が実際に減ったかどうか', '安全確保と教育の自由を両立する具体策'],
      note: '「安全の見直し」と「平和教育の否定」を同じ意味として扱いません。',
      voices: '危険な活動を見直すべきという声と、学ぶ機会や教育の自由を守るべきという声があります。',
      sourceLabel: '教育活動の経緯を見る'
    }
  };

  var issueById = {};
  data.issues.forEach(function (issue) { issueById[issue.id] = issue; });
  var buttons = Array.prototype.slice.call(root.querySelectorAll('[data-entry-issue][role="tab"]'));
  var panel = root.querySelector('#henoko-entry-layers');
  var selection = root.querySelector('#henoko-entry-selection');
  var facts = root.querySelector('[data-entry-facts]');
  var pending = root.querySelector('[data-entry-pending]');
  var pendingNote = root.querySelector('[data-entry-pending-note]');
  var voices = root.querySelector('[data-entry-voices]');
  var count = root.querySelector('[data-entry-issue-count]');
  var share = root.querySelector('[data-entry-issue-share]');
  var sourceLink = root.querySelector('[data-entry-fact-link]');
  var mapLink = root.querySelector('[data-entry-map-link]');
  var bridgeLabel = root.querySelector('#henoko-entry-bridge-label');
  var mapButton = root.querySelector('#henoko-entry-open-map');
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var activeId = buttons.length ? buttons[0].dataset.entryIssue : null;

  function listInto(element, values) {
    element.replaceChildren();
    values.forEach(function (value) {
      var item = document.createElement('li');
      item.textContent = value;
      element.appendChild(item);
    });
  }

  function select(id, focus) {
    var issue = issueById[id];
    var words = copy[id];
    if (!issue || !words) return;
    activeId = id;
    buttons.forEach(function (button) {
      var selected = button.dataset.entryIssue === id;
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    panel.setAttribute('aria-labelledby', 'henoko-entry-tab-' + id.replace('henoko-student-accident-', ''));
    selection.textContent = issue.label;
    listInto(facts, words.facts);
    listInto(pending, words.pending);
    pendingNote.textContent = words.note;
    voices.textContent = words.voices;
    count.textContent = issue.count.toLocaleString('ja-JP');
    share.textContent = '全意見の' + issue.share_pct.toFixed(1) + '%';
    sourceLink.childNodes[0].nodeValue = words.sourceLabel;
    bridgeLabel.textContent = '「' + issue.label + '」の山を選択して開きます';
    mapButton.dataset.entryIssue = id;
    panel.classList.remove('is-changing');
    void panel.offsetWidth;
    panel.classList.add('is-changing');
    if (focus) buttons.find(function (button) { return button.dataset.entryIssue === id; }).focus();
  }

  function openMountain(event) {
    if (event) event.preventDefault();
    var map = window.HenokoConnectedMap;
    if (map) map.selectIssue(activeId);
    var mountain = document.getElementById('planet-block');
    if (mountain) mountain.scrollIntoView({ block: 'start', behavior: reducedMotion ? 'auto' : 'smooth' });
  }

  buttons.forEach(function (button, index) {
    button.addEventListener('click', function () { select(button.dataset.entryIssue, false); });
    button.addEventListener('keydown', function (event) {
      var next = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? (index + 1) % buttons.length
        : event.key === 'ArrowLeft' || event.key === 'ArrowUp' ? (index + buttons.length - 1) % buttons.length
        : event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : null;
      if (next === null) return;
      event.preventDefault();
      select(buttons[next].dataset.entryIssue, true);
    });
  });
  mapButton.addEventListener('click', openMountain);
  mapLink.addEventListener('click', openMountain);
  select(activeId, false);
}());
