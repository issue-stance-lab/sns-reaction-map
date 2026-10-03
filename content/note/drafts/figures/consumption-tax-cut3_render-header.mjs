// note第3回の見出し画像を、背景写真に文字を重ねて書き出す（1920x1006）。
//
// 使い方（node_modules を複製した作業ツリーのルートで実行する。複製の手順は OPERATIONS.md ⓪）:
//   node content/note/drafts/figures/consumption-tax-cut3_render-header.mjs
// 前提: 背景写真 content/note/drafts/photos/consumption-tax-cut3-two-rulers.png がある（オーナーがGPTimage2で生成）。
// 出力: content/note/drafts/images/consumption-tax-cut3_note-header.png
//
// file:// 直読みだと相対パスで失敗することがあるため、drafts/ を一時的に http で配信して描画する。
import { createRequire } from 'node:module';
import http from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const drafts = path.resolve(here, '..');
const root = path.resolve(drafts, '..', '..', '..');
const require = createRequire(path.join(process.env.PLAYWRIGHT_ROOT || root, 'package.json'));
const { chromium } = require('playwright');

const types = { '.html': 'text/html; charset=utf-8', '.png': 'image/png', '.mjs': 'text/javascript' };
const server = http.createServer(async (req, res) => {
  try {
    const file = path.join(drafts, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!file.startsWith(drafts)) throw new Error('out of root');
    const body = await readFile(file);
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end('not found');
  }
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const port = server.address().port;

const out = process.env.HEADER_OUT || path.join(drafts, 'images', 'consumption-tax-cut3_note-header.png');
await mkdir(path.dirname(out), { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1006 }, deviceScaleFactor: 1 });
await page.goto(`http://127.0.0.1:${port}/figures/consumption-tax-cut3_note-header.html`, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1920, height: 1006 } });
await browser.close();
server.close();
console.log('書き出し:', out);
