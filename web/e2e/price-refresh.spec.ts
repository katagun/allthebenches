import { expect, test, type Page } from '@playwright/test';
import type { AppData } from '../src/data/snapshots';

// These tests never substitute price/feed data. Freeze only the real run time so
// a quote cannot cross the expiry boundary between reading it and checking UI.
async function publication(page: Page) {
  const now = Date.now();
  await page.clock.setFixedTime(new Date(now));
  const loaded = page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/data/comparison.json'));
  await page.goto('./');
  const response = await loaded;
  expect(response.ok()).toBe(true);
  const data = await response.json() as AppData;
  // Independent contract calculation, deliberately not the app's selector.
  const fresh = data.market.prices.filter(quote => {
    const route = data.market.routes.find(row => row.id === quote.route_id);
    const age = now - Date.parse(quote.observed_at);
    return route && ['available', 'listed'].includes(route.availability ?? '') && quote.available === true
      && quote.currency === 'USD' && ['USD per 1M tokens', 'USD / 1M tokens'].includes(quote.price_unit)
      && age >= 0 && age < 48 * 60 * 60 * 1000;
  });
  return { data, fresh };
}

for (const width of [320, 390, 844]) {
  test(`unmocked published price evidence at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width === 844 ? 390 : 844 });
    const { data, fresh } = await publication(page);
    const routeIds = new Set(data.market.routes.filter(route => route.model_id === 'claude_opus55').map(route => route.id));
    const hasPrice = fresh.some(quote => routeIds.has(quote.route_id!));
    await page.getByRole('button', { name: 'Show prices', exact: true }).click();
    const price = page.getByRole('button', { name: 'API prices for Claude Opus 5.5', exact: true });
    await expect(price).toContainText(hasPrice ? 'Input $' : 'Unknown, not free');
    await price.click();
    await expect(page.getByRole('heading', { name: 'API prices · Claude Opus 5.5' })).toBeVisible();
    if (hasPrice) {
      await expect(page.getByText(/Quote under 48 hours old · Observed/).first()).toBeVisible();
      await expect(page.getByRole('link', { name: /Pricing source/ }).first()).toHaveAttribute('href', /^https:\/\//);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}

for (const width of [1440, 390]) {
  test(`unmocked feed health matches the published snapshot at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 844 });
    const { data, fresh } = await publication(page);
    const routeIds = new Set(fresh.map(quote => quote.route_id));
    const modelIds = new Set(data.market.routes.filter(route => routeIds.has(route.id)).map(route => route.model_id));
    await page.locator('.feed-health summary').click();
    await expect(page.getByText(`Fresh available prices: ${modelIds.size} of ${data.catalog.models.length} releases · ${routeIds.size} routes.`, { exact: false })).toBeVisible();
    const rows = page.locator('.feed-health li');
    await expect(rows).toHaveCount(data.manifest.feeds.length);
    for (const [index, feed] of data.manifest.feeds.entries()) {
      const row = rows.nth(index);
      const stamp = (value?: string | null) => value ? new Date(value).toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, ' UTC') : 'Unknown';
      await expect(row).toContainText(`Last accepted: ${stamp(feed.as_of)}`);
      await expect(row).toContainText(`Last attempt: ${stamp(feed.attempted_at)}`);
      if (feed.status === 'stale') await expect(row).toContainText('Refresh failed · retained data');
      if (feed.status === 'ok') await expect(row).toContainText('Accepted');
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath('published-feed-health.png') });
  });
}

test('published market and comparison prices agree', async ({ request }) => {
  const marketResponse = await request.get('data/market.json');
  const comparisonResponse = await request.get('data/comparison.json');
  expect(marketResponse.ok()).toBe(true);
  expect(comparisonResponse.ok()).toBe(true);
  const market = await marketResponse.json();
  const comparison = await comparisonResponse.json();
  expect(comparison.market.prices).toEqual(market.prices);
  const quotes = new Map<string, { observed_at: string }>(market.prices.map((p: { route_id: string; observed_at: string }) => [p.route_id, p]));
  const alibaba = comparison.manifest.feeds.find((f: { source_id: string }) => f.source_id === 'alibaba');
  if (alibaba?.status === 'ok') {
    expect(quotes.get('alibaba:qwen3.8-max:singapore:international')?.observed_at.replace(/\+00:00$/, 'Z'))
      .toBe(alibaba.as_of.replace(/\+00:00$/, 'Z'));
  }
  expect(market.routes.length).toBeGreaterThan(0);
});
