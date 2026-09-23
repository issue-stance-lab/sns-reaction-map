/* 工程5: 投票7×3=21通りの保存先・番号が連動表示と共存しても現行のまま動くことを、
   実ブラウザで1件ずつクリックして確認する。本番Supabaseへの通信は/functions/v1/cast-voteの
   パス名一致だけをテスト応答へ差し替え、それ以外は本番configのまま素通り・別オリジンは遮断する
   （消費税版tests/test_consumption_tax_connected_page_browser.cjsの投票検査と同じ手法）。
   bukatsu-chiikiの投票ボタンはtax版と違いid属性を持たず、VOTE_ISSUES/STANCES配列の並び順
   （nth-index）だけで区別される設計のため、順序を入れ替えて壊れないかの検査ではなく、
   「現在の並び順で21通り全部が期待どおりの番号で保存されるか」を確認する
   （並び順自体が変わらないことは tests/test_bukatsu_connected.py の
   test_display_adapts_to_changed_counts_while_vote_payload_stays_fixed が別途保証する）。 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const url=process.env.BUKATSU_CONNECTED_URL;
if(!url || !['127.0.0.1','localhost'].includes(new URL(url).hostname))throw new Error('ローカル候補のURLが必要です（BUKATSU_CONNECTED_URL）');
const root=path.resolve(__dirname,'..');
const TOPIC='bukatsu-chiiki-issue-stance-v1';
const STORAGE_KEY='sns_vote_'+TOPIC+'_my';
// 表示順どおり（docs/bukatsu-chiiki-reaction-map.htmlのVOTE_ISSUES/STANCESと同じ並び）。
const ISSUE_LABELS=['費用・家庭負担','受け皿・指導者','教員の働き方','教育的意義・機会','地域格差','制度・移行プロセス','その他・わからない'];
const STANCE_LABELS=['反対・慎重','どちらでもない','賛成・推進'];

async function open(browser){
  const context=await browser.newContext({viewport:{width:1280,height:950}});
  const page=await context.newPage(),errors=[],requests=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/*',async route=>{
    const req=route.request(),target=new URL(req.url());
    if(target.origin===new URL(url).origin)return route.continue();
    if(target.pathname==='/functions/v1/cast-vote'){
      if(req.method()==='POST')requests.push({url:req.url(),body:req.postDataJSON()});
      return route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify({accepted:true,duplicate:false,counts:{}})});
    }
    return route.abort();
  });
  await page.goto(url,{waitUntil:'networkidle'});await page.locator('#vote-section').waitFor();
  return {context,page,errors,requests};
}

(async()=>{
  const browser=await chromium.launch({headless:true});
  const summary=[];
  try{
    const {context,page,errors,requests}=await open(browser);
    for(let issueIdx=0;issueIdx<ISSUE_LABELS.length;issueIdx++){
      for(let stanceIdx=0;stanceIdx<STANCE_LABELS.length;stanceIdx++){
        await page.evaluate(key=>localStorage.removeItem(key),STORAGE_KEY);
        await page.reload({waitUntil:'networkidle'});
        // 初期表示は件数最多の論点へ自動着地する（工程3の仕様）。投票操作の前後でこの状態が
        // 変わらないことを確認する（「変わらない」の基準を、reloadごとの実際の着地状態にする）。
        const mapStateBefore=await page.evaluate(()=>window.BukatsuConnectedMap.getState());
        await page.locator('.vote-issue-btn').nth(issueIdx).click();
        await page.locator('.vote-stance-btn').nth(stanceIdx).click();
        await page.locator('#vote-result').waitFor({state:'visible'});
        const expectedChoiceIdx=issueIdx*STANCE_LABELS.length+stanceIdx;
        const last=requests.at(-1);
        assert.equal(last.body.topic_id,TOPIC,`issue${issueIdx} stance${stanceIdx}`);
        assert.equal(last.body.choice_idx,expectedChoiceIdx,`issue${issueIdx} stance${stanceIdx}`);
        const saved=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),STORAGE_KEY);
        assert.deepEqual(saved,{issueIdx,stanceIdx});
        const label=await page.locator('#vote-position-label').innerText();
        assert.ok(label.includes(ISSUE_LABELS[issueIdx])&&label.includes(STANCE_LABELS[stanceIdx]),label);
        // 投票操作は連動表示側の閲覧状態（山なみの選択）を変えない。
        const mapStateAfter=await page.evaluate(()=>window.BukatsuConnectedMap.getState());
        assert.deepEqual(mapStateAfter,mapStateBefore,`issue${issueIdx} stance${stanceIdx}: 投票で山なみの選択が変わっている`);
      }
    }
    assert.equal(requests.length,21,'21件のPOST以外が発生している');
    assert.deepEqual(errors,[],'コンソールエラーが発生している');
    summary.push({voteChoices:21,realRequestsSent:0,mapStateUnaffected:true});
    await context.close();
    console.log(JSON.stringify(summary,null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
