#!/usr/bin/env python3
"""Upgrade the constitutional topic page to the issue-arena page format."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs/constitutional-amendment-reaction-map.html"
DATA = ROOT / "social-samples/constitutional_amendment_hermes_arena_classified.json"

ISSUES = [
    ("改憲全般", "憲法を時代に合わせるべきか、現行憲法の原則を守るべきか。"),
    ("9条・自衛隊", "自衛隊を憲法に明記する意義と、9条の平和主義への影響。"),
    ("緊急事態条項", "災害などへの迅速な対応と、政府への権限集中リスク。"),
    ("国民投票・広告", "CM・ネット広告・資金力の差を含む国民投票の公平性。"),
    ("政党・発議手続き", "政党の姿勢、国会での合意形成、発議までの進め方。"),
    ("情報・議論の質", "事実確認、過激な断定、論点を理解できる情報環境。"),
]

ISSUE_STANCE_LABELS = [
    {
        "con": ("改憲に慎重", "現行憲法の原則を守り、改憲を急ぐことに慎重"),
        "neutral": ("情報・検討", "賛否を定めず、改憲論議の情報や論点を共有"),
        "process": ("合意を優先", "具体案と幅広い合意を整えてから判断"),
        "pro": ("改憲を支持", "社会や安全保障環境の変化に合わせた改正を支持"),
    },
    {
        "con": ("9条改正に反対", "9条改正・自衛隊明記による平和主義の後退を警戒"),
        "neutral": ("位置づけを検討", "自衛隊の法的位置づけや改正論点を説明・検討"),
        "process": ("議論を優先", "自衛隊明記の前に国民的議論と手続きを重視"),
        "pro": ("自衛隊明記を支持", "自衛隊の憲法明記と国防上の位置づけ明確化を支持"),
    },
    {
        "con": ("権限集中を警戒", "政府への権限集中、選挙停止、条項の濫用を警戒"),
        "neutral": ("条項内容を検討", "緊急事態条項の内容や必要性を説明・検討"),
        "process": ("制度設計を優先", "国民への周知、適用条件、権力抑制の設計を優先"),
        "pro": ("条項新設を支持", "災害や有事への迅速な対応のため条項新設を支持"),
    },
    {
        "con": ("投票の公平性を懸念", "広告量や資金力、最低投票率の不備から現行制度を批判"),
        "neutral": ("手続き情報を共有", "国民投票の仕組み、採決結果、制度上の論点を共有"),
        "process": ("広告規制を重視", "CM・ネット広告規制と公平な判断環境の整備を重視"),
        "pro": ("国民投票を支持", "現行手続きに沿って国民投票で判断することを支持"),
    },
    {
        "con": ("拙速な発議に反対", "政党の姿勢や国会審議を批判し、拙速な発議に反対"),
        "neutral": ("政党動向を共有", "各党の賛否、議席状況、国会審議の動向を共有"),
        "process": ("合意形成を重視", "発議前の十分な審議と幅広い政党間合意を重視"),
        "pro": ("発議を支持", "改憲案を発議し、国民投票へ進めることを支持"),
    },
    {
        "con": ("情報環境を警戒", "一方的な主張や現政権下の議論環境に懸念"),
        "neutral": ("事実確認・論点整理", "数値、発言、一次資料を確認し、論点を整理"),
        "process": ("対話を重視", "賛否を封殺せず、根拠に基づく対話を重視"),
        "pro": ("改憲論の発信を支持", "改憲の必要性や賛成理由を伝える情報発信を支持"),
    },
]


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def issue_index(row: dict) -> int:
    c = row.get("classification") or {}
    main_issue = str(c.get("main_issue") or "")
    for idx, (name, _) in enumerate(ISSUES):
        if main_issue == name:
            return idx
    issue = str(c.get("issue") or "")
    category = str(c.get("category") or "")
    if issue == "9条・自衛隊" or category.startswith("9条・"):
        return 1
    if issue == "緊急事態条項" or category.startswith("緊急事態条項"):
        return 2
    if issue == "国民投票法" or category == "国民投票法・広告規制を重視":
        return 3
    if issue == "政党姿勢" or category == "政党・議員批判":
        return 4
    if issue in {"情報共有", "不明"} or category in {
        "事実確認・情報共有", "未確認・過激表現", "その他・分類保留"
    }:
        return 5
    return 0


def stance_key(row: dict) -> str:
    c = row.get("classification") or {}
    category = str(c.get("category") or "")
    stance = str(c.get("stance") or c.get("stance_to_target") or "")
    if stance == "改正推進":
        return "pro"
    if stance == "慎重・反対":
        return "con"
    if stance == "手続き重視":
        return "process"
    if stance == "中立":
        return "neutral"
    if "賛成" in category or stance in {"改憲支持", "支持"}:
        return "pro"
    if "反対" in category or "護憲" in category or stance in {"改憲反対", "反対", "問題視"}:
        return "con"
    if "国民投票" in category or "手続き" in category or stance in {"手続き重視", "慎重"}:
        return "process"
    return "neutral"


def intensity(row: dict) -> float:
    c = row.get("classification") or {}
    classified = str(c.get("intensity") or "")
    if classified in {"low", "medium", "high"}:
        return {"low": 0.34, "medium": 0.66, "high": 0.94}[classified]
    risk = str(c.get("risk") or "")
    text = str(row.get("text") or "")
    value = 0.34 + min(len(text), 260) / 520
    if risk in {"medium", "high"}:
        value += 0.18
    if any(mark in text for mark in ("！", "!", "絶対", "許さ", "💢", "危険")):
        value += 0.14
    return round(min(value, 1.0), 2)


def sample_cards(rows: list[dict], idx: int) -> str:
    candidates = [r for r in rows if issue_index(r) == idx and r.get("url")]
    candidates = [
        r for r in candidates
        if bool((r.get("classification") or {}).get("article_usable", True))
        and str((r.get("classification") or {}).get("risk") or "low") != "high"
    ]
    caution_phrases = ("選挙は不要", "拷問", "虐殺", "共和制移行", "戦争が近い")
    candidates.sort(
        key=lambda r: (
            not bool((r.get("classification") or {}).get("article_usable", True)),
            any(p in str((r.get("classification") or {}).get("summary") or "") for p in caution_phrases),
            -float((r.get("classification") or {}).get("confidence") or 0),
        )
    )
    picked: list[dict] = []
    seen: set[str] = set()
    order = (
        ("process", "con", "pro", "neutral") if idx == 3
        else ("neutral", "con", "pro", "process") if idx == 5
        else ("con", "pro", "process", "neutral")
    )
    for key in order:
        for row in candidates:
            if stance_key(row) == key and row["url"] not in seen:
                picked.append(row)
                seen.add(row["url"])
                break
        if len(picked) == 2:
            break
    for row in candidates:
        if len(picked) == 2:
            break
        if row["url"] not in seen:
            picked.append(row)
            seen.add(row["url"])
    labels = {"pro": "改憲・推進寄り", "con": "護憲・慎重寄り", "process": "手続き重視", "neutral": "中立・情報"}
    cards = []
    for row in picked:
        c = row.get("classification") or {}
        cards.append(
            '<div class="sample-card"><div class="meta">'
            + esc(labels[stance_key(row)])
            + " / conf "
            + esc(c.get("confidence") or "—")
            + "</div><p>"
            + esc(c.get("summary") or "投稿の要旨")
            + '</p><blockquote class="twitter-tweet" data-conversation="none" data-dnt="true"><a href="'
            + esc(row["url"])
            + '"></a></blockquote></div>'
        )
    return "".join(cards)


def build_explainer() -> str:
    cards = [
        (
            "general", "改憲全般",
            "憲法を社会の変化に合わせるのか、権力を縛る原則として慎重に守るのか。",
            "改正推進：現実に合うルールへ", "慎重・反対：拙速な変更を防ぐ",
        ),
        (
            "article9", "9条・自衛隊",
            "自衛隊の存在と任務を明記する意義と、9条の平和主義への影響を考える。",
            "改正推進：法的位置づけを明確に", "慎重・反対：平和主義の歯止めを維持",
        ),
        (
            "emergency", "緊急事態条項",
            "重大な危機への即応力と、政府への権限集中を防ぐ仕組みをどう設計するか。",
            "整備賛成：危機対応を迅速に", "慎重・反対：権限濫用を警戒",
        ),
        (
            "referendum", "国民投票・広告",
            "自由な意見表明を守りながら、資金力や広告量の差をどう整えるか。",
            "自由を重視：多様な意見を届ける", "公平性を重視：判断環境を整える",
        ),
        (
            "process", "政党・発議手続き",
            "具体案を国民に問う機会と、国会での十分な審議・合意形成をどう両立するか。",
            "発議推進：国民投票で判断を", "慎重論：幅広い合意を先に",
        ),
        (
            "information", "情報・議論の質",
            "条文・根拠・発言主体・引用関係を確認し、文脈不足の情報をどう扱うか。",
            "確認する：一次資料と文脈を見る", "保留する：不明な情報は断定しない",
        ),
    ]
    rendered = []
    for idx, (slug, title, desc, pro, con) in enumerate(cards, 1):
        image = f"images/topics/constitutional-amendment/constitutional-infographic-wide-{slug}.webp"
        rendered.append(
            f'<article class="explainer-card" data-img="{image}" data-alt="{esc(title)}">'
            '<div class="explainer-card-label">'
            f'<span class="explainer-num">争点{idx}</span><div>'
            f'<p class="explainer-card-title">{esc(title)}</p>'
            f'<p class="explainer-card-desc">{esc(desc)}</p>'
            '<div class="explainer-sides">'
            f'<span class="explainer-side pro">{esc(pro)}</span>'
            f'<span class="explainer-side con">{esc(con)}</span>'
            '</div></div></div>'
            f'<img src="{image}" alt="争点{idx} {esc(title)}" loading="lazy">'
            '</article>'
        )
    return """<section class="panel" id="explainer-section">
<div class="panel-title"><h2>このテーマを読み解く、6つの論点</h2><span>図解で全論点をチェック</span></div>
<p class="explainer-lead">憲法改正は、改正全般への賛否だけでは整理できません。9条、緊急事態条項、国民投票の公平性、発議手続き、情報環境ではそれぞれ対立の理由が異なります。6つの図解を確認してから、自分が重く見る論点を選んでください。画像はタップで拡大できます。</p>
<div class="explainer-grid">""" + "".join(rendered) + """</div>
<p class="explainer-note"><strong>使い方:</strong> 6つの争点を図解で確認してから、次の投票で「一番気になる論点」を選んでください。</p>
</section>
<div class="explainer-modal" id="explainer-modal" role="dialog" aria-modal="true" aria-hidden="true">
  <button class="explainer-modal-close" id="explainer-modal-close" type="button" aria-label="閉じる">×</button>
  <img src="" alt="" id="explainer-modal-img">
</div>
<script>
(function(){
  var modal=document.getElementById('explainer-modal');
  var modalImg=document.getElementById('explainer-modal-img');
  var closeBtn=document.getElementById('explainer-modal-close');
  document.querySelectorAll('#explainer-section .explainer-card').forEach(function(card){
    card.addEventListener('click',function(){
      modalImg.src=card.dataset.img;
      modalImg.alt=card.dataset.alt;
      modal.classList.add('open');
      modal.setAttribute('aria-hidden','false');
    });
  });
  function closeModal(){modal.classList.remove('open');modal.setAttribute('aria-hidden','true');}
  closeBtn.addEventListener('click',closeModal);
  modal.addEventListener('click',function(e){if(e.target===modal)closeModal();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal();});
})();
</script>"""


def build_vote() -> str:
    issues = json.dumps(
        [{"k": name, "d": desc, "icon": icon} for (name, desc), icon in zip(
            ISSUES, ("📜", "🕊️", "🚨", "🗳️", "🏛️", "🔎")
        )],
        ensure_ascii=False,
    )
    return f"""<section class="panel" id="vote-section">
<div class="panel-title"><h2>あなたはどの論点を重く見る？</h2><span>SNSの声を見る前に</span></div>
<p>憲法改正は、9条や緊急事態条項だけでなく、国民投票の公平性や議論の進め方まで含むテーマです。まず一番気になる論点を選び、次に改正への総合的な考えを選んでください。</p>
<div class="data-method"><strong>データの集め方:</strong> 「憲法改正」「9条」「緊急事態条項」「国民投票法」などのキーワードで、Yahooリアルタイム検索からSNS投稿422件を取得し、AIが自動分類しました。</div>
<div id="vote-step1"><p class="vote-step-label"><span class="step-num">1</span>一番気になる論点を選ぶ <small>（全2問）</small></p><div id="vote-issue-btns"></div></div>
<div id="vote-step2" hidden><p class="vote-step-label"><span class="step-num">2</span>憲法改正への考えは？ <small class="vote-step2-helper">選ぶと結果を表示します</small></p><div id="vote-stance-btns"></div></div>
<div id="vote-result" hidden></div>
</section>
<script>
(function(){{
  const issues={issues};
  const stances=[
    {{k:'改正を進める',d:'必要な項目を具体化し、改正を前へ進めたい',c:'#2563eb',icon:'→'}},
    {{k:'慎重・反対',d:'平和主義や権力制限を守り、改正には慎重でありたい',c:'#dc2626',icon:'×'}},
    {{k:'手続きを優先',d:'中身の前に、公平な国民投票と合意形成を整えたい',c:'#059669',icon:'◎'}},
    {{k:'まだ決められない',d:'論点ごとの情報を見てから考えたい',c:'#64748b',icon:'?'}}
  ];
  let selected=-1;
  const issueBox=document.getElementById('vote-issue-btns');
  issues.forEach((v,i)=>{{const b=document.createElement('button');b.className='vote-issue-btn';b.innerHTML='<span>'+v.icon+'</span><span><strong>'+v.k+'</strong><small>'+v.d+'</small></span>';b.onclick=()=>{{selected=i;document.getElementById('vote-step1').hidden=true;document.getElementById('vote-step2').hidden=false;}};issueBox.appendChild(b);}});
  const stanceBox=document.getElementById('vote-stance-btns');
  stances.forEach(v=>{{const b=document.createElement('button');b.className='vote-stance-btn';b.style.setProperty('--stance-color',v.c);b.innerHTML='<b>'+v.icon+'</b><strong>'+v.k+'</strong><small>'+v.d+'</small>';b.onclick=()=>{{document.getElementById('vote-step2').hidden=true;const r=document.getElementById('vote-result');r.hidden=false;r.innerHTML='<strong>あなたの選択</strong><p>「'+issues[selected].k+'」を重視し、総合的には「'+v.k+'」</p><button type="button" id="vote-redo">選び直す</button>';window.setConstitutionalVoteMarker?.(selected,v.c);document.getElementById('vote-redo').onclick=()=>{{r.hidden=true;document.getElementById('vote-step1').hidden=false;}};}};stanceBox.appendChild(b);}});
}})();
</script>"""


def build_arena(rows: list[dict]) -> str:
    points = []
    counts = Counter()
    stance_counts: list[Counter] = [Counter() for _ in ISSUES]
    for row in rows:
        idx = issue_index(row)
        key = stance_key(row)
        counts[idx] += 1
        stance_counts[idx][key] += 1
        c = row.get("classification") or {}
        points.append({
            "i": idx, "t": intensity(row), "s": str(c.get("summary") or "")[:120],
            "u": row.get("url") or "", "k": key,
        })
    issue_data = [{"k": name, "n": counts[i]} for i, (name, _) in enumerate(ISSUES)]
    return f"""<section class="panel stance-map-section" id="stance-map-section">
<div id="stance-map-inner">
<div class="panel-title"><h2>SNS反応マップ</h2><span>意見422件 | セクター=論点 / 中心に近いほど冷静 / 色=立場 | ホバーで詳細・クリックでXへ</span></div>
<div id="sm-wrap">
  <canvas id="smCanvasHeat" width="640" height="640"></canvas>
  <canvas id="smCanvasMain" width="640" height="640"></canvas>
</div>
<p class="map-caption">中心の「憲法改正」を6つの論点セクターが囲みます。扇の大きさは投稿数、中心からの距離は主張の強さ（外側ほど強い反応）、点の色は立場（青=改正推進 / 赤=慎重・反対 / 緑=手続き重視 / 灰=中立）。点をクリックすると元のXポストを開きます。</p>
<div class="sm-controls"><div class="sm-legend"><span><i style="background:#2563eb"></i>改正推進</span><span><i style="background:#dc2626"></i>慎重・反対</span><span><i style="background:#059669"></i>手続き重視</span><span><i style="background:#64748b"></i>中立・情報</span></div><div class="sm-filters" id="sm-filters"></div></div>
<div id="sm-tooltip"></div>
</div>
</section>
<div class="arena-divider"><img src="images/shared/arena-divider.webp" alt="" loading="lazy"></div>
<script>
(function(){{
  'use strict';
const ISSUES={json.dumps(issue_data, ensure_ascii=False)};
const P={json.dumps(points, ensure_ascii=False, separators=(',', ':'))};
const colors={{pro:'#2563eb',con:'#dc2626',process:'#059669',neutral:'#64748b'}};
const W=640,CX=320,CY=320,R_MIN=64,R_MAX=214,R_HOLE=56,R_LBL=244,PAD_DEG=2.5;
const canvas=document.getElementById('smCanvasMain');
const heat=document.getElementById('smCanvasHeat');
const ctx=canvas.getContext('2d');
const hctx=heat.getContext('2d');
const tip=document.getElementById('sm-tooltip');
let filter=-1,marker=null;

const total=ISSUES.reduce((a,v)=>a+v.n,0);
const usable=360-PAD_DEG*2*ISSUES.length;
let acc=-90;
ISSUES.forEach(v=>{{
  const span=usable*v.n/Math.max(total,1);
  v.a0=acc+PAD_DEG;v.a1=v.a0+span;v.mid=(v.a0+v.a1)/2;
  acc=v.a1+PAD_DEG;
}});

function rnd(seed){{const x=Math.sin(seed*127.1+311.7)*43758.5453;return x-Math.floor(x);}}
const pts=[];
P.forEach((p,j)=>{{
  const v=ISSUES[p.i];if(!v)return;
  const angle=v.a0+rnd(j)*(v.a1-v.a0);
  const strength=Math.max(0,Math.min(1,p.t+(rnd(j+500)-.5)*.26));
  let radius=R_MIN+10+strength*(R_MAX-R_MIN-28);
  radius=Math.max(R_MIN+4,Math.min(R_MAX-4,radius));
  const rad=angle*Math.PI/180;
  pts.push({{x:CX+Math.cos(rad)*radius,y:CY+Math.sin(rad)*radius,p}});
}});

function drawHeat(){{
  hctx.clearRect(0,0,W,W);
  hctx.fillStyle='#fdfdff';hctx.fillRect(0,0,W,W);
  const maxN=Math.max(...ISSUES.map(v=>v.n));
  ISSUES.forEach(v=>{{
    const a0=v.a0*Math.PI/180,a1=v.a1*Math.PI/180;
    hctx.beginPath();
    hctx.moveTo(CX+R_MIN*Math.cos(a0),CY+R_MIN*Math.sin(a0));
    hctx.arc(CX,CY,R_MAX,a0,a1);
    hctx.arc(CX,CY,R_MIN,a1,a0,true);
    hctx.closePath();
    hctx.fillStyle='rgba(37,99,235,'+(0.035+v.n/maxN*.09).toFixed(3)+')';
    hctx.fill();
    hctx.strokeStyle='rgba(100,116,139,.28)';hctx.lineWidth=1;hctx.stroke();
  }});
  hctx.setLineDash([3,5]);hctx.strokeStyle='rgba(100,116,139,.28)';
  [110,160,R_MAX].forEach(r=>{{hctx.beginPath();hctx.arc(CX,CY,r,0,Math.PI*2);hctx.stroke();}});
  hctx.setLineDash([]);
}}

function draw(){{
  ctx.clearRect(0,0,W,W);
  pts.forEach(pt=>{{
    const dim=filter>=0&&pt.p.i!==filter;
    ctx.globalAlpha=dim?.08:.82;
    ctx.beginPath();ctx.arc(pt.x,pt.y,4,0,Math.PI*2);
    ctx.fillStyle=colors[pt.p.k];ctx.fill();
  }});
  ctx.globalAlpha=1;
  ctx.font='900 12px "Noto Sans JP",sans-serif';
  ISSUES.forEach((v,i)=>{{
    const rad=v.mid*Math.PI/180,lx=CX+R_LBL*Math.cos(rad),ly=CY+R_LBL*Math.sin(rad),c=Math.cos(rad);
    ctx.textAlign=c>.35?'left':(c<-.35?'right':'center');
    ctx.textBaseline='middle';
    ctx.fillStyle=(filter>=0&&i!==filter)?'rgba(100,116,139,.4)':'#334155';
    ctx.fillText(v.k+' '+v.n,lx,ly);
  }});
  ctx.beginPath();ctx.arc(CX,CY,R_HOLE,0,Math.PI*2);
  ctx.fillStyle='#fff';ctx.fill();ctx.strokeStyle='#bfdbfe';ctx.lineWidth=1.5;ctx.stroke();
  ctx.fillStyle='#172554';ctx.textAlign='center';ctx.textBaseline='alphabetic';
  ctx.font='900 15px "Noto Sans JP",sans-serif';
  ctx.fillText('憲法',CX,CY-9);ctx.fillText('改正',CX,CY+12);
  ctx.font='400 10px "Noto Sans JP",sans-serif';ctx.fillStyle='#64748b';
  ctx.fillText('冷静',CX,CY-R_MIN-8);ctx.fillText('主張が強い',CX,CY-R_MAX-8);
  if(marker){{
    const v=ISSUES[marker.i];
    if(v){{
      const ang=v.mid*Math.PI/180,x=CX+Math.cos(ang)*150,y=CY+Math.sin(ang)*150;
      ctx.beginPath();ctx.arc(x,y,12,0,Math.PI*2);ctx.fillStyle='#fff';ctx.fill();
      ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.fillStyle=marker.c;ctx.fill();
      ctx.strokeStyle=marker.c;ctx.lineWidth=2;ctx.stroke();
      ctx.fillStyle=marker.c;ctx.font='900 12px "Noto Sans JP",sans-serif';ctx.textAlign='center';
      ctx.fillText('あなたはココ',x,y-18);
    }}
  }}
}}
function near(ev){{
  const r=canvas.getBoundingClientRect(),x=(ev.clientX-r.left)*W/r.width,y=(ev.clientY-r.top)*W/r.height;
  let best=null,bd=225;
  pts.forEach(q=>{{if(filter>=0&&q.p.i!==filter)return;const d=(q.x-x)**2+(q.y-y)**2;if(d<bd){{best=q;bd=d;}}}});
  return best;
}}
canvas.onmousemove=ev=>{{
  const q=near(ev);
  if(!q){{tip.style.display='none';canvas.style.cursor='crosshair';return;}}
  const rect=canvas.getBoundingClientRect();
  tip.style.display='block';
  tip.style.left=Math.min(ev.clientX-rect.left+14,rect.width-270)+'px';
  tip.style.top=(ev.clientY-rect.top+14)+'px';
  tip.innerHTML='<strong>'+ISSUES[q.p.i].k+'</strong><br>'+q.p.s.replace(/</g,'&lt;')+'<br><small>クリックでXの投稿へ</small>';
  canvas.style.cursor=q.p.u?'pointer':'default';
}};
canvas.onmouseleave=()=>{{tip.style.display='none';}};
canvas.onclick=ev=>{{const q=near(ev);if(q?.p.u)window.open(q.p.u,'_blank','noopener');}};
const filters=document.getElementById('sm-filters');
['すべて',...ISSUES.map(v=>v.k)].forEach((k,i)=>{{
  const b=document.createElement('button');b.className='sm-fbtn'+(i===0?' active':'');b.textContent=k;
  b.onclick=()=>{{filter=i-1;filters.querySelectorAll('button').forEach(x=>x.classList.remove('active'));b.classList.add('active');draw();}};
  filters.appendChild(b);
}});
window.setConstitutionalVoteMarker=(i,c)=>{{marker={{i,c}};draw();document.getElementById('stance-map-section').scrollIntoView({{behavior:'smooth'}});}};
drawHeat();draw();
}})();
</script>"""


def build_issues(rows: list[dict]) -> str:
    blocks = []
    for idx, (name, desc) in enumerate(ISSUES):
        subset = [r for r in rows if issue_index(r) == idx]
        counts = Counter(stance_key(r) for r in subset)
        issue_labels = ISSUE_STANCE_LABELS[idx]
        summary = " / ".join(
            f"{issue_labels[k][0]} {counts[k]}"
            for k in ("con", "neutral", "process", "pro")
            if counts[k]
        )
        total = max(len(subset), 1)
        bar_order = (
            ("con", "con"),
            ("neutral", "neutral"),
            ("process", "process"),
            ("pro", "pro"),
        )
        segments = []
        legends = []
        for key, class_name in bar_order:
            count = counts[key]
            if not count:
                continue
            _, legend_label = issue_labels[key]
            percentage = count / total * 100
            percentage_label = f"{round(percentage)}%" if percentage >= 7 else ""
            segments.append(
                f'<div class="temp-seg {class_name}" style="width:{percentage:.2f}%">'
                f"{percentage_label}</div>"
            )
            legends.append(
                f'<span><i class="{class_name}"></i>{esc(legend_label)}（{count}件）</span>'
            )
        stance_bar = (
            '<div class="temp-bar-wrap">'
            '<div class="temp-bar-label"><span>X投稿のスタンス構成</span>'
            f'<span>{esc(summary)}</span></div>'
            f'<div class="temp-bar">{"".join(segments)}</div>'
            f'<div class="temp-bar-legend">{"".join(legends)}</div>'
            '</div>'
        )
        blocks.append(
            f'<article class="issue-block" id="issue-{idx}"><div class="issue-head"><span class="axis-kicker">論点 {idx + 1}</span>'
            f'<h3>{esc(name)}<span class="issue-count">{len(subset)}件</span></h3></div>'
            f'<p class="issue-desc">{esc(desc)}</p>{stance_bar}'
            f'<div class="sample-grid">{sample_cards(rows, idx)}</div></article>'
        )
    return '<section class="panel conflict-panel"><div class="panel-title"><h2>6つの論点とXの声</h2><span>論点ごとに立場を読み比べる</span></div>' + "".join(blocks) + "</section>"


def replace_between(source: str, start: str, end: str, replacement: str) -> str:
    a = source.index(start)
    b = source.index(end, a)
    return source[:a] + replacement + "\n" + source[b:]


def main() -> None:
    rows = json.loads(DATA.read_text())
    source = PAGE.read_text()
    source = re.sub(r'topic-modern\.css\?v=\d+', 'topic-modern.css?v=11', source)
    source = re.sub(
        r'\s*<section class="panel" id="manga-section">.*?</section>\s*'
        r'(?=<section class="panel" id="explainer-section">)',
        "\n",
        source,
        count=1,
        flags=re.S,
    )
    source = re.sub(
        r'\s*<script src="manga-viewer\.js"></script>\s*'
        r'<script>\s*MangaViewer\.init\(\{.*?</script>\s*',
        "\n",
        source,
        count=1,
        flags=re.S,
    )
    source = re.sub(
        r'\n\s*\.manga-intro \{.*?\.manga-modal \.manga-next \{.*?\}\n',
        "\n",
        source,
        count=1,
        flags=re.S,
    )
    source = source.replace('      .manga-grid { grid-template-columns: 1fr; }\n', '')
    if 'id="explainer-section"' not in source:
        source = source.replace(
            '<section class="panel" id="vote-section">',
            build_explainer() + '\n<section class="panel" id="vote-section">',
            1,
        )
    arena_section = (
        '<section class="panel" id="stance-map-section">'
        if '<section class="panel" id="stance-map-section">' in source
        else '<section class="panel stance-map-section" id="stance-map-section">'
    )
    source = replace_between(
        source,
        '<section class="panel" id="vote-section">',
        arena_section,
        build_vote(),
    )
    source = re.sub(
        r'<script src="vote2d\.js\?v=10"></script>.*?(?=<section class="panel" id="stance-map-section">)',
        "",
        source,
        flags=re.S,
    )
    issue_section = (
        '<section class="panel"><div class="panel-title"><h2>象限別の代表的な声</h2>'
        if '象限別の代表的な声' in source
        else '<section class="panel conflict-panel"><div class="panel-title"><h2>6つの論点とXの声</h2>'
    )
    source = replace_between(
        source,
        arena_section,
        issue_section,
        build_arena(rows),
    )
    source = replace_between(
        source,
        issue_section,
        '<section class="panel background-panel">',
        build_issues(rows),
    )
    css = """
    .data-method{font-size:12px;color:var(--muted);background:var(--accent-soft);border-radius:8px;padding:10px 14px;margin:0 0 20px}
    .vote-step-label{display:flex;align-items:center;gap:8px;font-weight:900;margin:18px 0 14px}.vote-step-label small{font-weight:400;color:var(--muted)}
    .step-num{display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--accent);color:#fff;font-size:13px}
    #vote-issue-btns{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.vote-issue-btn{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);border-radius:10px;padding:14px;background:#fff;text-align:left;cursor:pointer;font-family:inherit}.vote-issue-btn>span:first-child{font-size:22px}.vote-issue-btn strong,.vote-issue-btn small{display:block}.vote-issue-btn small{color:var(--muted);margin-top:4px}
    #vote-stance-btns{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.vote-stance-btn{border:1px solid var(--line);border-top:5px solid var(--stance-color);border-radius:10px;padding:14px;background:#fff;text-align:left;cursor:pointer;font-family:inherit}.vote-stance-btn b,.vote-stance-btn strong,.vote-stance-btn small{display:block}.vote-stance-btn b{color:var(--stance-color);font-size:22px}.vote-stance-btn small{color:var(--muted);margin-top:5px}
    #vote-result{border-left:5px solid var(--accent);background:var(--accent-soft);padding:14px 18px;border-radius:8px}#vote-result p{margin:5px 0}#vote-redo{border:1px solid var(--line);background:#fff;border-radius:7px;padding:6px 10px;cursor:pointer}
    .stance-map-section{background:#0f0e2e url('images/shared/arena-bg.webp') center/cover no-repeat!important}.stance-map-section .panel-title h2{color:#fff}.stance-map-section .panel-title span,.map-caption{color:rgba(255,255,255,.72)}
    #stance-map-inner{max-width:800px;margin:auto}#sm-wrap{position:relative;max-width:660px;margin:16px auto;background:#fff;border-radius:14px;padding:6px;box-shadow:0 18px 50px rgba(0,0,0,.35)}#sm-wrap #smCanvasHeat{top:6px;left:6px;width:calc(100% - 12px);height:calc(100% - 12px)}#smCanvasMain{display:block;width:100%;border-radius:10px}#sm-tooltip{position:absolute;display:none;z-index:5;max-width:260px;background:#172554;color:#fff;padding:10px 12px;border-radius:8px;font-size:12px;pointer-events:none}
    .sm-controls{max-width:760px;margin:auto}.sm-legend,.sm-filters{display:flex;gap:8px;flex-wrap:wrap;color:#fff;font-size:12px}.sm-legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px}.sm-filters{margin-top:10px}.sm-fbtn{border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:6px 10px;background:rgba(255,255,255,.1);color:#fff;cursor:pointer}.sm-fbtn.active{background:var(--accent)}
    .arena-divider{line-height:0}.arena-divider img{display:block;width:100%}.issue-block{border:1px solid var(--line);border-radius:12px;background:#fff;padding:22px;margin-bottom:22px;box-shadow:var(--shadow)}.issue-head h3{font-size:24px;margin:5px 0}.issue-count{font-size:13px;color:var(--accent);background:var(--accent-soft);border-radius:999px;padding:3px 10px;margin-left:8px}.issue-balance{font-size:12px;font-weight:800;color:var(--muted);margin-bottom:14px}.temp-bar-wrap{margin:0 0 18px}.temp-bar-label{display:flex;justify-content:space-between;gap:12px;margin-bottom:7px;color:var(--muted);font-size:12px;font-weight:800}.temp-bar{display:flex;height:28px;overflow:hidden;border-radius:7px;background:#e7e7f7}.temp-seg{display:flex;align-items:center;justify-content:center;min-width:2px;color:#fff;font-size:11px;font-weight:900}.temp-seg.con{background:#dc2626}.temp-seg.neutral{background:#94a3b8}.temp-seg.process{background:#059669}.temp-seg.pro{background:#2563eb}.temp-bar-legend{display:flex;flex-wrap:wrap;gap:7px 14px;margin-top:7px;color:var(--muted);font-size:11px;font-weight:800}.temp-bar-legend i{display:inline-block;width:10px;height:10px;margin-right:4px;border-radius:2px;vertical-align:middle}.temp-bar-legend i.con{background:#dc2626}.temp-bar-legend i.neutral{background:#94a3b8}.temp-bar-legend i.process{background:#059669}.temp-bar-legend i.pro{background:#2563eb}.sample-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.sample-card{border:1px solid var(--line);border-radius:8px;padding:14px;background:#fff}.sample-card .meta{font-size:12px;color:var(--accent);font-weight:900}
    @media(max-width:760px){#vote-issue-btns,#vote-stance-btns,.sample-grid{grid-template-columns:1fr}.temp-bar-label{flex-direction:column;gap:2px}.temp-bar-legend{gap:5px 10px}}
"""
    explainer_css = """
    #explainer-section .explainer-lead{font-size:14px;color:var(--ink);line-height:1.85;margin:0 0 18px;max-width:1000px}
    #explainer-section .explainer-grid{display:flex;flex-direction:column;gap:18px}
    #explainer-section .explainer-card{border-radius:12px;overflow:hidden;background:#fff;border:1.5px solid #e4eaf3;box-shadow:0 8px 24px rgba(16,24,40,.08);cursor:zoom-in;transition:transform .2s ease,box-shadow .2s ease}
    #explainer-section .explainer-card:hover{transform:translateY(-3px);box-shadow:0 16px 36px rgba(16,24,40,.14);border-color:#c7d4ea}
    #explainer-section .explainer-card img{display:block;width:100%;aspect-ratio:1916/821;object-fit:cover;background:var(--accent-soft)}
    #explainer-section .explainer-card-label{display:flex;align-items:flex-start;gap:12px;padding:14px 18px;background:#fff;border-bottom:1.5px solid #e4eaf3}
    #explainer-section .explainer-num{flex-shrink:0;background:#0a3d91;color:#fff;font-size:11px;font-weight:900;letter-spacing:.05em;border-radius:6px;padding:4px 10px;margin-top:3px;line-height:1.3}
    #explainer-section .explainer-card-title{font-size:16px;font-weight:900;color:#0a245e;margin:0 0 4px;line-height:1.35}
    #explainer-section .explainer-card-desc{font-size:12px;color:#637089;margin:0 0 7px;line-height:1.65}
    #explainer-section .explainer-sides{display:flex;gap:6px;flex-wrap:wrap}
    #explainer-section .explainer-side{font-size:11px;font-weight:800;border-radius:5px;padding:3px 9px;line-height:1.4}
    #explainer-section .explainer-side.pro{background:#eff6ff;color:#075ef2;border:1px solid #bfdbfe}
    #explainer-section .explainer-side.con{background:#fff2ee;color:#c0410f;border:1px solid #fdbcaa}
    #explainer-section .explainer-note{font-size:12px;color:var(--muted);background:var(--accent-soft);border-radius:8px;padding:10px 14px;margin:16px 0 0;line-height:1.65}
    .explainer-modal{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(15,23,42,.9)}
    .explainer-modal.open{display:flex}
    .explainer-modal img{max-width:96vw;max-height:92vh;border-radius:8px;object-fit:contain;box-shadow:0 24px 70px rgba(0,0,0,.45)}
    .explainer-modal-close{position:absolute;top:16px;right:20px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.28);border-radius:50%;width:42px;height:42px;color:#fff;font-size:24px;cursor:pointer}
    @media(max-width:760px){#explainer-section .explainer-grid{gap:12px}#explainer-section .explainer-card-label{padding:12px;gap:8px}#explainer-section .explainer-card-title{font-size:14px}#explainer-section .explainer-card img{aspect-ratio:1916/821}}
"""
    if ".data-method{font-size:12px" not in source:
        source = source.replace("</style>", css + "\n  </style>", 1)
    if "#explainer-section .explainer-grid" not in source:
        source = source.replace("</style>", explainer_css + "\n  </style>", 1)
    source = source.replace(
        '<div class="stat"><span>総サンプル</span><strong>422</strong></div>',
        '<div class="stat"><span>分類投稿</span><strong>422件</strong></div>',
    ).replace(
        '<div class="stat"><span>ソース</span><strong>Yahooリアルタイム検索</strong></div>',
        '<div class="stat"><span>論点セクター</span><strong>6論点</strong></div>',
    )
    source = re.sub(
        r'<p class="lead">Yahooリアルタイム検索で取得したX反応サンプルを、.*?</p>',
        '<p class="lead">収集したSNS投稿のうち、分析対象となった意見422件をAIが6つの論点に整理しました。世論調査ではなく、SNS反応サンプルの論点比較です。</p>',
        source,
        count=1,
    )
    source = re.sub(
        r'<div class="thirty-summary"[^>]*>.*?</ul></div>',
        '<div class="thirty-summary" aria-label="まず結論：今回の分析で見えたこと">'
        '<header class="thirty-summary-title"><h2>まず結論</h2><p>今回の分析で見えたこと</p></header><ul>'
        '<li>最多論点は「改憲全般」116件。次いで「9条・自衛隊」103件、「国民投票・広告」96件。</li>'
        '<li>慎重・反対が218件で最多。改正推進91件、中立91件、手続き重視22件と、論点ごとに構図が変わります。</li>'
        '<li>9条・自衛隊では推進56件が慎重・反対33件を上回る一方、緊急事態条項では慎重・反対30件が推進2件を大きく上回りました。</li>'
        '</ul></div>',
        source,
        count=1,
        flags=re.S,
    )
    source = re.sub(
        r'<div class="stat"><span>最多カテゴリ</span><strong>.*?</strong></div>',
        '<div class="stat"><span>最多論点</span><strong>改憲全般 116件</strong></div>',
        source,
        count=1,
    )
    source = re.sub(
        r'<div class="stat"><span>最多スタンス</span><strong>.*?</strong></div>',
        '<div class="stat"><span>最多スタンス</span><strong>慎重・反対 218件</strong></div>',
        source,
        count=1,
    )
def _sync_issue_counts() -> None:
    """論点カードの件数を貼り直す。ここを外すと再ビルドで件数が消える。"""
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "sync_issue_counts.py"), "constitutional-amendment"],
        check=True,
    )


    PAGE.write_text(source)
    _sync_issue_counts()


if __name__ == "__main__":
    main()
