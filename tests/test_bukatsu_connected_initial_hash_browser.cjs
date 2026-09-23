/* オーナー報告2026-09-23: hash付きURL（前回訪問した論点をブラウザが覚えている再訪問等）で
   開くと、読書面のtemplateがまだパースされる前に既存init（PLANET_SECTION末尾の同期処理）が
   land()を呼んでしまい、drawPanel()が旧描画（升目100個の待避図等）へ一度だけ後退したまま
   固定される不具合があった（論点を押すまで直らない）。document.getElementByIdを差し替えて
   「templateがまだ無い」状況を確実に再現し、bridge.jsのinitialLand()が
   DOMContentLoaded後に読書面の描画状態を確かめて補正することを確認する。
   本番への通信は行わない（同一オリジンのみ許可）。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const url=process.env.BUKATSU_CONNECTED_URL;
if(!url || !['127.0.0.1','localhost'].includes(new URL(url).hostname))throw new Error('ローカル候補のURLが必要です（BUKATSU_CONNECTED_URL）');

(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    const context=await browser.newContext();
    const page=await context.newPage();
    await page.route('**/*',async route=>{
      const target=new URL(route.request().url());
      if(target.origin===new URL(url).origin)return route.continue();
      return route.abort();
    });
    // 最初のbukatsu-reading-*問い合わせだけnullにして「templateが未パース」を再現する。
    await page.addInitScript(()=>{
      const real=Document.prototype.getElementById;
      let blocked=0;
      Document.prototype.getElementById=function(id){
        if(typeof id==='string' && id.indexOf('bukatsu-reading-')===0 && blocked<1){blocked++;return null;}
        return real.call(this,id);
      };
    });
    const target=new URL(url); target.hash='bukatsu-chiiki-kyoin';
    await page.goto(target.href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>!!document.querySelector('.bkt-selected-head'),{timeout:5000});
    const result=await page.evaluate(()=>({
      hasSelectedHead:!!document.querySelector('.bkt-selected-head'),
      hasEvidence:!!document.querySelector('.bkt-evidence'),
      dotboxInDocument:!!document.getElementById('dotbox'),
      state:window.BukatsuConnectedMap.getState(),
    }));
    assert.equal(result.hasSelectedHead, true, '読書面（.bkt-selected-head）が描けていません（旧描画のまま固定）');
    assert.equal(result.hasEvidence, true, '資料欄（.bkt-evidence）が描けていません');
    assert.equal(result.dotboxInDocument, false, '旧の升目100個（#dotbox）が残っています');
    assert.deepEqual(result.state, {stanceId:'all', issueId:'bukatsu-chiiki-kyoin'});
    console.log('OK  hash付きURLでtemplate未パースの競合が起きても読書面へ補正される');
  } finally {
    await browser.close();
  }
})().catch(error=>{ console.error('NG', error.message); process.exitCode=1; });
