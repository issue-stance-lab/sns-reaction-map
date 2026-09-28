const {chromium}=require('playwright');
const assert=require('node:assert/strict');

const url=process.env.CONSTITUTIONAL_LAYOUT_URL;
if(!url || !['127.0.0.1','localhost'].includes(new URL(url).hostname)){
  throw new Error('ローカル候補のURLが必要です（CONSTITUTIONAL_LAYOUT_URL）');
}

(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    for(const width of [375,820,1280,1600]){
      const context=await browser.newContext({viewport:{width,height:900}});
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',error=>errors.push(error.message));
      await page.route('**/*',route=>{
        const target=new URL(route.request().url());
        return target.origin===new URL(url).origin ? route.continue() : route.abort();
      });
      await page.goto(url,{waitUntil:'networkidle'});
      await page.locator('.ca-status').waitFor();
      const result=await page.evaluate(()=>{
        const rect=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return{x:r.x,width:r.width,right:r.right};};
        return {
          entry:rect('#change-lens'),
          status:rect('.ca-status'),
          planet:rect('.planet-panel'),
          viewport:document.documentElement.clientWidth,
          scrollWidth:document.documentElement.scrollWidth,
        };
      });
      for(const target of [result.entry,result.status]){
        assert.ok(Math.abs(target.x-result.planet.x)<1,`${width}px: 左端がSNS反応マップとずれています ${JSON.stringify(result)}`);
        assert.ok(Math.abs(target.width-result.planet.width)<1,`${width}px: 幅がSNS反応マップとずれています ${JSON.stringify(result)}`);
      }
      assert.ok(result.scrollWidth<=result.viewport+1,`${width}px: 横スクロールが発生しています`);
      assert.deepEqual(errors,[],`${width}px: JavaScriptエラー`);

      await page.locator('#change-lens-tabs').scrollIntoViewIfNeeded();
      for(const tab of ['article9','emergency','referendum','reasons']){
        await page.locator(`[data-lens-tab="${tab}"]`).scrollIntoViewIfNeeded();
        const before=await page.evaluate(()=>({x:scrollX,y:scrollY}));
        await page.locator(`[data-lens-tab="${tab}"]`).click();
        await page.waitForTimeout(450);
        const after=await page.evaluate(()=>({x:scrollX,y:scrollY}));
        assert.deepEqual(after,before,`${width}px: ${tab}タブで画面位置が動きました`);
        await page.locator(`[data-lens-panel="${tab}"]`).waitFor({state:'visible'});
      }
      await context.close();
    }
    console.log('OK: 375/820/1280/1600pxで幅が一致し、4タブの切替で画面位置が動かない');
  } finally {
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
