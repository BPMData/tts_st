import { expect, test } from '@playwright/test';
import { strings } from '../../shared/strings.ts';

test('meets Chrome install checks and reopens offline without caching API replies', async ({ page, context }, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: strings.welcome })).toBeVisible();
  await expect(page.getByRole('status')).toContainText(strings.offlineReady);
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
    await fetch('/api/health');
  });
  // A fresh first visit is controlled on its next navigation in prompt mode.
  await page.reload();
  await expect.poll(() => page.evaluate(() => Boolean(navigator.serviceWorker.controller))).toBe(true);
  const cdp = await context.newCDPSession(page);
  await cdp.send('Page.enable');
  const manifest = await cdp.send('Page.getAppManifest');
  expect(manifest.errors).toEqual([]);
  expect(JSON.parse(manifest.data!)).toMatchObject({ name: strings.appName, display: 'standalone' });
  const { installabilityErrors } = await cdp.send('Page.getInstallabilityErrors');
  expect(installabilityErrors).toEqual([]);
  await cdp.detach();
  // Chrome's visible install prompt still needs the real-device check in README.
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: strings.skipLink })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('home.png'), fullPage: true });

  await context.setOffline(true);
  await expect.poll(() => page.evaluate(() => navigator.onLine)).toBe(false);
  await page.reload();
  await expect(page.getByRole('heading', { name: strings.welcome })).toBeVisible();
  await expect(page.getByRole('status')).toContainText(strings.offline);
  // A new tab exercises reopening the installed app's start URL, not just a warm tab.
  const reopened = await context.newPage();
  await reopened.goto('/');
  await expect(reopened.getByRole('heading', { name: strings.welcome })).toBeVisible();
  await expect(reopened.getByRole('status')).toContainText(strings.offline);
  const apiWorksOffline = await reopened.evaluate(async () => {
    try { await fetch('/api/health'); return true; } catch { return false; }
  });
  expect(apiWorksOffline).toBe(false);
  const cachedPaths = await reopened.evaluate(async () => {
    const requests = await Promise.all((await caches.keys()).map(async (name) => (await caches.open(name)).keys()));
    return requests.flat().map((request) => new URL(request.url).pathname);
  });
  expect(cachedPaths.some((path) => path.startsWith('/api'))).toBe(false);
  await reopened.close();
  await context.setOffline(false);
  await expect(page.getByRole('status')).toContainText(strings.online);
  expect(errors).toEqual([]);
});
