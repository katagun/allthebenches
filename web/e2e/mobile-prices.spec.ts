import { expect, test } from '@playwright/test';
import { HOUR, installPriceFixture } from './fixtures/prices';
import { DEFAULT_VIEW } from '../src/state/viewState';

for (const width of [320, 390, 844]) {
  test(`mobile prices are discoverable, saved and source-linked at ${width}px`, async ({ page }) => {
    await installPriceFixture(page);
    await page.setViewportSize({ width, height: width === 844 ? 390 : 844 });
    await page.goto('./');
    await page.getByRole('button', { name: 'Show prices', exact: true }).click();
    const price = page.getByRole('button', { name: 'API prices for Claude Opus 5.5', exact: true });
    await expect(price).toContainText('Input $');
    await expect(price).toContainText('USD / 1M tokens');
    await expect(page.getByRole('button', { name: 'API prices for Muse Wonder Full', exact: true })).toContainText('Unknown, not free');
    await price.click();
    await expect(page.getByRole('heading', { name: 'API prices · Claude Opus 5.5' })).toBeVisible();
    await expect(page.getByRole('link', { name: /Pricing source/ }).first()).toHaveAttribute('href', 'https://openrouter.ai/api/v1/models/anthropic/claude-opus-5.5/endpoints');
    await expect(page.getByText(/Quote under 48 hours old · Observed/).first()).toBeVisible();
    await page.screenshot({ path: `/tmp/allthebenches-mobile-prices-detail-${width}.png` });
    await page.getByRole('button', { name: 'Close', exact: true }).click();
    await page.reload();
    await expect(page.getByRole('button', { name: 'Hide prices', exact: true })).toBeVisible();
    await expect(price).toContainText('Input $');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `/tmp/allthebenches-mobile-prices-${width}.png` });
    await page.getByRole('button', { name: 'Hide prices', exact: true }).click();
    await expect(price).toHaveCount(0);
    await expect(page.locator('.portrait-model-score .score-button').first()).toBeVisible();
    await expect(page.locator('.portrait-model-score').filter({ hasText: 'Other setups' })).toHaveCount(0);
  });
}

test('price-only mobile views retain releases and distinguish explicit zero quotes', async ({ page }) => {
  await installPriceFixture(page);
  await page.setViewportSize({ width: 390, height: 844 });
  const view = { ...structuredClone(DEFAULT_VIEW), presetId: 'all_models_oct2026', search: 'Dots3', visibleColumnIds: ['market:price'], includeUnbenchmarked: true };
  await page.goto(`./#/?v=${encodeURIComponent(JSON.stringify(view))}`);
  await expect(page.getByRole('button', { name: 'API prices for Dots3-Note Preview', exact: true })).toContainText('Input $0 · Output $0');
});

for (const { label, ageMs, fresh } of [
  { label: 'one millisecond before expiry', ageMs: 48 * HOUR - 1, fresh: true },
  { label: 'exactly at expiry', ageMs: 48 * HOUR, fresh: false },
  { label: 'future observation', ageMs: -1, fresh: false },
]) {
  test(`mobile price eligibility: ${label}`, async ({ page }) => {
    await installPriceFixture(page, ageMs);
    await page.setViewportSize({ width: 390, height: 844 });
    const view = { ...structuredClone(DEFAULT_VIEW), presetId: 'all_models_oct2026', search: 'Claude Opus 5.5', visibleColumnIds: ['market:price'], includeUnbenchmarked: true };
    await page.goto(`./#/?v=${encodeURIComponent(JSON.stringify(view))}`);
    const price = page.getByRole('button', { name: 'API prices for Claude Opus 5.5', exact: true });
    await expect(price).toContainText(fresh ? 'Input $4 · Output $20' : 'Unknown, not free');
    await page.reload();
    await expect(price).toContainText(fresh ? 'Input $4 · Output $20' : 'Unknown, not free');
  });
}
