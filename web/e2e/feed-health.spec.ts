import { expect, test } from '@playwright/test';

for (const width of [1440, 390]) {
  test(`published feed health and price coverage at ${width}px`, async ({ page }) => {
    await page.clock.setFixedTime(new Date('2026-10-24T20:00:00Z'));
    await page.setViewportSize({ width, height: 844 });
    await page.goto('./');
    const summary = page.locator('.feed-health summary');
    await summary.scrollIntoViewIfNeeded();
    await summary.click();
    await expect(page.getByText(/Fresh available prices: 25 of 47 releases · 275 routes/)).toBeVisible();
    await expect(page.getByText('Refresh failed · retained data', { exact: true })).toBeVisible();
    await expect(page.getByText(/not a live monitor/)).toBeVisible();
    const failed = page.locator('.feed-health li').filter({ hasText: 'deepseek/deepseek-r1/endpoints' });
    await expect(failed).toContainText('Last accepted: 2026-10-18');
    await expect(failed).toContainText('Last attempt: 2026-10-24');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await failed.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `/tmp/allthebenches-feed-health-${width}.png`, fullPage: false });
  });
}
