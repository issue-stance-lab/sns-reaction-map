/* ローカル候補を実ブラウザで確認する。外部への投票・計測・埋め込み通信は遮断。 */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const url = process.env.TAX_CONNECTED_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('TAX_CONNECTED_URL にローカル候補のURLを指定してください');
}
(async () => {
  const browser = await chromium.launch({headless: true});
  const results = [];
  try {
    for (const width of [375, 1280]) {
      const context = await browser.newContext({viewport: {width, height: 900}, reducedMotion: 'reduce'});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.route('**/*', route => new URL(route.request().url()).origin === new URL(url).origin
        ? route.continue() : route.abort());
      await page.addInitScript(() => {
        window.__taxTestEvents = [];
        window.gtag = (...args) => window.__taxTestEvents.push(args);
      });
      await page.goto(url, {waitUntil: 'networkidle'});
      await page.locator('body.tax-connected').waitFor();
      assert.deepEqual(await page.evaluate(() => window.ConsumptionTaxMap.getState()), {stanceId: 'all', issueId: null});
      await page.locator('[data-stance-id="consumption-tax-cut-conditional"]').click();
      assert.equal(await page.locator('#modes [aria-pressed="true"]').getAttribute('data-m'), '条件付き賛成・政府案に不満');
      await page.locator('#btn-consumption-tax-cut-scope').click();
      assert.match(await page.locator('#panel').innerText(), /331件/);
      assert.equal(await page.locator('#panel').getAttribute('data-tax-issue-id'), 'consumption-tax-cut-scope');
      assert.equal(await page.locator('#tax-content-scope').count(), 1);
      // 同じ論点をもう一度開いても、本文の差し替え後に注記が残る。
      await page.locator('#btn-consumption-tax-cut-scope').click();
      assert.equal(await page.locator('#tax-content-scope').count(), 1);
      await page.locator('#modes [data-m="減税反対・慎重"]').click();
      assert.equal(await page.locator('#stance-glance .sg-pick-btn[aria-pressed="true"]').getAttribute('data-stance-id'), 'consumption-tax-cut-cautious');
      await page.locator('#btn-consumption-tax-cut-effect').click();
      assert.match(await page.locator('#panel').innerText(), /403件/);
      await page.locator('#modes [data-m="all"]').click();
      assert.equal(await page.locator('#stance-glance .sg-pick-btn[aria-pressed="true"]').count(), 0);
      for (const id of ['support', 'conditional', 'cautious', 'neutral']) {
        await page.locator('[data-stance-id="consumption-tax-cut-' + id + '"]').click();
        assert.equal((await page.evaluate(() => window.ConsumptionTaxMap.getState())).stanceId, 'consumption-tax-cut-' + id);
      }
      assert.equal(await page.evaluate(() => window.ConsumptionTaxMap.selectStance('unknown')), false);
      assert.equal(await page.evaluate(() => window.ConsumptionTaxMap.selectIssue('unknown')), false);
      assert.equal(await page.locator('#vote-result').isVisible(), false);
      const tracked = await page.evaluate(() => window.__taxTestEvents.filter(x => x[0] === 'event'));
      assert.deepEqual(tracked, [], '閲覧の切替で投票・立場の分析イベントを送らない');
      assert.deepEqual(errors, []);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      results.push({width, twoWayStanceSync: true, scopeConditional: 331, effectCautious: 403, errors});
      await context.close();
    }
    const context = await browser.newContext({javaScriptEnabled: false, viewport: {width: 375, height: 900}});
    const page = await context.newPage();
    await page.route('**/*', route => new URL(route.request().url()).origin === new URL(url).origin ? route.continue() : route.abort());
    await page.goto(url, {waitUntil: 'networkidle'});
    assert.equal(await page.locator('[id^="fb-consumption-tax-cut-"]').count(), 7);
    assert.equal(await page.locator('#claim-audit [data-claim-id]').count(), 6);
    assert.equal(await page.locator('#issue-cards .twitter-tweet').count(), 14);
    assert.equal(await page.locator('#fb-consumption-tax-cut-scope').isVisible(), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    results.push({javascriptDisabled: true, issues: 7, claims: 6, posts: 14});
    await context.close();
    console.log(JSON.stringify(results, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
