/* 学校あだ名禁止の課題77候補をChromium/WebKit・3幅で確認する。 */
const {chromium, webkit} = require('playwright');
const assert = require('node:assert/strict');

const url = process.env.SCHOOL_NICKNAME_CONNECTED_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('SCHOOL_NICKNAME_CONNECTED_URL にローカル候補を指定してください');
}

async function contextFor(browser, options = {}) {
  const context = await browser.newContext({viewport: {width: 1280, height: 900}, reducedMotion: 'reduce', ...options});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/*', route => {
    if (new URL(route.request().url()).origin !== new URL(url).origin) return route.abort();
    return route.continue();
  });
  return {context, page, errors};
}

(async () => {
  const engineName = process.env.SCHOOL_NICKNAME_BROWSER || 'chromium';
  assert.ok(['chromium', 'webkit'].includes(engineName));
  const launchOptions = {headless: true};
  if (process.env.SCHOOL_NICKNAME_EXECUTABLE && engineName === 'chromium') launchOptions.executablePath = process.env.SCHOOL_NICKNAME_EXECUTABLE;
  const browser = await ({chromium, webkit})[engineName].launch(launchOptions);
  try {
    for (const width of [1280, 375, 320]) {
      const {context, page, errors} = await contextFor(browser, {viewport: {width, height: 900}});
      await page.goto(url, {waitUntil: 'domcontentloaded'});
      await page.evaluate(() => localStorage.removeItem('isa-seen-school-nickname-ban'));
      await page.reload({waitUntil: 'domcontentloaded'});
      await page.waitForTimeout(350);
      assert.equal(await page.locator('body.school-nickname-ban-connected').count(), 1);
      assert.equal(await page.locator('#progress > span').first().innerText(), '探ったところ');
      assert.equal(await page.locator('#pnum').innerText(), '1 / 17');
      assert.doesNotMatch(
        await page.locator('body').innerText(),
        /AI分類。代表投稿|AIが自動でつけた区分|人が読んだ結果だけ|AIを使用した工程|収集・分類で分かったこと|Powered by Yahooリアルタイム検索/,
      );
      await page.evaluate(() => scrollTo(0, document.documentElement.scrollHeight));
      await page.waitForTimeout(80);
      assert.equal(await page.locator('#pnum').innerText(), '1 / 17');
      await page.locator('#btn-school-nickname-ban-psychological-safety').click();
      assert.equal(await page.locator('#pnum').innerText(), '2 / 17');
      await page.reload({waitUntil: 'domcontentloaded'});
      await page.waitForTimeout(120);
      assert.equal(await page.locator('#pnum').innerText(), '2 / 17');
      await page.goto(url, {waitUntil: 'domcontentloaded'});
      await page.waitForTimeout(120);
      assert.equal(await page.locator('#pnum').innerText(), '2 / 17');
      const guideTabs = page.locator('#school-nickname-guide [data-school-nickname-guide-tab]');
      const guidePanels = page.locator('#school-nickname-guide [data-school-nickname-guide-panel]');
      assert.equal(await guideTabs.count(), 3);
      assert.equal(await guidePanels.count(), 3);
      assert.equal(await guideTabs.first().getAttribute('aria-selected'), 'true');
      assert.equal(await page.locator('#school-nickname-guide [data-school-nickname-guide-panel]:visible').count(), 1);
      await guideTabs.first().press('ArrowRight');
      assert.equal(await guideTabs.nth(1).getAttribute('aria-selected'), 'true');
      assert.equal(await guidePanels.nth(1).isVisible(), true);
      assert.equal(await page.locator('#pnum').innerText(), '2 / 17');
      await guideTabs.first().click();
      await guidePanels.first().locator('[data-school-nickname-map-link]').click();
      await page.waitForTimeout(80);
      assert.equal(await page.locator('#pnum').innerText(), '3 / 17');
      assert.deepEqual(await page.evaluate(() => window.SchoolNicknameBanConnectedMap.getState()), {
        stanceId: 'all', issueId: 'school-nickname-ban-school-practice',
      });
      assert.ok(await page.evaluate(() => document.querySelector('#planet-block').getBoundingClientRect().top < innerHeight));
      await page.evaluate(() => window.SchoolNicknameBanConnectedMap.selectIssue('school-nickname-ban-uniform-rule'));
      const guideMarker = await page.locator('.school-nickname-guide-head').evaluate(element => {
        const head = element.getBoundingClientRect();
        const kicker = element.querySelector('.school-nickname-guide-kicker').getBoundingClientRect();
        const marker = getComputedStyle(element, '::before');
        const markerRight = head.left + parseFloat(marker.left) + parseFloat(marker.width);
        return {markerRight, kickerLeft: kicker.left};
      });
      assert.ok(guideMarker.markerRight + 8 <= guideMarker.kickerLeft, JSON.stringify(guideMarker));
      assert.equal(await page.locator('#school-nickname-faq details').count(), 10);
      await page.locator('#school-nickname-faq details').first().locator('summary').click();
      assert.equal(await page.locator('#school-nickname-faq details').first().getAttribute('open'), '');
      assert.deepEqual(await page.evaluate(() => window.SchoolNicknameBanConnectedMap.getState()), {
        stanceId: 'all', issueId: 'school-nickname-ban-uniform-rule',
      });
      const data = await page.evaluate(() => window.PLANET_DATA);
      const index = await page.locator('#school-nickname-connected-data').evaluate(element => JSON.parse(element.textContent));
      for (const issue of data.issues) {
        await page.locator('#btn-' + issue.id).click();
        assert.equal(await page.locator('#panel').getAttribute('data-school-nickname-issue-id'), issue.id);
        assert.equal(await page.locator('#panel [data-school-nickname-post-url]').count(), 2, issue.id);
        assert.doesNotMatch(await page.locator('#panel').innerText(), /NaN|Infinity/);
      }
      await page.locator('#btn-school-nickname-ban-uniform-rule').click();
      await page.locator('[data-school-nickname-reason="group-5"] > summary').click();
      assert.equal(await page.locator('[data-school-nickname-reason="group-5"] [data-school-nickname-reason-post-url]').count(), 2);
      for (const mode of data.modes) {
        await page.locator('#modes button[data-m="' + mode.id + '"]').click();
        assert.equal(await page.locator('#modes button[aria-pressed="true"]').getAttribute('data-m'), mode.id);
      }
      await page.evaluate(() => window.SchoolNicknameBanConnectedMap.selectIssue('school-nickname-ban-uniform-rule'));
      await page.waitForTimeout(60);
      await page.locator('[data-school-nickname-discover]').click();
      assert.equal(await page.locator('.school-nickname-source-stories [data-school-nickname-discovery]').count(), 4);
      await page.locator('[data-school-nickname-quiz]').click();
      assert.equal(await page.locator('#quiz [data-verdict]').count(), 3);
      assert.equal(await page.locator('#quiz').innerText().then(text => text.includes('問 1 / 4')), true);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      const mobileMountain = await page.evaluate(() => document.querySelector('#section').getBoundingClientRect().height);
      assert.equal(mobileMountain, width <= 760 ? 180 : 210);
      assert.deepEqual(errors, []);
      await context.close();
    }
    const {context, page} = await contextFor(browser, {viewport: {width: 375, height: 900}, javaScriptEnabled: false});
    await page.goto(url, {waitUntil: 'domcontentloaded'});
    assert.equal(await page.locator('#fallback').isVisible(), true);
    assert.equal(await page.locator('#issue-cards').isVisible(), true);
    assert.equal(await page.locator('#school-nickname-guide [data-school-nickname-guide-panel]').count(), 3);
    assert.equal(await page.locator('#school-nickname-guide [data-school-nickname-guide-panel]:visible').count(), 3);
    assert.doesNotMatch(
      await page.locator('body').innerText(),
      /AI分類。代表投稿|AIが自動でつけた区分|人が読んだ結果だけ|この論点の中身（編集部|ここから下は集計ではありません/,
    );
    await context.close();
    console.log(JSON.stringify({engine: engineName, widths: [1280, 375, 320], javascriptDisabled: true}));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
