/* 工程5: 表示・操作まわりの回帰検査。本番への通信は行わない（同一オリジンのみ許可）。
   320/375/PC幅での横はみ出し、動きを減らす設定でのアニメーション省略、キーボード操作、
   立場切替アニメーション中のフォーカス維持、未再読論点の空状態表示を確認する。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const url=process.env.BUKATSU_CONNECTED_URL;
if(!url || !['127.0.0.1','localhost'].includes(new URL(url).hostname))throw new Error('ローカル候補のURLが必要です（BUKATSU_CONNECTED_URL）');

async function open(browser,opts={}){
  const context=await browser.newContext({viewport:{width:1280,height:950},...opts});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/*',async route=>{
    const req=route.request(),target=new URL(req.url());
    if(target.origin===new URL(url).origin)return route.continue();
    return route.abort();
  });
  await page.goto(url,{waitUntil:'networkidle'});await page.locator('#panel h2').waitFor();
  return {context,page,errors};
}

(async()=>{
  const browser=await chromium.launch({headless:true});
  const summary=[];
  try{
    // 320/375/PC幅で、全論点×全立場（7×5=35通り）を一巡し横はみ出しが無いことを確認。
    for(const width of [320,375,1280]){
      const {context,page,errors}=await open(browser,{viewport:{width,height:800}});
      const issueIds=await page.evaluate(()=>window.PLANET_DATA.issues.map(i=>i.id));
      const stanceIds=await page.evaluate(()=>window.PLANET_DATA.stances.map(s=>s.id).concat(['all']));
      const overflow=[];
      for(const sid of stanceIds){
        await page.evaluate(id=>window.BukatsuConnectedMap.selectStance(id),sid);
        for(const iid of issueIds){
          await page.evaluate(id=>window.BukatsuConnectedMap.selectIssue(id),iid);
          const sw=await page.evaluate(()=>document.documentElement.scrollWidth);
          const cw=await page.evaluate(()=>document.documentElement.clientWidth);
          if(sw>cw+2)overflow.push({stance:sid,issue:iid,sw,cw});
        }
      }
      assert.deepEqual(overflow,[],`width=${width}: 横はみ出しが発生`);
      assert.deepEqual(errors,[],`width=${width}: コンソールエラー`);
      summary.push({width,combinationsChecked:issueIds.length*stanceIds.length,overflow:0});
      await context.close();
    }
    // 動きを減らす設定: 立場切替が即時反映され、アニメーション用の中間フレームを経由しない。
    {
      const {context,page,errors}=await open(browser,{reducedMotion:'reduce'});
      await page.evaluate(()=>window.BukatsuConnectedMap.selectStance('all'));
      const before=await page.evaluate(()=>{
        const hill=document.querySelector('.hill');
        return {width:hill.getBoundingClientRect().width,id:hill.dataset.i};
      });
      const targetWidthAfterSwitch=await page.evaluate(()=>{
        window.BukatsuConnectedMap.selectStance('bukatsu-chiiki-transition-support');
        const hill=document.querySelector('.hill');
        return hill.getBoundingClientRect().width;
      });
      // reduce時はbktAnimate内で即座にrender()するため、呼び出し直後(同一tick)で
      // 既に最終形（layout('bukatsu-chiiki-transition-support')相当）になっているはず。
      // 通常motionでは同じ確認をすると最初のフレーム（開始値に近い値）のままになる。
      await page.waitForTimeout(600);
      const afterSettle=await page.evaluate(()=>document.querySelector('.hill').getBoundingClientRect().width);
      assert.ok(Math.abs(targetWidthAfterSwitch-afterSettle)<0.5,'reduce設定なのに呼び出し直後と収束後で幅が違う（アニメーション経由の疑い）');
      summary.push({reducedMotionInstant:true,widthAtCall:targetWidthAfterSwitch,widthAfterSettle:afterSettle});
      await context.close();
    }
    // 通常motion: 切替直後はまだ途中の値で、時間経過後に収束する（アニメーションが実際に動いている確認）。
    {
      const {context,page}=await open(browser);
      await page.evaluate(()=>window.BukatsuConnectedMap.selectStance('all'));
      const immediate=await page.evaluate(()=>{
        window.BukatsuConnectedMap.selectStance('bukatsu-chiiki-transition-support');
        return document.querySelector('.hill').getBoundingClientRect().width;
      });
      await page.waitForTimeout(600);
      const settled=await page.evaluate(()=>document.querySelector('.hill').getBoundingClientRect().width);
      assert.notEqual(immediate,settled,'通常motionなのに切替直後から最終値のまま（アニメーションしていない）');
      summary.push({normalMotionAnimates:true,widthImmediate:immediate,widthSettled:settled});
      await context.close();
    }
    // キーボード操作: 山にフォーカス→Enterで選択、立場切替アニメーション中もフォーカスを失わない。
    {
      const {context,page,errors}=await open(browser);
      await page.evaluate(()=>window.BukatsuConnectedMap.selectIssue(null));
      await page.locator('.hill[data-i="2"]').focus();
      await page.keyboard.press('Enter');
      const landed=await page.evaluate(()=>window.BukatsuConnectedMap.getState().issueId);
      assert.equal(landed,await page.evaluate(()=>window.PLANET_DATA.issues[2].id));
      await page.locator('.hill[data-i="1"]').focus();
      await page.evaluate(()=>window.BukatsuConnectedMap.selectStance('bukatsu-chiiki-transition-support'));
      await page.waitForTimeout(100);
      const focusedMid=await page.evaluate(()=>document.activeElement.dataset.i);
      await page.waitForTimeout(600);
      const focusedAfter=await page.evaluate(()=>document.activeElement.dataset.i);
      assert.equal(focusedMid,'1','アニメーション中にフォーカスが外れた');
      assert.equal(focusedAfter,'1','アニメーション完了後にフォーカスが外れた');
      assert.deepEqual(errors,[]);
      summary.push({keyboardSelect:true,focusRetainedDuringAnimation:true});
      await context.close();
    }
    // 未再読論点（その他・地域格差）は0件・架空の理由を出さず、空状態の断り書きだけを出す。
    {
      const {context,page,errors}=await open(browser);
      for(const iid of ['bukatsu-chiiki-sonota','bukatsu-chiiki-kakusa']){
        await page.evaluate(id=>window.BukatsuConnectedMap.selectIssue(id),iid);
        const text=await page.locator('#panel').innerText();
        assert.ok(/まだ.*読み直していません|未再読|読み直し/.test(text),iid+': 未再読の断り書きが見当たらない');
        assert.equal(/NaN|undefined|Infinity/.test(text),false,iid+': 不正な値が表示されている');
      }
      assert.deepEqual(errors,[]);
      summary.push({unreviewedIssuesHonest:true});
      await context.close();
    }
    console.log(JSON.stringify(summary,null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
