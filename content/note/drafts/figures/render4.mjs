import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const figures = path.join(root, 'figures');
const images = path.join(root, 'images');
const execFileAsync = promisify(execFile);
await mkdir(images, { recursive: true });
const browser = await chromium.launch({ headless: true });

// 見出し画像（1280x670 → noteの推奨比に合わせて1920x1006へ拡張）
const page = await browser.newPage({ viewport: { width: 1280, height: 670 }, deviceScaleFactor: 1.5 });
await page.goto(`file://${path.join(figures, 'bukatsu4_note-header.html')}`, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: path.join('/tmp', 'bukatsu4_note-header-raw.png'), clip: { x: 0, y: 0, width: 1280, height: 670 } });
await execFileAsync('magick', [path.join('/tmp', 'bukatsu4_note-header-raw.png'), '-gravity', 'south', '-background', '#07111E', '-extent', '1920x1006', path.join(images, 'bukatsu4_note-header.png')]);
await page.screenshot({ path: path.join(images, 'bukatsu4_note-header-square.png'), clip: { x: 0, y: 0, width: 670, height: 670 } });
await page.close();

for (const [w, h, suffix] of [[300, 157, '300px'], [375, 196, '375px']]) {
  const p = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  await p.goto(`file://${path.join(figures, 'bukatsu4_note-header.html')}`, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.addStyleTag({ content: `html,body{width:${w}px!important;height:${h}px!important}.canvas{transform:scale(${w / 1280});transform-origin:top left}` });
  await p.screenshot({ path: path.join(images, `bukatsu4_note-header-${suffix}.png`) });
  await p.close();
}

// 図3点。375px幅のプレビューも出して、スマホで文字が読めるか確認する
const figs = [
  ['bukatsu4_fig1-reread', 800, 1130],
  ['bukatsu4_fig2-kyoto-kobe', 800, 1330],
  ['bukatsu4_fig3-weekday', 800, 900],
];
for (const [name, w, h] of figs) {
  const f = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 3 });
  await f.goto(`file://${path.join(figures, `${name}.html`)}`, { waitUntil: 'networkidle' });
  await f.evaluate(() => document.fonts.ready);
  await f.screenshot({ path: path.join(images, `${name}.png`), clip: { x: 0, y: 0, width: w, height: h } });
  await f.close();
  const scale = 375 / w;
  const ph = Math.round(h * scale);
  const fp = await browser.newPage({ viewport: { width: 375, height: ph }, deviceScaleFactor: 1 });
  await fp.goto(`file://${path.join(figures, `${name}.html`)}`, { waitUntil: 'networkidle' });
  await fp.evaluate(() => document.fonts.ready);
  await fp.addStyleTag({ content: `html,body{width:375px!important;height:${ph}px!important}.canvas{transform:scale(${scale});transform-origin:top left}` });
  await fp.screenshot({ path: path.join(images, `${name}-375px.png`) });
  await fp.close();
}

await browser.close();
console.log('Rendered all note 4 images.');
