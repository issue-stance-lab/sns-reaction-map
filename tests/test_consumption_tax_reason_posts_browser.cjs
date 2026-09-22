/* 理由と投稿の対応・クリック時だけの読込・遅延/失敗・小画面をローカル候補で確認する。 */
const {chromium,webkit}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const url=process.env.TAX_CONNECTED_URL;
if(!url||!['127.0.0.1','localhost'].includes(new URL(url).hostname))throw Error('ローカル候補URLが必要です');
const selected=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../configs/consumption-tax-reason-posts.json'))).issues;
const results=[];
async function open(browser,width,{mock=true}={}){
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/*',route=>new URL(route.request().url()).origin===new URL(url).origin?route.continue():route.abort());
  await page.addInitScript(mock=>{
    window.__events=[];window.__loads=[];window.gtag=(...args)=>window.__events.push(args);
    window.__widget=()=>({widgets:{load(holder){
      window.__loads.push(holder.querySelector('a').href);
      const tweet=holder.querySelector('.twitter-tweet');
      const card=Object.assign(document.createElement('div'),{className:'test-x-card',textContent:'X投稿カードのテスト応答'});
      card.style.minWidth='250px';tweet.replaceWith(card);
      return Promise.resolve();
    }}});
    if(mock)window.twttr=window.__widget();
  },mock);
  await page.goto(url,{waitUntil:'networkidle'});
  await page.locator('body.tax-connected').waitFor();
  return {context,page,errors};
}
(async()=>{
  for(const [engine,type] of Object.entries({chromium,webkit})){
    const browser=await type.launch();
    try{
      for(const width of [1280,375,320]){
        const {context,page,errors}=await open(browser,width);
        assert.deepEqual(await page.evaluate(()=>__loads),[],'初期表示で理由の投稿を読み込まない');
        let opened=0;
        for(const [iid,reasons] of Object.entries(selected)){
          await page.evaluate(iid=>ConsumptionTaxMap.selectIssue(iid),iid);
          const progress=await page.locator('#progress').innerText();
          const more=page.locator('.tax-more-reasons');
          if(await more.count())await more.locator('summary').first().click();
          assert.equal((await page.evaluate(()=>__loads)).length,opened,'理由一覧を増やすだけでは読込しない');
          for(const [bid,ids] of Object.entries(reasons)){
            const detail=page.locator('#panel [data-tax-reason-posts="'+bid+'"]');
            const summary=detail.locator('summary');
            await summary.focus();await page.keyboard.press('Enter');
            await page.waitForFunction(n=>__loads.length===n,++opened);
            assert.equal(await detail.getAttribute('open'),'');
            const links=await detail.locator('article > a').evaluateAll(nodes=>nodes.map(n=>n.href));
            assert.deepEqual(links.map(link=>link.split('/').at(-1)),ids);
            assert.ok((await detail.locator('.tax-reason-post-summary').innerText()).length>10);
            assert.equal(await detail.locator('.test-x-card').count(),ids.length);
            assert.equal(await detail.locator('.tax-reason-embed').evaluate(holder=>holder.clientWidth>=250),true,'公式カードの最小幅を確保する');
            assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
            const outside=await detail.locator('summary,p,a').evaluateAll(nodes=>nodes.filter(n=>n.getClientRects().length&&(n.getBoundingClientRect().left<0||n.getBoundingClientRect().right>innerWidth+1)).map(n=>n.textContent));
            assert.deepEqual(outside,[]);
            await page.keyboard.press('Enter');assert.equal(await detail.getAttribute('open'),null);
            await page.keyboard.press('Enter');assert.equal(await detail.getAttribute('open'),'');
            assert.equal((await page.evaluate(()=>__loads)).length,opened,'開き直しても外部カードを作り直さない');
            await page.keyboard.press('Enter');
          }
          assert.equal(await page.locator('#progress').innerText(),progress,'投稿例は既存の読了数へ加算しない');
        }
        assert.equal(opened,25);
        const events=await page.evaluate(()=>__events.filter(e=>e[0]==='event'&&e[1]==='reason_post_open'));
        assert.equal(events.length,25);
        assert.ok(events.every(e=>JSON.stringify(e[2])==='{"topic_id":"consumption-tax-cut"}'),'閲覧した理由や立場を送らない');
        await page.evaluate(()=>ConsumptionTaxMap.selectIssue('consumption-tax-cut-effect'));
        const detail=page.locator('#panel [data-tax-reason-posts="A"]');
        await detail.locator('summary').click();
        await page.evaluate(()=>ConsumptionTaxMap.selectStance('consumption-tax-cut-conditional'));
        assert.equal(await detail.getAttribute('open'),'','立場切替で開閉状態を保つ');
        assert.equal((await page.evaluate(()=>__loads)).length,25);
        await page.evaluate(()=>{window.dispatchEvent(new Event('beforeprint'));window.dispatchEvent(new Event('afterprint'));});
        assert.equal((await page.evaluate(()=>__loads)).length,25,'印刷で非選択の投稿を読み込まない');
        assert.deepEqual(errors,[]);
        await context.close();results.push({engine,width,reasons:opened,lazyLoad:true,keyboard:true,noOverflow:true});
      }
      {
        const {context,page,errors}=await open(browser,375,{mock:false});
        const reason=page.locator('#panel [data-tax-reason-posts="A"]');
        await reason.locator('summary').click();
        assert.equal(await reason.locator('article > a').isVisible(),true,'Xが読めなくても元投稿へ進める');
        assert.equal(await reason.locator('.tax-reason-post-summary').isVisible(),true);
        assert.deepEqual(await page.evaluate(()=>__loads),[]);
        assert.equal(await reason.locator('blockquote.twitter-tweet').count(),0,'API到着前は自動走査の対象に出さない');
        assert.equal(await reason.locator('template.tax-reason-embed-template').count(),1);
        await page.evaluate(()=>{window.twttr=window.__widget();document.querySelector('script[src="https://platform.twitter.com/widgets.js"]').dispatchEvent(new Event('load'));});
        await page.waitForFunction(()=>__loads.length===1);
        assert.equal(await reason.locator('.test-x-card').count(),1,'遅れて届いたXも表示する');
        assert.deepEqual(errors,[]);
        await context.close();results.push({engine,blockedEmbedFallback:true,lateWidgetReady:true});
      }
      for(const failure of ['empty','reject','throw']){
        const {context,page,errors}=await open(browser,375,{mock:false});
        await page.evaluate(mode=>{
          const good=window.__widget();let attempt=0;
          window.twttr={widgets:{load(holder){
            if(attempt++===0){
              __loads.push('failed');
              const original=holder.querySelector('blockquote');
              original.classList.add('twitter-tweet-error');original.setAttribute('data-twitter-extracted-test','true');
              if(mode==='throw')throw Error('test failure');
              if(mode==='reject')return Promise.reject(Error('test failure'));
              return Promise.resolve([]);
            }
            if(holder.querySelector('[data-twitter-extracted-test]'))throw Error('processed element was reused');
            return good.widgets.load(holder);
          }}};
        },failure);
        const reason=page.locator('#panel [data-tax-reason-posts="A"]');
        await reason.locator('summary').click();
        await page.waitForFunction(()=>__loads.length===1&&!document.querySelector('[data-tax-widget-requested]'));
        await reason.locator('summary').click();await reason.locator('summary').click();
        await page.waitForFunction(()=>__loads.length===2);
        assert.equal(await reason.locator('.test-x-card').count(),1);
        assert.deepEqual(errors,[]);
        await context.close();results.push({engine,retryAfter:failure});
      }
      for(const autoResult of ['success','error']){
        const {context,page,errors}=await open(browser,375,{mock:false});
        await page.evaluate(result=>{
          const good=window.__widget();let attempt=0;
          window.__autoFinished=false;window.__detachedSource=false;
          window.twttr={widgets:{load(holder){
            if(attempt++>0)return good.widgets.load(holder);
            __loads.push('manual-empty');
            const source=holder.querySelector('blockquote');
            // 公式の自動走査が先に取得し、手動走査は対象0件で完了する順序。
            source.setAttribute('data-twitter-extracted-test','true');
            setTimeout(()=>{
              window.__detachedSource=!source.isConnected;
              if(result==='error')source.classList.add('twitter-tweet-error');
              else source.replaceWith(Object.assign(document.createElement('div'),{className:'test-x-card',textContent:'自動走査の完了'}));
              window.__autoFinished=true;
            },100);
            return Promise.resolve();
          }}};
        },autoResult);
        const reason=page.locator('#panel [data-tax-reason-posts="A"]');
        await reason.locator('summary').click();
        await page.waitForFunction(()=>__autoFinished);
        assert.equal(await page.evaluate(()=>__detachedSource),false,'自動走査の描画先を途中で破棄しない');
        if(autoResult==='error'){
          await reason.locator('summary').click();await reason.locator('summary').click();
          await page.waitForFunction(()=>__loads.length===2);
        }
        assert.equal(await reason.locator('.test-x-card').count(),1);
        assert.deepEqual(errors,[]);
        await context.close();results.push({engine,concurrentAutoScan:autoResult});
      }
    }finally{await browser.close();}
  }
  console.log(JSON.stringify(results,null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
