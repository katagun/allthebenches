import { describe, expect, it } from 'vitest';
import type { PriceObservation, ServingRoute } from '../generated/dataset';
import { DEFAULT_VIEW, parseViewState } from '../state/viewState';
import { eligiblePrices, priceAtMost, priceFreshness, PRICE_MAX_AGE_MS } from './prices';

const now = Date.parse('2026-10-22T12:00:00Z');
const route = { id: 'route', availability: 'listed' } as ServingRoute;
const price = { id: 'quote', route_id: 'route', currency: 'USD', price_unit: 'USD per 1M tokens', available: true, input_price: '1', output_price: '2', observed_at: new Date(now - PRICE_MAX_AGE_MS + 1).toISOString() } as PriceObservation;
const eligible = (quote = price, changes = {}, routes = [route]) => eligiblePrices([quote], routes, { ...DEFAULT_VIEW.filters, ...changes }, now);

describe('price eligibility', () => {
  it('expires exactly at 48 hours and only accepts stale dates with explicit historical opt-in', () => {
    expect(priceFreshness(price, now)).toBe('fresh');
    expect(eligible()).toHaveLength(1);
    const stale = { ...price, observed_at: new Date(now - PRICE_MAX_AGE_MS).toISOString() };
    expect(priceFreshness(stale, now)).toBe('stale');
    expect(eligible(stale)).toEqual([]);
    expect(eligible(stale, { includeStalePrices: true })).toHaveLength(1);
    for (const date of ['invalid', new Date(now + 1).toISOString()]) {
      expect(eligible({ ...price, observed_at: date }, { includeStalePrices: true })).toEqual([]);
    }
  });
  it('rejects unsupported units, currencies, unavailable quotes and routes, even in historical mode', () => {
    for (const change of [{ currency: 'EUR' }, { price_unit: 'USD per token' }, { available: false }, { route_id: null }]) {
      expect(eligible({ ...price, ...change }, { includeStalePrices: true })).toEqual([]);
    }
    for (const availability of ['unavailable', 'unknown', 'retired']) expect(eligible(price, {}, [{ ...route, availability }])).toEqual([]);
    expect(eligible(price, { routeIds: ['different'] })).toEqual([]);
    expect(eligible({ ...price, input_price: '0', output_price: '0' }, { includeFreeRoutes: false })).toEqual([]);
    expect(eligible({ ...price, input_price: '0', output_price: '0' })).toHaveLength(1);
  });
  it('compares decimal thresholds exactly and refuses absent or malformed prices', () => {
    expect(priceAtMost('0.100000000000000001', 0.1)).toBe(false);
    expect(priceAtMost('0.100000000000000000', 0.1)).toBe(true);
    expect(priceAtMost('1e-7', 0.0000001)).toBe(true);
    expect(priceAtMost(0, 0)).toBe(true);
    for (const value of [null, undefined, '', '-1', 'NaN', 'Infinity']) expect(priceAtMost(value, 1)).toBe(false);
  });
  it('defaults old saved views to fresh quotes and preserves an explicit historical choice', () => {
    const old = structuredClone(DEFAULT_VIEW) as unknown as { filters: Record<string, unknown> };
    delete old.filters.includeStalePrices;
    expect(parseViewState(old)).toMatchObject({ ok: true, value: { filters: { includeStalePrices: false } } });
    old.filters.includeStalePrices = true;
    expect(parseViewState(old)).toMatchObject({ ok: true, value: { filters: { includeStalePrices: true } } });
    old.filters.includeStalePrices = 'true';
    expect(parseViewState(old).ok).toBe(false);
  });
});
