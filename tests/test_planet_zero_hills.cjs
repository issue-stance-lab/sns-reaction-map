/* 実ブラウザーで高さ0の山を押す回帰検査。
 * NODE_PATH に Playwright のある node_modules、PLANET_PREVIEW_URL にローカル見本を指定。
 * 外部通信は遮断し、実票やアクセス計測を送信しない。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({headless:true});
  const results=[];
  try {
    for(const width of [375,1440]){
      const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
      const page=await context.newPage(), errors=[];
      page.on('pageerror', e=>errors.push(e.message));
      await page.route('https://**/*',route=>route.abort());
      await page.goto(process.env.PLANET_PREVIEW_URL || 'http://127.0.0.1:8766/quality/prototypes/school-nickname-ban-page-preview.html',{waitUntil:'networkidle'});
      await page.evaluate(()=>localStorage.clear());
      await page.reload({waitUntil:'networkidle'});
      const count=await page.locator('#planet-block .hill').count();
      const zeroResults=[];
      for(let i=0;i<count;i++){
        await page.locator('#planet-block .chart-box').evaluate(e=>e.scrollIntoView({block:'center',behavior:'instant'}));
        const point=await page.locator('#planet-block .hill').nth(i).evaluate(e=>{
          const p=e.querySelector('path').getBoundingClientRect();
          const x=p.x+p.width/2,y=p.y+p.height/2;
          return {x,y,height:p.height,label:e.getAttribute('aria-label'),isZero:/強い表現0\.0%/.test(e.getAttribute('aria-label'))};
        });
        // force/dispatchEventではなく実際のポインターで山の位置を押す。
        await page.mouse.click(point.x,point.y);
        assert.equal(parseInt(await page.locator('#pnum').innerText(),10),i+1,point.label);
        if(point.isZero){assert.equal(point.height,0,'表示する高さは水増ししない');zeroResults.push(point.label)}
      }
      assert.ok(zeroResults.length>0,'高さ0の論点を含む見本で検査する');
      assert.deepEqual(errors,[]);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      results.push({width,allHillsClicked:count,zeroResults,errors});
      await context.close();
    }
    console.log(JSON.stringify(results,null,2));
  } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
