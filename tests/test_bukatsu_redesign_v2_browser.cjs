/* 部活動の地域移行・新デザイン（最新の型。scripts/build_bukatsu_redesign_v2.py）の公開候補の表示・操作検査。
   消費税減税 tests/test_consumption_tax_redesign_browser.cjs と同じ項目に、自治体の絞り込み・全文・印刷版・初期型の旧アンカーを足した。
   ローカルで配信した候補だけを対象にする。
   NODE_PATH=<main>/node_modules BUKATSU_REDESIGN_URL=http://127.0.0.1:8811/bukatsu-chiiki-reaction-map.html \
   BUKATSU_EVIDENCE_DIR=quality/prototypes/bukatsu-chiiki-release-v2/evidence node tests/test_bukatsu_redesign_v2_browser.cjs
   投票は押さない（本番Supabaseへ送らないため。localhost では投票設定自体が無効になる）。
   x.com・platform.twitter.com・twimg.com への通信はすべて遮断する（X埋め込みは失敗時の表示を確かめる）。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

const url = process.env.BUKATSU_REDESIGN_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) {
  throw new Error('ローカル候補のURLが必要です（BUKATSU_REDESIGN_URL）');
}
const evidence = process.env.BUKATSU_EVIDENCE_DIR;
const shot = (page, name, full = false) => evidence ? page.screenshot({ path: path.join(evidence, name), fullPage: full }) : null;
const ISSUES = 7;
const X_HOSTS = /(^|\.)(x\.com|twitter\.com|twimg\.com)$/;
const R = '#bukatsu-chiiki-reading';
const BG = '#bukatsu-chiiki-background';
const BG_ROWS = 7;
const TREND = '#bukatsu-chiiki-trend';
const P = 'bukatsu-chiiki-';

async function open(browser, options = {}) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, ...options });
  await context.route(r => X_HOSTS.test(new URL(r).hostname), r => r.abort());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => {
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
      assert.equal(await page.evaluate(() => scrollY), 0, `${name}: 読み込み時に画面が動きました`);
      assert.equal(await page.evaluate(() => document.activeElement === document.body), true, `${name}: 読み込み時にフォーカスが移りました`);
      const first = await page.evaluate(() => document.querySelector('[data-default-issue]').dataset.defaultIssue);
      const top = await page.evaluate(() => window.PLANET_DATA.issues.slice().sort((a, b) => b.count - a.count)[0]);
      assert.equal(first, top.id);
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), first);
      assert.ok((await page.locator('#panel h2').innerText()).includes(top.label), `${name}: 山なみの選択パネルが件数1位の論点ではありません`);
      await shot(page, `page-${name}.png`, true);

      // 山なみ：立場モードを切り替える
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
      const hill = page.locator('#section .hill').nth(1);
      await hill.scrollIntoViewIfNeeded();
      const hillId = await page.evaluate(() => window.PLANET_DATA.issues[1].id);
      await hill.click({ force: true });
      await page.waitForFunction(id => location.hash === '#issue-' + id, hillId);
      await page.waitForTimeout(1500);
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), hillId);
      const topPx = await page.locator('[data-issue-panel][data-selected]').evaluate(e => e.getBoundingClientRect().top);
      assert.ok(topPx >= -4 && topPx < 300, `${name}: 山を押しても読書面が画面に来ません（${topPx}px）`);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'fr-h-' + hillId, `${name}: 見出しにフォーカスがありません`);
      const planetLabel = await page.evaluate(() => window.PLANET_DATA.issues[1].label);
      assert.ok((await page.locator('#panel h2').innerText()).includes(planetLabel), `${name}: 山なみの選択パネルが押した山の論点になりません`);
      await shot(page, `hill-to-reading-${name}.png`);
      // 論点ボタン（山なみの一覧）を人が押すと、山なみの中で切り替わり、読書面も合わせる
      await page.locator(`#btn-${P}hiyo`).click();
      await page.waitForTimeout(500);
      assert.equal(await page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel'), P + 'hiyo');
      assert.equal(await page.evaluate(() => location.hash), `#issue-${P}hiyo`);
      // 理由のある論点（教員の働き方）：理由一覧の行を押すと、その理由の説明だけが出る。「同じ論点の次の理由」で次へ
      await page.locator(`${R} .fr-tab[data-issue-id="${P}kyoin"]`).click();
      await page.locator(`${R} .fr-tabs`).scrollIntoViewIfNeeded();
      await shot(page, `reading-1-${name}.png`);
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
      assert.deepEqual(shownN, [await rowsR.nth(2).getAttribute('data-reason')], `${name}: 「次の理由」で次の理由へ移りません`);
      // 理由が未公開の2論点（住む地域で差が出る・その他）は「未公開」と書く
      for (const id of [`${P}kakusa`, `${P}sonota`]) {
        await page.locator(`${R} .fr-tab[data-issue-id="${id}"]`).click();
        assert.equal(await page.locator(`#issue-${id} [data-unpublished]`).isVisible(), true, `${name}: ${id} に理由は未公開の表示がありません`);
      }
      for (const id of [`${P}kyoin`, `${P}ukezara`, `${P}kakusa`]) {
        await page.locator(`${R} .fr-tab[data-issue-id="${id}"]`).click();
        const sel = page.locator('[data-issue-panel][data-selected]');
        for (const d of await sel.locator('details').all()) await d.evaluate(e => { e.open = true; });
        assert.ok(await wideOf(page) <= 0, `${name}: 読書面（${id}）の折りたたみを開くと横にはみ出します`);
        for (const d of await sel.locator('details').all()) await d.evaluate(e => { e.open = false; });
      }

      // 背景の開閉行
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
      // 自分の自治体は？：自治体名で絞り込む
      const filter = page.locator('#bg-municipal [data-muni-filter]');
      const all = await page.locator('#bg-municipal [data-muni-row]').count();
      await filter.fill('神戸');
      const hit = await page.locator('#bg-municipal [data-muni-row]').evaluateAll(rs => rs.filter(r => !r.hidden).length);
      assert.ok(hit >= 1 && hit < all, `${name}: 自治体の絞り込みが働きません（${hit}/${all}）`);
      await filter.scrollIntoViewIfNeeded();
      await shot(page, `municipal-filter-${name}.png`);
      await filter.fill('');
      for (let i = 0; i < n; i++) await rows.nth(i).locator('summary').click();

      // 意見の推移（引き継いだカード）：折りたたみを開くとグラフが描かれ、「論点の変化」に切り替わる
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
      await page.locator('#cap-method > summary').click();
      for (const d of await page.locator('#detail-data details').all()) await d.evaluate(e => { e.open = true; });
      assert.ok(await wideOf(page) <= 0, `${name}: 詳細データを開くと横にはみ出します`);
      assert.deepEqual(errors, [], `${name}: コンソールエラー`);
      summary.push(`${name}: はみ出し0・読み込み時のハッシュ無し・画面とフォーカスは動かない・既定の論点＝件数1位（山なみと一致）・立場モード切替・論点タブ${ISSUES}つで scrollY 不変・山で読書面へ（見出しにフォーカス、山なみも同じ論点）・論点ボタンで読書面も切替・理由の切替と「次の理由」・理由は未公開の2論点・読書面の折りたたみ全開・背景${n}行の開閉・自治体の絞り込み（神戸 ${hit}/${all}行）・推移を開いて描画と切替・作り方と詳細データ・エラー0`);
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
      await page.locator(`#btn-${P}ukezara`).click();
      await page.waitForTimeout(500);
      assert.equal(await page.evaluate(() => history.length), length, '論点の切替・山の選択で履歴が増えました');
      assert.match(page.url(), /#issue-/);
      await page.goBack({ waitUntil: 'domcontentloaded' });
      assert.equal(page.url(), previous, '戻るで前のページへ戻りません');
      summary.push(`戻る: 論点${ISSUES}回の切替・山の選択・論点ボタンで history.length 不変、戻るで前のページ（index.html）へ`);
      await context.close();
    }

    // 旧アンカー（初期型と、さらに前の旧形式）と論点・理由への直接リンク
    {
      const { context, page } = await open(browser);
      const selected = () => page.locator('[data-issue-panel][data-selected]').getAttribute('data-issue-panel');
      const fresh = async hash => { await page.goto('about:blank'); await page.goto(url + hash, { waitUntil: 'networkidle' }); };
      const lands = async (hash, id) => {
        await fresh(hash);
        await page.waitForFunction(x => location.hash.includes(x), id);
        assert.equal(await selected(), id, hash);
      };
      await lands('#' + P + 'hiyo', P + 'hiyo');                // 初期型の読書面の欄・授業用ページのリンク（論点の素のID）
      assert.ok((await page.locator('#panel h2').innerText()).includes('費用'), '論点の素のIDで山なみが合いません');
      await lands('#heading-3', P + 'ukezara');                  // 初期型の見出し
      await lands('#fb-' + P + 'kyoiku', P + 'kyoiku');          // 旧形式のJSなし本文
      await lands('#issue-' + P + 'seido', P + 'seido');
      await fresh('#' + P + 'kyoin--L');                         // 初期型の理由の欄
      await page.waitForFunction(() => location.hash.startsWith('#fr-r-'));
      assert.equal(await selected(), P + 'kyoin');
      assert.equal(await page.locator(`#fr-r-${P}kyoin-L`).isVisible(), true, '初期型の理由の欄から理由が開きません');
      for (const [old, target] of [['#classroom', 'bg-classroom'], ['#faq', 'bg-faq'], ['#bukatsu-check', 'bg-municipal'],
                                   ['#bukatsu-background', 'bg-system'], ['#local', 'bg-municipal'], ['#classroom-title', 'bg-classroom'],
                                   ['#method', 'cap-method']]) {
        await fresh(old);
        await page.waitForFunction(t => location.hash === '#' + t, target);
        assert.equal(await page.locator('#' + target).evaluate(d => d.open), true, `${old} で ${target} が開きません`);
      }
      for (const [old, target] of [['#schedule', 'bko-steps'], ['#map', 'planet-block'], ['#stance-glance', 'bko-count'],
                                   ['#reading', 'bukatsu-chiiki-reading'], ['#background', 'bukatsu-chiiki-background'], ['#answers', 'bukatsu-open']]) {
        await fresh(old);
        await page.waitForFunction(t => location.hash === '#' + t, target);
      }
      for (const kind of ['stance', 'issue']) {
        await fresh(`#bukatsu-chiiki-trend-panel-${kind}`);
        await page.waitForTimeout(600);
        assert.equal(await page.locator(`#bukatsu-chiiki-trend-panel-${kind}`).isVisible(), true, `推移の${kind}タブへのリンクで表示されません`);
        assert.equal(await page.locator(`${TREND} [data-trend-tab="${kind}"]`).getAttribute('aria-pressed'), 'true');
      }
      await fresh('#detail-data');
      assert.equal(await page.locator('#detail-data').isVisible(), true, '#detail-data で詳細データが開きません');
      for (const kept of ['vote-section', 'detail-data', 'related-topics', 'caution', 'research-conditions', 'planet-block', 'modes']) {
        assert.equal(await page.locator('#' + kept).count(), 1, `#${kept} がありません`);
      }
      summary.push('旧アンカー: 論点の素のID・#heading-3・#fb-…・#issue-…→その論点（山なみも合う）、#{論点}--L→その理由の説明、#classroom・#faq・#bukatsu-check・#bukatsu-background・#local・#classroom-title・#method→該当の行／折りたたみが開く、#schedule→段の一覧、#map→山なみ、#stance-glance→件数欄、#reading・#background・#answers→各節、推移の2タブ（外部の埋め込み）は折りたたみを開いてそのタブ、#detail-data など7件はそのまま');
      await context.close();
    }

    // キーボード：論点名を Tab で選び Enter、背景の行を Enter で開く、投票ボタンへフォーカス
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
      await page.locator('#bg-faq > summary').focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#bg-faq').evaluate(d => d.open), true, 'Enter で背景の行が開きません');
      const voteBtn = page.locator('#vote-issue-btns button').first();
      await voteBtn.focus();
      assert.equal(await page.evaluate(() => document.activeElement.classList.contains('vote-issue-btn')), true);
      assert.equal(await page.locator('#vote-issue-btns button').count(), 7, '投票の論点ボタンが7つではありません');
      assert.deepEqual(errors, []);
      summary.push('キーボード: Tab で論点名を移動、Enter で選択（位置不変）、Enter で背景を開く、投票ボタン7つへフォーカス可（押していない）');
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
      const parts = await page.evaluate(() => Object.fromEntries([['冒頭', '#bukatsu-open'], ['山なみ', '.fr-map'], ['背景', '#bukatsu-chiiki-background'], ['推移の要約', '#cap-trend'], ['投票', '#vote-section']]
        .map(([k, s]) => [k, Math.round(document.querySelector(s).getBoundingClientRect().height)])));
      const mainChars = await visibleChars('main');
      const panels = [];
      for (const tab of await page.locator(`${R} .fr-tab`).all()) {
        await tab.click();
        const id = await tab.getAttribute('data-issue-id');
        const h = await page.locator('[data-issue-panel][data-selected]').evaluate(e => Math.round(e.getBoundingClientRect().height));
        if (width === 375) assert.ok(h <= 2500, `論点の欄 ${id} が375pxで2,500pxを超えます（${h}px）`);
        panels.push(`${(await tab.innerText()).split('\n')[0].trim()} ${h}px/${await visibleChars('#issue-' + id)}字`);
      }
      if (width === 375) assert.ok(total <= 13000, `375pxのページ全体が13,000pxを超えます（${total}px）`);
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

    // JavaScriptなし：7論点の読書面と背景がすべて読める
    {
      const { context, page } = await open(browser, { javaScriptEnabled: false });
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      const visible = await page.locator('[data-issue-panel]').evaluateAll(ps => ps.filter(p => p.offsetHeight > 0).length);
      assert.equal(visible, ISSUES, `JSなしで${ISSUES}論点が表示されません`);
      await page.locator('#cap-trend-more > summary').click();
      await page.locator('#cap-method > summary').click();
      const text = await page.locator('main').innerText();
      for (const word of ['部活動の地域移行', 'いつから？', 'よくある質問', '世論調査', 'このページの作り方', '全文・印刷版', '論点の一覧']) {
        assert.ok(text.includes(word), `JSなしで「${word}」が読めません`);
      }
      assert.ok(!text.includes('試作'), 'JSなしで「試作」の語が出ます');
      await page.locator('#bg-faq > summary').click();
      assert.equal(await page.locator('#bg-faq').evaluate(d => d.open), true, 'JSなしで背景の行が開きません');
      assert.ok(await wideOf(page) <= 0, 'JSなしで横にはみ出します');
      await shot(page, 'nojs-desktop.png');
      summary.push(`JSなし: ${ISSUES}論点すべて表示、図が使えないときの論点一覧・本文・推移の要約・作り方・詳細データ・背景の開閉・全文・印刷版への案内とも可、「試作」の語なし`);
      await context.close();
    }

    // 全文・印刷版：スクリプトなしで7論点・全理由・背景を続けて読める。印刷の見た目でも横にはみ出さない
    {
      for (const [width, name] of [[1280, 'desktop'], [375, 'mobile']]) {
        const { context, page, errors } = await open(browser, { viewport: { width, height: 900 } });
        await page.goto(new URL('bukatsu-chiiki-full.html', url).href, { waitUntil: 'networkidle' });
        assert.equal(await page.locator('script').count(), 0, '全文・印刷版にスクリプトがあります');
        assert.equal(await page.locator('.fr-panel').evaluateAll(ps => ps.filter(p => p.offsetHeight > 0).length), ISSUES);
        assert.ok(await wideOf(page) <= 0, `${name}: 全文・印刷版が横にはみ出します`);
        if (name === 'desktop') {
          await page.emulateMedia({ media: 'print' });
          assert.ok(await wideOf(page) <= 0, '印刷の見た目で横にはみ出します');
          await shot(page, 'full-print.png');
          await page.emulateMedia({ media: 'screen' });
        }
        await shot(page, `full-${name}.png`);
        assert.deepEqual(errors, []);
        await context.close();
      }
      summary.push(`全文・印刷版: スクリプト0、${ISSUES}論点表示、1280/375pxと印刷の見た目で横はみ出し0`);
    }
  } finally {
    await browser.close();
  }
  console.log(summary.join('\n'));
  console.log('OK bukatsu-chiiki redesign v2 browser checks');
})().catch(e => { console.error(e); process.exit(1); });
