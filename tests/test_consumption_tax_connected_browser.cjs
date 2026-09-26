/* 実データのローカル候補だけを操作する。投票・計測等の外部通信は遮断する。 */
const {chromium,webkit} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const url = process.env.TAX_CONNECTED_URL;
if (!url || !['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) throw new Error('TAX_CONNECTED_URL にローカル候補を指定してください');
const id = suffix => 'consumption-tax-cut-' + suffix;
const results = [];
async function contextFor(browser, options = {}, transform) {
  const context = await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce',...options});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/*', async route => {
    if (new URL(route.request().url()).origin !== new URL(url).origin) return route.abort();
    if (transform && route.request().isNavigationRequest()) {
      const response = await route.fetch();
      const original = await response.text();
      const changed = original.replace(/(<script id="planet-data">window\.PLANET_DATA=)(.*?)(;<\/script>)/s, (_,a,json,b)=>a+JSON.stringify(transform(JSON.parse(json)))+b);
      return route.fulfill({response,body:changed});
    }
    return route.continue();
  });
  await page.addInitScript(() => { window.__taxTestEvents=[]; window.gtag=(...args)=>window.__taxTestEvents.push(args); });
  return {context,page,errors};
}
async function load(page, hash = '') {
  await page.goto(url + hash, {waitUntil:'networkidle'});
  await page.locator('body.tax-connected').waitFor();
}
async function checkIssue(page, issue, mode, connection) {
  await page.locator('#btn-' + issue.id).click();
  assert.equal(await page.locator('#panel').getAttribute('data-tax-issue-id'),issue.id);
  assert.equal(await page.locator('[data-tax-count]').innerText(),mode.counts[issue.id].toLocaleString('ja-JP')+'件');
  const collect = attr => page.locator('#panel ['+attr+']').evaluateAll((els,key)=>els.map(el=>el.getAttribute(key)),attr);
  for (const [attr,key] of [['data-tax-claim','claim_ids'],['data-tax-policy','policy_ids'],['data-tax-timeline','timeline_ids'],['data-tax-source-only','source_only_ids'],['data-tax-concern','shared_concern_ids']]) {
    assert.deepEqual(await collect(attr),connection[key],issue.id+' '+key);
  }
  assert.deepEqual(await collect('data-tax-post-url'),connection.post_urls);
  assert.equal(await page.locator('#tax-content-scope').count(),1);
  assert.equal(await page.locator('#panel .tax-image-action').count(),1);
  assert.equal(await page.locator('#panel [data-tax-reason]').count(),issue.sub.items?.length || 0);
  if (issue.sub.status !== 'reread') assert.match(await page.locator('#panel .tax-opinions').innerText(), /理由別に分ける再読をまだ行っていません/);
  if (!connection.claim_ids.length) assert.match(await page.locator('#panel .tax-evidence').innerText(), /資料照合は、まだ登録されていません/);
  assert.doesNotMatch(await page.locator('#panel').innerText(), /NaN|Infinity/);
}
(async()=>{
  const engine=process.env.TAX_BROWSER||'chromium';
  assert.ok(['chromium','webkit'].includes(engine));
  const browser=await ({chromium,webkit})[engine].launch({headless:true});
  results.push({engine});
  try {
    for (const width of [1280,375,320]) {
      const {context,page,errors}=await contextFor(browser,{viewport:{width,height:900}});
      await load(page);
      const data=await page.evaluate(()=>window.PLANET_DATA);
      const index=await page.locator('#tax-connected-data').evaluate(el=>JSON.parse(el.textContent));
      const statusBox=await page.locator('.tax-status').boundingBox();
      const planetBox=await page.locator('.planet-panel').boundingBox();
      assert.ok(statusBox && planetBox,'制度確認帯またはSNS反応マップが見つかりません');
      assert.ok(Math.abs(statusBox.x-planetBox.x)<1 && Math.abs(statusBox.width-planetBox.width)<1,`制度確認帯の幅がSNS反応マップと揃っていません（${width}px）`);
      assert.deepEqual(await page.evaluate(()=>window.ConsumptionTaxMap.getState()),{stanceId:'all',issueId:id('scope')});
      // 最初に内容が異なる3論点を確認してから、全7論点へ広げる。
      for (const suffix of ['scope','finance-welfare','business-burden']) {
        const issue=data.issues.find(x=>x.id===id(suffix));
        await checkIssue(page,issue,data.modes[0],index.issues[issue.id]);
      }
      for (const mode of data.modes) {
        await page.locator('#modes button').evaluateAll((buttons,key)=>buttons.find(b=>b.dataset.m===key).click(),mode.id);
        for (const issue of data.issues) await checkIssue(page,issue,mode,index.issues[issue.id]);
      }
      await page.locator('#stance-glance .sg-pick-btn[data-stance-id="'+id('conditional')+'"]').click();
      assert.equal(await page.locator('#modes [aria-pressed="true"]').getAttribute('data-m'),data.stances.find(x=>x.id===id('conditional')).key);
      await page.locator('#btn-'+id('scope')).click();
      const conditionalMode=data.modes.find(mode=>mode.id===data.stances.find(x=>x.id===id('conditional')).key);
      assert.equal(await page.locator('[data-tax-count]').innerText(),conditionalMode.counts[id('scope')].toLocaleString('ja-JP')+'件');
      assert.equal(await page.locator('#stance-glance .temp-seg.tax-selected-stance').count(),1);
      await page.locator('#modes [data-m="減税反対・慎重"]').click();
      assert.equal(await page.locator('#stance-glance .sg-pick-btn[aria-pressed="true"]').getAttribute('data-stance-id'),id('cautious'));
      // 論点切替で画面を飛ばさず、理由の展開を立場切替で失わない。
      await page.locator('#btn-'+id('scope')).scrollIntoViewIfNeeded();
      const before=await page.evaluate(()=>scrollY);
      await page.locator('#btn-'+id('finance-welfare')).click();
      assert.ok(Math.abs((await page.evaluate(()=>scrollY))-before)<4);
      await page.locator('#btn-'+id('scope')).click();
      await page.locator('.tax-more-reasons > summary').click();
      await page.evaluate(()=>window.ConsumptionTaxMap.selectStance('all'));
      assert.equal(await page.locator('.tax-more-reasons').getAttribute('open'),'');
      // 図解とキーボード操作。
      await page.locator('.tax-image-action').focus();
      await page.keyboard.press('Enter');
      await page.locator('#explainer-modal.open').waitFor();
      assert.match(await page.locator('#explainer-modal-img').getAttribute('src'),/taishou-v2/);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#explainer-modal.open').count(),0);
      assert.equal((await page.evaluate(()=>window.ConsumptionTaxMap.getState())).issueId,id('scope'));
      await page.locator('#btn-'+id('business-burden')).focus();
      await page.keyboard.press('Enter');
      assert.equal((await page.evaluate(()=>window.ConsumptionTaxMap.getState())).issueId,id('business-burden'));
      // 長い資料名を開き、scrollWidthだけでなく文字の実座標を確認する。
      await page.locator('#panel details').evaluateAll(els=>els.forEach(el=>{if(!el.matches('.tax-embed'))el.open=true;}));
      const clipped=await page.locator('#panel a, #panel summary, #panel p').evaluateAll(els=>els.filter(el=>el.getClientRects().length && (el.getBoundingClientRect().left < -1 || el.getBoundingClientRect().right > innerWidth+1)).map(el=>el.textContent.slice(0,40)));
      assert.deepEqual(clipped,[],'長い出典等のはみ出し');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      const order=await page.evaluate(()=>({chart:document.querySelector('.chart-box').getBoundingClientRect().top,list:document.querySelector('#list').getBoundingClientRect().top,panel:document.querySelector('#panel').getBoundingClientRect().top}));
      assert.ok(order.chart<order.list && order.list<order.panel,'山→論点選択→本文の順');
      await page.locator('#btn-'+id('scope')).click();
      if(process.env.TAX_SCREENSHOT_DIR){
        fs.mkdirSync(process.env.TAX_SCREENSHOT_DIR,{recursive:true});
        await page.locator('#modes').scrollIntoViewIfNeeded();
        await page.screenshot({path:path.join(process.env.TAX_SCREENSHOT_DIR,'stage3-'+width+'.png')});
        await page.locator('#panel').screenshot({path:path.join(process.env.TAX_SCREENSHOT_DIR,'reading-'+width+'.png')});
      }
      assert.equal(await page.locator('#vote-result').isVisible(),false);
      assert.deepEqual(await page.evaluate(()=>window.__taxTestEvents.filter(x=>x[0]==='event')),[]);
      assert.deepEqual(errors,[]);
      results.push({width,combinations:35,firstThreeIssues:true,sourceBounds:true,keyboardAndImage:true});
      await context.close();
    }
    // 通常の動きで中間形が存在し、連打後は最後の選択へ収束する。
    {
      const {context,page,errors}=await contextFor(browser,{reducedMotion:'no-preference'});
      await load(page);
      const data=await page.evaluate(()=>window.PLANET_DATA);
      const hill=()=>page.locator('#section .hill[data-i="1"] > path').getAttribute('d');
      const start=await hill();
      await page.evaluate(()=>window.ConsumptionTaxMap.selectStance('consumption-tax-cut-conditional'));
      await page.waitForTimeout(220);
      const middle=await hill();
      await page.waitForTimeout(400);
      const end=await hill();
      assert.notEqual(start,middle); assert.notEqual(middle,end);
      await page.evaluate(()=>{ for(const s of ['support','neutral','conditional','cautious'])window.ConsumptionTaxMap.selectStance('consumption-tax-cut-'+s); });
      await page.waitForTimeout(550);
      assert.equal((await page.evaluate(()=>window.ConsumptionTaxMap.getState())).stanceId,id('cautious'));
      const settled=await hill(); await page.waitForTimeout(80); assert.equal(await hill(),settled);
      // 予想は全体の数字を使い、山への移動は明示操作にする。
      await page.locator('.tax-guesses > summary').click();
      await page.locator('[data-k="g1"] [data-i="0"]').click();
      const orderedStances=data.stances.slice().sort((a,b)=>b.count-a.count);
      assert.match(await page.locator('[data-k="g1"] .gans').innerText(),new RegExp(orderedStances[0].count.toLocaleString('ja-JP')+'件'));
      await page.locator('[data-k="g2"] [data-i="2"]').click();
      const peak=data.issues.filter(issue=>issue.count>0).sort((a,b)=>b.intensity.high/b.count-a.intensity.high/a.count)[0];
      const peakRate=(100*peak.intensity.high/peak.count).toFixed(1);
      assert.match(await page.locator('[data-k="g2"] .gans').innerText(),new RegExp(peak.count.toLocaleString('ja-JP')+'件中'+peak.intensity.high.toLocaleString('ja-JP')+'件、'+peakRate+'%'));
      await page.locator('[data-k="g2"] .tax-answer-link').click();
      assert.deepEqual(await page.evaluate(()=>window.ConsumptionTaxMap.getState()),{stanceId:'all',issueId:id('scope')});
      assert.deepEqual(errors,[]); await context.close();
      results.push({animatedIntermediateFrame:true,rapidSwitchSettles:true,guesses:true});
    }
    for(const prefix of ['#','#issue-','#fb-']){
      const {context,page}=await contextFor(browser); await load(page,prefix+id('finance-welfare'));
      assert.equal((await page.evaluate(()=>window.ConsumptionTaxMap.getState())).issueId,id('finance-welfare'));
      await context.close();
    }
    // 選択中の立場が0件の検証入力。論点・資料は消さず割合は算出しない。
    {
      const {context,page,errors}=await contextFor(browser,{},data=>{
        const m=data.modes.find(m=>m.id==='中立・情報'), iid=id('business-burden');
        m.total-=m.counts[iid]; m.counts[iid]=0; m.high_counts[iid]=0; m.high_pct[iid]=0; m.width_pct[iid]=0;
        return data;
      });
      await load(page);
      await page.evaluate(()=>{window.ConsumptionTaxMap.selectIssue('consumption-tax-cut-business-burden');window.ConsumptionTaxMap.selectStance('consumption-tax-cut-neutral');});
      assert.equal(await page.locator('[data-tax-count]').innerText(),'0件');
      assert.equal(await page.locator('[data-tax-zero]').isVisible(),true);
      assert.match(await page.locator('[data-tax-ratio]').innerText(),/強い表現の割合 算出できません/);
      assert.equal(await page.locator('#panel [data-tax-source-only]').count(),3);
      assert.deepEqual(errors,[]); await context.close();
    }
    {
      const {context,page}=await contextFor(browser,{javaScriptEnabled:false,viewport:{width:375,height:900}});
      await page.goto(url,{waitUntil:'networkidle'});
      assert.equal(await page.locator('[id^="fb-consumption-tax-cut-"]').count(),7);
      assert.equal(await page.locator('#claim-audit [data-claim-id]').count(),6);
      assert.equal(await page.locator('#issue-cards .twitter-tweet').count(),14);
      assert.equal(await page.locator('#fb-'+id('scope')).isVisible(),true);
      assert.equal(await page.locator('#claim-audit').isVisible(),true);
      assert.equal(await page.locator('#issue-cards').isVisible(),true);
      await context.close();
    }
    results.push({initialLinks:3,zeroCount:true,javascriptDisabled:true});
    // 同数・同率の入力では、等しい答えを誤答扱いしない。
    {
      const {context,page,errors}=await contextFor(browser,{},data=>{
        const support=data.stances.find(s=>s.id===id('support'));
        data.stances.find(s=>s.id===id('cautious')).count=support.count;
        for(const suffix of ['scope','political-trust']) {
          const issue=data.issues.find(i=>i.id===id(suffix)); issue.intensity.high=issue.count;
        }
        return data;
      });
      await load(page); await page.locator('.tax-guesses > summary').click();
      await page.locator('[data-k="g1"] [data-i="2"]').click();
      assert.match(await page.locator('[data-k="g1"] .gans').innerText(),/同じ件数でした/);
      await page.locator('[data-k="g2"] [data-i="1"]').click();
      assert.equal(await page.locator('[data-k="g2"] .gopts .hit').count(),2);
      assert.deepEqual(errors,[]); await context.close();
      results.push({equalCountsAndTiedRatios:true});
    }
    console.log(JSON.stringify(results,null,2));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
