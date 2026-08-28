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

async function render(name, width, height) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 3 });
  await page.goto(`file://${path.join(figures, `${name}.html`)}`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(images, `${name}.png`), clip: { x: 0, y: 0, width, height } });
  const preview = await browser.newPage({ viewport: { width: 375, height: Math.ceil(height * 375 / width) }, deviceScaleFactor: 1 });
  await preview.goto(`file://${path.join(figures, `${name}.html`)}`, { waitUntil: 'networkidle' });
  await preview.evaluate(() => document.fonts.ready);
  await preview.addStyleTag({ content: `html,body{width:${width}px!important;height:${height}px!important}.canvas{transform:scale(${375 / width});transform-origin:top left}` });
  await preview.screenshot({ path: path.join(images, `${name}-375px.png`) });
  await page.close(); await preview.close();
}

const header = await browser.newPage({ viewport: { width: 1280, height: 670 }, deviceScaleFactor: 1.5 });
await header.goto(`file://${path.join(figures, 'bukatsu2_note-header.html')}`, { waitUntil: 'networkidle' });
await header.evaluate(() => document.fonts.ready);
await header.screenshot({ path: path.join('/tmp', 'bukatsu2_note-header-raw.png'), clip: { x: 0, y: 0, width: 1280, height: 670.6666667 } });
await execFileAsync('magick', [path.join('/tmp', 'bukatsu2_note-header-raw.png'), '-gravity', 'south', '-background', '#07111E', '-extent', '1920x1006', path.join(images, 'bukatsu2_note-header.png')]);
await header.screenshot({ path: path.join(images, 'bukatsu2_note-header-square.png'), clip: { x: 305, y: 0, width: 670, height: 670 } });
const tiny = await browser.newPage({ viewport: { width: 300, height: 157 }, deviceScaleFactor: 1 });
await tiny.goto(`file://${path.join(figures, 'bukatsu2_note-header.html')}`, { waitUntil: 'networkidle' });
await tiny.evaluate(() => document.fonts.ready);
await tiny.addStyleTag({ content: 'html,body{width:300px!important;height:157px!important}.canvas{transform:scale(.234375);transform-origin:top left}' });
await tiny.screenshot({ path: path.join(images, 'bukatsu2_note-header-300px.png') });
const small = await browser.newPage({ viewport: { width: 375, height: 196 }, deviceScaleFactor: 1 });
await small.goto(`file://${path.join(figures, 'bukatsu2_note-header.html')}`, { waitUntil: 'networkidle' });
await small.evaluate(() => document.fonts.ready);
await small.addStyleTag({ content: 'html,body{width:375px!important;height:196px!important}.canvas{transform:scale(.29296875);transform-origin:top left}' });
await small.screenshot({ path: path.join(images, 'bukatsu2_note-header-375px.png') });
await header.close(); await tiny.close(); await small.close();
await render('bukatsu2_fig1-227', 800, 420);
await render('bukatsu2_fig2-reread', 800, 1230);
await render('bukatsu2_fig3-answer', 800, 1100);
await browser.close();
console.log('Rendered note 2 header and figures at their specified logical sizes.');
