/* 見本の操作体験: 近接した操作、選択の強調、スクロールを動かさない切替。 */
const {chromium,webkit}=require('playwright');
const assert=require('node:assert/strict');
const url=process.env.TAX_CONNECTED_URL;
if(!url||!['localhost','127.0.0.1'].includes(new URL(url).hostname))throw Error('ローカル候補URLが必要です');
(async()=>{
 const results=[];
 for(const [engine,type] of Object.entries({chromium,webkit})){
  const browser=await type.launch();
  try{for(const width of [1280,375,320]){
   const page=await browser.newPage({viewport:{width,height:1000},reducedMotion:'reduce'}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(url).origin?r.continue():r.abort());
   await page.goto(url,{waitUntil:'networkidle'});
   assert.equal(await page.locator('#stance-glance #modes button').count(),5);
   assert.equal(await page.locator('#planet-block > .panel-title h2').innerText(),'意見は、どこで分かれている？');
   const data=await page.evaluate(()=>PLANET_DATA);
   const rect=()=>page.locator('#section').evaluate(e=>({top:e.getBoundingClientRect().top+scrollY,scroll:scrollY}));
   await page.locator('#modes').evaluate(e=>scrollTo(0,e.getBoundingClientRect().top+scrollY-135));
   const before=await rect();
   for(const stance of [{id:'all',key:'all',color:'#075ef2'},...data.stances]){
    await page.locator('#modes button').evaluateAll((bs,key)=>bs.find(b=>b.dataset.m===key).click(),stance.key);
    const position=await rect();
    assert.ok(Math.abs(position.scroll-before.scroll)<2,'立場切替でスクロールを動かさない');
    assert.ok(Math.abs(position.top-before.top)<2,'立場切替で山の位置を動かさない');
    const controls=await page.locator('#modes button').evaluateAll(bs=>bs.map(b=>({active:b.getAttribute('aria-pressed')==='true',bg:getComputedStyle(b).backgroundColor,color:getComputedStyle(b).color})));
    assert.deepEqual(controls.filter(v=>v.active).map(v=>[v.bg,v.color]),[['rgb(7, 26, 61)','rgb(255, 255, 255)']],'選んだボタンは即座に紺背景・白文字');
    assert.ok(controls.filter(v=>!v.active).every(v=>v.bg==='rgb(255, 255, 255)'&&v.color==='rgb(7, 26, 61)'),'非選択ボタンは即座に白背景');
    assert.equal(await page.locator('#section .hill[aria-pressed="true"]').count(),1);
    const appearance=await page.locator('#section .hill').evaluateAll(gs=>gs.map(g=>({active:g.getAttribute('aria-pressed')==='true',fill:g.querySelector('path').getAttribute('fill'),opacity:+getComputedStyle(g.querySelector('path')).opacity})));
    assert.ok(appearance.every(v=>v.fill===stance.color));
    assert.ok(appearance.filter(v=>!v.active).every(v=>v.opacity<.3));
    assert.ok(appearance.find(v=>v.active).opacity>.8);
    const mode=data.modes.find(m=>m.id===stance.key);
    for(const issue of data.issues){
     assert.equal(await page.locator('#btn-'+issue.id+' .m').innerText(),mode.counts[issue.id].toLocaleString('ja-JP')+'件');
    }
   }
   await page.locator('#stance-glance-result .tax-leading-issue').focus();
   await page.keyboard.press('Enter');
   assert.equal(await page.evaluate(()=>document.activeElement.matches('.tax-leading-issue')),true,'最多論点をキーボードで選んでも焦点を保つ');
   const hill=page.locator('#section .hill[data-i="5"]');
   await hill.focus();await page.keyboard.press('Enter');
   assert.equal(await hill.getAttribute('aria-pressed'),'true');
   assert.equal(await page.evaluate(()=>document.activeElement.matches('#section .hill[data-i="5"]')),true);
   assert.match(await page.locator('#section .tax-selected-label').textContent(),/件 · [\d.]+%/);
   assert.equal(await page.locator('#panel').getAttribute('data-tax-issue-id'),'consumption-tax-cut-business-burden');
   assert.equal(await page.locator('#section .tax-selected-label').evaluate(e=>{const r=e.getBoundingClientRect(),svg=e.closest('svg').getBoundingClientRect();return r.left>=svg.left&&r.right<=svg.right;}),true,'右端の山の数値も切れない');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   assert.deepEqual(errors,[]);await page.close();results.push({engine,width,unifiedControls:true,stableMapPosition:true,strongSelection:true,keyboardFocus:true});
  }
  // 変形の途中でスマホ幅からPC幅へ変えても、監視通知の循環を起こさない。
  const page=await browser.newPage({viewport:{width:375,height:1000},reducedMotion:'no-preference'}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(url).origin?r.continue():r.abort());
  await page.goto(url,{waitUntil:'networkidle'});
  await page.evaluate(()=>{for(let i=0;i<20;i++)ConsumptionTaxMap.selectStance(PLANET_DATA.stances[i%4].id);});
  await page.waitForTimeout(100);await page.setViewportSize({width:1280,height:1000});await page.waitForTimeout(550);
  assert.equal(await page.locator('#section').evaluate(e=>e.getBoundingClientRect().height),210);
  assert.equal(await page.locator('#modes [aria-pressed="true"]').getAttribute('data-m'),'中立・情報');
  assert.deepEqual(errors,[]);await page.close();results.push({engine,resizeDuringAnimation:true});
  }finally{await browser.close();}
 }
 console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
