import { test, expect } from '@playwright/test';

test.use({ isMobile: true, hasTouch: true });

for (const [width, height] of [[320, 740], [390, 844], [844, 390]]) {
  test(`${width}x${height}: find TRACES from the default benchmark picker and open its evidence`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height });
    await page.goto('./');
    const picker = page.getByRole('button', { name: 'Choose benchmark', exact: true });
    await picker.click();
    await page.getByRole('searchbox', { name: 'Search benchmarks', exact: true }).fill('TRACES');
    await expect(page.getByRole('option')).toHaveCount(4);
    await page.screenshot({ path: testInfo.outputPath('traces-picker.png'), animations: 'disabled' });
    await page.getByRole('option', { name: /TRACES Influence Failure Rate — interactive/ }).click();
    await expect(picker).toContainText('TRACES Influence Failure Rate — interactive');
    await expect(page.locator('.portrait-model-card')).toHaveCount(5);
    await expect(page.locator('.mobile-score-bar')).toHaveCount(5);
    await expect(page.locator('.portrait-model-card').first()).toContainText('GPT-5.6 Sol');
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    await page.screenshot({ path: testInfo.outputPath('traces-results.png'), animations: 'disabled' });
    await page.locator('.portrait-model-card').first().getByRole('button', { name: /show evidence/ }).click();
    await expect(page.getByRole('heading', { name: 'Result evidence', exact: true })).toBeVisible();
    await expect(page.getByRole('dialog')).toContainText('Intellicat');
    await page.getByRole('button', { name: 'Close', exact: true }).click();
    await page.reload();
    await expect(picker).toContainText('TRACES Influence Failure Rate — interactive');
    await expect(page.locator('.mobile-score-bar')).toHaveCount(5);
  });
}

test('mobile main search exposes the TRACES view without opening Options', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto('./');
  await page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks' }).fill('TRACES');
  await expect(page.getByRole('button', { name: /Show TRACES/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('traces-search.png'), animations: 'disabled' });
  await page.getByRole('button', { name: /Show TRACES/ }).click();
  await expect(page.getByRole('button', { name: 'Choose benchmark', exact: true })).toContainText('TRACES');
  await expect(page.locator('.mobile-score-bar')).toHaveCount(5);
});
