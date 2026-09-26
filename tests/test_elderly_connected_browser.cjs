/* 高齢者免許返納の課題77候補を、実ブラウザで3幅・資料タブ・JS無効まで確認する。 */
const {chromium, webkit} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const url = process.env.ELDERLY_CONNECTED_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ELDERLY_CONNECTED_URL にローカル候補を指定してください');
}

const artifactDir = process.env.ELDERLY_ARTIFACT_DIR || path.join(__dirname, '..', '.staging', 'task77-elderly');
fs.mkdirSync(artifactDir, {recursive: true});

async function open(browser, width) {
  const context = await browser.newContext({viewport: {width, height: 950}, reducedMotion: 'reduce'});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/*', route => {
    const target = new URL(route.request().url());
    return target.origin === new URL(url).origin ? route.continue() : route.abort();
  });
  await page.goto(url, {waitUntil: 'domcontentloaded'});
  await page.locator('body.elderly-license-connected').waitFor();
  await page.locator('#panel [data-elc-count]').waitFor();
  return {context, page, errors};
}

async function waitState(page, issueId, stanceId = 'all') {
  await page.waitForFunction(([issueId, stanceId]) => {
    const state = window.ElderlyLicenseConnectedMap.getState();
    return state.issueId === issueId && state.stanceId === stanceId;
  }, [issueId, stanceId]);
}

async function attrValues(page, selector, attr) {
  return page.locator(selector).evaluateAll((elements, attr) => elements.map(element => element.getAttribute(attr)), attr);
}

(async () => {
  const engineName = process.env.ELDERLY_BROWSER || 'chromium';
  assert.ok(['chromium', 'webkit'].includes(engineName));
  const browser = await ({chromium, webkit})[engineName].launch({headless: true});
  const results = [];
  try {
    for (const width of [1280, 375, 320]) {
      const {context, page, errors} = await open(browser, width);
      const data = await page.evaluate(() => window.PLANET_DATA);
      const index = await page.locator('#elderly-connected-data').evaluate(element => JSON.parse(element.textContent));
      const top = data.issues.reduce((a, b) => b.count > a.count ? b : a);
      await waitState(page, top.id);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true, `横スクロール ${width}px`);

      for (const issue of data.issues) {
        await page.locator('#btn-' + issue.id).click();
        await waitState(page, issue.id);
        assert.equal(await page.locator('#panel').getAttribute('data-elc-issue-id'), issue.id);
        assert.equal(await page.locator('#panel [data-elc-count]').innerText(), String(data.modes[0].counts[issue.id] || 0));
        assert.deepEqual(await attrValues(page, '#panel [data-elc-claim]', 'data-elc-claim'), index.issues[issue.id].claim_ids, issue.id + ' claims');
        assert.deepEqual(await attrValues(page, '#panel [data-elc-source-only]', 'data-elc-source-only'), index.issues[issue.id].source_only_ids, issue.id + ' source-only');
        assert.deepEqual(await attrValues(page, '#panel [data-elc-reason-posts]', 'data-elc-reason-posts'), index.issues[issue.id].reason_ids, issue.id + ' reasons');
        assert.doesNotMatch(await page.locator('#panel').innerText(), /NaN|Infinity/, issue.id);
      }

      for (const stance of data.stances) {
        await page.locator('#modes button[data-m="' + stance.key + '"]').click();
        await waitState(page, (await page.evaluate(() => window.ElderlyLicenseConnectedMap.getState())).issueId, stance.id);
        assert.equal(await page.locator('#modes button[aria-pressed="true"]').getAttribute('data-m'), stance.key);
      }
      await page.evaluate(() => window.ElderlyLicenseConnectedMap.selectStance('all'));
      await page.evaluate(id => window.ElderlyLicenseConnectedMap.selectIssue(id), top.id);
      await waitState(page, top.id, 'all');

      await page.locator('[data-elc-discover]').click();
      assert.equal(await page.locator('.elc-source-stories [data-elc-discovery]').count(), data.ocean.sunk_continents.length);
      await page.locator('[data-elc-read]').click();
      await page.locator('[data-elc-quiz]').click();
      for (const [i, claim] of data.claims.entries()) {
        assert.equal(await page.locator('#quiz').getAttribute('data-claim-id'), claim.id);
        const owner = data.issues.find(issue => issue.claims.some(item => item.id === claim.id));
        assert.equal((await page.evaluate(() => window.ElderlyLicenseConnectedMap.getState())).issueId, owner.id);
        await page.locator('#quiz [data-verdict="' + claim.verdict + '"]').click();
        assert.ok((await page.locator('#quiz .qans').innerText()).includes(claim.finding));
        await page.locator('#quiz .qnext').click();
      }
      assert.match(await page.locator('#quiz').innerText(), new RegExp(data.claims.length + ' \/ ' + data.claims.length + '問正解'));
      await page.locator('[data-elc-finish]').click();

      await page.locator('#panel .elc-image-action').click();
      assert.equal(await page.locator('#explainer-modal.open').count(), 1);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#explainer-modal.open').count(), 0);
      assert.deepEqual(errors, []);
      await page.screenshot({path: path.join(artifactDir, 'elderly-connected-' + width + '.png'), fullPage: false});
      results.push({width, issues: data.issues.length, sourceOnly: data.ocean.sunk_continents.length, quiz: data.claims.length});
      await context.close();
    }

    const {context, page} = await open(browser, 1280);
    await page.evaluate(() => window.ElderlyLicenseConnectedMap.selectStance('all'));
    const first = await page.locator('#section .hill path').first().getAttribute('d');
    const stance = await page.evaluate(() => window.PLANET_DATA.stances[1]);
    await page.evaluate(id => window.ElderlyLicenseConnectedMap.selectStance(id), stance.id);
    await page.waitForTimeout(220);
    const mid = await page.locator('#section .hill path').first().getAttribute('d');
    assert.notEqual(mid, first, '立場切替の途中形状が変化していません');
    await page.waitForTimeout(350);
    assert.equal(await page.locator('#modes button[aria-pressed="true"]').getAttribute('data-m'), stance.key);
    await context.close();

    const noJsContext = await browser.newContext({viewport: {width: 375, height: 950}, javaScriptEnabled: false});
    const noJsPage = await noJsContext.newPage();
    await noJsPage.goto(url, {waitUntil: 'domcontentloaded'});
    assert.equal(await noJsPage.locator('#fallback').isVisible(), true);
    assert.equal(await noJsPage.locator('#issue-cards').isVisible(), true);
    assert.equal(await noJsPage.locator('#fallback .landing-panel').count(), 6);
    await noJsContext.close();
    results.push({reducedMotion: true, javascriptDisabled: true});

    console.log(JSON.stringify({engine: engineName, results}, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
