/* 生成AIと著作権・新デザインの公開候補の表示・操作検査（副首都 tests/test_fukushuto_redesign_browser.cjs と同じ項目。冒頭の時制の切替は無い）。
   ローカルで配信した候補だけを対象にする。
   NODE_PATH=<main>/node_modules AI_COPYRIGHT_REDESIGN_URL=http://127.0.0.1:8767/ai-copyright-reaction-map.html \
   AI_COPYRIGHT_EVIDENCE_DIR=quality/prototypes/ai-copyright-release/evidence node tests/test_ai_copyright_redesign_browser.cjs
   投票は押さない（本番Supabaseへ送らないため。localhost では投票設定自体が無効になる）。
   2026-10-12 部活動型の圧縮に合わせた：論点名は読書面の論点タブ（.fr-tab）、山は対話式の山なみ（#section .hill）。
   推移・作り方・詳細データ・投稿例は折りたたみの中にあるので、開いてから確かめる。
   x.com・platform.twitter.com への通信はすべて遮断する（X埋め込みは失敗時の表示を確かめる）。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

const url = process.env.AI_COPYRIGHT_REDESIGN_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ローカル候補のURLが必要です（AI_COPYRIGHT_REDESIGN_URL）');
}
const evidence = process.env.AI_COPYRIGHT_EVIDENCE_DIR;
const shot = (page, name, full = false) => evidence ? page.screenshot({ path: path.join(evidence, name), fullPage: full }) : null;
const ISSUES = 7;
const X_HOSTS = /(^|\.)(x\.com|twitter\.com|twimg\.com)$/;

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

(async () => {
  const browser = await chromium.launch({ headless: true });
  const summary = [];
  try {
    for (const [width, name] of [[1280, 'desktop'], [375, 'mobile']]) {
      const { context, page, errors } = await open(browser, { viewport: { width, height: 900 } });
      await page.goto(url, { waitUntil: 'networkidle' });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 0, `${name}: 横にはみ出しています（${overflow}px）`);
      await shot(page, `page-${name}.png`, true);

      // 論点を選んでも、ページの位置は動かない
      const chips = page.locator('#ai-copyright-reading .fr-tab');
      assert.equal(await chips.count(), ISSUES);
      for (let i = 0; i < ISSUES; i++) {
        const chip = chips.nth(i);
        await chip.scrollIntoViewIfNeeded();
        const before = await page.evaluate(() => scrollY);
        const id = await chip.getAttribute('data-issue-id');
        await chip.click();
        const after = await page.evaluate(() => scrollY);
        assert.equal(after, before, `${name}: 論点 ${id} の選択で scrollY が ${before}→${after}`);
        const selected = await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel');
        assert.equal(selected, id);
        assert.equal(await page.locator('[data-issue-panel]:not([data-selected])').first().isVisible(), false);
        const wide = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        assert.ok(wide <= 0, `${name}: 論点 ${id} の表示で横にはみ出しています`);
      }
      // 山を押すと、その論点の読書面へ移る（設計記録 10-3）
      const hill = page.locator('#section .hill').nth(5);
      await hill.scrollIntoViewIfNeeded();
      const hillId = await page.evaluate(() => window.PLANET_DATA.issues[5].id);
      await hill.click({ force: true });
      await page.waitForFunction(id => location.hash === '#issue-' + id, hillId);
      await page.waitForTimeout(1500);  // なめらかなスクロールが止まるまで待つ
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), hillId);
      const top = await page.locator('[data-issue-panel][data-selected]').evaluate(e => e.getBoundingClientRect().top);
      assert.ok(top >= 0 && top < 300, `${name}: 山を押しても読書面が画面に来ません（${top}px）`);
      await chips.first().click();
      await page.locator('#ai-copyright-reading .fr-tabs').scrollIntoViewIfNeeded();
      await shot(page, `reading-1-${name}.png`);
      await page.evaluate(() => scrollBy(0, innerHeight - 60));
      await shot(page, `reading-2-${name}.png`);
      // 理由一覧の行を押すと、その理由の説明だけが出る。「この論点の別の理由」で次へ
      const panel = page.locator('[data-issue-panel][data-selected]');
      const rowsR = panel.locator('.fr-reasons li.fr-reason');
      assert.equal(await panel.locator('.fr-reasons > .fr-reason-list li.fr-reason').count(), 4, `${name}: 理由一覧の上位が4件ではありません`);
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
      const wideFold = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(wideFold <= 0, `${name}: 読書面の折りたたみを開くと横にはみ出します`);
      for (const d of await panel.locator('details').all()) await d.evaluate(e => { e.open = false; });

      // 背景の開閉行
      const rows = page.locator('#ai-copyright-background details.fb-row');
      const n = await rows.count();
      assert.ok(n >= 7, `背景の行が少なすぎます（${n}）`);
      for (let i = 0; i < n; i++) {
        const row = rows.nth(i);
        await row.locator('summary').click();
        assert.equal(await row.evaluate(d => d.open), true);
        const wide = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        assert.ok(wide <= 0, `${name}: 背景の行 ${i} を開くと横にはみ出します`);
      }
      await rows.first().scrollIntoViewIfNeeded();
      await shot(page, `background-open-${name}.png`);
      for (let i = 0; i < n; i++) {
        await rows.nth(i).locator('summary').click();
        assert.equal(await rows.nth(i).evaluate(d => d.open), false);
      }
      // 意見の推移（引き継いだ部品）：折りたたみを開くとグラフが描かれ、タブを切り替えても横にはみ出さない
      await page.locator('#acp-trend-more > summary').scrollIntoViewIfNeeded();
      await page.locator('#acp-trend-more > summary').click();
      await page.waitForTimeout(600);
      const stageW = await page.locator('#ai-copyright-trend-panel-stance [data-trend-stage] svg').evaluate(e => e.getBoundingClientRect().width);
      assert.ok(stageW > 280 || width < 500, `${name}: 開いた推移のグラフの幅が足りません（${stageW}px）`);
      const trendTab = page.locator('.trend-card [data-trend-tab="issue"]');
      await trendTab.scrollIntoViewIfNeeded();
      await trendTab.click();
      assert.equal(await page.locator('#ai-copyright-trend-panel-issue').isVisible(), true, `${name}: 推移の「論点の変化」が開きません`);
      assert.equal(await page.locator('.trend-card img[src^="images/trend/ai-copyright-"]').count(), 4);
      const wideTrend = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(wideTrend <= 0, `${name}: 推移の表示で横にはみ出します`);
      await page.locator('#acp-trend').scrollIntoViewIfNeeded();
      await shot(page, `trend-open-${name}.png`);
      // 詳細データの折りたたみも、開いて横にはみ出さない
      await page.locator('#acp-method > summary').click();
      assert.equal(await page.locator('#acp-method').evaluate(d => d.open), true);
      for (const d of await page.locator('#detail-data details').all()) await d.evaluate(e => { e.open = true; });
      const wideDetail = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(wideDetail <= 0, `${name}: 詳細データを開くと横にはみ出します`);
      assert.deepEqual(errors, [], `${name}: コンソールエラー`);
      summary.push(`${name}: はみ出し0・論点タブ${ISSUES}つで scrollY 不変・山で読書面へ・理由の切替と「別の理由」・読書面の折りたたみ全開・背景${n}行の開閉・推移を開いて描画とタブ・作り方と詳細データ・エラー0`);
      await context.close();
    }

    // 戻る：論点を何度切り替えても履歴は増えず、「戻る」で前のページへ戻る
    {
      const { context, page } = await open(browser);
      const previous = new URL('index.html', url).href;
      await page.goto(previous, { waitUntil: 'domcontentloaded' });
      await page.goto(url, { waitUntil: 'networkidle' });
      const length = await page.evaluate(() => history.length);
      for (const chip of await page.locator('#ai-copyright-reading .fr-tab').all()) await chip.click();
      assert.equal(await page.evaluate(() => history.length), length, '論点の切替で履歴が増えました');
      assert.match(page.url(), /#issue-/);
      await page.goBack({ waitUntil: 'domcontentloaded' });
      assert.equal(page.url(), previous, '戻るで前のページへ戻りません');
      summary.push(`戻る: 論点${ISSUES}回の切替で history.length 不変、戻るで前のページ（index.html）へ`);
      await context.close();
    }

    // 旧アンカーと論点への直接リンク
    {
      const { context, page } = await open(browser);
      const selected = () => page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel');
      await page.goto(url + '#fb-ai-copyright-creator-rights', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => ['#issue-ai-copyright-creator-rights', '#ai-copyright-creator-rights'].includes(location.hash));
      assert.equal(await selected(), 'ai-copyright-creator-rights');
      await page.goto(url + '#ai-copyright-reading-ai-copyright-tech-promotion', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => ['#issue-ai-copyright-tech-promotion', '#ai-copyright-tech-promotion'].includes(location.hash));
      assert.equal(await selected(), 'ai-copyright-tech-promotion');
      await page.goto(url + '#copyright-entry', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#bg-kangaekata');
      assert.equal(await page.locator('#bg-kangaekata').evaluate(d => d.open), true);
      await page.goto(url + '#bukatsu-check', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#bg-rules');
      assert.equal(await page.locator('#bg-rules').evaluate(d => d.open), true);
      await page.goto(url + '#bukatsu-background', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#ai-copyright-background');
      await page.goto(url + '#aic-search-entry', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#ai-copyright-opening');
      await page.goto(url + '#stance-glance', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#ai-copyright-reading');
      await page.goto(url + '#issue-ai-copyright-other', { waitUntil: 'networkidle' });
      assert.equal(await selected(), 'ai-copyright-other');
      // 推移の埋め込みコードから来た人（別ページから開く）。同じ文書の中の移動にしないため、いったん空のページへ
      await page.goto('about:blank');
      await page.goto(url + '#ai-copyright-trend-panel-issue', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('#ai-copyright-trend-panel-issue').isVisible(), true, '推移の埋め込み先 #ai-copyright-trend-panel-issue が開きません');
      // 折りたたみの中の旧アンカー（作り方・詳細データ）も、開いて見せる
      await page.goto('about:blank');
      await page.goto(url + '#detail-data', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('#detail-data').isVisible(), true, '#detail-data で詳細データが開きません');
      for (const kept of ['vote-section', 'detail-data', 'related-topics', 'article-trust-title', 'caution', 'ai-copyright-trend-panel-stance']) {
        assert.equal(await page.locator('#' + kept).count(), 1, `#${kept} がありません`);
      }
      summary.push('旧アンカー: #fb-…・#ai-copyright-reading-…→論点、#copyright-entry→文化庁の考え方を開く、#bukatsu-check→ルールの違いを開く、#bukatsu-background→背景、#aic-search-entry→冒頭、#stance-glance→読書面、#issue-…で論点選択、推移の埋め込み先 #ai-copyright-trend-panel-issue が開く、#vote-section など6件はそのまま');
      await context.close();
    }

    // キーボード：論点名を Tab で選び Enter、背景の行を Enter で開く
    {
      const { context, page, errors } = await open(browser);
      await page.goto(url, { waitUntil: 'networkidle' });
      const target = page.locator('#ai-copyright-reading .fr-tab').nth(2);
      const id = await target.getAttribute('data-issue-id');
      await page.locator('#ai-copyright-reading .fr-tab').nth(1).focus();
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.issueId), id, 'Tab で次の論点名へ移れません');
      const before = await page.evaluate(() => scrollY);
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), id);
      assert.equal(await page.evaluate(() => scrollY), before, 'Enter で位置が動きました');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.issueId), id, 'フォーカスが論点名から外れました');
      const summaryEl = page.locator('#bg-faq > summary');
      await summaryEl.focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#bg-faq').evaluate(d => d.open), true, 'Enter で背景の行が開きません');
      const focusVisible = await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle);
      assert.notEqual(focusVisible, 'none', 'フォーカスの枠が見えません');
      const voteBtn = page.locator('#vote-issue-btns button').first();
      await voteBtn.focus();
      assert.equal(await page.evaluate(() => document.activeElement.classList.contains('vote-issue-btn')), true);
      assert.equal(await page.locator('#vote-issue-btns button').count(), 7, '投票の論点ボタンが7つではありません');
      assert.deepEqual(errors, []);
      summary.push('キーボード: Tab で論点名を移動、Enter で選択（位置・フォーカス不変）、Enter で背景を開く、投票ボタン7つへフォーカス可');
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
      await shot(page, 'x-embed-fallback.png');
      const pageErrors = errors.filter(e => e.startsWith('pageerror'));
      assert.deepEqual(pageErrors, [], 'X埋め込みの失敗でページのエラー');
      summary.push(`X埋め込み失敗（x.com・platform.twitter.com を遮断）: 「表示できません」の案内と元投稿リンク${links.length}件が残る、ページエラー0`);
      await context.close();
    }

    // JavaScriptなし：7論点の読書面と背景がすべて読める
    {
      const { context, page } = await open(browser, { javaScriptEnabled: false });
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      const visible = await page.locator('[data-issue-panel]').evaluateAll(ps => ps.filter(p => p.offsetHeight > 0).length);
      assert.equal(visible, ISSUES, `JSなしで${ISSUES}論点が表示されません`);
      // 折りたたみは JavaScript なしでも開く（推移・作り方と詳細データ）
      await page.locator('#acp-trend-more > summary').click();
      await page.locator('#acp-method > summary').click();
      const text = await page.locator('main').innerText();
      for (const word of ['生成AIと著作権', 'どんな理由で語られている', 'よくある質問', '世論調査ではありません', 'このページの作り方', '詳細データ', 'SNS上の意見の推移']) {
        assert.ok(text.includes(word), `JSなしで「${word}」が読めません`);
      }
      await page.locator('#bg-faq > summary').click();
      assert.equal(await page.locator('#bg-faq').evaluate(d => d.open), true, 'JSなしで背景の行が開きません');
      await shot(page, 'nojs-desktop.png');
      summary.push(`JSなし: ${ISSUES}論点すべて表示、本文・推移・作り方・詳細データ・背景の開閉とも可`);
      await context.close();
    }
  } finally {
    await browser.close();
  }
  console.log(summary.join('\n'));
  console.log('OK ai-copyright redesign browser checks');
})().catch(e => { console.error(e); process.exit(1); });
