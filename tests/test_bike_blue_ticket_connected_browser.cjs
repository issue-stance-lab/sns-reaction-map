/* 自転車青切符の連動表示候補をローカル配信時だけ確認する。外部通信は遮断する。 */
const {chromium, webkit} = require('playwright');
const assert = require('node:assert/strict');

const url = process.env.BIKE_CONNECTED_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('BIKE_CONNECTED_URL にローカル候補を指定してください');
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
  const engineName = process.env.BIKE_BROWSER || 'chromium';
  assert.ok(['chromium', 'webkit'].includes(engineName));
  const browser = await ({chromium, webkit})[engineName].launch({headless: true});
  try {
    for (const width of [1280, 375, 320]) {
      const {context, page, errors} = await contextFor(browser, {viewport: {width, height: 900}});
      await page.goto(url, {waitUntil: 'domcontentloaded'});
      await page.waitForTimeout(350);
      assert.equal(await page.locator('body.bike-blue-ticket-connected').count(), 1);
      const bandAlignment = await page.evaluate(() => {
        const status = document.querySelector('.bike-status')?.getBoundingClientRect();
        const panel = document.querySelector('.planet-panel')?.getBoundingClientRect();
        return status && panel ? {statusX: status.x, statusWidth: status.width, panelX: panel.x, panelWidth: panel.width} : null;
      });
      assert.ok(bandAlignment, '制度の確認時点帯またはSNS反応マップが見つからない');
      assert.ok(Math.abs(bandAlignment.statusX - bandAlignment.panelX) < 0.5, `width=${width}: 制度の確認時点帯の左端がSNS反応マップとずれている`);
      assert.ok(Math.abs(bandAlignment.statusWidth - bandAlignment.panelWidth) < 0.5, `width=${width}: 制度の確認時点帯の幅がSNS反応マップとずれている`);
      assert.deepEqual(await page.evaluate(() => window.BikeBlueTicketConnectedMap.getState()), {
        stanceId: 'all', issueId: 'bike-blue-ticket-other',
      });
      const data = await page.evaluate(() => window.PLANET_DATA);
      const index = await page.locator('#bike-connected-data').evaluate(element => JSON.parse(element.textContent));
      for (const issue of data.issues) {
        await page.locator('#btn-' + issue.id).click();
        assert.equal(await page.locator('#panel').getAttribute('data-bike-issue-id'), issue.id);
        assert.equal(await page.locator('#panel [data-bike-post-url]').count(), 2, issue.id);
        assert.deepEqual(
          await page.locator('#panel [data-bike-check]').evaluateAll(elements => elements.map(element => element.dataset.bikeCheck)),
          index.issues[issue.id].check_ids,
        );
        assert.doesNotMatch(await page.locator('#panel').innerText(), /NaN|Infinity/);
      }
      for (const mode of data.modes) {
        await page.locator('#modes button[data-m="' + mode.id + '"]').click();
        assert.equal(await page.locator('#modes button[aria-pressed="true"]').getAttribute('data-m'), mode.id);
      }
      await page.evaluate(() => window.BikeBlueTicketConnectedMap.selectIssue('bike-blue-ticket-rule-ambiguity'));
      await page.waitForTimeout(60);
      await page.locator('[data-bike-discover]').click();
      assert.equal(await page.locator('.bike-source-stories [data-bike-discovery]').count(), 4);
      await page.locator('[data-bike-quiz]').click();
      assert.equal(await page.locator('#quiz [data-verdict]').count(), 3);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      assert.deepEqual(errors, []);
      await context.close();
    }
    const {context, page} = await contextFor(browser, {viewport: {width: 375, height: 900}, javaScriptEnabled: false});
    await page.goto(url, {waitUntil: 'domcontentloaded'});
    assert.equal(await page.locator('#fallback').isVisible(), true);
    assert.equal(await page.locator('#issue-cards').isVisible(), true);
    await context.close();
    console.log(JSON.stringify({engine: engineName, widths: [1280, 375, 320], javascriptDisabled: true}));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
