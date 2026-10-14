/* 消費税減税・新デザインの公開候補の表示・操作検査（辺野古 tests/test_henoko_redesign_browser.cjs と同じ項目）。
   ローカルで配信した候補だけを対象にする。
   NODE_PATH=<main>/node_modules CONSUMPTION_TAX_REDESIGN_URL=http://127.0.0.1:8799/consumption-tax-cut-reaction-map.html \
   CONSUMPTION_TAX_EVIDENCE_DIR=quality/prototypes/consumption-tax-cut-release/evidence node tests/test_consumption_tax_redesign_browser.cjs
   投票は押さない（本番Supabaseへ送らないため。localhost では投票設定自体が無効になる）。
   論点名は読書面の論点タブ（.fr-tab）、山は対話式の山なみ（#section .hill）。意見の推移（10回分）・作り方・
   詳細データ・投稿例は折りたたみの中にあるので、開いてから確かめる。
   x.com・platform.twitter.com・twimg.com への通信はすべて遮断する（X埋め込みは失敗時の表示を確かめる）。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

const url = process.env.CONSUMPTION_TAX_REDESIGN_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ローカル候補のURLが必要です（CONSUMPTION_TAX_REDESIGN_URL）');
}
const evidence = process.env.CONSUMPTION_TAX_EVIDENCE_DIR;
const shot = (page, name, full = false) => evidence ? page.screenshot({ path: path.join(evidence, name), fullPage: full }) : null;
const ISSUES = 7;
const X_HOSTS = /(^|\.)(x\.com|twitter\.com|twimg\.com)$/;
const R = '#consumption-tax-cut-reading';
const BG = '#consumption-tax-cut-background';
const BG_ROWS = 8;
const TREND = '#consumption-tax-cut-trend';
const P = 'consumption-tax-cut-';

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
      assert.equal(await page.evaluate(() => location.hash), '', `${name}: 読み込み時に URL にハッシュが付きました`);
      // 最初に開く論点は件数1位で、山なみの選択パネルも同じ論点
      const first = await page.evaluate(() => document.querySelector('[data-default-issue]').dataset.defaultIssue);
      const top = await page.evaluate(() => window.PLANET_DATA.issues.slice().sort((a, b) => b.count - a.count)[0]);
      assert.equal(first, top.id);
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), first);
      assert.ok((await page.locator('#panel h2').innerText()).includes(top.label), `${name}: 山なみの選択パネルが件数1位の論点ではありません`);
      await shot(page, `page-${name}.png`, true);

      // 冒頭のレシート：買い方を切り替えると税率と税込額が替わる
      await page.locator('#cto-calc').scrollIntoViewIfNeeded();
      const before = await page.locator('#cto-receipt [data-cto="after_rate"]').innerText();
      await page.locator('#cto-tab-eatin').click();
      assert.equal(await page.locator('#cto-tab-eatin').getAttribute('aria-selected'), 'true');
      assert.notEqual(await page.locator('#cto-receipt [data-cto="after_rate"]').innerText(), before, `${name}: レシートが切り替わりません`);
      await shot(page, `receipt-eatin-${name}.png`);
      await page.locator('#cto-tab-food').click();

      // 山なみ：立場モードを切り替える
      await page.locator('#planet-block').scrollIntoViewIfNeeded();
      await shot(page, `planet-${name}.png`);
      const modeBtn = page.locator('#modes button[data-m]').nth(3);
      const modeId = await modeBtn.getAttribute('data-m');
      await modeBtn.click();
      await page.waitForTimeout(700);
      assert.equal(await page.locator(`#modes button[data-m="${modeId}"]`).getAttribute('aria-pressed'), 'true');
      await page.locator('#modes').scrollIntoViewIfNeeded();
      await shot(page, `planet-mode-${name}.png`);
      await page.locator('#modes button[data-m="all"]').click();
      await page.waitForTimeout(600);
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

      // 論点タブを選んでも、ページの位置は動かない
      const tabs = page.locator(`${R} .fr-tab`);
      assert.equal(await tabs.count(), ISSUES);
      for (let i = 0; i < ISSUES; i++) {
        const tab = tabs.nth(i);
        await tab.scrollIntoViewIfNeeded();
        const y = await page.evaluate(() => scrollY);
        const id = await tab.getAttribute('data-issue-id');
        await tab.click();
        assert.equal(await page.evaluate(() => scrollY), y, `${name}: 論点 ${id} の選択で scrollY が動きました`);
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
      const topPx = await page.locator('[data-issue-panel][data-selected]').evaluate(e => e.getBoundingClientRect().top);
      assert.ok(topPx >= 0 && topPx < 300, `${name}: 山を押しても読書面が画面に来ません（${topPx}px）`);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'fr-h-' + hillId, `${name}: 見出しにフォーカスがありません`);
      const planetLabel = await page.evaluate(() => window.PLANET_DATA.issues[2].label);
      assert.ok((await page.locator('#panel h2').innerText()).includes(planetLabel), `${name}: 山なみの選択パネルが押した山の論点になりません`);
      await shot(page, `hill-to-reading-${name}.png`);
      // 理由のある論点（食料品だけか、全品目か）：理由一覧の行を押すと、その理由の説明だけが出る。「この論点の別の理由」で次へ
      await page.locator(`${R} .fr-tab[data-issue-id="${P}scope"]`).click();
      await page.locator(`${R} .fr-tabs`).scrollIntoViewIfNeeded();
      await shot(page, `reading-1-${name}.png`);
      await page.evaluate(() => scrollBy(0, innerHeight - 60));
      await shot(page, `reading-2-${name}.png`);
      const panel = page.locator('[data-issue-panel][data-selected]');
      const rowsR = panel.locator('.fr-reasons li.fr-reason');
      assert.equal(await panel.locator('.fr-reasons > .fr-reason-list li.fr-reason').count(), 4, `${name}: 理由一覧が4件ではありません`);
      await rowsR.nth(1).locator('a').click();
      const shownR = await panel.locator('.fr-reason-detail').evaluateAll(as => as.filter(a => a.offsetHeight > 0).map(a => a.dataset.reason));
      assert.deepEqual(shownR, [await rowsR.nth(1).getAttribute('data-reason')], `${name}: 選んだ理由の説明だけが出ていません`);
      await panel.locator('.fr-reason-detail[data-on]').scrollIntoViewIfNeeded();
      await shot(page, `reason-open-${name}.png`);
      await panel.locator('.fr-reason-detail[data-on] .fr-next a').click();
      const shownN = await panel.locator('.fr-reason-detail').evaluateAll(as => as.filter(a => a.offsetHeight > 0).map(a => a.dataset.reason));
      assert.deepEqual(shownN, [await rowsR.nth(2).getAttribute('data-reason')], `${name}: 「この論点の別の理由」で次の理由へ移りません`);
      // 理由が未公開の論点（選挙の約束は守られたのか）は「未公開」と書く
      await page.locator(`${R} .fr-tab[data-issue-id="${P}political-trust"]`).click();
      assert.equal(await page.locator(`#issue-${P}political-trust [data-unpublished]`).isVisible(), true, `${name}: 理由は未公開の表示がありません`);
      for (const id of [`${P}scope`, `${P}political-trust`]) {
        await page.locator(`${R} .fr-tab[data-issue-id="${id}"]`).click();
        const sel = page.locator('[data-issue-panel][data-selected]');
        for (const d of await sel.locator('details').all()) await d.evaluate(e => { e.open = true; });
        assert.ok(await wideOf(page) <= 0, `${name}: 読書面（${id}）の折りたたみを開くと横にはみ出します`);
        for (const d of await sel.locator('details').all()) await d.evaluate(e => { e.open = false; });
      }

      // 背景の開閉行（各論点の「0%案と各党の案を背景で読む」で行が開く）
      await page.locator(`#issue-${P}political-trust a[href="#bg-parties"]`).click();
      await page.waitForTimeout(300);
      assert.equal(await page.locator('#bg-parties').evaluate(d => d.open), true, `${name}: 背景へのリンクで行が開きません`);
      await page.locator('#bg-parties > summary').click();
      const rows = page.locator(`${BG} details.fb-row`);
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

      // 意見の推移（引き継いだ10回分のカード）：折りたたみを開くとグラフが描かれ、「論点の変化」に切り替わる
      await page.locator('#cap-trend-more > summary').scrollIntoViewIfNeeded();
      await page.locator('#cap-trend-more > summary').click();
      await page.waitForTimeout(1500);
      const lines = await page.locator(`${TREND} .trend-svg path, ${TREND} .trend-svg polyline, ${TREND} .trend-svg line`).count();
      assert.ok(lines >= 4, `${name}: 開いた推移のグラフが描かれていません（${lines}）`);
      const issueTab = page.locator(`${TREND} [data-trend-tab="issue"]`);
      await issueTab.click();
      assert.equal(await issueTab.getAttribute('aria-pressed'), 'true');
      assert.ok(await wideOf(page) <= 0, `${name}: 推移の表示で横にはみ出します`);
      await page.locator('#cap-trend').scrollIntoViewIfNeeded();
      await shot(page, `trend-open-${name}.png`);
      await page.locator(`${TREND} [data-trend-tab="stance"]`).click();
      await page.locator('#cap-trend-more > summary').click();
      // 読書面の「推移のグラフを開く」：折りたたみを開き、「論点の変化」に切り替えて移る（履歴は増やさない）
      await page.locator(`${R} .fr-tab[data-issue-id="${P}scope"]`).click();
      const len = await page.evaluate(() => history.length);
      await panel.locator('.fr-glance-link').click();
      await page.waitForTimeout(600);
      assert.equal(await page.locator('#cap-trend-more').evaluate(d => d.open), true, `${name}: 「推移のグラフを開く」で折りたたみが開きません`);
      assert.equal(await issueTab.getAttribute('aria-pressed'), 'true', `${name}: 「推移のグラフを開く」で論点の変化になりません`);
      assert.equal(await page.evaluate(() => history.length), len);
      // 作り方と詳細データの折りたたみも、開いて横にはみ出さない
      await page.locator('#cap-method > summary').click();
      assert.equal(await page.locator('#cap-method').evaluate(d => d.open), true);
      for (const d of await page.locator('#detail-data details').all()) await d.evaluate(e => { e.open = true; });
      assert.ok(await wideOf(page) <= 0, `${name}: 詳細データを開くと横にはみ出します`);
      assert.deepEqual(errors, [], `${name}: コンソールエラー`);
      summary.push(`${name}: はみ出し0・読み込み時のハッシュ無し・既定の論点＝件数1位（山なみと一致）・レシートの切替・立場モード切替・論点タブ${ISSUES}つで scrollY 不変・山で読書面へ（見出しにフォーカス、山なみも同じ論点）・理由の切替と「別の理由」・理由は未公開の表示・読書面の折りたたみ全開・背景${n}行の開閉と背景へのリンク・推移を開いて描画と切替・「推移のグラフを開く」・作り方と詳細データ・エラー0`);
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
      await page.locator('#section .hill').nth(1).click({ force: true });
      await page.waitForTimeout(800);
      assert.equal(await page.evaluate(() => history.length), length, '論点の切替・山の選択で履歴が増えました');
      assert.match(page.url(), /#issue-/);
      await page.goBack({ waitUntil: 'domcontentloaded' });
      assert.equal(page.url(), previous, '戻るで前のページへ戻りません');
      summary.push(`戻る: 論点${ISSUES}回の切替と山の選択で history.length 不変、戻るで前のページ（index.html）へ`);
      await context.close();
    }

    // 旧アンカーと論点・理由への直接リンク
    {
      const { context, page } = await open(browser);
      const selected = () => page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel');
      const fresh = async hash => { await page.goto('about:blank'); await page.goto(url + hash, { waitUntil: 'networkidle' }); };
      const lands = async (hash, id) => {
        await fresh(hash);
        await page.waitForFunction(x => ['#issue-' + x, '#' + x].includes(location.hash), id);
        assert.equal(await selected(), id, hash);
      };
      await lands('#fb-' + P + 'effect', P + 'effect');
      await lands('#tax-reading-' + P + 'alternatives', P + 'alternatives');
      await lands('#' + P + 'finance-welfare', P + 'finance-welfare');  // 論点の素のID（旧ページの山なみの着地）
      assert.ok((await page.locator('#panel h2').innerText()).length > 0);
      await lands('#rate10', P + 'scope');  // 旧「主張の照合」のカード
      await lands('#register', P + 'business-burden');
      for (const [old, target] of [['#bukatsu-background', 'bg-timeline'], ['#bukatsu-check', 'bg-status'], ['#policy-benefit', 'bg-benefit'],
                                   ['#classroom-title', 'bg-classroom'], ['#tax-faq-title', 'tax-faq']]) {
        await fresh(old);
        await page.waitForFunction(t => location.hash === '#' + t, target);
        assert.equal(await page.locator('#' + target).evaluate(d => d.open), true, `${old} で ${target} が開きません`);
      }
      await fresh('#tax-faq');
      assert.equal(await page.locator('#tax-faq').evaluate(d => d.open), true, '#tax-faq でよくある質問が開きません');
      for (const [old, target] of [['#tax-brief', 'tax-open'], ['#tax-case-tabs', 'cto-calc'], ['#tax-brief-stage', 'cto-steps'], ['#stance-glance', 'cto-count']]) {
        await fresh(old);
        await page.waitForFunction(t => location.hash === '#' + t, target);
      }
      // 外部の埋め込みコードが指す推移のタブ：折りたたみを開き、そのタブに切り替える
      for (const kind of ['stance', 'issue']) {
        await fresh(`#consumption-tax-cut-trend-panel-${kind}`);
        await page.waitForTimeout(600);
        assert.equal(await page.locator(`#consumption-tax-cut-trend-panel-${kind}`).isVisible(), true, `推移の${kind}タブへのリンクで表示されません`);
        assert.equal(await page.locator(`${TREND} [data-trend-tab="${kind}"]`).getAttribute('aria-pressed'), 'true');
      }
      await fresh('#modes');
      assert.equal(await page.locator('#modes').isVisible(), true);
      await fresh('#issue-' + P + 'alternatives');
      assert.equal(await selected(), P + 'alternatives');
      const reasonId = await page.evaluate(p => document.querySelector(`#issue-${p}effect .fr-reason-detail:last-of-type`).id, P);
      await fresh('#' + reasonId);
      assert.equal(await selected(), P + 'effect');
      assert.equal(await page.locator('#' + reasonId).isVisible(), true, '#fr-r-… で理由が開きません');
      await fresh('#detail-data');
      assert.equal(await page.locator('#detail-data').isVisible(), true, '#detail-data で詳細データが開きません');
      for (const kept of ['vote-section', 'detail-data', 'related-topics', 'caution', 'research-conditions', 'planet-block']) {
        assert.equal(await page.locator('#' + kept).count(), 1, `#${kept} がありません`);
      }
      summary.push('旧アンカー: #fb-…・#tax-reading-…・論点の素のID→論点、#rate10・#register（旧「主張の照合」）→その論点、#bukatsu-background→年表、#bukatsu-check→「決まったこと」、#policy-benefit→支援金、#classroom-title→授業、#tax-faq・#tax-faq-title→よくある質問の行が開く、#tax-brief→冒頭、#tax-case-tabs→レシート、#tax-brief-stage→段階図、#stance-glance→件数欄、推移の2タブ（外部の埋め込み）は折りたたみを開いてそのタブ、#modes、#issue-…、#fr-r-…、#detail-data、#vote-section など6件はそのまま');
      await context.close();
    }

    // キーボード：論点名を Tab で選び Enter、背景の行を Enter で開く、レシートの矢印キー
    {
      const { context, page, errors } = await open(browser);
      await page.goto(url, { waitUntil: 'networkidle' });
      const target = page.locator(`${R} .fr-tab`).nth(2);
      const id = await target.getAttribute('data-issue-id');
      await page.locator(`${R} .fr-tab`).nth(1).focus();
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.issueId), id, 'Tab で次の論点名へ移れません');
      const y = await page.evaluate(() => scrollY);
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), id);
      assert.equal(await page.evaluate(() => scrollY), y, 'Enter で位置が動きました');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.issueId), id, 'フォーカスが論点名から外れました');
      await page.locator('#tax-faq > summary').focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#tax-faq').evaluate(d => d.open), true, 'Enter で背景の行が開きません');
      await page.locator('#cto-tab-food').focus();
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.evaluate(() => document.activeElement.id), 'cto-tab-takeout', 'レシートの矢印キーで次の買い方へ移れません');
      const voteBtn = page.locator('#vote-issue-btns button').first();
      await voteBtn.focus();
      assert.equal(await page.evaluate(() => document.activeElement.classList.contains('vote-issue-btn')), true);
      assert.equal(await page.locator('#vote-issue-btns button').count(), 7, '投票の論点ボタンが7つではありません');
      assert.deepEqual(errors, []);
      summary.push('キーボード: Tab で論点名を移動、Enter で選択（位置・フォーカス不変）、Enter で背景を開く、レシートの矢印キー、投票ボタン7つへフォーカス可');
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
      const parts = await page.evaluate(() => Object.fromEntries([['冒頭', '#tax-open'], ['山なみ', '.fr-map'], ['背景', '#consumption-tax-cut-background'], ['推移の要約', '#cap-trend'], ['投票', '#vote-section']]
        .map(([k, s]) => [k, Math.round(document.querySelector(s).getBoundingClientRect().height)])));
      const mainChars = await visibleChars('main');
      const panels = [];
      for (const tab of await page.locator(`${R} .fr-tab`).all()) {
        await tab.click();
        const id = await tab.getAttribute('data-issue-id');
        const h = await page.locator('[data-issue-panel][data-selected]').evaluate(e => Math.round(e.getBoundingClientRect().height));
        panels.push(`${(await tab.innerText()).split('\n')[0].trim()} ${h}px/${await visibleChars('#issue-' + id)}字`);
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

    // JavaScriptなし：7論点の読書面と背景がすべて読める。レシートの代わりに全品目の表が出る
    {
      const { context, page } = await open(browser, { javaScriptEnabled: false });
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      const visible = await page.locator('[data-issue-panel]').evaluateAll(ps => ps.filter(p => p.offsetHeight > 0).length);
      assert.equal(visible, ISSUES, `JSなしで${ISSUES}論点が表示されません`);
      assert.equal(await page.locator('[data-cto-static]').isVisible(), true, 'JSなしで品目の表が出ません');
      await page.locator('#cap-trend-more > summary').click();
      await page.locator('#cap-method > summary').click();
      const text = await page.locator('main').innerText();
      for (const word of ['消費税減税', 'いつから・何%・いつまで？', '何が1%になる？', 'よくある質問', '世論調査', 'このページの作り方', '詳細データ',
                          '減税への立場の割合', '論点の一覧', '決まるまでの年表']) {
        assert.ok(text.includes(word), `JSなしで「${word}」が読めません`);
      }
      await page.locator('#tax-faq > summary').click();
      assert.equal(await page.locator('#tax-faq').evaluate(d => d.open), true, 'JSなしで背景の行が開きません');
      await shot(page, 'nojs-desktop.png');
      summary.push(`JSなし: ${ISSUES}論点すべて表示、品目の表・図が使えないときの論点一覧・本文・推移の要約・作り方・詳細データ・背景の開閉とも可`);
      await context.close();
    }
  } finally {
    await browser.close();
  }
  console.log(summary.join('\n'));
  console.log('OK consumption-tax-cut redesign browser checks');
})().catch(e => { console.error(e); process.exit(1); });
