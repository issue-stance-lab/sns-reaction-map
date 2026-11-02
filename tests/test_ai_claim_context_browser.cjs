/* 未公開のローカル候補だけで、6主張の表示・出典・スマホのはみ出しを確認する。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const url=process.env.AI_CLAIM_CANDIDATE_URL;
const out=process.env.AI_CLAIM_SCREENSHOT_DIR;
if(!url||!['localhost','127.0.0.1'].includes(new URL(url).hostname))throw Error('ローカル候補URLが必要です');
const expected={unauthorized_learning_infringement:8,data_disclosure_needed:0,compensation_required:0,creator_protection_insufficient:0,ai_output_has_copyright:6,tech_innovation_over_regulation:86};
(async()=>{
 const browser=await chromium.launch({headless:true});const results=[];
 try{
  for(const width of [320,375,1280]){
   const context=await browser.newContext({viewport:{width,height:812},reducedMotion:'reduce'});
   const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',route=>new URL(route.request().url()).origin===new URL(url).origin?route.continue():route.abort());
   await page.goto(url,{waitUntil:'networkidle'});
   const data=await page.evaluate(()=>window.PLANET_DATA);
   assert.equal(data.totals.opinions,3975);
   for(const claim of data.claims){
    const id=claim.id;
    assert.equal(claim.matched_post_count,expected[id]);
    const owner=data.issues.find(i=>i.claims.some(c=>c.id===id));
    await page.locator(`.fr-tab[data-issue-id="${owner.id}"]:visible`).first().click();
    const node=page.locator(`.fr-panel[data-selected] .fr-claim[data-claim="${id}"]`);
    await node.locator(':scope > summary').click();
    const text=await node.innerText();
    assert.ok(text.includes(`${expected[id]}件`),id);
    assert.ok(text.includes(claim.source_summary)&&text.includes(claim.finding),id);
    if(expected[id]===0)assert.ok(text.includes('直接の表明は見つかりませんでした'),id);
    if(claim.verdict===null){
     assert.equal(await node.locator('.fr-verdict').innerText(),id==='ai_output_has_copyright'?'条件を確認':'評価の論点');
     assert.equal(await node.evaluate(n=>n.classList.contains('fr-verdict-gap')),false);
    }
    await node.locator('.fr-sources > summary').click();
    for(const source of claim.sources){
     const link=node.locator(`a[href="${source.url}"]`);assert.equal(await link.count(),1);assert.ok(await link.isVisible());
    }
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),`overflow ${width}/${id}`);
    if(out&&width===375&&['ai_output_has_copyright','tech_innovation_over_regulation'].includes(id)){
     fs.mkdirSync(out,{recursive:true});await node.scrollIntoViewIfNeeded();await page.screenshot({path:`${out}/${id}-375.png`});
    }
   }
   assert.deepEqual(errors,[]);results.push({width,claims:6,counts:true,explanations:true,sourceLinks:true,overflow:0,pageErrors:0});
   await context.close();
  }
  const context=await browser.newContext({viewport:{width:375,height:812},javaScriptEnabled:false});
  const page=await context.newPage();await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(url).origin?r.continue():r.abort());
  await page.goto(url,{waitUntil:'networkidle'});
  assert.equal(await page.locator('.fr-panel[data-issue-panel]').count(),7);
  for(const id of Object.keys(expected))assert.ok(await page.locator(`.fr-claim[data-claim="${id}"]`).count()>0);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
  results.push({javascript:false,claims:6,panels:7,overflow:0});
  await context.close();console.log(JSON.stringify(results,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
