import type { PriceObservation, ServingRoute } from '../generated/dataset';
import type { ViewState } from '../state/viewState';

export const PRICE_MAX_AGE_MS = 48 * 60 * 60 * 1000;
export function priceFreshness(price: PriceObservation, asOf: number): 'fresh' | 'stale' | 'invalid' {
  const observed = Date.parse(price.observed_at);
  if (!Number.isFinite(observed) || observed > asOf) return 'invalid';
  return asOf - observed < PRICE_MAX_AGE_MS ? 'fresh' : 'stale';
}

/** Decimal comparison without rounding quoted amounts through binary floating point. */
export function priceAtMost(value: string | number | null | undefined, limit: number): boolean {
  const decimal = (input: string) => {
    const match = /^(\d+)(?:\.(\d+))?(?:e([+-]?\d+))?$/i.exec(input);
    if (!match) return null;
    const exponent = Number(match[3] ?? 0) - (match[2]?.length ?? 0);
    if (Math.abs(exponent) > 1000) return null;
    return { coefficient: BigInt(match[1] + (match[2] ?? '')), exponent };
  };
  if (value == null || !Number.isFinite(limit) || limit < 0) return false;
  const a = decimal(String(value)); const b = decimal(String(limit));
  if (!a || !b) return false;
  const exponent = Math.min(a.exponent, b.exponent);
  return a.coefficient * 10n ** BigInt(a.exponent - exponent) <= b.coefficient * 10n ** BigInt(b.exponent - exponent);
}

export function eligiblePrices(prices: PriceObservation[], routes: ServingRoute[], filters: ViewState['filters'], asOf: number): PriceObservation[] {
  return prices.filter(price => {
    const route = routes.find(item => item.id === price.route_id);
    const freshness = priceFreshness(price, asOf);
    return !!route && ['available', 'listed'].includes(route.availability ?? '') && price.available === true
      && price.currency === 'USD' && ['USD per 1M tokens', 'USD / 1M tokens'].includes(price.price_unit)
      && freshness !== 'invalid' && (freshness === 'fresh' || filters.includeStalePrices)
      && (!filters.routeIds.length || filters.routeIds.includes(route.id))
      && (filters.includeFreeRoutes || !(priceAtMost(price.input_price, 0) && priceAtMost(price.output_price, 0)));
  });
}
export function priceFiltersActive(filters: ViewState['filters']): boolean {
  return filters.maxInputPricePerMillion !== null || filters.maxOutputPricePerMillion !== null || filters.routeIds.length > 0 || !filters.includeFreeRoutes;
}
