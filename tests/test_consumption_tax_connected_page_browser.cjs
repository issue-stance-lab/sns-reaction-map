/* 工程4の一巡検査。本番への通信は全遮断し、投票APIもテスト応答に置き換える。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');
const url=process.env.TAX_CONNECTED_URL;
if(!url || !['127.0.0.1','localhost'].includes(new URL(url).hostname))throw new Error('ローカル候補のURLが必要です');
const root=path.resolve(__dirname,'..');
const original=JSON.parse(fs.readFileSync(path.join(root,'quality/designs/2026-09-22-task77-consumption-tax-content-contract.json')));
const background=JSON.parse(fs.readFileSync(path.join(root,'configs/consumption-tax-background.json')));
const classroom=JSON.parse(fs.readFileSync(path.join(root,'configs/classroom/consumption-tax-cut.json')));
const out=process.env.TAX_ARTIFACT_DIR||path.join(root,'.staging/task77-connected');fs.mkdirSync(out,{recursive:true});
const id=s=>'consumption-tax-cut-'+s;
const summary=[];
async function open(browser,width=1280,seed=[],transform){
  const context=await browser.newContext({viewport:{width,height:950},reducedMotion:'reduce'});
  await context.addInitScript(seed=>{
    localStorage.setItem('isa-seen-consumption-tax-cut',JSON.stringify(seed));
    window.__events=[];window.gtag=(...args)=>window.__events.push(args);
    window.__copied=[];Object.defineProperty(navigator,'clipboard',{value:{writeText:text=>{window.__copied.push(text);return Promise.resolve();}},configurable:true});
    window.__prints=[];window.print=()=>window.__prints.push(document.body.classList.contains('tax-print-classroom'));
  },seed);
  const page=await context.newPage(),errors=[],requests=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/*',async route=>{
    const req=route.request(),target=new URL(req.url());
    if(target.origin===new URL(url).origin){
      if(req.isNavigationRequest()){
        const response=await route.fetch(),headers={...response.headers()};delete headers['content-security-policy'];
        const body=await response.text();return route.fulfill({response,headers,body:transform?transform(body):body});
      }
      return route.continue();
    }
    if(target.pathname==='/functions/v1/cast-vote'){
      if(req.method()==='POST')requests.push({url:req.url(),body:req.postDataJSON()});
      return route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify({accepted:true,duplicate:false,counts:{}})});
    }
    return route.abort();
  });
  await page.goto(url,{waitUntil:'networkidle'});await page.locator('.tax-evidence-controls').waitFor();
  return {context,page,errors,requests};
}
const state=page=>page.evaluate(()=>window.ConsumptionTaxMap.getState());
const seen=page=>page.evaluate(()=>JSON.parse(localStorage.getItem('isa-seen-consumption-tax-cut')));
async function waitState(page,issue,stance='all'){
  await page.waitForFunction(([issue,stance])=>{const s=window.ConsumptionTaxMap.getState();return s.issueId===issue&&s.stanceId===stance;},[issue,stance]);
}
(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    for(const width of [1280,375,320]){
      const {context,page,errors,requests}=await open(browser,width);
      const data=await page.evaluate(()=>window.PLANET_DATA);
      const order=await page.evaluate(()=>['#planet-block','#bukatsu-background','#consumption-tax-cut-tide-widget','#vote-section','.classroom-section'].map(s=>document.querySelector(s).getBoundingClientRect().top));
      assert.deepEqual([...order].sort((a,b)=>a-b),order);
      for(let i=0;i<background.timeline.length;i++){
        await page.locator('.tax-timeline-nav button').nth(i).click();
        const active=page.locator('.bg-tl [role="tabpanel"]:visible');
        assert.equal(await active.count(),1);assert.equal(await active.getAttribute('data-timeline-id'),background.timeline[i].id);
        assert.match(await active.innerText(),new RegExp(background.timeline[i].body.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
        assert.equal(await active.locator('a').first().getAttribute('href'),background.timeline[i].links[0][0]);
      }
      await page.locator('.tax-timeline-nav button').last().focus();await page.keyboard.press('Home');
      assert.equal(await page.locator('.tax-timeline-nav [aria-selected="true"]').innerText(),background.timeline[0].date);
      const before=await state(page);
      await page.locator('[data-tide-mode="issue"]').click();
      assert.equal(await page.locator('[data-tide-mode="issue"]').getAttribute('aria-pressed'),'true');
      await page.locator('[data-tide-replay]').click();assert.deepEqual(await state(page),before);
      // 6問の答え・出典・所属論点は同じ資料データと一致。
      await page.locator('#panel [data-tax-quiz]').click();
      for(const [i,claim] of data.claims.entries()){
        assert.equal(await page.locator('#quiz').getAttribute('data-claim-id'),claim.id);
        assert.equal((await state(page)).issueId,data.issues.find(x=>x.claims.some(c=>c.id===claim.id)).id);
        await page.locator('#quiz [data-verdict="'+claim.verdict+'"]').click();
        assert.ok((await page.locator('#quiz .qans').innerText()).includes(claim.finding));
        assert.deepEqual(await page.locator('#quiz .tax-quiz-sources a').evaluateAll(a=>a.map(x=>x.href)),claim.sources.map(s=>s.url));
        await page.locator('#quiz .qnext').click();
      }
      assert.match(await page.locator('#quiz').innerText(),/6 \/ 6問正解/);
      await page.locator('[data-tax-finish]').click();assert.equal(await page.locator('#panel .tax-reading-sources').isVisible(),true);
      const counts=await seen(page);await page.evaluate(()=>{for(let j=0;j<3;j++){ConsumptionTaxMap.selectStance('consumption-tax-cut-support');ConsumptionTaxMap.selectStance('all');}});
      assert.deepEqual(await seen(page),counts,'再描画で進捗を増やさない');
      assert.equal((await seen(page)).filter(x=>x.startsWith('c:')).length,6);
      // 長い出典と資料クイズの文字も、実座標で横切れを検査。
      await page.locator('#btn-'+id('business-burden')).click();
      await page.locator('#panel details').evaluateAll(a=>a.forEach(d=>{if(!d.matches('.tax-embed'))d.open=true;}));
      const clipped=await page.locator('#panel a,#bukatsu-background a,.classroom-section a').evaluateAll(a=>a.filter(e=>e.getClientRects().length && (e.getBoundingClientRect().left<0 || e.getBoundingClientRect().right>innerWidth+1)).map(e=>e.textContent));
      assert.deepEqual(clipped,[]);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      assert.deepEqual(requests,[],'閲覧やクイズだけでは投票しない');assert.deepEqual(errors,[]);
      await page.locator('.tax-timeline-nav').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'timeline-'+width+'.png')});
      summary.push({width,timeline:3,quiz:6,progressUnique:true,sourceBounds:true});await context.close();
    }
    {
      const {context,page,errors}=await open(browser);
      await page.locator('#btn-'+id('finance-welfare')).click();await page.locator('#modes [data-m="減税推進"]').click();await page.locator('#btn-'+id('business-burden')).click();
      await page.goBack();await waitState(page,id('finance-welfare'),id('support'));
      await page.goBack();await waitState(page,id('finance-welfare'));
      await page.goBack();await waitState(page,id('scope'));
      await page.goForward();await waitState(page,id('finance-welfare'));
      // 6つの授業リンク、引用の内容とURL、既存計測の1回だけの発火。
      const reasons=[...classroom.reasons_pro,...classroom.reasons_con];
      for(let i=0;i<reasons.length;i++){
        await page.locator('.classroom-section a[href^="#issue-"]').nth(i).click();await waitState(page,reasons[i].issue_id);
        await page.locator('#panel .cite-copy-btn').click();await page.waitForFunction(n=>window.__copied.length===n,i+1);
        const text=await page.evaluate(()=>window.__copied.at(-1));
        assert.ok(text.includes('#issue-'+reasons[i].issue_id));assert.ok(text.includes('3890件'));assert.ok(text.includes('社会全体の世論調査ではありません'));
        const label=await page.evaluate(id=>PLANET_DATA.issues.find(i=>i.id===id).label,reasons[i].issue_id);
        assert.ok(text.includes(label),label);
      }
      const events=await page.evaluate(()=>window.__events.filter(e=>e[0]==='event'));
      assert.equal(events.filter(e=>e[1]==='classroom_link_click').length,6);assert.equal(events.filter(e=>e[1]==='cite_copy').length,6);
      assert.equal(events.some(e=>/stance|立場/.test(JSON.stringify(e[2]))),false);
      // 授業のA4と、全論点の印刷を実際のPDFへ出す。
      await page.locator('.classroom-print-btn').click();assert.deepEqual(await page.evaluate(()=>window.__prints),[true]);
      assert.equal(await page.evaluate(()=>window.__events.filter(e=>e[0]==='event'&&e[1]==='classroom_print').length),1);
      await page.pdf({path:path.join(out,'classroom.pdf'),format:'A4',printBackground:true,preferCSSPageSize:true});
      assert.equal(await page.locator('body.tax-print-classroom').count(),0);
      await page.locator('#panel [data-tax-quiz]').click();
      const beforePrint=await seen(page);
      await page.waitForFunction(()=>[...document.querySelectorAll('#fallback img')].every(img=>img.complete&&img.naturalWidth>0));
      assert.equal(await page.locator('#fallback img').count(),7);
      await page.emulateMedia({media:'print'});
      assert.equal(await page.locator('.share-x-fab').isVisible(),false);
      assert.equal(await page.locator('#fallback-nav').isVisible(),false);
      for(const img of await page.locator('#fallback img').all())assert.equal(await img.isVisible(),true);
      await page.emulateMedia({media:null});
      await page.pdf({path:path.join(out,'full-page.pdf'),format:'A4',printBackground:true,preferCSSPageSize:true});
      await page.waitForTimeout(50);assert.deepEqual(await seen(page),beforePrint,'印刷のための展開では進捗を増やさない');
      const classroomText=execFileSync('pdftotext',[path.join(out,'classroom.pdf'),'-'],{encoding:'utf8'}).replace(/\s/g,'');
      for(const reason of reasons)assert.ok(classroomText.includes(reason.text.replace(/\s/g,'')),reason.text);
      for(const source of classroom.primary_sources){
        assert.ok(classroomText.includes(source.title.replace(/\s/g,'')),source.title);
        assert.ok(classroomText.includes(source.note.replace(/\s/g,'')),source.note);
      }
      for(const q of classroom.questions)assert.ok(classroomText.includes(q.replace(/\s/g,'')),q);
      const pdfInfo=execFileSync('pdfinfo',[path.join(out,'classroom.pdf')],{encoding:'utf8'});assert.match(pdfInfo,/Pages:\s+1\b/);
      const full=execFileSync('pdftotext',[path.join(out,'full-page.pdf'),'-'],{encoding:'utf8'}).replace(/\s/g,'');
      const data=await page.evaluate(()=>window.PLANET_DATA);
      for(const issue of data.issues)assert.ok(full.includes(issue.label),issue.id);
      for(const issue of data.issues)for(const reason of issue.sub.items||[]){
        assert.ok(full.includes((reason.label+reason.count+'件').replace(/\s/g,'')),issue.id+' '+reason.id);
      }
      for(const claim of data.claims)assert.ok(full.includes(claim.claim.replace(/\s/g,'')),claim.id);
      assert.deepEqual(errors,[]);summary.push({history:true,classroomLinks:6,citations:6,classroomA4:1,fullPrintAllIssues:true,fullPrintReasons:data.issues.reduce((n,i)=>n+(i.sub.items||[]).length,0)});await context.close();
    }
    {
      const seed=['o:'+id('sc-1'),'s:'+id('sc-1'),'unknown'];
      const {context,page}=await open(browser,375,seed);const saved=await seen(page);
      assert.equal(saved.filter(x=>x==='s:'+id('sc-1')).length,1);assert.ok(!saved.some(x=>x.startsWith('o:')||x==='unknown'));
      await context.close();summary.push({oldProgressMigrated:true});
    }
    // 実際のVoteStoreは使い、APIの受け口だけテスト応答にする。
    {
      const {context,page,errors,requests}=await open(browser);
      for(const choice of original.vote.choices){
        await page.evaluate(key=>localStorage.removeItem(key),original.vote.storage_key);await page.reload({waitUntil:'networkidle'});
        await page.locator('[data-vote-issue="'+choice.issue_id+'"]').click();
        await page.locator('[data-vote-stance="'+choice.stance_id+'"]').click();await page.locator('#vote-result').waitFor({state:'visible'});
        assert.equal(requests.at(-1).body.topic_id,original.vote.topic_id);assert.equal(requests.at(-1).body.choice_idx,choice.choice_idx);
        const saved=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),original.vote.storage_key);
        assert.deepEqual(saved,{issueIdx:Math.floor(choice.choice_idx/4),stanceIdx:choice.choice_idx%4});
        assert.deepEqual(await state(page),{issueId:id('scope'),stanceId:'all'},'投票で閲覧の選択は変えない');
      }
      assert.equal(requests.length,28);assert.deepEqual(errors,[]);
      await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#vote-result').isVisible(),true);
      assert.match(await page.locator('#vote-position-label').innerText(),/その他.*中立/);assert.equal(requests.length,28);
      await context.close();summary.push({voteChoices:28,realRequestsSent:0,oldStorageCompatible:true});
    }
    {
      const {context,page,requests}=await open(browser,1280,[],source=>source.replace(/(var STANCES=\[[\s\S]*?\];)/, '$1\nVOTE_ISSUES.reverse();STANCES.reverse();'));
      await page.locator('[data-vote-issue="'+id('finance-welfare')+'"]').click();await page.locator('[data-vote-stance="'+id('cautious')+'"]').click();
      await page.locator('#vote-result').waitFor({state:'visible'});assert.equal(requests[0].body.choice_idx,14);
      await page.reload({waitUntil:'networkidle'});assert.match(await page.locator('#vote-position-label').innerText(),/財源・社会保障.*反対・慎重/);
      assert.equal(requests.length,1);await context.close();summary.push({reorderedVoteDisplayKeepsIdMapping:true});
    }
    console.log(JSON.stringify(summary,null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
