/* 生成AIテーマの制度確認帯とSNS反応マップの配置回帰検査。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const url=process.env.AI_COPYRIGHT_CONNECTED_URL;
if(!url || !['127.0.0.1','localhost'].includes(new URL(url).hostname))throw new Error('ローカル候補のURLが必要です（AI_COPYRIGHT_CONNECTED_URL）');

(async()=>{
  const browser=await chromium.launch({headless:true});
  const summary=[];
  try{
    for(const width of [320,375,1280]){
      const context=await browser.newContext({viewport:{width,height:800}});
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',error=>errors.push(error.message));
      await page.route('**/*',async route=>{
        const target=new URL(route.request().url());
        if(target.origin===new URL(url).origin)return route.continue();
        return route.abort();
      });
      await page.goto(url,{waitUntil:'networkidle'});
      await page.locator('.aic-status').waitFor();
      const result=await page.evaluate(()=>{
        const status=document.querySelector('.aic-status')?.getBoundingClientRect();
        const panel=document.querySelector('.planet-panel')?.getBoundingClientRect();
        return {
          status:status&&{x:status.x,width:status.width},
          panel:panel&&{x:panel.x,width:panel.width},
          scrollWidth:document.documentElement.scrollWidth,
          clientWidth:document.documentElement.clientWidth,
        };
      });
      assert.ok(result.status&&result.panel,'制度の確認時点帯またはSNS反応マップが見つからない');
      assert.ok(Math.abs(result.status.x-result.panel.x)<0.5,`width=${width}: 制度の確認時点帯の左端がSNS反応マップとずれている`);
      assert.ok(Math.abs(result.status.width-result.panel.width)<0.5,`width=${width}: 制度の確認時点帯の幅がSNS反応マップとずれている`);
      assert.ok(result.scrollWidth<=result.clientWidth+2,`width=${width}: 横スクロールが発生`);
      assert.deepEqual(errors,[],`width=${width}: コンソールエラー`);
      summary.push({width,bandAlignment:true,overflow:0});
      await context.close();
    }
    console.log(JSON.stringify(summary,null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
