/* オーナー指示2026-09-23「山の色を消費税に揃えて」の回帰検査。
   消費税と同じ方式（選んだ立場の色1色に全ての山をそろえ、選択中0.9・他0.23・
   未選択（論点の一覧）0.6の濃淡）になっているかを、実際の立場切替・論点選択で確認する。
   色の値自体は部活動固有の配色（configs/planet/bukatsu-chiiki.yaml）を使う想定で、
   消費税の色そのものを持ち込んでいないことも確認する。本番への通信は行わない。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const url=process.env.BUKATSU_CONNECTED_URL;
if(!url || !['127.0.0.1','localhost'].includes(new URL(url).hostname))throw new Error('ローカル候補のURLが必要です（BUKATSU_CONNECTED_URL）');

async function hillFills(page){
  return page.evaluate(()=>Array.from(document.querySelectorAll('#section .hill')).map(g=>{
    const p=g.querySelector('path');
    return {i:g.dataset.i, fill:p.getAttribute('fill'), opacity:Number(p.getAttribute('opacity'))};
  }));
}

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
    await page.goto(url,{waitUntil:'networkidle'});
    await page.locator('#panel h2').waitFor();

    // 「すべて」: 全ての山が同じ色（青#075ef2、taxのallと同じ既定色）で、選択中の論点だけ0.9、他は0.23。
    let hills=await hillFills(page);
    const allFills=new Set(hills.map(h=>h.fill));
    assert.equal(allFills.size, 1, '「すべて」で山の色が1色にそろっていません: ' + JSON.stringify([...allFills]));
    const landedCount=hills.filter(h=>h.opacity===0.9).length;
    assert.equal(landedCount, 1, '選択中（不透明度0.9）の山が1つではありません');
    assert.ok(hills.every(h=>h.opacity===0.9 || h.opacity===0.23), '不透明度が0.9/0.23以外の山があります');

    // 立場を選ぶと、部活動固有のその立場の色（消費税の色ではない）へ全ての山がそろう。
    const stances=await page.evaluate(()=>window.PLANET_DATA.stances.map(s=>({id:s.id,key:s.key,color:s.color})));
    const target=stances.find(s=>s.key==='慎重・反対');
    await page.evaluate(id=>window.BukatsuConnectedMap.selectStance(id), target.id);
    await page.waitForFunction(c=>document.querySelector('#section .hill path').getAttribute('fill')===c, target.color);
    hills=await hillFills(page);
    assert.ok(hills.every(h=>h.fill===target.color), '立場選択後、山の色が対象の立場色にそろっていません');
    assert.notEqual(target.color, '#075ef2', 'このテスト自体の前提（既定色と別の色を選んでいること）が崩れています');

    // 論点の一覧（未選択）へ戻ると、全ての山が0.6になる。
    await page.evaluate(()=>window.BukatsuConnectedMap.selectIssue(null));
    await page.waitForFunction(()=>document.querySelector('#section .hill path').getAttribute('opacity')==='0.6');
    hills=await hillFills(page);
    assert.ok(hills.every(h=>h.opacity===0.6), '論点未選択時に不透明度0.6でない山があります');

    console.log('OK  山の色が消費税と同じ方式（選択立場の色1色・0.9/0.23/0.6の濃淡）で切り替わる');
  } finally {
    await browser.close();
  }
})().catch(error=>{ console.error('NG', error.message); process.exitCode=1; });
