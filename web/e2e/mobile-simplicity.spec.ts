import { test, expect } from '@playwright/test';

for (const [width, height] of [[320, 740], [390, 844], [844, 390], [1024, 768]]) {
  test(`${width}x${height}: simple model rows and progressive controls`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.goto('./');
    await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    await expect(page.locator('table')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Filters', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Choose benchmark', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    const geometry = await page.locator('.portrait-model-card').evaluateAll(rows => rows.map(row => {
      const card = row.getBoundingClientRect();
      const name = row.querySelector('.model-link')!.getBoundingClientRect();
      const score = row.querySelector('.score-button')!.getBoundingClientRect();
      return { height: card.height, bottom: card.bottom, aligned: Math.abs((name.top + name.bottom - score.top - score.bottom) / 2) < 2 };
    }));
    expect(geometry.every(row => row.height <= 48 && row.aligned)).toBe(true);
    if (width > height) expect(geometry.filter(row => row.bottom <= height).length).toBeGreaterThanOrEqual(5);
    await page.screenshot({ path: `/tmp/allthebenches-compact-${width}.png`, animations: 'disabled' });
    const bars = page.locator('.mobile-score-bar');
    expect(await bars.count()).toBeGreaterThan(2);
    expect(await bars.evaluateAll(items => new Set(items.map(el => (el as HTMLElement).style.backgroundColor)).size)).toBeGreaterThan(1);
    await page.locator('.portrait-model-score .score-button[data-heat]').first().click();
    await expect(page.getByRole('heading', { name: 'Result evidence', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Close', exact: true }).click();
    await page.getByRole('button', { name: 'Options', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Comparison options' })).toBeVisible();
    await expect(page.getByRole('combobox', { name: 'Table orientation' })).toBeHidden();
    await expect(page.getByRole('button', { name: 'Dense matrix', exact: true })).toBeHidden();
    await page.screenshot({ path: `/tmp/allthebenches-compact-options-${width}.png`, animations: 'disabled' });
    await page.locator('.mobile-advanced summary').click();
    await expect(page.getByRole('combobox', { name: 'Table orientation' })).toBeVisible();
    await page.locator('.mobile-advanced summary').click();
    await page.getByRole('button', { name: 'Filters', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Apply filters', exact: true })).toBeInViewport();
    await page.getByRole('button', { name: 'Cancel', exact: true }).click();
    await page.getByRole('button', { name: 'Done', exact: true }).click();
    await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    await expect(page.locator('[data-state=closed][role=dialog]')).toHaveCount(0);
    await expect(page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks' })).toBeInViewport();
    await page.screenshot({ path: `/tmp/allthebenches-mobile-${width}.png`, fullPage: false, animations: 'disabled' });
    await page.setViewportSize({ width: height, height: width });
    await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    await expect(page.locator('table')).toHaveCount(0);
  });
}
