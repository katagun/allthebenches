import { expect, test } from '@playwright/test';
import { fixtureFeeds, installPriceFixture } from './fixtures/prices';

for (const width of [1440, 390]) {
  test(`controlled feed health and price coverage at ${width}px`, async ({ page }) => {
    await installPriceFixture(page);
    await page.setViewportSize({ width, height: 844 });
    await page.goto('./');
    const summary = page.locator('.feed-health summary');
    await summary.scrollIntoViewIfNeeded();
    await summary.click();
    await expect(page.getByText(/Fresh available prices: 2 of \d+ releases · 2 routes/)).toBeVisible();
    await expect(page.getByText('Refresh failed · retained data', { exact: true })).toBeVisible();
    await expect(page.getByText(/not a live monitor/)).toBeVisible();
    const failed = page.locator('.feed-health li').filter({ hasText: 'deepseek/deepseek-r1/endpoints' });
    await expect(failed).toContainText(`Last accepted: ${fixtureFeeds[1].as_of!.slice(0, 10)}`);
    await expect(failed).toContainText(`Last attempt: ${fixtureFeeds[1].attempted_at!.slice(0, 10)}`);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await failed.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `/tmp/allthebenches-feed-health-${width}.png`, fullPage: false });
  });
}
