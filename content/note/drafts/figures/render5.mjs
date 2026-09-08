import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const playwrightModule = process.env.PLAYWRIGHT_MODULE
  ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
  : 'playwright';
const playwright = await import(playwrightModule);
const chromium = playwright.chromium ?? playwright.default.chromium;
const figures = path.join(root, 'figures');
const images = path.join(root, 'images');
const execFileAsync = promisify(execFile);
await mkdir(images, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH || undefined,
});

const header = await browser.newPage({ viewport: { width: 1280, height: 670 }, deviceScaleFactor: 1.5 });
await header.goto(`file://${path.join(figures, 'bukatsu5_note-header.html')}`, { waitUntil: 'networkidle' });
await header.evaluate(() => document.fonts.ready);
await header.screenshot({ path: path.join('/tmp', 'bukatsu5_note-header-raw.png'), clip: { x: 0, y: 0, width: 1280, height: 670 } });
await execFileAsync('magick', [path.join('/tmp', 'bukatsu5_note-header-raw.png'), '-gravity', 'south', '-background', '#07111E', '-extent', '1920x1006', path.join(images, 'bukatsu5_note-header.png')]);
await header.screenshot({ path: path.join(images, 'bukatsu5_note-header-square.png'), clip: { x: 0, y: 0, width: 670, height: 670 } });
await header.close();

for (const [w, h, suffix] of [[300, 157, '300px'], [375, 196, '375px']]) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  await page.goto(`file://${path.join(figures, 'bukatsu5_note-header.html')}`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({ content: `html,body{width:${w}px!important;height:${h}px!important}.canvas{transform:scale(${w / 1280});transform-origin:top left}` });
  await page.screenshot({ path: path.join(images, `bukatsu5_note-header-${suffix}.png`) });
  await page.close();
}

for (const [name, width, height] of [['bukatsu5_fig1-history', 800, 1680], ['bukatsu5_fig2-schedule', 800, 1490]]) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 3 });
  await page.goto(`file://${path.join(figures, `${name}.html`)}`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(images, `${name}.png`), clip: { x: 0, y: 0, width, height } });
  await page.close();
  const previewHeight = Math.round(height * 375 / width);
  const preview = await browser.newPage({ viewport: { width: 375, height: previewHeight }, deviceScaleFactor: 1 });
  await preview.goto(`file://${path.join(figures, `${name}.html`)}`, { waitUntil: 'networkidle' });
  await preview.evaluate(() => document.fonts.ready);
  await preview.addStyleTag({ content: `html,body{width:375px!important;height:${previewHeight}px!important}.canvas{transform:scale(${375 / width});transform-origin:top left}` });
  await preview.screenshot({ path: path.join(images, `${name}-375px.png`) });
  await preview.close();
}

await browser.close();
console.log('Rendered all note 5 images.');
