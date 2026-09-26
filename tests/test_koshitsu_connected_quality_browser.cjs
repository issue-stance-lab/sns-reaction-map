/* 課題77・皇室典範の表示・操作回帰検査。ローカル候補だけを対象にする。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const url = process.env.KOSHITSU_CONNECTED_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ローカル候補のURLが必要です（KOSHITSU_CONNECTED_URL）');
}

async function open(browser, options = {}) {
  const waitForPanel = options.waitForPanel !== false;
  delete options.waitForPanel;
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, ...options });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url, { waitUntil: 'networkidle' });
  if (waitForPanel) await page.locator('#panel h2').waitFor();
  return { context, page, errors };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const summary = [];
  try {
    for (const width of [320, 375, 1280]) {
      const { context, page, errors } = await open(browser, {
        viewport: { width, height: 900 },
        reducedMotion: 'reduce',
      });
      const ids = await page.evaluate(() => ({
        issues: window.PLANET_DATA.issues.map(issue => issue.id),
        stances: window.PLANET_DATA.stances.map(stance => stance.id).concat(['all']),
      }));
      const overflow = [];
      for (const stance of ids.stances) {
        await page.evaluate(id => window.KoshitsuConnectedMap.selectStance(id), stance);
        for (const issue of ids.issues) {
          await page.evaluate(id => window.KoshitsuConnectedMap.selectIssue(id), issue);
          const size = await page.evaluate(() => ({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
          }));
          if (size.scrollWidth > size.clientWidth + 2) overflow.push({ stance, issue, ...size });
        }
      }
      assert.deepEqual(overflow, [], `width=${width}: 横はみ出しが発生`);
      assert.deepEqual(errors, [], `width=${width}: コンソールエラー`);
      summary.push({ width, combinationsChecked: ids.issues.length * ids.stances.length });
      await context.close();
    }

    {
      const { context, page, errors } = await open(browser, { reducedMotion: 'reduce' });
      assert.deepEqual(
        await page.locator('.aic-evidence-controls button').allTextContents(),
        ['資料を読む', 'x投稿で語られない話', '一次資料クイズ · 6問'],
      );
      await page.locator('[data-aic-discover]').click();
      assert.equal(await page.locator('.aic-source-stories[hidden]').count(), 0);
      await page.locator('[data-aic-quiz]').click();
      assert.match(await page.locator('#quiz').innerText(), /問 1 \/ 6/);
      await page.locator('[data-verdict]').first().click();
      await page.locator('.qnext').click();
      assert.match(await page.locator('#quiz').innerText(), /問 2 \/ 6/);
      assert.deepEqual(errors, []);
      summary.push({ evidenceTabs: true, discovery: true, quiz: true });
      await context.close();
    }

    {
      const { context, page, errors } = await open(browser, {
        javaScriptEnabled: false,
        waitForPanel: false,
        viewport: { width: 375, height: 900 },
      });
      assert.ok(await page.locator('#issue-cards').isVisible());
      assert.ok(await page.locator('#bukatsu-background').isVisible());
      assert.match(await page.locator('body').innerText(), /皇室典範改正/);
      assert.deepEqual(errors, []);
      summary.push({ javascriptDisabled: true, readableContent: true });
      await context.close();
    }

    {
      const { context, page, errors } = await open(browser);
      await page.emulateMedia({ media: 'print' });
      const displays = await page.evaluate(() => Object.fromEntries(
        ['#issue-cards', '#koshitsu-audit', '#ocean', '#bukatsu-check', '#fallback']
          .map(selector => [selector, getComputedStyle(document.querySelector(selector)).display]),
      ));
      assert.deepEqual(displays, {
        '#issue-cards': 'block',
        '#koshitsu-audit': 'block',
        '#ocean': 'block',
        '#bukatsu-check': 'block',
        '#fallback': 'block',
      });
      assert.deepEqual(errors, []);
      summary.push({ printContent: true });
      await context.close();
    }
    console.log(JSON.stringify(summary, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
