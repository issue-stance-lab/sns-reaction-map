#!/usr/bin/env node
// Regenerate takaichi-arena-data.js from Hermes classified JSON.
// Run after classify_takaichi_arena_hermes.py completes.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const check = args.includes('--check');
function option(name, fallback) {
  const index = args.indexOf(name);
  if (index < 0) return fallback;
  if (!args[index + 1]) throw new Error(`${name} requires a path`);
  return path.resolve(root, args[index + 1]);
}
const dataPath = option('--input', path.join(root, 'social-samples', 'takaichi_hermes_arena_classified.json'));
const htmlTemplatePath = option('--html-template', path.join(root, 'docs', 'takaichi-reaction-map-standard.html'));
const arenaPath = option('--output-data', path.join(root, 'docs', 'takaichi-arena-data.js'));
const htmlPath = option('--output-html', path.join(root, 'docs', 'takaichi-reaction-map-standard.html'));

const allPosts = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

const issueDefs = [
  { key: 'accountability', mainIssue: '中傷動画・説明責任' },
  { key: 'bunshun',        mainIssue: '文春報道の真偽' },
  { key: 'token',          mainIssue: 'サナエトークン疑惑' },
  { key: 'matsui',         mainIssue: '松井健氏・工作の実態' },
  { key: 'comparison',     mainIssue: '比較・政治倫理' },
];

const mainIssueToKey = new Map(issueDefs.map((d) => [d.mainIssue, d.key]));

function stanceFor(post) {
  const stance = post.classification.stance;
  if (stance === '批判・追及') return 'accuse';
  if (stance === '擁護・懐疑') return 'defend';
  if (stance === '慎重・保留') return 'skeptical';
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

console.log(`Arena posts: ${arenaPosts.length}`);

const counts = Object.fromEntries(
  issueDefs.map((d) => [d.key, arenaPosts.filter((p) => p.issue === d.key).length]),
);
console.log('Counts by issue:', counts);

const stanceCounts = {};
for (const p of arenaPosts) stanceCounts[p.stance] = (stanceCounts[p.stance] || 0) + 1;
console.log('Counts by stance:', stanceCounts);

// Write arena-data.js
const arenaData = `window.TAKAICHI_ARENA_DATA = ${JSON.stringify(arenaPosts)};\n`;
const currentArena = fs.existsSync(arenaPath) ? fs.readFileSync(arenaPath, 'utf8') : '';

// Patch issue counts in the HTML
let html = fs.readFileSync(htmlTemplatePath, 'utf8');
for (const def of issueDefs) {
  const n = counts[def.key] ?? 0;
  html = html.replace(
    new RegExp(`(key:'${def.key}',[^}]*count:)\\d+`, 'g'),
    `$1${n}`,
  );
}
// Patch total count label in arena caption
const total = arenaPosts.length;
html = html.replace(
  /(<span>)\d+(件 \| セクター=論点)/,
  `$1${total}$2`,
);
html = html.replace(
  /(Yahooリアルタイム検索で取得した公開投稿 )\d+(件)/,
  `$1${allPosts.length}$2`,
);
const cardSlugs = {
  accountability: 'chusho',
  bunshun: 'bunshun',
  token: 'token',
  matsui: 'matsui',
  comparison: 'hikaku',
};
for (const def of issueDefs) {
  html = html.replace(
    new RegExp(`(<span class="explainer-count" id="issue-count-takaichi-${cardSlugs[def.key]}">)\\d+件(</span>)`),
    `$1${counts[def.key] ?? 0}件$2`,
  );
}
// insight-stats の件数・割合を正典から自動更新
const opinionPosts = allPosts.filter((p) => p.classification.is_relevant && p.classification.is_opinion);
const opinionCount = opinionPosts.length;
const accuseN = opinionPosts.filter((p) => p.classification.stance === '批判・追及').length;
const defendN = opinionPosts.filter((p) => p.classification.stance === '擁護・懐疑').length;
const debateTotalN = accuseN + defendN;
const accusePct = debateTotalN ? ((accuseN / debateTotalN) * 100).toFixed(1) : '0.0';
const defendPct = debateTotalN ? ((defendN / debateTotalN) * 100).toFixed(1) : '0.0';
const diff = Math.abs(accuseN - defendN);
const diffLabel = `${diff}件差・批判${diff < 30 ? 'がやや優勢' : 'が優勢'}`;
const accountabilityN = opinionPosts.filter((p) => p.classification.main_issue === '中傷動画・説明責任').length;
const accountabilityPct = opinionCount ? Math.round(accountabilityN * 100 / opinionCount) : 0;
const bunshunPosts = opinionPosts.filter((p) => p.classification.main_issue === '文春報道の真偽');
const bunshunDefendN = bunshunPosts.filter((p) => p.classification.stance === '擁護・懐疑').length;
const bunshunAccuseN = bunshunPosts.filter((p) => p.classification.stance === '批判・追及').length;
// カード1: 意見件数
html = html.replace(
  /(<strong class="insight-value">)\d+(<small>件<\/small><\/strong>\s*<p class="insight-note">説明責任)/,
  `$1${opinionCount}$2`,
);
// カード2: 意見の割れ方
html = html.replace(
  /(<span class="insight-chip">)\d+件差・批判(?:がやや優勢|が優勢)(<\/span>)/,
  `$1${diffLabel}$2`,
);
html = html.replace(
  /(<span>批判・追及<b>)\d+(<\/b><\/span>)/,
  `$1${accuseN}$2`,
);
html = html.replace(
  /(<span>擁護・懐疑<b>)\d+(<\/b><\/span><em>VS<\/em>)/,
  `$1${defendN}$2`,
);
html = html.replace(
  /(<div class="insight-split"[^>]*><i style="width:)[\d.]+(%"><\/i><i style="width:)[\d.]+(%"><\/i><\/div>)/s,
  `$1${accusePct}$2${defendPct}$3`,
);
// カード3: 最も話された論点（説明責任）
html = html.replace(
  /(<strong class="insight-value">説明責任 )\d+(<small>件<\/small><\/strong>)/,
  `$1${accountabilityN}$2`,
);
html = html.replace(
  /(data-tone="topic"[\s\S]*?<i style="width:)\d+(%"><\/i><\/div>)/,
  `$1${accountabilityPct}$2`,
);
// カード4: 唯一の逆転論点（文春報道の真偽）
html = html.replace(
  /(<span>擁護・懐疑<b>)\d+(<\/b><\/span><em>VS<\/em><span>批判・追及<b>)\d+(<\/b><\/span>)/,
  `$1${bunshunDefendN}$2${bunshunAccuseN}$3`,
);

const currentHtml = fs.existsSync(htmlPath) ? fs.readFileSync(htmlPath, 'utf8') : '';
const changed = currentArena !== arenaData || currentHtml !== html;
if (!check) {
  fs.mkdirSync(path.dirname(arenaPath), { recursive: true });
  fs.writeFileSync(arenaPath, arenaData, 'utf8');
  fs.mkdirSync(path.dirname(htmlPath), { recursive: true });
  fs.writeFileSync(htmlPath, html, 'utf8');
}
console.log(`${check ? (changed ? 'would update' : 'unchanged') : 'written'}: ${arenaPath}`);
console.log(`${check ? (changed ? 'would update' : 'unchanged') : 'patched'}: ${htmlPath}`);
if (check && changed) process.exitCode = 1;
