import type { Page } from '@playwright/test';
import type { ManifestSnapshot, PriceObservation, ServingRoute, Source } from '../../src/generated/dataset';

// This clock belongs only to synthetic quotes, never to published observations.
export const FIXTURE_NOW = Date.UTC(2030, 0, 15, 12);
export const HOUR = 60 * 60 * 1000;
export const fixtureFeeds: ManifestSnapshot['feeds'] = [
  { source_id: 'openrouter-endpoints', url: 'https://openrouter.ai/api/v1/models/anthropic/claude-opus-5.5/endpoints', status: 'ok', as_of: new Date(FIXTURE_NOW - HOUR).toISOString(), attempted_at: new Date(FIXTURE_NOW - HOUR).toISOString(), record_count: 1 },
  { source_id: 'openrouter-endpoints', url: 'https://openrouter.ai/api/v1/models/deepseek/deepseek-r1/endpoints', status: 'stale', as_of: new Date(FIXTURE_NOW - 72 * HOUR).toISOString(), attempted_at: new Date(FIXTURE_NOW - 10 * 60 * 1000).toISOString(), record_count: 1 },
];
const source: Source = { id: 'test-price-source', title: 'Controlled endpoint price evidence', publisher: 'OpenRouter', url: fixtureFeeds[0].url! };
const routes: ServingRoute[] = [
  { id: 'test-paid-route', model_id: 'claude_opus55', provider: 'Test provider', availability: 'listed', source_ids: [source.id] },
  { id: 'test-free-route', model_id: 'dots3_note_preview', provider: 'Test provider', availability: 'listed', source_ids: [source.id] },
];

/** Keep the real app/worker/catalog; isolate only changing price and feed inputs. */
export async function installPriceFixture(page: Page, ageMs = HOUR) {
  await page.clock.setFixedTime(new Date(FIXTURE_NOW));
  const prices: PriceObservation[] = routes.map((route, index) => ({
    id: `test-price-${index}`, route_id: route.id, source_id: source.id,
    quote_scope: 'Test endpoint price', currency: 'USD', price_unit: 'USD per 1M tokens',
    input_price: index ? '0' : '4', output_price: index ? '0' : '20', available: true,
    observed_at: new Date(FIXTURE_NOW - ageMs).toISOString(),
  }));
  await page.route('**/data/comparison.json', async route => {
    const response = await route.fetch();
    const data = await response.json();
    data.market.prices = prices;
    data.market.routes = routes;
    data.manifest.feeds = fixtureFeeds;
    await route.fulfill({ response, json: data });
  });
  await page.route('**/data/evidence-*.json', async route => {
    const response = await route.fetch();
    const data = await response.json();
    data.sources.push(source);
    await route.fulfill({ response, json: data });
  });
}
