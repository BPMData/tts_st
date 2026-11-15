// Render the source vector with Chromium; no photos or external assets are used.
import { chromium } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const source = await readFile(new URL('../public/icons/icon.svg', import.meta.url), 'utf8');
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  for (const [name, size, maskable] of [
    ['icon-192.png', 192, false],
    ['icon-512.png', 512, false],
    ['apple-touch-icon.png', 180, true],
    ['maskable-512.png', 512, true],
  ]) {
    const svg = (maskable ? source.replace('rx="112"', 'rx="0"') : source)
      .replace('<svg ', `<svg width="${size}" height="${size}" `);
    await page.setViewportSize({ width: size, height: size });
    await page.setContent(`<style>body { margin: 0; } svg { display: block; }</style>${svg}`);
    await page.screenshot({ path: new URL(`../public/icons/${name}`, import.meta.url).pathname, omitBackground: !maskable });
  }
} finally {
  await browser.close();
}
