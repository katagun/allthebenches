import { expect, test } from '@playwright/test';

for (const width of [390, 768, 1440]) {
  test(`reference pages work without JavaScript at ${width}px`, async ({ browser, baseURL }) => {
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width, height: 844 } });
    const page = await context.newPage();
    for (const path of ['models/gpt61_sol/', 'benchmarks/arc_agi_3_standard/']) {
      await page.goto(`${baseURL?.replace(/\/$/, '')}/${path}`);
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.getByRole('heading', { name: /Reviewed (benchmark results|scores)/ })).toBeVisible();
      await expect(page.locator('a[href^="https://arcprize.org/results/"]').first()).toBeVisible();
      await expect(page.getByRole('link', { name: 'Comparison matrix', exact: true })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    }
    await context.close();
  });
}
