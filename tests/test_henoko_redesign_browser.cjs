/* 辺野古高校生死亡事故・新デザインの公開候補の表示・操作検査（学校でのあだ名禁止 tests/test_nickname_redesign_browser.cjs と同じ項目）。
   ローカルで配信した候補だけを対象にする。
   NODE_PATH=<main>/node_modules HENOKO_REDESIGN_URL=http://127.0.0.1:8798/henoko-student-accident-reaction-map.html \
   HENOKO_EVIDENCE_DIR=quality/prototypes/henoko-student-accident-release/evidence node tests/test_henoko_redesign_browser.cjs
   投票は押さない（本番Supabaseへ送らないため。localhost では投票設定自体が無効になる）。
   論点名は読書面の論点タブ（.fr-tab）、山は対話式の山なみ（#section .hill）。前の収集回との比較（潮目のカード）・作り方・
   詳細データ・投稿例は折りたたみの中にあるので、開いてから確かめる。
   x.com・platform.twitter.com・twimg.com への通信はすべて遮断する（X埋め込みは失敗時の表示を確かめる）。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

const url = process.env.HENOKO_REDESIGN_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ローカル候補のURLが必要です（HENOKO_REDESIGN_URL）');
}
const evidence = process.env.HENOKO_EVIDENCE_DIR;
const shot = (page, name, full = false) => evidence ? page.screenshot({ path: path.join(evidence, name), fullPage: full }) : null;
const ISSUES = 6;
const X_HOSTS = /(^|\.)(x\.com|twitter\.com|twimg\.com)$/;
const R = '#henoko-student-accident-reading';
const BG_ROWS = 7;
const TIDE = '#henoko-tide-widget';
const P = 'henoko-student-accident-';
// 配慮：山なみ・投票・本文に、船・波の絵文字や避けた語が見えていない
const AVOID = ['同志社', '平和丸', '不屈', '女子高', '女子生徒', '遺族', '🛟', '⚓', '🚢', '🌊'];

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
      // 件数の少ない山を広げた注記（#floor-note）。立場ごとにどの論点かを記録する（「論点を切り分ける」が9割なので、他の立場では細い山が多い）
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
      // 配慮：見えている文字（山なみが描いた論点ボタン・選択パネル・投票ボタンを含む）に、避けた語・船や波の絵文字が無い
      const shown = await page.evaluate(() => document.body.innerText);
      for (const word of AVOID) assert.ok(!shown.includes(word), `${name}: 見えている文字に「${word}」があります`);
      // 冒頭の短答「経緯を年表で見る」で、背景の年表の行が開く
      await page.locator('#henoko-open a[href="#bg-timeline"]').click();
      await page.waitForTimeout(400);
      assert.equal(await page.locator('#bg-timeline').evaluate(d => d.open), true, `${name}: 「経緯を年表で見る」で年表が開きません`);
      await page.locator('#bg-timeline').scrollIntoViewIfNeeded();
      await shot(page, `timeline-open-${name}.png`);
      await page.locator('#bg-timeline > summary').click();
      await page.evaluate(() => history.replaceState(null, '', location.pathname));

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
      // 1つ目の論点（安全管理と、事故の責任）の理由区分は5つ。上位4つが一覧に出て、残り1つは「ほかの理由を読む」の中
      assert.equal(await panel.locator('.fr-reasons > .fr-reason-list li.fr-reason').count(), 4, `${name}: 理由一覧が4件ではありません`);
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
      const rows = page.locator('#henoko-student-accident-background details.fb-row');
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
      summary.push(`${name}: はみ出し0・避けた語と船や波の絵文字が見えない・「経緯を年表で見る」で年表が開く・立場モード切替・論点タブ${ISSUES}つで scrollY 不変・山で読書面へ（見出しにフォーカス）・理由の切替と「別の理由」・読書面の折りたたみ全開・背景${n}行の開閉・比較を開いて描画と切替・「回ごとの比較へ」・作り方と詳細データ・エラー0`);
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
      await fresh('#fb-' + P + 'base-politics');
      await page.waitForFunction(id => ['#issue-' + id, '#' + id].includes(location.hash), P + 'base-politics');
      assert.equal(await selected(), P + 'base-politics');
      await fresh('#henoko-student-accident-reading-' + P + 'neutrality');
      await page.waitForFunction(id => ['#issue-' + id, '#' + id].includes(location.hash), P + 'neutrality');
      assert.equal(await selected(), P + 'neutrality');
      // 論点の素のID（旧ページの山なみの着地が使っていた）で来たときも、その論点の欄へ
      await fresh('#' + P + 'peace-education');
      await page.waitForFunction(id => ['#issue-' + id, '#' + id].includes(location.hash), P + 'peace-education');
      assert.equal(await selected(), P + 'peace-education');
      await fresh('#henoko-entry-tab-victim-dignity');
      await page.waitForFunction(id => ['#issue-' + id, '#' + id].includes(location.hash), P + 'victim-dignity');
      assert.equal(await selected(), P + 'victim-dignity');
      await fresh('#bukatsu-background');
      await page.waitForFunction(() => location.hash === '#bg-timeline');
      assert.equal(await page.locator('#bg-timeline').evaluate(d => d.open), true);
      await fresh('#bukatsu-check');
      await page.waitForFunction(id => ['#issue-' + id, '#' + id].includes(location.hash), P + 'safety');
      assert.equal(await selected(), P + 'safety');
      await fresh('#henoko-entry-pending');
      await page.waitForFunction(() => location.hash === '#bg-official');
      assert.equal(await page.locator('#bg-official').evaluate(d => d.open), true);
      await fresh('#henoko-entry');
      await page.waitForFunction(() => location.hash === '#henoko-open');
      await fresh('#henoko-entry-open-map');
      await page.waitForFunction(() => location.hash === '#planet-block');
      await fresh('#stance-glance');
      await page.waitForFunction(() => location.hash === '#hop-count');
      await fresh('#classroom-title');
      await page.waitForFunction(() => location.hash === '#bg-classroom');
      assert.equal(await page.locator('#bg-classroom').evaluate(d => d.open), true);
      await fresh('#henoko-faq');
      assert.equal(await page.locator('#henoko-faq').evaluate(d => d.open), true, '#henoko-faq でよくある質問が開きません');
      await fresh('#henoko-faq-title');
      await page.waitForFunction(() => location.hash === '#henoko-faq');
      assert.equal(await page.locator('#henoko-faq').evaluate(d => d.open), true);
      await fresh('#correction-20260906');
      await page.waitForFunction(() => location.hash === '#article-trust-title');
      assert.equal(await page.locator('#article-trust-title').isVisible(), true, '#correction-20260906 で作り方が開きません');
      await fresh('#issue-' + P + 'public-response');
      assert.equal(await selected(), P + 'public-response');
      const reasonId = await page.evaluate(() => document.querySelector('#issue-henoko-student-accident-safety .fr-reason-detail:last-of-type').id);
      await fresh('#' + reasonId);
      assert.equal(await selected(), P + 'safety');
      assert.equal(await page.locator('#' + reasonId).isVisible(), true, '#fr-r-… で理由が開きません');
      // 折りたたみの中の場所（潮目のカード・詳細データ）は、外側を開いて見せる
      await fresh(TIDE);
      assert.equal(await page.locator(TIDE).isVisible(), true, '潮目のカードへのリンクで折りたたみが開きません');
      await fresh('#detail-data');
      assert.equal(await page.locator('#detail-data').isVisible(), true, '#detail-data で詳細データが開きません');
      for (const kept of ['vote-section', 'detail-data', 'related-topics', 'caution', 'research-conditions', 'planet-block']) {
        assert.equal(await page.locator('#' + kept).count(), 1, `#${kept} がありません`);
      }
      summary.push('旧アンカー: #fb-…・#henoko-student-accident-reading-…・論点の素のID・#henoko-entry-tab-…→論点、#bukatsu-background→年表の行を開く、#bukatsu-check→安全管理の欄、#henoko-entry-pending→公表の行を開く、#henoko-entry→冒頭、#henoko-entry-open-map→山なみ、#stance-glance→冒頭の件数、#classroom-title→授業の行、#henoko-faq・#henoko-faq-title→よくある質問の行が開く、#correction-20260906→作り方、#issue-…で論点選択、#fr-r-…で理由が開く、潮目のカード・#detail-data は折りたたみを開いて表示、#vote-section など6件はそのまま');
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
      await page.locator('#henoko-faq > summary').focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#henoko-faq').evaluate(d => d.open), true, 'Enter で背景の行が開きません');
      const voteBtn = page.locator('#vote-issue-btns button').first();
      await voteBtn.focus();
      assert.equal(await page.evaluate(() => document.activeElement.classList.contains('vote-issue-btn')), true);
      assert.equal(await page.locator('#vote-issue-btns button').count(), 6, '投票の論点ボタンが6つではありません');
      assert.deepEqual(errors, []);
      summary.push('キーボード: Tab で論点名を移動、Enter で選択（位置・フォーカス不変）、Enter で背景を開く、投票ボタン6つへフォーカス可');
      await context.close();
    }

    // 計測：ページ全体の高さ（初期表示）、表示中の文字数（閉じた details の中と非表示を除く）、論点の欄ごとの高さと文字数
    for (const [width, name] of [[375, 'mobile'], [1280, 'desktop']]) {
      const { context, page } = await open(browser, { viewport: { width, height: 900 } });
      await page.goto(url, { waitUntil: 'networkidle' });
      const visibleChars = sel => page.evaluate(s => {
        const root = document.querySelector(s); let n = 0;
        const walk = node => {
          if (node.nodeType === 3) { n += node.textContent.replace(/\s+/g, '').length; return; }
          if (node.nodeType !== 1) return;
          if (['SCRIPT', 'STYLE', 'TEMPLATE', 'svg'].includes(node.tagName)) return;
          if (node.checkVisibility && !node.checkVisibility()) return;
          if (node.tagName === 'DETAILS' && !node.open) { const s2 = node.querySelector(':scope > summary'); if (s2) walk(s2); return; }
          node.childNodes.forEach(walk);
        };
        walk(root); return n;
      }, sel);
      const total = await page.evaluate(() => document.documentElement.scrollHeight);
      const parts = await page.evaluate(() => Object.fromEntries([['冒頭', '#henoko-open'], ['山なみ', '.fr-map'], ['背景', '#henoko-student-accident-background'], ['比較の要約', '#cap-trend'], ['投票', '#vote-section']]
        .map(([k, s]) => [k, Math.round(document.querySelector(s).getBoundingClientRect().height)])));
      const mainChars = await visibleChars('main');
      const panels = [];
      for (const tab of await page.locator(`${R} .fr-tab`).all()) {
        await tab.click();
        const id = await tab.getAttribute('data-issue-id');
        const h = await page.locator('[data-issue-panel][data-selected]').evaluate(e => Math.round(e.getBoundingClientRect().height));
        panels.push(`${(await tab.innerText()).split('\n')[0]} ${h}px/${await visibleChars('#issue-' + id)}字`);
      }
      summary.push(`計測 ${width}px: ページ全体 ${total}px・main の表示文字 ${mainChars}字・${Object.entries(parts).map(([k, v]) => `${k} ${v}px`).join('・')}／論点の欄 ${panels.join('、')}`);
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
      for (const word of ['辺野古', '何があった？', '原因は分かった？', '何が争点？', 'よくある質問', '世論調査', 'このページの作り方', '詳細データ', '前の回からどう動いたか', '論点の一覧', '経緯の年表']) {
        assert.ok(text.includes(word), `JSなしで「${word}」が読めません`);
      }
      await page.locator('#henoko-faq > summary').click();
      assert.equal(await page.locator('#henoko-faq').evaluate(d => d.open), true, 'JSなしで背景の行が開きません');
      await shot(page, 'nojs-desktop.png');
      summary.push(`JSなし: ${ISSUES}論点すべて表示、図が使えないときの論点一覧・本文・比較の要約・作り方・詳細データ・背景の開閉とも可`);
      await context.close();
    }
  } finally {
    await browser.close();
  }
  console.log(summary.join('\n'));
  console.log('OK henoko redesign browser checks');
})().catch(e => { console.error(e); process.exit(1); });
