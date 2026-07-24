#!/usr/bin/env node
// Regenerate takaichi-arena-data.js from Hermes classified JSON.
// Run after classify_takaichi_arena_hermes.py completes.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dataPath = path.join(root, 'social-samples', 'takaichi_hermes_arena_classified.json');
const arenaPath = path.join(root, 'docs', 'takaichi-arena-data.js');
const htmlPath = path.join(root, 'docs', 'takaichi-reaction-map-standard.html');

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
fs.writeFileSync(arenaPath, arenaData, 'utf8');
console.log(`Written: ${arenaPath}`);

// Patch issue counts in the HTML
let html = fs.readFileSync(htmlPath, 'utf8');
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
fs.writeFileSync(htmlPath, html, 'utf8');
console.log(`Patched counts in: ${htmlPath}`);
