/* 副首都・新デザインの公開候補の表示・操作検査（皇室 tests/test_koshitsu_redesign_browser.cjs と同じ項目）。
   ローカルで配信した候補だけを対象にする。
   NODE_PATH=<main>/node_modules FUKUSHUTO_REDESIGN_URL=http://127.0.0.1:8766/fukushuto-reaction-map.html \
   FUKUSHUTO_EVIDENCE_DIR=quality/prototypes/fukushuto-release/evidence node tests/test_fukushuto_redesign_browser.cjs
   投票は押さない（本番Supabaseへ送らないため。localhost では投票設定自体が無効になる）。
   2026-10-12 部活動型の圧縮に合わせた（生成AIと著作権 tests/test_ai_copyright_redesign_browser.cjs と同じ項目）：
   論点名は読書面の論点タブ（.fr-tab）、山は対話式の山なみ（#section .hill）。10-11 に山なみを対話式へ戻した時点で
   .fr-chip・.fr-hill が無くなり動かなくなっていたのも直した。作り方・詳細データ・投稿例は折りたたみの中にあるので、開いてから確かめる。
   GA4 の issue_view は gtag を差し替えて記録だけを見る（localhost では GA のタグ自体が読み込まれない）。
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
  await context.addInitScript(() => { window.gtag = (...a) => { (window.__ga = window.__ga || []).push(a); }; });
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
      const chips = page.locator('#fukushuto-reading .fr-tab');
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
      // 山を押すと、その論点の読書面へ移る（設計記録 10節）。GA4 の issue_view もその論点で記録される
      const hill = page.locator('#section .hill').nth(1);
      await hill.scrollIntoViewIfNeeded();
      const hillId = await page.evaluate(() => window.PLANET_DATA.issues[1].id);
      await hill.click({ force: true });
      await page.waitForFunction(id => location.hash === '#issue-' + id, hillId);
      await page.waitForTimeout(1500);  // なめらかなスクロールが止まるまで待つ
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), hillId);
      const top = await page.locator('[data-issue-panel][data-selected]').evaluate(e => e.getBoundingClientRect().top);
      assert.ok(top >= 0 && top < 300, `${name}: 山を押しても読書面が画面に来ません（${top}px）`);
      const ga = await page.evaluate(() => (window.__ga || []).filter(a => a[0] === 'event' && a[1] === 'issue_view').map(a => a[2].issue_id));
      assert.ok(ga.includes(hillId), `${name}: GA4 の issue_view が ${hillId} で記録されません（${ga}）`);
      // 既定の論点（都構想・維新）は理由区分が無いので、理由の確かめは候補地で行う
      await chips.first().click();
      await page.locator('#fukushuto-reading .fr-tabs').scrollIntoViewIfNeeded();
      await shot(page, `reading-1-${name}.png`);
      await page.evaluate(() => scrollBy(0, innerHeight - 60));
      await shot(page, `reading-2-${name}.png`);
      await page.locator('#fukushuto-reading .fr-tab[data-issue-id="fukushuto-location"]').click();
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
      // 読書面の折りたたみをすべて開いても横にはみ出さない（全論点）
      for (const id of await chips.evaluateAll(as => as.map(a => a.dataset.issueId))) {
        await page.locator(`#fukushuto-reading .fr-tab[data-issue-id="${id}"]`).click();
        for (const d of await panel.locator('details').all()) await d.evaluate(e => { e.open = true; });
        const wideFold = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        assert.ok(wideFold <= 0, `${name}: 論点 ${id} の折りたたみを開くと横にはみ出します`);
        for (const d of await panel.locator('details').all()) await d.evaluate(e => { e.open = false; });
      }
      await chips.first().click();

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
      // 作り方と詳細データの折りたたみも、開いて横にはみ出さない
      await page.locator('#fu-method > summary').scrollIntoViewIfNeeded();
      await page.locator('#fu-method > summary').click();
      assert.equal(await page.locator('#fu-method').evaluate(d => d.open), true);
      for (const d of await page.locator('#detail-data details').all()) await d.evaluate(e => { e.open = true; });
      const wideDetail = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(wideDetail <= 0, `${name}: 詳細データを開くと横にはみ出します`);
      assert.deepEqual(errors, [], `${name}: コンソールエラー`);
      summary.push(`${name}: はみ出し0・論点タブ${ISSUES}つで scrollY 不変・山で読書面へ（issue_view 記録）・理由の切替と「別の理由」・全論点の折りたたみ全開・背景${n}行の開閉・作り方と詳細データ・エラー0`);
      await context.close();
    }

    // 戻る：論点を何度切り替えても履歴は増えず、「戻る」で前のページへ戻る
    {
      const { context, page } = await open(browser);
      const previous = new URL('index.html', url).href;
      await page.goto(previous, { waitUntil: 'domcontentloaded' });
      await page.goto(url, { waitUntil: 'networkidle' });
      const length = await page.evaluate(() => history.length);
      for (const chip of await page.locator('#fukushuto-reading .fr-tab').all()) await chip.click();
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
      // 山なみのスクリプトが #fukushuto-finance に書き換えることがある（10-11 に対話式へ戻してから。生成AIと同じ）
      await page.waitForFunction(() => ['#issue-fukushuto-finance', '#fukushuto-finance'].includes(location.hash));
      assert.equal(await selected(), 'fukushuto-finance');
      await page.goto(url + '#fukushuto-faq', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#bg-faq');
      assert.equal(await page.locator('#bg-faq').evaluate(d => d.open), true);
      await page.goto(url + '#bukatsu-background', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => location.hash === '#fukushuto-background');
      await page.goto(url + '#issue-fukushuto-priority', { waitUntil: 'networkidle' });
      assert.equal(await selected(), 'fukushuto-priority');
      // 折りたたみの中の旧アンカー（作り方・詳細データ）も、開いて見せる
      await page.goto('about:blank');
      await page.goto(url + '#detail-data', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('#detail-data').isVisible(), true, '#detail-data で詳細データが開きません');
      await page.goto('about:blank');
      await page.goto(url + '#article-trust-title', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('#article-trust-title').isVisible(), true, '#article-trust-title で作り方が開きません');
      // 理由への直接リンク（#fr-r-{論点}-{区分}）で、その論点とその理由が開く
      await page.goto('about:blank');
      const rid = await (async () => { await page.goto(url, { waitUntil: 'networkidle' }); return page.locator('#issue-fukushuto-location .fr-reason').nth(2).getAttribute('data-reason'); })();
      await page.goto('about:blank');
      await page.goto(url + `#fr-r-fukushuto-location-${rid}`, { waitUntil: 'networkidle' });
      assert.equal(await selected(), 'fukushuto-location');
      assert.equal(await page.locator(`#fr-r-fukushuto-location-${rid}`).isVisible(), true, '理由への直接リンクで説明が開きません');
      for (const kept of ['vote-section', 'detail-data', 'related-topics', 'article-trust-title', 'caution']) {
        assert.equal(await page.locator('#' + kept).count(), 1, `#${kept} がありません`);
      }
      summary.push('旧アンカー: #fb-…→論点、#fukushuto-faq→よくある質問を開く、#bukatsu-background→背景、#issue-…で論点選択、#detail-data・#article-trust-title は折りたたみを開く、#fr-r-…で理由が開く、#vote-section など5件はそのまま');
      await context.close();
    }

    // キーボード：論点名を Tab で選び Enter、背景の行を Enter で開く
    {
      const { context, page, errors } = await open(browser);
      await page.goto(url, { waitUntil: 'networkidle' });
      const target = page.locator('#fukushuto-reading .fr-tab').nth(2);
      const id = await target.getAttribute('data-issue-id');
      await page.locator('#fukushuto-reading .fr-tab').nth(1).focus();
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
      // 折りたたみは JavaScript なしでも開く（作り方と詳細データ）
      await page.locator('#fu-method > summary').click();
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
