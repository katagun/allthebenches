import { expect, test } from '@playwright/test';

test('published price evidence is readable on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('./');
  await page.getByRole('button', { name: 'Show prices', exact: true }).click();
  await page.getByRole('button', { name: 'API prices for Claude Opus 5.5', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'API prices · Claude Opus 5.5' })).toBeVisible();
  // A failed upstream may legitimately leave an unknown quote: never fake freshness.
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('published market and comparison prices agree', async ({ request }) => {
  const market = await (await request.get('data/market.json')).json();
  const comparison = await (await request.get('data/comparison.json')).json();
  expect(comparison.market.prices).toEqual(market.prices);
  const quotes = new Map<string, { observed_at: string }>(market.prices.map((p: { route_id: string; observed_at: string }) => [p.route_id, p]));
  const alibaba = comparison.manifest.feeds.find((f: { source_id: string }) => f.source_id === 'alibaba');
  if (alibaba?.status === 'ok') {
    expect(quotes.get('alibaba:qwen3.8-max:singapore:international')?.observed_at).toBe(alibaba.as_of);
  }
  expect(market.routes.length).toBeGreaterThan(195);
});
