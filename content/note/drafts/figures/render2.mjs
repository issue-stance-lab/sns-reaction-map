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
const page = await browser.newPage({ viewport: { width: 1280, height: 670 }, deviceScaleFactor: 1.5 });
await page.goto(`file://${path.join(figures, 'bukatsu2_note-header.html')}`, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);

await page.screenshot({
  path: path.join('/tmp', 'bukatsu2_note-header-raw.png'),
  clip: { x: 0, y: 0, width: 1280, height: 670.6666667 }
});
await execFileAsync('magick', [
  path.join('/tmp', 'bukatsu2_note-header-raw.png'),
  '-gravity', 'south', '-background', '#07111E', '-extent', '1920x1006',
  path.join(images, 'bukatsu2_note-header.png')
]);

await page.screenshot({
  path: path.join(images, 'bukatsu2_note-header-square.png'),
  clip: { x: 305, y: 0, width: 670, height: 670 }
});

const preview = await browser.newPage({ viewport: { width: 300, height: 157 }, deviceScaleFactor: 1 });
await preview.goto(`file://${path.join(figures, 'bukatsu2_note-header.html')}`, { waitUntil: 'networkidle' });
await preview.evaluate(() => document.fonts.ready);
await preview.addStyleTag({ content: `
  html, body { width: 300px !important; height: 157px !important; }
  .canvas { transform: scale(0.234375); transform-origin: top left; }
` });
await preview.screenshot({ path: path.join(images, 'bukatsu2_note-header-300px.png') });

const fig1 = await browser.newPage({ viewport: { width: 1200, height: 380 }, deviceScaleFactor: 2 });
await fig1.goto(`file://${path.join(figures, 'bukatsu2_fig1-227.html')}`, { waitUntil: 'networkidle' });
await fig1.evaluate(() => document.fonts.ready);
await fig1.screenshot({
  path: path.join(images, 'bukatsu2_fig1-227.png'),
  clip: { x: 0, y: 0, width: 1200, height: 380 }
});

const fig2 = await browser.newPage({ viewport: { width: 1200, height: 820 }, deviceScaleFactor: 2 });
await fig2.goto(`file://${path.join(figures, 'bukatsu2_fig2-reread.html')}`, { waitUntil: 'networkidle' });
await fig2.evaluate(() => document.fonts.ready);
await fig2.screenshot({
  path: path.join(images, 'bukatsu2_fig2-reread.png'),
  clip: { x: 0, y: 0, width: 1200, height: 820 }
});

const fig3 = await browser.newPage({ viewport: { width: 1200, height: 760 }, deviceScaleFactor: 2 });
await fig3.goto(`file://${path.join(figures, 'bukatsu2_fig3-answer.html')}`, { waitUntil: 'networkidle' });
await fig3.evaluate(() => document.fonts.ready);
await fig3.screenshot({
  path: path.join(images, 'bukatsu2_fig3-answer.png'),
  clip: { x: 0, y: 0, width: 1200, height: 760 }
});

await browser.close();
console.log('Rendered note 2 header, square crop, 300px preview, and figures 1–3.');
