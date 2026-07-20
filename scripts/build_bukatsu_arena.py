#!/usr/bin/env python3
"""部活動の地域移行 HTMLに論点アリーナを追加する変換スクリプト"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML_PATH = ROOT / "docs" / "bukatsu-chiiki-reaction-map.html"
JSON_PATH = ROOT / "social-samples" / "bukatsu-chiiki_2d_classified.json"

ISSUE_MAP = {
    "費用・家庭負担": 0,
    "受け皿・指導者": 1,
    "教員の働き方": 2,
    "教育的意義・機会": 3,
    "地域格差": 4,
    "制度・移行プロセス": 5,
    "その他": 6,
}

# === SM_RAW 生成 ===
def gen_sm_raw():
    data = json.loads(JSON_PATH.read_text())
    lines = []
    for p in data:
        if not p.get("is_opinion"):
            continue
        mi = p.get("main_issue", "その他")
        i = ISSUE_MAP.get(mi, 6)
        x = round(p.get("stance_transfer", 0), 1)
        e = round(p.get("emotional_intensity", 0), 1)
        c = round(p.get("confidence", 0.7), 2)
        s = (p.get("summary", "") or "").replace('"', '\\"')[:60]
        u = p.get("url", "")
        lines.append(f'{{x:{x},e:{e},c:{c},i:{i},s:"{s}",u:"{u}"}}')
    return "const SM_RAW = [\n" + ",\n".join(lines) + "\n];"


# === 追加CSS ===
EXTRA_CSS = """
    /* === 論点アリーナ === */
    .arena-section{position:relative;background:#0f0e2e;border-top:0;padding:42px min(6vw,72px)}
    .arena-section .panel-title h2{color:#fff}.arena-section .panel-title span{color:rgba(255,255,255,.7)}
    #sm-wrap{position:relative;width:100%;max-width:660px;margin:0 auto;background:#fff;border-radius:12px;box-shadow:0 16px 48px rgba(0,0,0,.35);padding:6px}
    #sm-wrap canvas{display:block;width:100%;border:0;border-radius:8px}
    #smCanvasMain{cursor:crosshair;position:relative;z-index:2;background:transparent}
    #smCanvasHeat{position:absolute;top:6px;left:6px;width:calc(100% - 12px);height:calc(100% - 12px);border-radius:8px;pointer-events:none;z-index:1;background:#fdfdff}
    .map-caption{max-width:760px;margin:12px auto 0;color:rgba(255,255,255,.72);font-size:13px}
    #your-marker-note{color:rgba(255,255,255,.7)!important}
    .sm-controls{max-width:660px;margin:14px auto 0;display:flex;flex-direction:column;gap:10px}
    .sm-legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;font-weight:800;color:rgba(255,255,255,.8);align-items:center}
    .sm-legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px}
    .sm-filters{display:flex;gap:6px;flex-wrap:wrap}
    .sm-fbtn{border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:6px 12px;background:rgba(255,255,255,.1);color:rgba(255,255,255,.85);cursor:pointer;font-size:12px;font-weight:800}
    .sm-fbtn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
    #sm-tooltip{position:absolute;display:none;z-index:5;max-width:260px;background:#1e1b4b;color:#fff;font-size:12px;line-height:1.5;border-radius:8px;padding:10px 12px;pointer-events:none;box-shadow:0 12px 32px rgba(0,0,0,.3)}
    /* === 論点explainer === */
    .explainer-section{background:#fff}
    .explainer-lead{font-size:15px;line-height:1.9;color:var(--ink);margin:0 0 24px;max-width:880px}
    .explainer-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px}
    .explainer-card{border:1px solid var(--line);border-radius:12px;background:#fff;box-shadow:0 4px 16px rgba(16,24,40,.06);padding:18px;cursor:default}
    .explainer-num{display:inline-block;background:var(--accent);color:#fff;border-radius:999px;font-size:11px;font-weight:900;padding:2px 10px;margin-bottom:8px}
    .explainer-card-title{font-size:15px;font-weight:900;margin:0 0 6px;line-height:1.4}
    .explainer-card-desc{font-size:13px;color:var(--muted);line-height:1.7;margin:0 0 10px}
    .explainer-sides{display:flex;flex-direction:column;gap:5px}
    .explainer-side{font-size:12px;border-radius:6px;padding:5px 9px;font-weight:700}
    .explainer-side.con{background:#fef2f2;color:#991b1b}
    .explainer-side.pro{background:#ecfdf5;color:#065f46}
    .explainer-note{font-size:12px;color:var(--muted);margin:12px 0 0}
    /* === 2ステップ投票 === */
    .vote-step-label{display:flex;align-items:center;gap:10px;font-size:14px;font-weight:800;margin:0 0 14px}
    .step-num{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:var(--accent);color:#fff;font-size:13px;font-weight:900;flex-shrink:0}
    .vote-issue-btn{border:1px solid var(--line);border-radius:10px;padding:10px 14px;background:#fff;cursor:pointer;font-size:13px;font-weight:800;text-align:left;display:flex;align-items:center;gap:8px;transition:border-color .15s,background .15s}
    .vote-issue-btn:hover{border-color:var(--accent);background:var(--accent-soft)}
    .vote-issue-icon{font-size:20px;flex-shrink:0}
    .vote-stance-btn{border:2px solid;border-radius:12px;padding:14px 18px;background:#fff;cursor:pointer;display:flex;flex-direction:column;gap:4px;min-width:160px;transition:transform .15s,box-shadow .15s;border-color:var(--stance-color,#ccc)}
    .vote-stance-btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px var(--stance-shadow,rgba(0,0,0,.12))}
    .vs-icon{font-size:22px;font-weight:900;color:var(--stance-color)}
    .vs-title{font-size:14px;font-weight:900;color:var(--ink)}
    .vs-desc{font-size:12px;color:var(--muted);line-height:1.5}
    @media(max-width:767px){
      .explainer-grid{grid-template-columns:1fr}
      .vote-stance-btn{min-width:unset;width:100%}
    }
"""

# === explainer セクション ===
EXPLAINER_SECTION = """<section class="panel explainer-section" id="explainer-section">
<div class="panel-title"><h2>投票前に読む：6つの論点</h2><span>それぞれの問いを把握してから</span></div>
<p class="explainer-lead">「部活動の地域移行」の議論は「賛成か反対か」だけではありません。費用・指導者・教員の働き方・子どもの機会・地域差・行政手続き——6つの論点を整理してから投票に進んでください。</p>
<div class="explainer-grid">
  <article class="explainer-card">
    <span class="explainer-num">論点①</span>
    <p class="explainer-card-title">費用・家庭負担 — 「月8000円、年間28万円」</p>
    <p class="explainer-card-desc">移行後の月会費が公立部活の頃より大幅に上がるケースが続出。3人きょうだいでは年間30万円近くになる家庭も。低所得家庭への補助の有無で地域差も生まれる。</p>
    <div class="explainer-sides">
      <span class="explainer-side con">懸念：家計を直撃。格差が広がる</span>
      <span class="explainer-side pro">擁護：市税補助・一律化で解決できる</span>
    </div>
  </article>
  <article class="explainer-card">
    <span class="explainer-num">論点②</span>
    <p class="explainer-card-title">受け皿・指導者 — 「ボランティア頼みは限界」</p>
    <p class="explainer-card-desc">地域クラブの指導者がいない・報酬が最低賃金レベル・責任は重い。「タイミーで探した方が時給が高い」という声も。人材確保ができなければ移行自体が空洞化する。</p>
    <div class="explainer-sides">
      <span class="explainer-side con">懸念：報酬が安く人材が集まらない</span>
      <span class="explainer-side pro">擁護：生活できる報酬を社会全体で保障を</span>
    </div>
  </article>
  <article class="explainer-card">
    <span class="explainer-num">論点③</span>
    <p class="explainer-card-title">教員の働き方 — 「ブラック部活の解消」が最大動機</p>
    <p class="explainer-card-desc">教員が土日に無償で指導する構造が長時間労働の温床に。地域移行の最大の動機は教員の働き方改革。ただし「義務がなくなっても続ける教員が多い」という現実もある。</p>
    <div class="explainer-sides">
      <span class="explainer-side pro">賛成：強制をなくし教員の負担を減らせる</span>
      <span class="explainer-side con">懸念：移行後も実態は変わらない可能性</span>
    </div>
  </article>
  <article class="explainer-card">
    <span class="explainer-num">論点④</span>
    <p class="explainer-card-title">教育的意義・機会 — 「子どもの夢と居場所」</p>
    <p class="explainer-card-desc">部活動は競技だけでなく人間形成・チームワーク・居場所の場でもある。地域移行で不登校の子も参加しやすくなる可能性がある一方、「費用で夢を奪われる」という怒りも。</p>
    <div class="explainer-sides">
      <span class="explainer-side pro">期待：門戸が広がり多様な子に機会を</span>
      <span class="explainer-side con">懸念：費用・距離の壁で格差が生まれる</span>
    </div>
  </article>
  <article class="explainer-card">
    <span class="explainer-num">論点⑤</span>
    <p class="explainer-card-title">地域格差 — 「都市はできるが地方は無理」</p>
    <p class="explainer-card-desc">都市部は代替クラブや交通手段があるが、地方では受け皿となる団体自体が存在しない。少子化で単独チームが組めない学校も増えており、移行の実現可能性が地域で大きく異なる。</p>
    <div class="explainer-sides">
      <span class="explainer-side con">懸念：地方では移行自体が成立しない</span>
      <span class="explainer-side pro">視点：地域の実情に合わせた柔軟設計を</span>
    </div>
  </article>
  <article class="explainer-card">
    <span class="explainer-num">論点⑥</span>
    <p class="explainer-card-title">制度・移行プロセス — 「手探りのまま進んでいる」</p>
    <p class="explainer-card-desc">国の方針は出たが、担い手・費用負担のルールは自治体ごとの手探り。「クラブ化と言っているのにチームしか作っていない」という本質的な批判も。プロセス設計の問題を問う声が最多。</p>
    <div class="explainer-sides">
      <span class="explainer-side con">批判：制度設計が不透明なまま進んでいる</span>
      <span class="explainer-side pro">擁護：段階的に改善していくのは当然</span>
    </div>
  </article>
</div>
<p class="explainer-note"><strong>使い方:</strong> 6つの論点を把握してから、次の投票で「自分が一番気になる論点」を選んでください。</p>
</section>
"""

# === 2ステップ投票セクション ===
VOTE_SECTION = """<section class="panel" id="vote-section">
<div class="panel-title"><h2>あなたが一番気になる「論点」は？</h2><span>SNSの声を見る前に</span></div>
<p style="font-size:14px;color:var(--ink);line-height:1.75;margin:0 0 12px;">文部科学省が推進する「部活動の地域移行」。教員の働き方改革や少子化対策として期待される一方、費用負担や指導者不足、部活文化の喪失を懸念する声もあります。</p>
<div style="font-size:12px;color:var(--muted);background:var(--accent-soft);border-radius:8px;padding:10px 14px;margin:0 0 20px;line-height:1.65;"><strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿を取得し、AIが自動分類しました。</div>
<div id="vote-step1"><p class="vote-step-label"><span class="step-num">1</span>あなたが最も気になる論点をタップ <span style="font-size:12px;font-weight:400;color:var(--muted)">（全2問）</span></p><div id="vote-issue-btns" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;max-width:900px;"></div></div>
<div id="vote-step2" style="display:none;margin-top:4px;"><p class="vote-step-label"><span class="step-num">2</span>地域移行への賛否は？ <span style="font-size:12px;font-weight:400;color:var(--muted)">答えたら開票します</span></p><div id="vote-stance-btns" style="display:flex;gap:12px;flex-wrap:wrap;margin-top:10px;"></div></div>
<p style="font-size:11px;color:var(--muted);margin:10px 0 0;">※ 世論調査ではありません。投票は匿名で集計され、サーバーに保存されます。</p>
<div id="vote-result" style="display:none;margin-top:20px;">
  <div style="background:var(--accent-soft);border-radius:10px;padding:16px;margin-bottom:16px;">
    <div id="vote-position-label" style="font-weight:900;font-size:16px;color:var(--accent);margin-bottom:6px;"></div>
    <div id="vote-position-text" style="font-size:12px;color:var(--muted);"></div>
  </div>
  <a id="share-x" href="#" target="_blank" rel="noopener" style="display:inline-flex;margin-top:4px;padding:8px 16px;border-radius:8px;background:#000;color:#fff;text-decoration:none;font-weight:800;">Xでシェア</a>
  <button id="vote-redo-btn" type="button" style="margin-left:8px;padding:8px 16px;border-radius:8px;border:1px solid var(--line);background:#fff;font-weight:800;">投票をやり直す</button>
</div>
</section>
"""

# === 論点アリーナセクション ===
ARENA_SECTION = """<section class="arena-section" id="stance-map-section">
<div id="stance-map-inner" style="max-width:720px;margin:0 auto">
<div class="panel-title"><h2>論点アリーナ</h2><span>245件 | セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細</span></div>
<div id="sm-wrap">
  <canvas id="smCanvasHeat" width="640" height="640"></canvas>
  <canvas id="smCanvasMain" width="640" height="640"></canvas>
</div>
<p class="map-caption">中心の「部活動の地域移行」を6つの論点セクターが囲みます。扇の大きさは投稿数、中心からの距離は感情の熱量（外側ほど激しい）、点の色はスタンス（緑=移行支持 / 赤=移行反対 / 灰=中立）。点をクリックすると元のXポストを開きます。</p>
<p id="your-marker-note" style="display:none;font-size:12px;color:var(--muted);text-align:center;margin:8px 0 0;"></p>
<div class="sm-controls">
  <div class="sm-legend">
    <span><i style="background:#059669"></i>移行支持</span>
    <span><i style="background:#dc2626"></i>移行反対</span>
    <span><i style="background:#64748b"></i>中立</span>
    <span style="color:#888">中心＝冷静 / 外周＝感情的</span>
  </div>
  <div class="sm-filters" id="sm-filters"></div>
</div>
<div id="sm-tooltip"></div>
</div>
</section>
"""

# === 投票JS ===
VOTE_JS = """<script>
(function(){
  'use strict';
  var TOPIC='bukatsu-chiiki-issue-stance-v1';
  var STORAGE_KEY='sns_vote_'+TOPIC+'_my';
  var supabaseUrl="";
  var supabaseAnonKey="";
  var supabaseClient=null;
  if(supabaseUrl&&supabaseAnonKey&&typeof supabase!=='undefined'){
    supabaseClient=supabase.createClient(supabaseUrl,supabaseAnonKey);
  }
  var VOTE_ISSUES=[
    {k:'費用・家庭負担',    icon:'💴', desc:'月会費・家計への経済的負担・格差'},
    {k:'受け皿・指導者',    icon:'👤', desc:'指導者不足・報酬・人材確保'},
    {k:'教員の働き方',      icon:'🏫', desc:'残業・強制参加・ブラック部活の解消'},
    {k:'教育的意義・機会',  icon:'⭐', desc:'子どもの成長・不登校参加・文化継承'},
    {k:'地域格差',          icon:'🗾', desc:'都市と地方の格差・自治体差'},
    {k:'制度・移行プロセス',icon:'📋', desc:'国の方針・移行スピード・行政対応'},
    {k:'その他・わからない',icon:'💬', desc:'上記以外・様子見'}
  ];
  // VOTE_ISSUES index → ISSUES array index (費0 受1 教員2 教育3 地域4 制度5 その他6)
  var V2I=[0,1,2,3,4,5,6];
  var STANCES=[
    {k:'反対・慎重',    color:'#dc2626', bg:'#fef2f2', shadow:'rgba(220,38,38,.22)', icon:'!', desc:'このままの進め方には問題がある'},
    {k:'どちらでもない',color:'#64748b', bg:'#f8fafc', shadow:'rgba(100,116,139,.22)', icon:'?', desc:'条件や内容を見てから判断したい'},
    {k:'賛成・推進',    color:'#059669', bg:'#ecfdf5', shadow:'rgba(5,150,105,.22)', icon:'✓', desc:'教員の働き方改革や少子化対策として必要'}
  ];
  var selIssue=-1;
  var step1=document.getElementById('vote-step1');
  var step2=document.getElementById('vote-step2');
  var result=document.getElementById('vote-result');
  var issueBtns=document.getElementById('vote-issue-btns');
  var stanceBtns=document.getElementById('vote-stance-btns');

  VOTE_ISSUES.forEach(function(iss,i){
    var btn=document.createElement('button');
    btn.type='button';btn.className='vote-issue-btn';
    btn.innerHTML='<span class="vote-issue-icon">'+iss.icon+'</span><span class="vote-issue-title">'+iss.k+'</span>';
    btn.onclick=function(){selIssue=i;step1.style.display='none';step2.style.display='block';};
    issueBtns.appendChild(btn);
  });

  function showVote(issueIdx,stanceIdx,shouldScroll){
    var iss=VOTE_ISSUES[issueIdx];
    var st=STANCES[stanceIdx];
    var arenaIdx=V2I[issueIdx];
    selIssue=issueIdx;
    step1.style.display='none';step2.style.display='none';result.style.display='block';
    document.getElementById('vote-position-label').textContent='論点：'+iss.k+'　賛否：'+st.k;
    document.getElementById('vote-position-text').textContent=iss.desc;
    if(window.setStanceMapVoteMarker)window.setStanceMapVoteMarker(arenaIdx,st.color);
    var shareText='部活動の地域移行、私が最も気になる論点は「'+iss.k+'」。'+st.k+'の立場です。';
    document.getElementById('share-x').href='https://x.com/intent/tweet?text='+encodeURIComponent(shareText)+'&url='+encodeURIComponent('https://issue-stance-lab.github.io/sns-reaction-map/bukatsu-chiiki-reaction-map.html');
    setTimeout(function(){
      if(window.setStanceMapVoteMarker)window.setStanceMapVoteMarker(arenaIdx,st.color);
      var el=document.getElementById('stance-map-section');
      if(shouldScroll!==false&&el)el.scrollIntoView({behavior:'smooth',block:'center'});
    },300);
  }

  async function saveVote(issueIdx,stanceIdx){
    if(supabaseClient){
      var response;
      try{
        response=await supabaseClient.from('votes').insert([{topic_id:TOPIC,choice_idx:issueIdx*STANCES.length+stanceIdx}]);
      }catch(error){console.error('Supabase vote request failed:',error);alert('投票を保存できませんでした。');return false;}
      if(response.error){
        var message=(response.error.message||'')+(response.error.details||'');
        if(message.indexOf('already voted')!==-1||response.error.code==='23505'){alert('24時間以内にすでに投票されています。');}
        else{console.error('Supabase vote insert failed:',response.error);alert('投票を保存できませんでした。');}
        return false;
      }
    }
    localStorage.setItem(STORAGE_KEY,JSON.stringify({issueIdx:issueIdx,stanceIdx:stanceIdx}));
    return true;
  }

  STANCES.forEach(function(st,stanceIdx){
    var btn=document.createElement('button');
    btn.type='button';btn.className='vote-stance-btn';
    btn.style.setProperty('--stance-color',st.color);
    btn.style.setProperty('--stance-bg',st.bg);
    btn.style.setProperty('--stance-shadow',st.shadow);
    btn.innerHTML='<span class="vs-icon">'+st.icon+'</span><span class="vs-title">'+st.k+'</span><span class="vs-desc">'+st.desc+'</span>';
    btn.onclick=async function(){
      var buttons=stanceBtns.querySelectorAll('button');
      buttons.forEach(function(item){item.disabled=true;});
      var saved=await saveVote(selIssue,stanceIdx);
      buttons.forEach(function(item){item.disabled=false;});
      if(saved)showVote(selIssue,stanceIdx);
    };
    stanceBtns.appendChild(btn);
  });

  document.getElementById('vote-redo-btn').onclick=function(){
    localStorage.removeItem(STORAGE_KEY);
    selIssue=-1;step1.style.display='block';step2.style.display='none';result.style.display='none';
    if(window.clearStanceMapVoteMarker)window.clearStanceMapVoteMarker();
  };
  if(supabaseClient)document.getElementById('vote-redo-btn').style.display='none';
  try{
    var previous=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');
    if(previous&&Number.isInteger(previous.issueIdx)&&previous.issueIdx>=0&&previous.issueIdx<VOTE_ISSUES.length&&
       Number.isInteger(previous.stanceIdx)&&previous.stanceIdx>=0&&previous.stanceIdx<STANCES.length){
      showVote(previous.issueIdx,previous.stanceIdx,false);
    }
  }catch(error){localStorage.removeItem(STORAGE_KEY);}
})();
</script>
"""

# === アリーナ描画JS ===
ARENA_JS = """<script>
(function(){
  'use strict';
  const ISSUES=[
    {k:'費用・家庭負担',    n:16},
    {k:'受け皿・指導者',    n:34},
    {k:'教員の働き方',      n:58},
    {k:'教育的意義・機会',  n:28},
    {k:'地域格差',          n:8},
    {k:'制度・移行プロセス',n:51},
    {k:'その他',            n:50}
  ];
  const W=640,CX=320,CY=320,R_MIN=64,R_MAX=214,R_HOLE=56,R_LBL=242;
  const PAD_DEG=2.5;
  const canvasMain=document.getElementById('smCanvasMain');
  const canvasHeat=document.getElementById('smCanvasHeat');
  const ctx=canvasMain.getContext('2d');
  const hctx=canvasHeat.getContext('2d');
  const tooltip=document.getElementById('sm-tooltip');

  const total=ISSUES.reduce((a,b)=>a+b.n,0);
  const usable=360-PAD_DEG*2*ISSUES.length;
  let acc=-90;
  ISSUES.forEach(iss=>{
    const span=usable*iss.n/total;
    iss.a0=acc+PAD_DEG;iss.a1=iss.a0+span;iss.mid=(iss.a0+iss.a1)/2;
    acc=iss.a1+PAD_DEG;
  });

  function rnd(seed){const x=Math.sin(seed*127.1+311.7)*43758.5453;return x-Math.floor(x);}
  function colorOf(p){return p.x>=0.5?'#059669':(p.x<=-0.5?'#dc2626':'#64748b');}

  const pts=[];
  SM_RAW.forEach((p,idx)=>{
    const iss=ISSUES[p.i];if(!iss)return;
    const a=iss.a0+rnd(idx)*(iss.a1-iss.a0);
    let r=R_MIN+8+Math.abs(p.e)/2*(R_MAX-R_MIN-30)+(rnd(idx+500)-0.5)*26;
    r=Math.max(R_MIN,Math.min(R_MAX-4,r));
    const rad=a*Math.PI/180;
    pts.push({px:CX+r*Math.cos(rad),py:CY+r*Math.sin(rad),c:colorOf(p),p:p});
  });

  function drawHeat(){
    hctx.clearRect(0,0,W,W);
    const maxN=Math.max(...ISSUES.map(i=>i.n));
    ISSUES.forEach(iss=>{
      hctx.beginPath();
      hctx.moveTo(CX+R_MIN*Math.cos(iss.a0*Math.PI/180),CY+R_MIN*Math.sin(iss.a0*Math.PI/180));
      hctx.arc(CX,CY,R_MAX,iss.a0*Math.PI/180,iss.a1*Math.PI/180);
      hctx.arc(CX,CY,R_MIN,iss.a1*Math.PI/180,iss.a0*Math.PI/180,true);
      hctx.closePath();
      hctx.fillStyle='rgba(8,145,178,'+(0.03+iss.n/maxN*0.09).toFixed(3)+')';
      hctx.fill();
    });
    hctx.setLineDash([3,5]);hctx.strokeStyle='rgba(100,116,139,.3)';hctx.lineWidth=1;
    [110,160,R_MAX].forEach(r=>{hctx.beginPath();hctx.arc(CX,CY,r,0,Math.PI*2);hctx.stroke();});
    hctx.setLineDash([]);
    ISSUES.forEach(iss=>{
      hctx.strokeStyle='rgba(100,116,139,.35)';
      [iss.a0*Math.PI/180,iss.a1*Math.PI/180].forEach(rd=>{
        hctx.beginPath();
        hctx.moveTo(CX+R_MIN*Math.cos(rd),CY+R_MIN*Math.sin(rd));
        hctx.lineTo(CX+R_MAX*Math.cos(rd),CY+R_MAX*Math.sin(rd));
        hctx.stroke();
      });
    });
  }

  let filterIdx=-1;let voteMarker=null;

  function drawMain(){
    ctx.clearRect(0,0,W,W);
    pts.forEach(pt=>{
      const dim=filterIdx>=0&&pt.p.i!==filterIdx;
      ctx.globalAlpha=dim?0.08:0.82;
      ctx.beginPath();ctx.arc(pt.px,pt.py,4,0,Math.PI*2);
      ctx.fillStyle=pt.c;ctx.fill();
    });
    ctx.globalAlpha=1;
    ctx.font='900 12px "Noto Sans JP",sans-serif';
    ISSUES.forEach((iss,i)=>{
      const rad=iss.mid*Math.PI/180;
      const lx=CX+R_LBL*Math.cos(rad),ly=CY+R_LBL*Math.sin(rad);
      const c=Math.cos(rad);
      ctx.textAlign=c>0.35?'left':(c<-0.35?'right':'center');
      ctx.textBaseline='middle';
      ctx.fillStyle=(filterIdx>=0&&i!==filterIdx)?'rgba(100,116,139,.4)':'#334155';
      ctx.fillText(iss.k+' '+iss.n,lx,ly);
    });
    ctx.beginPath();ctx.arc(CX,CY,R_HOLE,0,Math.PI*2);
    ctx.fillStyle='#fff';ctx.fill();
    ctx.strokeStyle='#bae6fd';ctx.lineWidth=1.5;ctx.stroke();
    ctx.fillStyle='#0e7490';ctx.textAlign='center';
    ctx.font='900 13px "Noto Sans JP",sans-serif';
    ctx.fillText('部活動',CX,CY-9);
    ctx.fillText('地域移行',CX,CY+11);
    ctx.font='400 10px "Noto Sans JP",sans-serif';
    ctx.fillStyle='#94a3b8';ctx.textAlign='center';
    ctx.fillText('冷静',CX,CY-R_MIN-8);
    ctx.fillText('感情的',CX,CY-R_MAX-8);
    if(voteMarker){
      const mc=voteMarker.color||'#0891b2';
      const vi=ISSUES[voteMarker.sector];
      if(vi){
        ctx.beginPath();
        ctx.moveTo(CX+R_MIN*Math.cos(vi.a0*Math.PI/180),CY+R_MIN*Math.sin(vi.a0*Math.PI/180));
        ctx.arc(CX,CY,R_MAX,vi.a0*Math.PI/180,vi.a1*Math.PI/180);
        ctx.arc(CX,CY,R_MIN,vi.a1*Math.PI/180,vi.a0*Math.PI/180,true);
        ctx.closePath();
        ctx.strokeStyle=mc;ctx.lineWidth=3;ctx.stroke();
        ctx.fillStyle=mc+'14';ctx.fill();
      }
      const pulse=(Date.now()%1400)/1400;
      ctx.beginPath();ctx.arc(voteMarker.x,voteMarker.y,10+pulse*16,0,Math.PI*2);
      ctx.strokeStyle=mc;ctx.globalAlpha=0.55*(1-pulse);ctx.lineWidth=3;ctx.stroke();
      ctx.globalAlpha=1;
      ctx.beginPath();ctx.arc(voteMarker.x,voteMarker.y,11,0,Math.PI*2);
      ctx.fillStyle='#fff';ctx.fill();
      ctx.beginPath();ctx.arc(voteMarker.x,voteMarker.y,8,0,Math.PI*2);
      ctx.fillStyle=mc;ctx.fill();
      ctx.font='900 12px "Noto Sans JP",sans-serif';
      const txt='あなたはココ';
      const tw=ctx.measureText(txt).width;
      const bx=Math.max(tw/2+10,Math.min(W-tw/2-10,voteMarker.x));
      const by=voteMarker.y-32;
      ctx.beginPath();
      if(ctx.roundRect)ctx.roundRect(bx-tw/2-8,by-11,tw+16,22,11);
      else ctx.rect(bx-tw/2-8,by-11,tw+16,22);
      ctx.fillStyle='#fff';ctx.fill();
      ctx.strokeStyle=mc;ctx.lineWidth=2;ctx.stroke();
      ctx.fillStyle=mc;ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(txt,bx,by+1);
      ctx.textBaseline='alphabetic';
      ctx.beginPath();
      ctx.moveTo(voteMarker.x-4,by+11);ctx.lineTo(voteMarker.x,by+17);ctx.lineTo(voteMarker.x+4,by+11);
      ctx.fillStyle=mc;ctx.fill();
    }
  }

  // 投票前ブラー
  (function applyBlur(){
    var inner=document.getElementById('stance-map-inner');
    var section=document.getElementById('stance-map-section');
    if(!inner||!section)return;
    inner.style.filter='blur(8px)';inner.style.pointerEvents='none';inner.style.userSelect='none';
    section.style.position='relative';
    var ov=document.createElement('div');ov.id='chart-overlay';
    ov.style.cssText='position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:5;background:rgba(0,0,0,.35);border-radius:8px;';
    ov.innerHTML='<div style="text-align:center;"><div style="font-size:16px;font-weight:800;color:#fff;">まず投票してから結果を見よう</div><div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:4px;">上の投票で論点と賛否を選んでください</div></div>';
    section.appendChild(ov);
  })();

  function revealChart(){
    var inner=document.getElementById('stance-map-inner');
    if(inner){inner.style.transition='filter .6s ease';inner.style.filter='none';inner.style.pointerEvents='auto';inner.style.userSelect='auto';}
    var ov=document.getElementById('chart-overlay');if(ov)ov.remove();
  }
  function reBlurChart(){
    var inner=document.getElementById('stance-map-inner');
    if(inner){inner.style.transition='';inner.style.filter='blur(8px)';inner.style.pointerEvents='none';inner.style.userSelect='none';}
    var section=document.getElementById('stance-map-section');
    if(section&&!document.getElementById('chart-overlay')){
      var ov=document.createElement('div');ov.id='chart-overlay';
      ov.style.cssText='position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:5;background:rgba(0,0,0,.35);border-radius:8px;';
      ov.innerHTML='<div style="text-align:center;"><div style="font-size:16px;font-weight:800;color:#fff;">まず投票してから結果を見よう</div><div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:4px;">上の投票で論点と賛否を選んでください</div></div>';
      section.appendChild(ov);
    }
  }

  let pulseRAF=null;
  window.setStanceMapVoteMarker=function(issueIdx,stanceColor){
    revealChart();
    const iss=ISSUES[issueIdx]||ISSUES[0];
    const rad=iss.mid*Math.PI/180,r=(R_MIN+R_MAX)/2-14;
    voteMarker={x:CX+r*Math.cos(rad),y:CY+r*Math.sin(rad),color:stanceColor||'#0891b2',sector:issueIdx};
    const note=document.getElementById('your-marker-note');if(note)note.style.display='block';
    if(pulseRAF)cancelAnimationFrame(pulseRAF);
    (function loop(){drawMain();pulseRAF=requestAnimationFrame(loop);})();
  };
  window.clearStanceMapVoteMarker=function(){
    if(pulseRAF){cancelAnimationFrame(pulseRAF);pulseRAF=null;}
    voteMarker=null;
    const note=document.getElementById('your-marker-note');if(note)note.style.display='none';
    drawMain();reBlurChart();
  };

  const filters=document.getElementById('sm-filters');
  function addBtn(label,idx){
    const b=document.createElement('button');b.className='sm-fbtn'+(idx===-1?' active':'');
    b.textContent=label;
    b.onclick=function(){
      filterIdx=idx;
      filters.querySelectorAll('.sm-fbtn').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');drawMain();
    };
    filters.appendChild(b);
  }
  addBtn('全件 ('+total+')',-1);
  ISSUES.forEach((iss,i)=>{if(iss.k!=='その他')addBtn(iss.k+' ('+iss.n+')',i);});

  function evtPos(ev){
    const rect=canvasMain.getBoundingClientRect();
    const scale=W/rect.width;
    return{x:(ev.clientX-rect.left)*scale,y:(ev.clientY-rect.top)*scale};
  }
  function nearest(pos){
    let best=null,bd=196;
    pts.forEach(pt=>{
      if(filterIdx>=0&&pt.p.i!==filterIdx)return;
      const d=(pt.px-pos.x)**2+(pt.py-pos.y)**2;
      if(d<bd){bd=d;best=pt;}
    });
    return best;
  }
  canvasMain.addEventListener('mousemove',function(ev){
    const pt=nearest(evtPos(ev));
    if(pt){
      const rect=canvasMain.getBoundingClientRect();
      tooltip.style.display='block';
      tooltip.style.left=Math.min(ev.clientX-rect.left+14,rect.width-270)+'px';
      tooltip.style.top=(ev.clientY-rect.top+14)+'px';
      tooltip.innerHTML='<strong>'+ISSUES[pt.p.i].k+'</strong><br>'+pt.p.s;
    }else{tooltip.style.display='none';}
  });
  canvasMain.addEventListener('mouseleave',function(){tooltip.style.display='none';});
  canvasMain.addEventListener('click',function(ev){
    const pt=nearest(evtPos(ev));
    if(pt&&pt.p.u)window.open(pt.p.u,'_blank','noopener');
  });
  canvasMain.addEventListener('touchstart',function(ev){
    if(ev.touches.length!==1)return;
    const t=ev.touches[0];
    const pt=nearest(evtPos(t));
    if(pt&&pt.p.u){ev.preventDefault();window.open(pt.p.u,'_blank','noopener');}
  },{passive:false});

  drawHeat();drawMain();
})();
</script>
"""

def transform(html: str) -> str:
    # 1. Add CSS before </style>
    html = html.replace("</style>", EXTRA_CSS + "\n  </style>", 1)

    # 2. Remove old vote + stance sections, insert new ones
    # Find the manga section end + vote section start
    vote_start = html.find('    <section class="panel" id="vote-section">')
    # Find the end of stance-map-section closing </section>
    stance_end_marker = '</div><!-- /stance-map-inner -->\n</section>'
    stance_end = html.find(stance_end_marker)
    if stance_end == -1:
        raise ValueError("stance-map-inner end marker not found")
    stance_end += len(stance_end_marker)

    before = html[:vote_start]
    after = html[stance_end:]

    html = before + EXPLAINER_SECTION + "\n" + VOTE_SECTION + "\n" + ARENA_SECTION + after

    # 3. Replace SM_RAW block + old rendering JS
    # Find <script>\nconst SM_RAW
    sm_start = html.find('<script>\nconst SM_RAW')
    if sm_start == -1:
        sm_start = html.find('<script>\n const SM_RAW')
    if sm_start == -1:
        raise ValueError("SM_RAW script block not found")

    # Find the end of the old JS (closing </script> of the rendering script)
    # There are multiple scripts; find the one that contains drawHeatmap or smCanvasMain drawing code
    # Look for closing script tag after SM_RAW
    search_from = sm_start
    while True:
        script_end = html.find('</script>', search_from)
        if script_end == -1:
            raise ValueError("SM_RAW closing script not found")
        chunk = html[sm_start:script_end+9]
        # Check if this script block contains the rendering code
        if 'smCanvasMain' in chunk and ('drawHeat' in chunk or 'mousemove' in chunk or 'drawMain' in chunk):
            # This is the combined SM_RAW + rendering block
            after_scripts = html[script_end+9:]
            break
        search_from = script_end + 1

    sm_raw_js = "\n<script>\n" + gen_sm_raw() + "\n</script>\n"
    html = html[:sm_start] + sm_raw_js + VOTE_JS + ARENA_JS + after_scripts

    # 4. Remove old vote2d.js script tag and its inline script
    html = html.replace('<script src="vote2d.js?v=10"></script>\n', '')

    return html


if __name__ == "__main__":
    html = HTML_PATH.read_text()
    new_html = transform(html)
    HTML_PATH.write_text(new_html)
    print(f"Done. Lines: {len(html.splitlines())} → {len(new_html.splitlines())}")
