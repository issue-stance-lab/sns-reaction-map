/* 学校でのあだ名禁止・新デザインの公開候補の表示・操作検査（高齢者免許返納 tests/test_elderly_redesign_browser.cjs と同じ項目）。
   ローカルで配信した候補だけを対象にする。
   NODE_PATH=<main>/node_modules NICKNAME_REDESIGN_URL=http://127.0.0.1:8797/school-nickname-ban-reaction-map.html \
   NICKNAME_EVIDENCE_DIR=quality/prototypes/school-nickname-ban-release/evidence node tests/test_nickname_redesign_browser.cjs
   投票は押さない（本番Supabaseへ送らないため。localhost では投票設定自体が無効になる）。
   論点名は読書面の論点タブ（.fr-tab）、山は対話式の山なみ（#section .hill）。前の収集回との比較（潮目のカード）・作り方・
   詳細データ・投稿例は折りたたみの中にあるので、開いてから確かめる。
   x.com・platform.twitter.com・twimg.com への通信はすべて遮断する（X埋め込みは失敗時の表示を確かめる）。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

const url = process.env.NICKNAME_REDESIGN_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ローカル候補のURLが必要です（NICKNAME_REDESIGN_URL）');
}
const evidence = process.env.NICKNAME_EVIDENCE_DIR;
const shot = (page, name, full = false) => evidence ? page.screenshot({ path: path.join(evidence, name), fullPage: full }) : null;
const ISSUES = 6;
const X_HOSTS = /(^|\.)(x\.com|twitter\.com|twimg\.com)$/;
const R = '#school-nickname-ban-reading';
const BG_ROWS = 9;
const TIDE = '#school-nickname-ban-tide-widget';

async function open(browser, options = {}) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, ...options });
  await context.route(r => X_HOSTS.test(new URL(r).hostname), r => r.abort());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => {
    // 遮断した X への通信の失敗はブラウザが console に出す。ページ自身のエラーだけを数える
    if (m.type() === 'error' && !/ERR_FAILED|ERR_BLOCKED|net::/.test(m.text())) errors.push('console: ' + m.text());
  });
  return { context, page, errors };
}
const wideOf = page => page.evaluate(() => document.documentElement.scrollWidth - innerWidth);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const summary = [];
  try {
    for (const [width, name] of [[1280, 'desktop'], [375, 'mobile']]) {
      const { context, page, errors } = await open(browser, { viewport: { width, height: 900 } });
      await page.goto(url, { waitUntil: 'networkidle' });
      assert.ok(await wideOf(page) <= 0, `${name}: 横にはみ出しています`);
      await shot(page, `page-${name}.png`, true);

      // 山なみ：立場モードを切り替えると、100マスと件数が変わる
      await page.locator('#planet-block').scrollIntoViewIfNeeded();
      await shot(page, `planet-${name}.png`);
      const modeBtn = page.locator('#modes button[data-m]').nth(2);
      const modeId = await modeBtn.getAttribute('data-m');
      await modeBtn.click();
      await page.waitForTimeout(700);
      assert.equal(await page.locator(`#modes button[data-m="${modeId}"]`).getAttribute('aria-pressed'), 'true');
      await page.locator('#modes').scrollIntoViewIfNeeded();
      await shot(page, `planet-mode-${name}.png`);
      await page.locator('#modes button[data-m="all"]').click();
      await page.waitForTimeout(600);
      // 意見100件と少ないので、細すぎて押せない山を広げた注記（#floor-note）が出る。立場ごとにどの論点かを記録する
      if (name === 'desktop') {
        const floors = [];
        for (const m of await page.locator('#modes button[data-m]').all()) {
          await m.click();
          await page.waitForTimeout(650);
          floors.push(`${await m.getAttribute('data-m')}：${(await page.locator('#floor-note').textContent()).trim() || '（注記なし）'}`);
        }
        await page.locator('#modes button[data-m="all"]').click();
        await page.waitForTimeout(600);
        summary.push('細い山の注記: ' + floors.join(' ／ '));
      }
      // 冒頭の「つらい場合」に24時間こどもSOSダイヤルの番号が見える
      assert.equal(await page.locator('#school-nickname-safety .nop-phone a').isVisible(), true, `${name}: 冒頭に相談の電話番号が見えません`);

      // 論点タブを選んでも、ページの位置は動かない
      const tabs = page.locator(`${R} .fr-tab`);
      assert.equal(await tabs.count(), ISSUES);
      for (let i = 0; i < ISSUES; i++) {
        const tab = tabs.nth(i);
        await tab.scrollIntoViewIfNeeded();
        const before = await page.evaluate(() => scrollY);
        const id = await tab.getAttribute('data-issue-id');
        await tab.click();
        assert.equal(await page.evaluate(() => scrollY), before, `${name}: 論点 ${id} の選択で scrollY が動きました`);
        assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), id);
        assert.equal(await page.locator('[data-issue-panel]:not([data-selected])').first().isVisible(), false);
        assert.ok(await wideOf(page) <= 0, `${name}: 論点 ${id} の表示で横にはみ出しています`);
      }
      // 山を押すと、その論点の読書面へ移る
      const hill = page.locator('#section .hill').nth(2);
      await hill.scrollIntoViewIfNeeded();
      const hillId = await page.evaluate(() => window.PLANET_DATA.issues[2].id);
      await hill.click({ force: true });
      await page.waitForFunction(id => location.hash === '#issue-' + id, hillId);
      await page.waitForTimeout(1500);  // なめらかなスクロールが止まるまで待つ
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), hillId);
      const top = await page.locator('[data-issue-panel][data-selected]').evaluate(e => e.getBoundingClientRect().top);
      assert.ok(top >= 0 && top < 300, `${name}: 山を押しても読書面が画面に来ません（${top}px）`);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'fr-h-' + hillId, `${name}: 見出しにフォーカスがありません`);
      await shot(page, `hill-to-reading-${name}.png`);
      await tabs.first().click();
      await page.locator(`${R} .fr-tabs`).scrollIntoViewIfNeeded();
      await shot(page, `reading-1-${name}.png`);
      await page.evaluate(() => scrollBy(0, innerHeight - 60));
      await shot(page, `reading-2-${name}.png`);
      // 理由一覧の行を押すと、その理由の説明だけが出る。「この論点の別の理由」で次へ
      const panel = page.locator('[data-issue-panel][data-selected]');
      const rowsR = panel.locator('.fr-reasons li.fr-reason');
      // 1つ目の論点（一律に禁止して、効果はあるのか）の理由区分は3つ。上位4つまで一覧に出るので、3つとも一覧にある
      assert.equal(await panel.locator('.fr-reasons > .fr-reason-list li.fr-reason').count(), 3, `${name}: 理由一覧が3件ではありません`);
      await rowsR.nth(1).locator('a').click();
      const shownR = await panel.locator('.fr-reason-detail').evaluateAll(as => as.filter(a => a.offsetHeight > 0).map(a => a.dataset.reason));
      assert.deepEqual(shownR, [await rowsR.nth(1).getAttribute('data-reason')], `${name}: 選んだ理由の説明だけが出ていません`);
      await panel.locator('.fr-reason-detail[data-on]').scrollIntoViewIfNeeded();
      await shot(page, `reason-open-${name}.png`);
      await panel.locator('.fr-reason-detail[data-on] .fr-next a').click();
      const shownN = await panel.locator('.fr-reason-detail').evaluateAll(as => as.filter(a => a.offsetHeight > 0).map(a => a.dataset.reason));
      assert.deepEqual(shownN, [await rowsR.nth(2).getAttribute('data-reason')], `${name}: 「この論点の別の理由」で次の理由へ移りません`);
      // 読書面の折りたたみをすべて開いても横にはみ出さない
      for (const d of await panel.locator('details').all()) await d.evaluate(e => { e.open = true; });
      assert.ok(await wideOf(page) <= 0, `${name}: 読書面の折りたたみを開くと横にはみ出します`);
      for (const d of await panel.locator('details').all()) await d.evaluate(e => { e.open = false; });

      // 背景の開閉行
      const rows = page.locator('#school-nickname-ban-background details.fb-row');
      const n = await rows.count();
      assert.equal(n, BG_ROWS, `背景の行が${BG_ROWS}行ではありません（${n}）`);
      for (let i = 0; i < n; i++) {
        await rows.nth(i).locator('summary').click();
        assert.equal(await rows.nth(i).evaluate(d => d.open), true);
        assert.ok(await wideOf(page) <= 0, `${name}: 背景の行 ${i} を開くと横にはみ出します`);
      }
      await rows.first().scrollIntoViewIfNeeded();
      await shot(page, `background-open-${name}.png`);
      for (let i = 0; i < n; i++) await rows.nth(i).locator('summary').click();

      // 前回の収集との比較（引き継いだ潮目のカード）：折りたたみを開くとグラフが描かれ、「論点の変化」に切り替わる
      await page.locator('#cap-trend-more > summary').scrollIntoViewIfNeeded();
      await page.locator('#cap-trend-more > summary').click();
      await page.waitForTimeout(1200);
      const lines = await page.locator(TIDE + ' [data-tide-series] line').count();
      const mobileRows = await page.locator(TIDE + ' [data-tide-mobile] .tide-mobile-row').count();
      assert.ok(lines >= 2 && mobileRows >= 2, `${name}: 開いた比較のグラフが描かれていません（${lines}/${mobileRows}）`);
      const issueMode = page.locator(TIDE + ' [data-tide-mode="issue"]');
      await issueMode.click();
      assert.equal(await issueMode.getAttribute('aria-pressed'), 'true');
      assert.ok(await wideOf(page) <= 0, `${name}: 比較の表示で横にはみ出します`);
      await page.locator('#cap-trend').scrollIntoViewIfNeeded();
      await shot(page, `trend-open-${name}.png`);
      await page.locator(TIDE + ' [data-tide-mode="stance"]').click();
      await page.locator('#cap-trend-more > summary').click();
      // 読書面の「収集回ごとの比較へ」：折りたたみを開き、「論点の変化」に切り替えて移る
      await tabs.first().click();
      await panel.locator('.fr-glance-link').click();
      await page.waitForTimeout(500);
      assert.equal(await page.locator('#cap-trend-more').evaluate(d => d.open), true, `${name}: 「収集回ごとの比較へ」で折りたたみが開きません`);
      assert.equal(await issueMode.getAttribute('aria-pressed'), 'true', `${name}: 「収集回ごとの比較へ」で論点の変化になりません`);
      // 作り方と詳細データの折りたたみも、開いて横にはみ出さない
      await page.locator('#cap-method > summary').click();
      assert.equal(await page.locator('#cap-method').evaluate(d => d.open), true);
      for (const d of await page.locator('#detail-data details').all()) await d.evaluate(e => { e.open = true; });
      assert.ok(await wideOf(page) <= 0, `${name}: 詳細データを開くと横にはみ出します`);
      assert.deepEqual(errors, [], `${name}: コンソールエラー`);
      summary.push(`${name}: はみ出し0・冒頭に相談の電話番号・立場モード切替・論点タブ${ISSUES}つで scrollY 不変・山で読書面へ（見出しにフォーカス）・理由の切替と「別の理由」・読書面の折りたたみ全開・背景${n}行の開閉・比較を開いて描画と切替・「回ごとの比較へ」・作り方と調査上の注意・エラー0`);
      await context.close();
    }

    // 戻る：論点を何度切り替えても履歴は増えず、「戻る」で前のページへ戻る
    {
      const { context, page } = await open(browser);
      const previous = new URL('index.html', url).href;
      await page.goto(previous, { waitUntil: 'domcontentloaded' });
      await page.goto(url, { waitUntil: 'networkidle' });
      const length = await page.evaluate(() => history.length);
      for (const tab of await page.locator(`${R} .fr-tab`).all()) await tab.click();
      assert.equal(await page.evaluate(() => history.length), length, '論点の切替で履歴が増えました');
      assert.match(page.url(), /#issue-/);
      await page.goBack({ waitUntil: 'domcontentloaded' });
      assert.equal(page.url(), previous, '戻るで前のページへ戻りません');
      summary.push(`戻る: 論点${ISSUES}回の切替で history.length 不変、戻るで前のページ（index.html）へ`);
      await context.close();
    }

    // 旧アンカーと論点・理由への直接リンク
    {
      const { context, page } = await open(browser);
      const selected = () => page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel');
      const fresh = async hash => { await page.goto('about:blank'); await page.goto(url + hash, { waitUntil: 'networkidle' }); };
      await fresh('#fb-school-nickname-ban-naming-culture');
      await page.waitForFunction(() => ['#issue-school-nickname-ban-naming-culture', '#school-nickname-ban-naming-culture'].includes(location.hash));
      assert.equal(await selected(), 'school-nickname-ban-naming-culture');
      await fresh('#school-nickname-ban-reading-school-nickname-ban-school-practice');
      await page.waitForFunction(() => ['#issue-school-nickname-ban-school-practice', '#school-nickname-ban-school-practice'].includes(location.hash));
      assert.equal(await selected(), 'school-nickname-ban-school-practice');
      // 論点の素のID（旧ページの検索入口が節の目印に使っていた）で来たときも、その論点の欄へ
      await fresh('#school-nickname-ban-psychological-safety');
      await page.waitForFunction(() => ['#issue-school-nickname-ban-psychological-safety', '#school-nickname-ban-psychological-safety'].includes(location.hash));
      assert.equal(await selected(), 'school-nickname-ban-psychological-safety');
      await fresh('#bukatsu-background');
      await page.waitForFunction(() => location.hash === '#bg-why');
      assert.equal(await page.locator('#bg-why').evaluate(d => d.open), true);
      await fresh('#bukatsu-check');
      await page.waitForFunction(() => location.hash === '#bg-school');
      assert.equal(await page.locator('#bg-school').evaluate(d => d.open), true);
      await fresh('#school-nickname-guide-panel-harm');
      await page.waitForFunction(() => location.hash === '#bg-voices');
      assert.equal(await page.locator('#bg-voices').evaluate(d => d.open), true);
      await fresh('#school-nickname-guide');
      await page.waitForFunction(() => location.hash === '#school-nickname-open');
      await fresh('#school-nickname-guide-tab-national-rule');
      await page.waitForFunction(() => location.hash === '#nop-q-rule');
      await fresh('#stance-glance');
      await page.waitForFunction(() => location.hash === '#school-nickname-opening-count');
      await fresh('#classroom-title');
      await page.waitForFunction(() => location.hash === '#bg-classroom');
      assert.equal(await page.locator('#bg-classroom').evaluate(d => d.open), true);
      await fresh('#school-nickname-faq');
      assert.equal(await page.locator('#school-nickname-faq').evaluate(d => d.open), true, '#school-nickname-faq でよくある質問が開きません');
      await fresh('#correction-20260906');
      await page.waitForFunction(() => location.hash === '#article-trust-title');
      assert.equal(await page.locator('#article-trust-title').isVisible(), true, '#correction-20260906 で作り方が開きません');
      await fresh('#issue-school-nickname-ban-individual-choice');
      assert.equal(await selected(), 'school-nickname-ban-individual-choice');
      await fresh('#fr-r-school-nickname-ban-uniform-rule-group-6');
      assert.equal(await selected(), 'school-nickname-ban-uniform-rule');
      assert.equal(await page.locator('#fr-r-school-nickname-ban-uniform-rule-group-6').isVisible(), true, '#fr-r-… で理由が開きません');
      // 折りたたみの中の場所（潮目のカード・詳細データ）は、外側を開いて見せる
      await fresh(TIDE);
      assert.equal(await page.locator(TIDE).isVisible(), true, '潮目のカードへのリンクで折りたたみが開きません');
      await fresh('#detail-data');
      assert.equal(await page.locator('#detail-data').isVisible(), true, '#detail-data で詳細データが開きません');
      for (const kept of ['vote-section', 'detail-data', 'related-topics', 'caution', 'research-conditions', 'planet-block']) {
        assert.equal(await page.locator('#' + kept).count(), 1, `#${kept} がありません`);
      }
      summary.push('旧アンカー: #fb-…・#school-nickname-ban-reading-…・論点の素のID→論点、#bukatsu-background→「なぜ議論になるのか」の行を開く、#bukatsu-check→学校のルールの行を開く、#school-nickname-guide-panel-harm→期待と懸念の行を開く、#school-nickname-guide→冒頭、#school-nickname-guide-tab-national-rule→冒頭の「本当に禁止なの？」、#stance-glance→冒頭の件数、#classroom-title→授業の行、#school-nickname-faq→よくある質問の行が開く、#correction-20260906→作り方、#issue-…で論点選択、#fr-r-…で理由が開く、潮目のカード・#detail-data は折りたたみを開いて表示、#vote-section など6件はそのまま');
      await context.close();
    }

    // キーボード：論点名を Tab で選び Enter、背景の行を Enter で開く
    {
      const { context, page, errors } = await open(browser);
      await page.goto(url, { waitUntil: 'networkidle' });
      const target = page.locator(`${R} .fr-tab`).nth(2);
      const id = await target.getAttribute('data-issue-id');
      await page.locator(`${R} .fr-tab`).nth(1).focus();
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.issueId), id, 'Tab で次の論点名へ移れません');
      const before = await page.evaluate(() => scrollY);
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), id);
      assert.equal(await page.evaluate(() => scrollY), before, 'Enter で位置が動きました');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.issueId), id, 'フォーカスが論点名から外れました');
      await page.locator('#school-nickname-faq > summary').focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#school-nickname-faq').evaluate(d => d.open), true, 'Enter で背景の行が開きません');
      const voteBtn = page.locator('#vote-issue-btns button').first();
      await voteBtn.focus();
      assert.equal(await page.evaluate(() => document.activeElement.classList.contains('vote-issue-btn')), true);
      assert.equal(await page.locator('#vote-issue-btns button').count(), 6, '投票の論点ボタンが6つではありません');
      assert.deepEqual(errors, []);
      summary.push('キーボード: Tab で論点名を移動、Enter で選択（位置・フォーカス不変）、Enter で背景を開く、投票ボタン6つへフォーカス可');
      await context.close();
    }

    // X埋め込みの失敗時：読み込みを遮断しても、案内と元投稿へのリンクが残る
    {
      const { context, page, errors } = await open(browser);
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.locator('[data-issue-panel][data-selected] details.fr-posts > summary').click();
      const posts = page.locator('[data-issue-panel][data-selected] details.original-posts');
      await posts.locator('summary').click();
      const status = posts.locator('.x-embed-status').first();
      await page.waitForFunction(el => /表示できません/.test(el.textContent), await status.elementHandle(), { timeout: 20000 });
      const links = await posts.locator('a.x-original-link').evaluateAll(as => as.map(a => a.href));
      assert.ok(links.length >= 1 && links.every(h => /^https:\/\/x\.com\/[^/]+\/status\/\d+$/.test(h)), '元投稿へのリンクがありません');
      await posts.scrollIntoViewIfNeeded();
      await shot(page, 'x-embed-fallback.png');
      assert.deepEqual(errors.filter(e => e.startsWith('pageerror')), [], 'X埋め込みの失敗でページのエラー');
      summary.push(`X埋め込み失敗（x.com・platform.twitter.com・twimg.com を遮断）: 「表示できません」の案内と元投稿リンク${links.length}件が残る、ページエラー0`);
      await context.close();
    }

    // JavaScriptなし：6論点の読書面と背景がすべて読める
    {
      const { context, page } = await open(browser, { javaScriptEnabled: false });
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      const visible = await page.locator('[data-issue-panel]').evaluateAll(ps => ps.filter(p => p.offsetHeight > 0).length);
      assert.equal(visible, ISSUES, `JSなしで${ISSUES}論点が表示されません`);
      await page.locator('#cap-trend-more > summary').click();
      await page.locator('#cap-method > summary').click();
      const text = await page.locator('main').innerText();
      for (const word of ['あだ名', '本当に禁止なの？', 'なぜ始まったの？', '0120-0-78310', 'よくある質問', '世論調査', 'このページの作り方', '調査上の注意', '禁止への賛否の割合も動いたのか', '論点の一覧', '少数']) {
        assert.ok(text.includes(word), `JSなしで「${word}」が読めません`);
      }
      await page.locator('#school-nickname-faq > summary').click();
      assert.equal(await page.locator('#school-nickname-faq').evaluate(d => d.open), true, 'JSなしで背景の行が開きません');
      await shot(page, 'nojs-desktop.png');
      summary.push(`JSなし: ${ISSUES}論点すべて表示、図が使えないときの論点一覧・本文・比較の要約・作り方・調査上の注意・背景の開閉とも可`);
      await context.close();
    }
  } finally {
    await browser.close();
  }
  console.log(summary.join('\n'));
  console.log('OK nickname redesign browser checks');
})().catch(e => { console.error(e); process.exit(1); });
