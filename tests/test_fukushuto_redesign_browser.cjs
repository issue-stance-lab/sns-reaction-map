/* 副首都・新デザインの公開候補の表示・操作検査（皇室 tests/test_koshitsu_redesign_browser.cjs と同じ項目）。
   ローカルで配信した候補だけを対象にする。
   NODE_PATH=<main>/node_modules FUKUSHUTO_REDESIGN_URL=http://127.0.0.1:8766/fukushuto-reaction-map.html \
   FUKUSHUTO_EVIDENCE_DIR=quality/prototypes/fukushuto-release/evidence node tests/test_fukushuto_redesign_browser.cjs
   投票は押さない（本番Supabaseへ送らないため。localhost では投票設定自体が無効になる）。
   x.com・platform.twitter.com への通信はすべて遮断する（X埋め込みは失敗時の表示を確かめる）。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

const url = process.env.FUKUSHUTO_REDESIGN_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ローカル候補のURLが必要です（FUKUSHUTO_REDESIGN_URL）');
}
const evidence = process.env.FUKUSHUTO_EVIDENCE_DIR;
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
      const chips = page.locator('#fukushuto-reading .fr-chip');
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
      // 山を押しても同じ
      const hill = page.locator('#fukushuto-reading .fr-hill').first();
      await hill.scrollIntoViewIfNeeded();
      const y0 = await page.evaluate(() => scrollY);
      await hill.click();
      assert.equal(await page.evaluate(() => scrollY), y0, `${name}: 山の選択で位置が動きました`);
      await chips.first().click();
      await page.locator('[data-issue-panel][data-selected]').scrollIntoViewIfNeeded();
      await shot(page, `issue-selected-${name}.png`);

      // 背景の開閉行
      const rows = page.locator('#fukushuto-background details.fb-row');
      const n = await rows.count();
      assert.ok(n >= 8, `背景の行が少なすぎます（${n}）`);
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
      // 詳細データの折りたたみも、開いて横にはみ出さない
      for (const d of await page.locator('#detail-data details').all()) await d.evaluate(e => { e.open = true; });
      const wideDetail = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(wideDetail <= 0, `${name}: 詳細データを開くと横にはみ出します`);
      assert.deepEqual(errors, [], `${name}: コンソールエラー`);
      summary.push(`${name}: はみ出し0・論点${ISSUES}つと山で scrollY 不変・背景${n}行の開閉・詳細データ・エラー0`);
      await context.close();
    }

    // 戻る：論点を何度切り替えても履歴は増えず、「戻る」で前のページへ戻る
    {
      const { context, page } = await open(browser);
      const previous = new URL('index.html', url).href;
      await page.goto(previous, { waitUntil: 'domcontentloaded' });
      await page.goto(url, { waitUntil: 'networkidle' });
      const length = await page.evaluate(() => history.length);
      for (const chip of await page.locator('#fukushuto-reading .fr-chip').all()) await chip.click();
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
      await page.goto(url + '#fb-fukushuto-finance', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#issue-fukushuto-finance');
      assert.equal(await selected(), 'fukushuto-finance');
      await page.goto(url + '#fukushuto-faq', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#bg-faq');
      assert.equal(await page.locator('#bg-faq').evaluate(d => d.open), true);
      await page.goto(url + '#bukatsu-background', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#fukushuto-background');
      await page.goto(url + '#issue-fukushuto-priority', { waitUntil: 'networkidle' });
      assert.equal(await selected(), 'fukushuto-priority');
      for (const kept of ['vote-section', 'detail-data', 'related-topics', 'article-trust-title', 'caution']) {
        assert.equal(await page.locator('#' + kept).count(), 1, `#${kept} がありません`);
      }
      summary.push('旧アンカー: #fb-…→論点、#fukushuto-faq→よくある質問を開く、#bukatsu-background→背景、#issue-…で論点選択、#vote-section など5件はそのまま');
      await context.close();
    }

    // キーボード：論点名を Tab で選び Enter、背景の行を Enter で開く
    {
      const { context, page, errors } = await open(browser);
      await page.goto(url, { waitUntil: 'networkidle' });
      const target = page.locator('#fukushuto-reading .fr-chip').nth(2);
      const id = await target.getAttribute('data-issue-id');
      await page.locator('#fukushuto-reading .fr-chip').nth(1).focus();
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

    // 読む日が締切・施行日を過ぎたら、冒頭の段階表示だけ JS で切り替わる（背景は次の更新で切り替わる）
    {
      const results = [];
      for (const [day, expectComment, expectEnforce] of [
        ['2026-10-12T10:00:00+09:00', /まで意見募集/, /施行予定日として/],
        ['2026-10-17T10:00:00+09:00', /締め切った/, /施行予定日として/],
        ['2026-10-31T10:00:00+09:00', /締め切った/, /施行予定でした/],
      ]) {
        const { context, page, errors } = await open(browser);
        await page.clock.setFixedTime(new Date(day));
        await page.goto(url, { waitUntil: 'networkidle' });
        const comment = await page.locator('#fukushuto-opening [data-step="draft"] p').innerText();
        const enforce = await page.locator('#fukushuto-opening [data-step="enforce"] p').innerText();
        assert.match(comment, expectComment, `${day}: 意見募集の表示 ${comment}`);
        assert.match(enforce, expectEnforce, `${day}: 施行の表示 ${enforce}`);
        const answer = await page.locator('#fukushuto-opening [data-answer="when"] p:not(.fop-answer__short)').innerText();
        assert.match(answer, expectComment.source === 'まで意見募集' ? /募集しています/ : /締め切られました/, `${day}: 「いつ決まる？」の答え ${answer}`);
        assert.deepEqual(errors, []);
        results.push(day.slice(5, 10));
        await context.close();
      }
      summary.push(`時制（読む日）: ${results.join('・')} で意見募集中→締切済み→施行日を過ぎた（未確認）に切り替わる`);
    }

    // JavaScriptなし：7論点の読書面と背景がすべて読める
    {
      const { context, page } = await open(browser, { javaScriptEnabled: false });
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      const visible = await page.locator('[data-issue-panel]').evaluateAll(ps => ps.filter(p => p.offsetHeight > 0).length);
      assert.equal(visible, ISSUES, `JSなしで${ISSUES}論点が表示されません`);
      const text = await page.locator('main').innerText();
      for (const word of ['副首都は', 'どんな理由で語られている', 'よくある質問', '世論調査ではありません', 'このページの作り方', '詳細データ']) {
        assert.ok(text.includes(word), `JSなしで「${word}」が読めません`);
      }
      await page.locator('#bg-faq > summary').click();
      assert.equal(await page.locator('#bg-faq').evaluate(d => d.open), true, 'JSなしで背景の行が開きません');
      await shot(page, 'nojs-desktop.png');
      summary.push(`JSなし: ${ISSUES}論点すべて表示、本文・作り方・詳細データ・背景の開閉とも可`);
      await context.close();
    }
  } finally {
    await browser.close();
  }
  console.log(summary.join('\n'));
  console.log('OK fukushuto redesign browser checks');
})().catch(e => { console.error(e); process.exit(1); });
