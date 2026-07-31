#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const htmlPath = path.join(root, 'docs', 'school-nickname-ban-reaction-map.html');
const dataPath = path.join(root, 'social-samples', 'school-nickname-ban_hermes_arena_classified.json');
const arenaPath = path.join(root, 'docs', 'school-nickname-ban-arena-data.js');

const allPosts = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

const issueDefs = [
  {
    key: 'safety',
    mainIssue: 'いじめ・心理的安全',
    title: 'いじめ・心理的安全',
    short: '心理的安全',
    icon: '🛡️',
    image: 'images/topics/school-nickname-ban/school-nickname-ban-infographic-wide-safety.webp',
    imageAlt: 'あだ名禁止の論点1、いじめ・心理的安全を解説するインフォグラフィック',
    explainerTitle: '呼び方のルールで、傷つく子を守れるか',
    explainerDesc: '最多17件。禁止支持6件、中立・体験10件、反対1件。被害予防と、対話・教育をどう組み合わせるかが焦点です。',
    explainerLeft: '支持：傷つく呼び方を予防',
    explainerRight: '慎重：対話・教育も必要',
    description: '嫌なあだ名やからかいを予防し、傷つく子を出さないために学校が介入すべきか。',
    support: '悪意の有無にかかわらず傷つく呼び方を予防し、安心を優先する。',
    oppose: '禁止だけでなく、相手の気持ちを聞く教育や個別対応も必要。',
    sideSupportLabel: '予防ルールで安全を優先',
    sideOpposeLabel: '対話・個別対応も組み合わせる',
    sampleStances: ['禁止支持', '一律禁止に反対'],
    barTitle: '傷つく呼び方への学校介入をどう見るか',
    stanceLabels: {
      oppose: ['個別対応を重視', '一律規制より対話・個別対応を重視'],
      conditional: ['条件付き介入', '本人の状況に応じた条件付き介入'],
      neutral: ['被害・実態を共有', '傷ついた経験や学校現場の実態を共有'],
      support: ['予防ルールを重視', '予防ルールで心理的安全を優先'],
    },
  },
  {
    key: 'effect',
    mainIssue: '一律禁止の実効性',
    title: '一律禁止の実効性',
    short: '実効性',
    icon: '🎯',
    image: 'images/topics/school-nickname-ban/school-nickname-ban-infographic-wide-effectiveness.webp',
    imageAlt: 'あだ名禁止の論点2、一律禁止の実効性を解説するインフォグラフィック',
    explainerTitle: '禁止すれば、いじめは減るのか',
    explainerDesc: '16件のうち一律禁止への反対が13件。入口を減らす予防効果と、問題が別の形で残る懸念を比べます。',
    explainerLeft: '予防：からかいの入口を減らす',
    explainerRight: '批判：いじめの本質は残る',
    description: '呼び方を一律に禁止することで、いじめの原因や関係性まで変えられるのか。',
    support: 'からかいの入口を減らす予防策として、一定の効果が期待できる。',
    oppose: '呼称だけを変えても、いじめの本質や別の攻撃手段は残る。',
    sideSupportLabel: 'からかいの入口を減らす',
    sideOpposeLabel: '本質的な関係改善を優先',
    sampleStances: ['条件付き・個別対応', '一律禁止に反対'],
    barTitle: '呼び方の禁止はいじめ予防に効くか',
    stanceLabels: {
      oppose: ['本質は変わらない', '禁止だけではいじめの本質は変わらない'],
      conditional: ['運用次第で効果', '対象や運用を絞れば予防効果がある'],
      neutral: ['運用実態を共有', '学校での禁止ルールや運用実態を共有'],
      support: ['入口を減らす', 'からかいの入口を減らす予防策として評価'],
    },
  },
  {
    key: 'culture',
    mainIssue: '親しさ・呼称文化',
    title: '親しさ・呼称文化',
    short: '呼称文化',
    icon: '🤝',
    image: 'images/topics/school-nickname-ban/school-nickname-ban-infographic-wide-culture.webp',
    imageAlt: 'あだ名禁止の論点3、親しさと呼称文化を解説するインフォグラフィック',
    explainerTitle: 'あだ名は親しさか、それとも負担か',
    explainerDesc: '13件のうち一律禁止への反対が10件。愛称が生む親しさと、受け手が感じる痛みの両方を扱います。',
    explainerLeft: '文化：親しさ・個性を尊重',
    explainerRight: '受け手：嫌なら止める',
    description: 'あだ名を親しさや個性の表現と見るか、傷つける可能性のある呼び方と見るか。',
    support: '本人が安心できる呼び方を優先し、学校が一定の線を引くべき。',
    oppose: '親しい愛称まで一律に禁じると、自然な関係づくりを損なう。',
    sideSupportLabel: '受け手の安心を優先',
    sideOpposeLabel: '親しさと個性を尊重',
    sampleStances: ['禁止支持', '一律禁止に反対'],
    barTitle: 'あだ名を親しさと負担のどちらから見るか',
    stanceLabels: {
      oppose: ['親しさを守る', '愛称や親しさを一律ルールで奪わない'],
      conditional: ['望む愛称だけ', '本人が望む愛称だけ柔軟に認める'],
      neutral: ['呼称文化を共有', '学校や世代による呼称文化の違いを共有'],
      support: ['傷つく呼称を止める', '傷つく可能性のある呼び方を学校が止める'],
    },
  },
  {
    key: 'experience',
    mainIssue: '学校運用・現場体験',
    title: '学校運用・現場体験',
    short: '現場体験',
    icon: '🏫',
    image: 'images/topics/school-nickname-ban/school-nickname-ban-infographic-wide-field.webp',
    imageAlt: 'あだ名禁止の論点4、学校運用と現場体験を解説するインフォグラフィック',
    explainerTitle: '現場では、ルールがどう受け止められるか',
    explainerDesc: '8件のうち6件が中立的な体験共有。学校・世代による差と、運用目的を説明できるかを見ます。',
    explainerLeft: '実態：学校・世代で違う',
    explainerRight: '運用：目的の説明が必要',
    description: '学校ごとの運用差や、自分・子どもが実際に経験した呼ばれ方から考える論点。',
    support: '嫌なあだ名がなくなり、安心して過ごせたという経験がある。',
    oppose: 'さん付けの強制に距離や窮屈さを感じたという経験がある。',
    sideSupportLabel: '安心につながった体験',
    sideOpposeLabel: '窮屈さを感じた体験',
    sampleStances: ['中立・情報', '禁止支持'],
    barTitle: '学校の呼称ルールを現場体験からどう評価するか',
    stanceLabels: {
      oppose: ['統一運用は窮屈', 'さん付けなどの統一運用に窮屈さを感じる'],
      conditional: ['現場ごとに調整', '学級や子どもの状況に応じた調整を求める'],
      neutral: ['現場体験を共有', '学校・家庭・世代ごとの体験や実態を共有'],
      support: ['安心につながった', '共通ルールで安心して過ごせた経験を共有'],
    },
  },
  {
    key: 'gender',
    mainIssue: 'さん付け・ジェンダー配慮',
    title: 'さん付け・ジェンダー配慮',
    short: 'さん付け',
    icon: '⚖️',
    image: 'images/topics/school-nickname-ban/school-nickname-ban-infographic-wide-gender.webp',
    imageAlt: 'あだ名禁止の論点5、さん付けとジェンダー配慮を解説するインフォグラフィック',
    explainerTitle: '「名字＋さん」統一は、対等さにつながるか',
    explainerDesc: '5件のうち一律禁止への反対が4件。性別で呼称を分けない配慮と、形式だけの統一への疑問を整理します。',
    explainerLeft: '配慮：性別で呼称を分けない',
    explainerRight: '懸念：形式だけでは変わらない',
    description: '「くん・ちゃん」の性差をなくし、名字＋さんへ統一する指導をどう見るか。',
    support: '性別や上下関係で呼び方を分けず、対等な敬称へ統一する。',
    oppose: 'さん付けの強制は形式的で、親しさや本人の希望を置き去りにする。',
    sideSupportLabel: '性別で呼称を分けない',
    sideOpposeLabel: '形式より本人希望を重視',
    sampleStances: ['一律禁止に反対', '中立・情報'],
    barTitle: '「名字＋さん」統一は対等さにつながるか',
    stanceLabels: {
      oppose: ['形式的な統一に疑問', 'さん付けの形式的な統一では対等さは生まれない'],
      conditional: ['本人希望も反映', '性別配慮と本人が望む呼び方を両立する'],
      neutral: ['呼称実態を共有', '学校での「くん・ちゃん・さん」の実態を共有'],
      support: ['性別で分けない', '性別で呼称を分けず対等な敬称に統一する'],
    },
  },
  {
    key: 'choice',
    mainIssue: '本人意思・柔軟運用',
    title: '本人意思と柔軟運用',
    short: '本人意思',
    icon: '🗣️',
    image: 'images/topics/school-nickname-ban/school-nickname-ban-infographic-wide-choice.webp',
    imageAlt: 'あだ名禁止の論点6、本人意思と柔軟運用を解説するインフォグラフィック',
    explainerTitle: '呼ばれる本人の意思を、中心に置けるか',
    explainerDesc: '4件すべてが条件付き・個別対応。望む愛称は認めつつ、嫌と言いにくい子をどう守るかが焦点です。',
    explainerLeft: '本人同意：望む愛称は認める',
    explainerRight: '支援：嫌と言いにくい子を守る',
    description: '禁止か自由かではなく、呼ばれる本人の意思をルールの中心に置けるか。',
    support: '嫌だと言いにくい子を守るには、共通ルールを出発点にすべき。',
    oppose: '本人が望む愛称は認め、嫌な呼び方だけを止めればよい。',
    sideSupportLabel: '共通ルールから守る',
    sideOpposeLabel: '本人意思で柔軟に',
    sampleStances: ['条件付き・個別対応'],
    barTitle: '呼び方のルールを誰の意思で決めるか',
    stanceLabels: {
      oppose: ['一律ルールに委ねない', '学校の一律ルールより個人間の関係を尊重'],
      conditional: ['本人意思で柔軟に', '望む愛称は認め、嫌な呼び方だけを止める'],
      neutral: ['本人の声を共有', '呼ばれる側の希望や言いにくさを共有'],
      support: ['共通ルールから守る', '嫌と言いにくい子を共通ルールから守る'],
    },
  },
];

const mainIssueToKey = new Map(issueDefs.map((issue) => [issue.mainIssue, issue.key]));

function stanceFor(post) {
  const stance = post.classification.stance;
  if (stance === '禁止支持') return 'support';
  if (stance === '一律禁止に反対') return 'oppose';
  if (stance === '条件付き・個別対応') return 'conditional';
  return 'neutral';
}

const intensityScale = { low: 0.3, medium: 0.64, high: 0.94 };
const arenaPosts = allPosts
  .filter((post) => (
    post.classification.is_relevant
    && post.classification.is_opinion
    && mainIssueToKey.has(post.classification.main_issue)
  ))
  .map((post, index) => ({
    issue: mainIssueToKey.get(post.classification.main_issue),
    stance: stanceFor(post),
    intensity: Math.max(0.18, Math.min(
      1,
      intensityScale[post.classification.intensity] + (post.classification.confidence - 0.75) * 0.18,
    )),
    summary: post.classification.summary,
    url: post.url,
    seed: index + 1,
  }));

const counts = Object.fromEntries(issueDefs.map((issue) => [
  issue.key,
  arenaPosts.filter((post) => post.issue === issue.key).length,
]));
const stanceOrder = ['oppose', 'conditional', 'neutral', 'support'];
const stanceColors = {
  oppose: '#dc2626',
  conditional: '#d97706',
  neutral: '#94a3b8',
  support: '#059669',
};
const stanceCounts = Object.fromEntries(issueDefs.map((issue) => [
  issue.key,
  Object.fromEntries(stanceOrder.map((stance) => [
    stance,
    arenaPosts.filter((post) => post.issue === issue.key && post.stance === stance).length,
  ])),
]));

if (arenaPosts.length !== 63) {
  throw new Error(`Expected 63 Hermes opinion posts, found ${arenaPosts.length}`);
}

fs.writeFileSync(
  arenaPath,
  `window.NICKNAME_ARENA_DATA=${JSON.stringify(arenaPosts)};\n`,
  'utf8',
);

const escapeHtml = (value) => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;');

function representativePosts(issue) {
  const matches = allPosts.filter((post) => (
    post.classification.is_relevant
    && post.classification.is_opinion
    && post.classification.main_issue === issue.mainIssue
  ));
  const usable = matches
    .filter((post) => post.classification.article_usable && post.classification.risk === 'low')
    .sort((a, b) => b.classification.confidence - a.classification.confidence);
  const pool = usable.length ? usable : matches;
  const selected = [];
  for (const stance of issue.sampleStances) {
    const match = pool.find((post) => (
      post.classification.stance === stance && !selected.includes(post)
    ));
    if (match) selected.push(match);
    if (selected.length === 2) break;
  }
  for (const post of pool) {
    if (!selected.includes(post)) selected.push(post);
    if (selected.length === 2) break;
  }
  return selected;
}

const explainerCards = issueDefs.map((issue, index) => `
  <article class="explainer-card" data-img="${issue.image}" data-alt="${issue.imageAlt}" tabindex="0" role="button" aria-label="論点${index + 1}の図解を拡大表示">
    <div class="explainer-card-label">
      <span class="explainer-num">論点${index + 1}</span>
      <div>
        <p class="explainer-card-title">${issue.icon} ${issue.title} — 「${issue.explainerTitle}」</p>
        <p class="explainer-card-desc">${issue.explainerDesc}</p>
        <div class="explainer-sides">
          <span class="explainer-side pro">${issue.explainerLeft}</span>
          <span class="explainer-side con">${issue.explainerRight}</span>
        </div>
      </div>
    </div>
    <img src="${issue.image}" alt="${issue.imageAlt}" loading="lazy" width="1915" height="821">
  </article>`).join('');

const issueBlocks = issueDefs.map((issue, index) => {
  const samples = representativePosts(issue).map((post) => `
      <div class="issue-x-sample">
        <div class="meta">${escapeHtml(issue.stanceLabels[stanceFor(post)][0])} / conf ${post.classification.confidence.toFixed(2)}</div>
        <p>${escapeHtml(post.classification.summary)}</p>
        <blockquote class="twitter-tweet" data-conversation="none" data-dnt="true"><a href="${post.url}"></a></blockquote>
      </div>`).join('');
  const issueStances = stanceCounts[issue.key];
  const stanceSegments = stanceOrder
    .filter((stance) => issueStances[stance] > 0)
    .map((stance) => {
      const percentage = issueStances[stance] / counts[issue.key] * 100;
      const visiblePercentage = percentage >= 10 ? `${Math.round(percentage)}%` : '';
      return `<div class="temp-seg ${stance}" style="width:${percentage.toFixed(2)}%" aria-label="${escapeHtml(issue.stanceLabels[stance][1])} ${issueStances[stance]}件">${visiblePercentage}</div>`;
    }).join('');
  const stanceSummary = stanceOrder
    .filter((stance) => issueStances[stance] > 0)
    .map((stance) => `${issue.stanceLabels[stance][0]} ${issueStances[stance]}`)
    .join(' / ');
  const stanceLegend = stanceOrder
    .filter((stance) => issueStances[stance] > 0)
    .map((stance) => `<span><i style="background:${stanceColors[stance]}"></i>${issue.stanceLabels[stance][1]}（${issueStances[stance]}件）</span>`)
    .join('');
  return `
  <article class="issue-block" id="issue-${issue.key}">
    <div class="issue-head">
      <span class="axis-kicker">論点${index + 1}${index === 0 ? ' · 最大勢力' : ''}</span>
      <h3>${issue.icon} ${issue.title}<span class="issue-count">${counts[issue.key]}件</span></h3>
    </div>
    <p class="issue-desc">${issue.description}</p>
    <div class="temp-bar-wrap">
      <div class="temp-bar-label"><span>${issue.barTitle}</span><span>${stanceSummary}</span></div>
      <div class="temp-bar" role="img" aria-label="${issue.barTitle}。${stanceSummary}">${stanceSegments}</div>
      <div class="temp-bar-legend">${stanceLegend}</div>
    </div>
    <div class="issue-sides">
      <div class="side support"><strong>${issue.sideSupportLabel}</strong>${issue.support}</div>
      <div class="side oppose"><strong>${issue.sideOpposeLabel}</strong>${issue.oppose}</div>
    </div>
    <div class="issue-x-grid">${samples}</div>
  </article>`;
}).join('');

const issueNav = issueDefs.map((issue) =>
  `<a href="#issue-${issue.key}">${issue.short} ${counts[issue.key]}</a>`).join('');

const issuesJson = JSON.stringify(issueDefs.map((issue) => ({
  key: issue.key,
  title: issue.title,
  short: issue.short,
  icon: issue.icon,
  count: counts[issue.key],
  description: issue.description,
})));

const replacementCss = `
    /* ===== 2026-07-24 SNS反応マップ版 ===== */
    #explainer-section .explainer-lead{max-width:920px;margin:0 0 20px;font-size:14px;line-height:1.85;color:var(--ink)}
    #explainer-section .explainer-grid{display:flex;flex-direction:column;gap:18px;max-width:920px;margin:0 auto 18px}
    #explainer-section .explainer-card{padding:0;border:1.5px solid #e4eaf3;border-radius:12px;overflow:hidden;background:#fff;box-shadow:0 8px 24px rgba(16,24,40,.08);cursor:zoom-in;transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}
    #explainer-section .explainer-card:hover,#explainer-section .explainer-card:focus-visible{transform:translateY(-3px);box-shadow:0 16px 36px rgba(16,24,40,.14);border-color:#9fb4d4;outline:none}
    #explainer-section .explainer-card img{display:block;width:100%;height:auto;aspect-ratio:21/9;object-fit:cover;background:var(--accent-soft)}
    #explainer-section .explainer-card-label{display:flex;align-items:flex-start;gap:12px;padding:14px 18px;background:#fff;border-bottom:1.5px solid #e4eaf3;pointer-events:none;user-select:none}
    #explainer-section .explainer-num{flex-shrink:0;background:#134e4a;color:#fff;font-size:11px;font-weight:900;letter-spacing:.05em;border-radius:6px;padding:4px 10px;margin-top:3px;line-height:1.3}
    #explainer-section .explainer-card-title{font-size:15px;font-weight:900;color:#173b3a;margin:0 0 4px;line-height:1.45;letter-spacing:-.02em}
    #explainer-section .explainer-card-desc{font-size:12px;color:#637089;margin:0 0 7px;line-height:1.65}
    #explainer-section .explainer-sides{display:flex;gap:6px;flex-wrap:wrap}
    #explainer-section .explainer-side{font-size:11px;font-weight:800;border-radius:5px;padding:3px 9px;line-height:1.4}
    #explainer-section .explainer-side.pro{background:#ecfdf5;color:#047857;border:1px solid #a7f3d0}
    #explainer-section .explainer-side.con{background:#fff7ed;color:#c2410c;border:1px solid #fed7aa}
    .explainer-modal{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(15,23,42,.88)}
    .explainer-modal.open{display:flex}.explainer-modal img{max-width:100%;max-height:90vh;border-radius:8px;object-fit:contain}.explainer-modal-close{position:absolute;top:16px;right:20px;background:rgba(255,255,255,.15);border:none;border-radius:50%;width:40px;height:40px;color:#fff;font-size:22px;cursor:pointer;line-height:40px;text-align:center}
    .explainer-note{font-size:12px;color:var(--muted);margin:4px 0 0}
    .vote-step-label{display:inline-flex;align-items:center;gap:8px;font-weight:900;font-size:15px;margin:0 0 12px}.vote-step-label .step-num{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:var(--accent);color:#fff;font-size:13px}
    #vote-issue-btns{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.vote-issue-btn{display:flex;align-items:center;gap:10px;border:1.5px solid rgba(15,118,110,.18);border-radius:10px;padding:12px;background:#fff;cursor:pointer;text-align:left;font-family:inherit;box-shadow:0 4px 14px rgba(16,24,40,.06)}.vote-issue-btn:hover{border-color:var(--accent);transform:translateY(-2px)}.vote-issue-icon{font-size:20px}.vote-issue-title{font-size:13px;font-weight:900}
    #vote-stance-btns{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.vote-stance-btn{border:1px solid var(--line);border-top:5px solid var(--stance-color);border-radius:12px;padding:16px 14px;background:#fff;cursor:pointer;text-align:left;font-family:inherit;box-shadow:0 6px 18px rgba(16,24,40,.09)}.vote-stance-btn:hover{transform:translateY(-3px)}.vote-stance-btn strong{display:block;color:var(--stance-color);font-size:15px}.vote-stance-btn span{display:block;color:var(--muted);font-size:12px;margin-top:5px;line-height:1.6}
    .polar-arena-section{position:relative;background:#0f172a url('images/shared/arena-bg.webp') center/cover no-repeat;padding:42px min(6vw,72px);color:#fff}.polar-arena-section .panel-title h2{color:#fff}.polar-arena-section .panel-title span{color:rgba(255,255,255,.78)!important;background:rgba(15,23,42,.56)!important;border:1px solid rgba(255,255,255,.2)!important;border-radius:999px;padding:6px 10px}.arena-caption{max-width:820px;margin:0 auto 16px;color:rgba(255,255,255,.78);font-size:13px;line-height:1.8}.arena-wrap{position:relative;max-width:760px;margin:0 auto}.arena-wrap canvas{display:block;width:100%;height:auto}.arena-legend{display:flex;justify-content:center;gap:18px;flex-wrap:wrap;font-size:12px;color:rgba(255,255,255,.78);margin-top:12px}.arena-dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px}.arena-tooltip{position:fixed;z-index:10000;max-width:280px;padding:10px 12px;border-radius:8px;background:#fff;color:#182230;font-size:12px;line-height:1.55;box-shadow:0 16px 40px rgba(0,0,0,.3);pointer-events:none;opacity:0}.arena-tooltip strong{display:block;margin-bottom:3px}
    .issue-block{border:1px solid var(--line);border-radius:12px;background:#fff;box-shadow:var(--shadow);padding:22px;margin:0 0 22px}.issue-head h3{margin:4px 0 8px;font-size:clamp(19px,2.4vw,26px)}.issue-count{display:inline-block;margin-left:8px;background:var(--accent-soft);color:var(--accent);border-radius:999px;padding:2px 12px;font-size:14px;vertical-align:middle}.issue-desc{font-size:14px;line-height:1.8}.issue-sides{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}.side{border-radius:10px;padding:13px;font-size:13px;line-height:1.7}.side strong{display:block;margin-bottom:4px}.side.support{background:#ecfdf5;border-left:4px solid #059669}.side.oppose{background:#fef2f2;border-left:4px solid #dc2626}.issue-x-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.issue-x-sample{min-width:0;border-top:1px solid var(--line);padding-top:12px}.issue-x-sample>p{font-size:13px;color:var(--muted)}
    .temp-bar-wrap{margin:14px 0 16px}.temp-bar-label{font-size:12px;font-weight:800;color:var(--muted);margin-bottom:7px;display:flex;justify-content:space-between;gap:12px}.temp-bar-label span:last-child{text-align:right}.temp-bar{display:flex;height:28px;border-radius:6px;overflow:hidden;background:#e7e7f7;position:relative}.temp-seg{display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;color:#fff;min-width:2px}.temp-seg.oppose{background:#dc2626}.temp-seg.conditional{background:#d97706}.temp-seg.neutral{background:#94a3b8}.temp-seg.support{background:#059669}.temp-bar-legend{display:flex;gap:8px 14px;margin-top:7px;font-size:11px;color:var(--muted);font-weight:800;flex-wrap:wrap}.temp-bar-legend span{line-height:1.55}.temp-bar-legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:middle}
    @media(max-width:760px){#explainer-section .explainer-card-label{padding:12px;gap:8px}#explainer-section .explainer-card-title{font-size:14px}#explainer-section .explainer-num{white-space:nowrap}#vote-issue-btns,#vote-stance-btns,.issue-sides,.issue-x-grid{grid-template-columns:1fr}.temp-bar-label{display:block}.temp-bar-label span{display:block;text-align:left!important}.temp-bar-label span+span{margin-top:3px}.polar-arena-section{padding-left:12px;padding-right:12px}.arena-caption{padding:0 8px}}
`;

const mainContent = `
<section class="panel" id="explainer-section">
  <div class="panel-title"><h2>このテーマを読み解く、6つの論点</h2><span>全体像をつかんでから選ぶ</span></div>
  <p class="explainer-lead">「賛成か反対か」だけでは見えない、呼称文化・現場体験・実効性・本人意思・心理的安全などの違いを、Hermesが分類した投稿数とともに整理しました。</p>
  <div class="explainer-grid">${explainerCards}</div>
  <p class="explainer-note">各画像をクリックすると拡大表示します。件数は関連する意見投稿63件を主論点ごとに集計したものです。</p>
</section>
<div class="explainer-modal" id="explainer-modal" role="dialog" aria-modal="true" aria-label="論点インフォグラフィック拡大表示">
  <button class="explainer-modal-close" id="explainer-modal-close" type="button" aria-label="閉じる">×</button>
  <img src="" alt="" id="explainer-modal-img">
</div>
<script>
(function(){
  var modal=document.getElementById('explainer-modal');
  var modalImage=document.getElementById('explainer-modal-img');
  var closeButton=document.getElementById('explainer-modal-close');
  var lastTrigger=null;
  function openModal(card){lastTrigger=card;modalImage.src=card.dataset.img;modalImage.alt=card.dataset.alt;modal.classList.add('open');document.body.style.overflow='hidden';closeButton.focus();}
  function closeModal(){modal.classList.remove('open');modalImage.src='';document.body.style.overflow='';if(lastTrigger)lastTrigger.focus();}
  document.querySelectorAll('#explainer-section .explainer-card').forEach(function(card){
    card.addEventListener('click',function(){openModal(card);});
    card.addEventListener('keydown',function(event){if(event.key==='Enter'||event.key===' '){event.preventDefault();openModal(card);}});
  });
  closeButton.addEventListener('click',closeModal);
  modal.addEventListener('click',function(event){if(event.target===modal)closeModal();});
  document.addEventListener('keydown',function(event){if(event.key==='Escape'&&modal.classList.contains('open'))closeModal();});
})();
</script>

<section class="panel" id="vote-section">
  <div class="panel-title"><h2>あなたが一番気になる「論点」は？</h2><span>SNSの声を見る前に</span></div>
  <p>まず重く見る論点を選び、次に「あだ名禁止・さん付け指導」への考えを選んでください。</p>
  <div style="font-size:12px;color:var(--muted);background:var(--accent-soft);border-radius:8px;padding:10px 14px;margin:0 0 20px;line-height:1.65;"><strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿374件を取得し、Hermesが関連性・意見性・論点・立場・熱量を再分類。関連する意見投稿63件を6論点へ整理しました。世論調査ではありません。</div>
  <div id="vote-step1"><p class="vote-step-label"><span class="step-num">1</span>最も気になる論点を選ぶ <span style="font-size:12px;font-weight:400;color:var(--muted)">（全2問）</span></p><div id="vote-issue-btns"></div></div>
  <div id="vote-step2" style="display:none;"><p class="vote-step-label"><span class="step-num">2</span>一律の「あだ名禁止」への考えは？ <small class="vote-step2-helper">選ぶと結果を表示します</small></p><div id="vote-stance-btns"></div></div>
  <div id="vote-result" style="display:none;margin-top:20px;"><div style="background:var(--accent-soft);border-radius:10px;padding:16px;"><div id="vote-position-label" style="font-weight:900;color:var(--accent);"></div><div id="vote-position-text" style="font-size:12px;color:var(--muted);margin-top:5px;"></div></div><a id="share-x" href="#" target="_blank" rel="noopener" style="display:inline-flex;margin-top:12px;padding:8px 16px;border-radius:8px;background:#000;color:#fff;text-decoration:none;font-weight:800;">Xでシェア</a><button id="vote-redo-btn" type="button" style="margin-left:8px;padding:8px 16px;border-radius:8px;border:1px solid var(--line);background:#fff;font-weight:800;">選び直す</button></div>
</section>
<script>
(function(){
  var issues=${issuesJson};
  var stances=[
    {key:'support',title:'一律ルールを支持',desc:'傷つく呼び方を予防するため、学校が共通ルールを設ける',color:'#059669'},
    {key:'conditional',title:'本人意思で柔軟に',desc:'嫌な呼び方は止め、本人が望む愛称は認める',color:'#d97706'},
    {key:'oppose',title:'一律禁止には反対',desc:'教育や個別対応を重視し、呼び方を一律に縛らない',color:'#dc2626'}
  ];
  var selectedIssue=null, step1=document.getElementById('vote-step1'), step2=document.getElementById('vote-step2'), result=document.getElementById('vote-result');
  var issueBox=document.getElementById('vote-issue-btns'), stanceBox=document.getElementById('vote-stance-btns');
  issues.forEach(function(issue){var btn=document.createElement('button');btn.type='button';btn.className='vote-issue-btn';btn.innerHTML='<span class="vote-issue-icon">'+issue.icon+'</span><span class="vote-issue-title">'+issue.title+' <small>('+issue.count+'件)</small></span>';btn.onclick=function(){selectedIssue=issue;step1.style.display='none';step2.style.display='block';};issueBox.appendChild(btn);});
  stances.forEach(function(stance){var btn=document.createElement('button');btn.type='button';btn.className='vote-stance-btn';btn.style.setProperty('--stance-color',stance.color);btn.innerHTML='<strong>'+stance.title+'</strong><span>'+stance.desc+'</span>';btn.onclick=function(){step2.style.display='none';result.style.display='block';document.getElementById('vote-position-label').textContent='論点：'+selectedIssue.title+' ／ '+stance.title;document.getElementById('vote-position-text').textContent=selectedIssue.description;var text='学校のあだ名禁止で気になる論点は「'+selectedIssue.title+'」。私の考えは「'+stance.title+'」 #SNS反応まっぷ';document.getElementById('share-x').href='https://x.com/intent/tweet?text='+encodeURIComponent(text)+'&url='+encodeURIComponent(location.href.split('#')[0]);localStorage.setItem('nickname-arena-vote',JSON.stringify({issue:selectedIssue.key,stance:stance.key,at:Date.now()}));setTimeout(function(){document.getElementById('issue-arena-section').scrollIntoView({behavior:'smooth'});},450);};stanceBox.appendChild(btn);});
  document.getElementById('vote-redo-btn').onclick=function(){selectedIssue=null;result.style.display='none';step2.style.display='none';step1.style.display='block';};
})();
</script>

<section class="polar-arena-section" id="issue-arena-section">
  <div class="panel-title"><h2>SNS反応マップ</h2><span>${arenaPosts.length}件 | セクター=論点 / 外側ほど熱量が高い / 色=立場</span></div>
  <p class="arena-caption">中心の「あだ名禁止」を6つの論点が囲みます。扇の幅は投稿数、中心からの距離はHermesが分類した表現の熱量、色は立場（緑=支持 / 赤=反対 / 黄=条件付き / 灰=中立）です。点をクリックすると元のX投稿を開きます。</p>
  <div class="arena-wrap"><canvas id="nickname-arena" width="760" height="760" aria-label="あだ名禁止をめぐる6論点の極座標マップ"></canvas></div>
  <div class="arena-legend"><span><i class="arena-dot" style="background:#10b981"></i>ルール支持</span><span><i class="arena-dot" style="background:#ef4444"></i>一律禁止に反対</span><span><i class="arena-dot" style="background:#f59e0b"></i>条件付き</span><span><i class="arena-dot" style="background:#94a3b8"></i>中立・情報共有</span></div>
  <div class="arena-tooltip" id="arena-tooltip"></div>
</section>
<script src="school-nickname-ban-arena-data.js"></script>
<script>
(function(){
  var canvas=document.getElementById('nickname-arena'),ctx=canvas.getContext('2d'),tip=document.getElementById('arena-tooltip');
  var issues=${issuesJson},posts=window.NICKNAME_ARENA_DATA||[],W=760,C=W/2,R0=92,R1=318,TAU=Math.PI*2,start=-Math.PI/2;
  var colors={support:'#10b981',oppose:'#ef4444',conditional:'#f59e0b',neutral:'#94a3b8'},fills=['rgba(15,118,110,.26)','rgba(37,99,235,.22)','rgba(100,116,139,.23)','rgba(220,38,38,.20)','rgba(217,119,6,.22)','rgba(124,58,237,.22)'];
  var total=issues.reduce(function(sum,i){return sum+i.count;},0),angles={},cursor=start;
  issues.forEach(function(issue){var span=TAU*(issue.count/total);angles[issue.key]={a0:cursor,a1:cursor+span,mid:cursor+span/2};cursor+=span;});
  function rand(seed){var x=Math.sin(seed*999)*43758.5453;return x-Math.floor(x);}
  var dots=posts.map(function(p,i){var a=angles[p.issue],angle=a.a0+.08+(a.a1-a.a0-.16)*rand(p.seed),radius=R0+34+(R1-R0-48)*p.intensity+(rand(p.seed+91)-.5)*28;return Object.assign({},p,{x:C+Math.cos(angle)*radius,y:C+Math.sin(angle)*radius});});
  function draw(){ctx.clearRect(0,0,W,W);ctx.save();ctx.translate(C,C);issues.forEach(function(issue,i){var a=angles[issue.key];ctx.beginPath();ctx.moveTo(Math.cos(a.a0)*R0,Math.sin(a.a0)*R0);ctx.arc(0,0,R1,a.a0,a.a1);ctx.lineTo(Math.cos(a.a1)*R0,Math.sin(a.a1)*R0);ctx.arc(0,0,R0,a.a1,a.a0,true);ctx.closePath();ctx.fillStyle=fills[i];ctx.fill();ctx.strokeStyle='rgba(255,255,255,.32)';ctx.stroke();var lr=R1+20,lx=Math.cos(a.mid)*lr,ly=Math.sin(a.mid)*lr;ctx.fillStyle='#fff';ctx.font='700 13px "Noto Sans JP"';ctx.textAlign=lx>18?'left':lx<-18?'right':'center';ctx.textBaseline='middle';ctx.fillText(issue.short+' '+issue.count,lx,ly);});[R0,170,245,R1].forEach(function(r){ctx.beginPath();ctx.arc(0,0,r,0,TAU);ctx.strokeStyle='rgba(255,255,255,.18)';ctx.stroke();});ctx.beginPath();ctx.arc(0,0,R0-5,0,TAU);ctx.fillStyle='rgba(15,23,42,.92)';ctx.fill();ctx.fillStyle='#fff';ctx.textAlign='center';ctx.font='900 17px "Noto Sans JP"';ctx.fillText('学校の',0,-11);ctx.fillText('あだ名禁止',0,14);ctx.restore();dots.forEach(function(d){ctx.beginPath();ctx.arc(d.x,d.y,5,0,TAU);ctx.fillStyle=colors[d.stance];ctx.fill();ctx.strokeStyle='rgba(255,255,255,.75)';ctx.lineWidth=1.2;ctx.stroke();});}
  function hit(e){var rect=canvas.getBoundingClientRect(),x=(e.clientX-rect.left)*W/rect.width,y=(e.clientY-rect.top)*W/rect.height,best=null,dist=11*W/rect.width;dots.forEach(function(d){var n=Math.hypot(d.x-x,d.y-y);if(n<dist){best=d;dist=n;}});return best;}
  canvas.addEventListener('mousemove',function(e){var d=hit(e);canvas.style.cursor=d?'pointer':'default';if(!d){tip.style.opacity=0;return;}var issue=issues.find(function(i){return i.key===d.issue;});tip.innerHTML='<strong>'+issue.icon+' '+issue.title+'</strong>'+escapeHtml(d.summary);tip.style.left=Math.min(innerWidth-300,e.clientX+14)+'px';tip.style.top=Math.min(innerHeight-120,e.clientY+14)+'px';tip.style.opacity=1;});
  canvas.addEventListener('mouseleave',function(){tip.style.opacity=0;});canvas.addEventListener('click',function(e){var d=hit(e);if(d)window.open(d.url,'_blank','noopener');});
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];});}
  draw();
})();
</script>

<section class="panel conflict-panel" id="issue-voices-section">
  <div class="panel-title"><h2>6つの論点とXの声</h2><span>論点ごとの両側の見方と代表投稿</span></div>
  <nav class="quadrant-nav">${issueNav}</nav>
${issueBlocks}
</section>

${fs.readFileSync(htmlPath, 'utf8').match(/<section class="panel" id="manga-section">[\s\S]*?<\/section>/)[0]}
`;

let html = fs.readFileSync(htmlPath, 'utf8');
html = html.replace(
  /<meta name="description" content="[^"]+">/,
  '<meta name="description" content="学校でのあだ名禁止・さん付け指導について、SNS投稿374件をHermesで再分類。関連する意見63件を6論点のアリーナで可視化します。">',
);
html = html.replace(
  /<meta property="og:description" content="[^"]+">/,
  '<meta property="og:description" content="あだ名禁止は優しさか、行き過ぎた規制か。Hermesで再分類した6論点とSNSの声を可視化。">',
);
html = html.replace(
  /<meta name="twitter:description" content="[^"]+">/,
  '<meta name="twitter:description" content="あだ名禁止は優しさか、行き過ぎた規制か。Hermesで再分類した6論点とSNSの声を可視化。">',
);
if (html.includes('/* ===== 2026-07-24 SNS反応マップ版 ===== */')) {
  html = html.replace(
    /\n    \/\* ===== 2026-07-24 SNS反応マップ版 ===== \*\/[\s\S]*?(?=\n  <\/style>)/,
    replacementCss,
  );
} else {
  html = html.replace('</style>', `${replacementCss}\n  </style>`);
}
html = html.replace(
  /<section class="hero">[\s\S]*?<\/section><svg class="wave-divider"/,
  `<section class="hero"><img class="hero-photo" src="images/topics/school-nickname-ban/school-nickname-hero.webp" alt="学校でのあだ名禁止の是非" loading="lazy"><div class="hero-inner"><nav class="top-nav"><a href="index.html">トップ</a></nav><span class="badge">教育・日常論争</span><h1>学校でのあだ名禁止 SNS反応まっぷ</h1><p class="question-line">傷つく呼び方を防ぐルールか、関係性を縛る一律規制か。</p><p class="lead">収集したSNS投稿のうち、分析対象となった意見63件をAIが6つの論点に整理しました。世論調査ではなく、SNS反応サンプルの論点比較です。</p><div class="thirty-summary" aria-label="まず結論：今回の分析で見えたこと"><header class="thirty-summary-title"><h2>まず結論</h2><p>今回の分析で見えたこと</p></header><ul><li>最多論点は「いじめ・心理的安全」17件。被害予防を重く見る声と、禁止だけでは足りないという声があります。</li><li>「一律禁止の実効性」16件と「親しさ・呼称文化」13件では、一律禁止への反対が中心です。</li><li>全63件では一律禁止に反対29件、禁止支持8件、条件付き7件、中立・体験19件でした。</li></ul></div></div></section><svg class="wave-divider"`,
);
html = html.replace(
  /<section class="stats">[\s\S]*?<\/section>/,
  '<section class="stats"><div class="stat"><span>収集投稿</span><strong>374件</strong></div><div class="stat"><span>関連する意見</span><strong>63件</strong></div><div class="stat"><span>論点数</span><strong>6論点</strong></div><div class="stat"><span>最多論点</span><strong>心理的安全 17</strong></div></section>',
);

const contentStart = html.includes('<section class="panel" id="explainer-section">')
  ? html.indexOf('<section class="panel" id="explainer-section">')
  : html.indexOf('<section class="panel" id="manga-section">');
const contentEnd = html.indexOf('<section class="panel background-panel">');
if (contentStart < 0 || contentEnd < 0 || contentEnd <= contentStart) {
  throw new Error('Could not locate main content replacement boundaries');
}
html = html.slice(0, contentStart) + mainContent + '\n' + html.slice(contentEnd);
html = html.replace(
  /<section class="panel conflict-panel"><div class="panel-title"><h2>争点カード<\/h2>[\s\S]*?<\/section>/,
  '',
);
html = html.replace(
  'Powered by Yahooリアルタイム検索 + AI分類',
  'Powered by Yahooリアルタイム検索 + Hermes分類',
);
html = html.replace(
  /<section class="panel details-panel" id="detail-data">[\s\S]*?<\/section>/,
  `<section class="panel details-panel" id="detail-data"><div class="panel-title"><h2>詳細データ</h2><span>折りたたみ</span></div><details open><summary>論点別件数（関連する意見${arenaPosts.length}件）</summary><div class="table-wrap"><table><tbody>${issueDefs.map((issue) => `<tr><th>${issue.title}</th><td>${counts[issue.key]}</td></tr>`).join('')}</tbody></table></div></details><details><summary>分類対象と注意</summary><ul><li>Yahooリアルタイム検索で取得した374件をHermesが再分類し、関連性と意見性がともに認められた${arenaPosts.length}件を表示しています。</li><li>これは世論調査ではなく、検索語・取得時点・検索サービスの表示仕様による偏りがあります。</li><li>論点・立場・熱量・要約はHermesによる自動分類で、誤分類を含む可能性があります。</li></ul></details></section>`,
);

fs.writeFileSync(htmlPath, html, 'utf8');

console.log(`Updated ${path.relative(root, htmlPath)}`);
console.log(`Created ${path.relative(root, arenaPath)} with ${arenaPosts.length} posts`);
console.log(counts);
