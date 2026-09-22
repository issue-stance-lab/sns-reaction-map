/* 工程5: キーボード・初期化失敗・投票の異常系と共通の参加者数表示。外部通信は全置換。 */
const {chromium,webkit}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const url=process.env.TAX_CONNECTED_URL;
if(!url||!['127.0.0.1','localhost'].includes(new URL(url).hostname))throw Error('ローカル候補URLが必要です');
const origin=new URL(url).origin,id=s=>'consumption-tax-cut-'+s;
const storage='sns_vote_consumption-tax-cut-issue-stance-v1_my';
const results=[];
async function open(browser,{fault=false,blocked=null}={}){
  const context=await browser.newContext({viewport:{width:1280,height:1500},reducedMotion:'reduce'});
  const page=await context.newPage(),errors=[],sent=[];
  const api={fail:false};
  await page.addInitScript(()=>{window.gtag=()=>{};window.__alerts=[];window.alert=t=>window.__alerts.push(t);});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const request=route.request(),target=new URL(request.url());
    if(target.origin===origin){
      if(blocked&&target.pathname.endsWith('/'+blocked))return route.abort();
      if(request.isNavigationRequest()){
        const response=await route.fetch(),headers={...response.headers()};delete headers['content-security-policy'];
        let body=await response.text();
        if(fault)body=body.replace('const D = window.PLANET_DATA;','throw new Error("quality: simulated map failure"); const D = window.PLANET_DATA;');
        return route.fulfill({response,headers,body});
      }
      return route.continue();
    }
    if(target.pathname==='/functions/v1/cast-vote'){
      if(request.method()==='POST')sent.push(request.postDataJSON());
      return route.fulfill({status:api.fail?500:200,contentType:'application/json',
        headers:{'access-control-allow-origin':'*','access-control-allow-methods':'GET,POST,OPTIONS','access-control-allow-headers':'*'},
        body:JSON.stringify(api.fail?{error:'test_failure'}:{accepted:true,duplicate:false,counts:{14:4}})});
    }
    return route.abort();
  });
  await page.goto(url,{waitUntil:'networkidle'});
  return {context,page,errors,sent,api};
}
async function enter(page,selector){await page.locator(selector).focus();await page.keyboard.press('Enter');}
const focused=(page,selector)=>page.evaluate(s=>document.activeElement.matches(s),selector);
(async()=>{
  for(const [engine,type] of Object.entries({chromium,webkit})){
    const browser=await type.launch();
    try{
      {
        const {context,page,errors,sent,api}=await open(browser);
        await enter(page,'[data-tax-quiz]');
        for(const claim of await page.evaluate(()=>PLANET_DATA.claims)){
          assert.equal(await focused(page,'#quiz .qh'),true);
          await enter(page,'#quiz [data-verdict="'+claim.verdict+'"]');
          assert.equal(await focused(page,'#quiz .qans'),true);
          await enter(page,'#quiz .qnext');
        }
        assert.equal(await focused(page,'#quiz h3'),true,'結果が画面内でも見出しへ焦点を移す');
        await enter(page,'[data-tax-finish]');
        assert.equal(await focused(page,'[data-tax-read]'),true,'隠れるクイズから資料の操作へ戻す');
        await enter(page,'[data-vote-issue="'+id('finance-welfare')+'"]');
        assert.equal(await focused(page,'[data-vote-stance]'),true);
        api.fail=true;
        const stance='[data-vote-stance="'+id('cautious')+'"]';
        await enter(page,stance);
        await page.waitForFunction(()=>window.__alerts.length===1);
        assert.equal(await page.locator('#vote-result').isVisible(),false);
        assert.equal(await page.locator('#vote-stance-btns [disabled]').count(),0);
        assert.equal(await focused(page,stance),true,'送信失敗後に再操作できる');
        assert.equal(await page.evaluate(key=>localStorage.getItem(key),storage),null);
        api.fail=false;await enter(page,stance);
        await page.waitForFunction(()=>document.activeElement.id==='vote-position-label');
        assert.equal(sent.length,2);assert.equal(sent.at(-1).choice_idx,14);
        assert.equal(sent.at(-1).topic_id,'consumption-tax-cut-issue-stance-v1');
        await page.locator('#vote-result[data-participant-count-loaded="true"]').waitFor();
        await page.waitForTimeout(100);
        assert.match(await page.locator('.participant-vote-summary').innerText(),/n=4（/);
        assert.deepEqual(await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),storage),{issueIdx:3,stanceIdx:2});
        await page.reload({waitUntil:'networkidle'});
        assert.equal(await focused(page,'#vote-position-label'),false,'保存済み投票を戻すだけでは焦点を奪わない');
        assert.equal(sent.length,2);assert.deepEqual(errors,[]);
        await context.close();results.push({engine,keyboardQuiz:6,keyboardVote:true,voteFailureRetry:true,participantCount:4});
      }
      for(const scenario of [{fault:true},{blocked:'consumption-tax-connected.js'},{blocked:'consumption-tax-connected-page.js'}]){
        const {context,page,errors}=await open(browser,scenario);
        if(scenario.fault){
          assert.equal(await page.locator('#fallback').isVisible(),true);
          assert.equal(await page.locator('#planet-block .stage').isVisible(),false);
          for(const element of await page.locator('[id^="fb-consumption-tax-cut-"]').all())assert.equal(await element.isVisible(),true);
          assert.equal(await page.locator('#claim-audit [data-claim-id]').count(),6);
          assert.equal(await page.locator('#issue-cards .twitter-tweet').count(),14);
          assert.deepEqual(errors,['quality: simulated map failure']);
        }else{
          assert.deepEqual(errors,[]);
          for(const button of await page.locator('#list button').all()){
            await button.click();assert.ok((await page.locator('#panel').innerText()).length>30);
          }
        }
        await context.close();
      }
      results.push({engine,failedInitializationShowsAllIssues:true,partialScriptFailures:2});
      if(engine==='chromium'){
        // 共通JSの修正が各テーマの結果欄で動くこと。投票送信はせず、完了表示を検証入力にする。
        const {context,page,sent}=await open(browser);
        const docs=path.resolve(__dirname,'../docs');
        const pages=fs.readdirSync(docs).filter(name=>name.endsWith('-reaction-map.html'));
        for(const name of pages){
          await page.goto(origin+'/'+name,{waitUntil:'networkidle'});
          await page.evaluate(()=>{
            const result=document.getElementById('vote-result');result.hidden=false;result.style.display='block';
            result.innerHTML='<div><div id="vote-position-label">検証用の投票結果</div><p id="vote-position-text">表示検査</p></div>';
          });
          await page.waitForFunction(()=>document.querySelector('.participant-vote-summary')?.textContent.includes('n=4（'));
          // 後から結果説明が更新されても取得済みの人数を消さない。
          await page.locator('#vote-position-text').evaluate(el=>{el.textContent='表示検査の追記';});
          await page.waitForTimeout(100);
          assert.match(await page.locator('.participant-vote-summary').innerText(),/n=4（/,name);
        }
        assert.deepEqual(sent,[]);await context.close();results.push({commonParticipantCountThemes:pages.length,realVotesSent:0});
      }
    }finally{await browser.close();}
  }
  console.log(JSON.stringify(results,null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
