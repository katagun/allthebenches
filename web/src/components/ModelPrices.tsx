import type { PriceObservation } from '../generated/dataset';
import type { DisplayRow } from '../data/selectors';
import type { FullAppData } from '../data/snapshots';
import type { ViewState } from '../state/viewState';
import { eligiblePrices, priceFreshness } from '../data/prices';
import { SheetDescription, SheetHeader, SheetTitle } from './ui/sheet';

export const amount = (value: string | number | null | undefined) => value == null ? 'Unknown' : `$${Number(value).toLocaleString(undefined, { maximumSignificantDigits: 6 })}`;
export function priceRangeLabel(prices: PriceObservation[], field: 'input_price' | 'output_price') {
  const values = prices.map(price => price[field]).filter(value => value != null).map(Number);
  if (!values.length) return 'Unknown';
  const low = Math.min(...values), high = Math.max(...values);
  return low === high ? amount(low) : `${amount(low)}–${amount(high)}`;
}
export function MobilePriceSummary({ row, asOf, onOpen }: { row: DisplayRow; asOf: number; onOpen: () => void }) {
  const routeCount = new Set(row.prices.map(price => price.route_id)).size;
  const stale = row.prices.some(price => priceFreshness(price, asOf) === 'stale');
  return <button className="mobile-price-summary" onClick={onOpen} aria-label={`API prices for ${row.model.name}`}>
    <span>{row.prices.length ? `Input ${priceRangeLabel(row.prices, 'input_price')} · Output ${priceRangeLabel(row.prices, 'output_price')}` : 'No eligible API price'}</span>
    <small>{row.prices.length ? `USD / 1M tokens · ${routeCount} route${routeCount === 1 ? '' : 's'}${stale ? ' · Historical' : ''} · Details ›` : 'Unknown, not free · Details ›'}</small>
  </button>;
}
export function ModelPrices({ data, modelId, filters, asOf }: { data: FullAppData; modelId: string; filters: ViewState['filters']; asOf: number }) {
  const model = data.catalog.models.find(item => item.id === modelId);
  const routes = data.market.routes.filter(route => route.model_id === modelId);
  const prices = eligiblePrices(data.market.prices, routes, filters, asOf);
  return <><SheetHeader><SheetTitle>API prices · {model?.name}</SheetTitle><SheetDescription>Provider route quotes in USD per 1 million tokens. Prices describe serving routes, not benchmark evaluation costs.</SheetDescription></SheetHeader>
    <div className="drawer-scroll detail-scroll price-details">
      <p>Quotes match the current route and freshness settings. Input and output ranges may come from different routes; inspect each route for a paired quote.</p>
      {!prices.length && <p>No eligible API price for this model. Pricing may be unpublished, unavailable, or older than 48 hours. Missing pricing is unknown, not free.</p>}
      {prices.map(price => { const route = routes.find(item => item.id === price.route_id)!; const source = data.details.sources.find(item => item.id === price.source_id); return <section className="route-card" key={price.id}>
        <h3>{route.provider}</h3><span>{route.routing_variant ?? 'Default route'} · {route.availability}</span>
        <p>Input {amount(price.input_price)} · Output {amount(price.output_price)} / 1M tokens</p>
        <p>{priceFreshness(price, asOf) === 'stale' ? 'Historical quote (48+ hours old)' : 'Quote under 48 hours old'} · Observed {`${new Date(price.observed_at).toLocaleString(undefined, { timeZone: 'UTC' })} UTC`}</p>
        {price.cache_read_price != null && <p>Cache read {amount(price.cache_read_price)} / 1M tokens</p>}
        {price.cache_write_price != null && <p>Cache write {amount(price.cache_write_price)} / 1M tokens</p>}
        {price.cache_write_1h_price != null && <p>1-hour cache write {amount(price.cache_write_1h_price)} / 1M tokens</p>}
        {(price.additional_charges ?? []).map(charge => <p key={charge.name}>{charge.name.replaceAll('_', ' ')}: {amount(charge.amount)} · {charge.unit}</p>)}
        {(price.restrictions ?? []).map((restriction, index) => <p key={index}>{restriction}</p>)}
        {source && <a href={source.url} target="_blank" rel="noreferrer">Pricing source · {source.publisher}</a>}
      </section>; })}
    </div></>;
}
