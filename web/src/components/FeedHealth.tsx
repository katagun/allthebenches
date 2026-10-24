import type { AppData } from '../data/snapshots';
import { eligiblePrices } from '../data/prices';
import { DEFAULT_VIEW } from '../state/viewState';

const timestamp = (value?: string | null) => value && Number.isFinite(Date.parse(value)) ? new Date(value).toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, ' UTC') : 'Unknown';

export function FeedHealth({ data, asOf }: { data: AppData; asOf: number }) {
  const feeds = data.manifest.feeds;
  const problems = feeds.filter(feed => feed.status !== 'ok').length;
  const prices = eligiblePrices(data.market.prices, data.market.routes, DEFAULT_VIEW.filters, asOf);
  const routeIds = new Set(prices.map(price => price.route_id));
  const models = new Set(data.market.routes.filter(route => routeIds.has(route.id)).map(route => route.model_id));
  return <details className="feed-health"><summary>Data health · {feeds.length ? problems ? `${problems} ${problems === 1 ? 'feed needs' : 'feeds need'} attention` : 'Latest recorded collections succeeded' : 'Collection status unknown'}</summary>
    <p>Fresh available prices: {models.size} of {data.catalog.models.length} releases · {routeIds.size} routes. Quotes expire after 48 hours. Missing prices are unknown, never free.</p>
    <p>These are the collection results recorded in this published snapshot, not a live monitor. A successful collection does not mean every model has a reviewed price. New discoveries require review before publication.</p>
    <ul>{feeds.map((feed, index) => <li key={`${feed.source_id}-${index}`}><strong>{feed.source_id}{feed.url ? ` · ${feed.url.replace(/^https?:\/\/[^/]+\//, '')}` : ''}</strong><span>{feed.status === 'ok' ? 'Accepted' : feed.status === 'stale' ? 'Refresh failed · retained data' : feed.status === 'error' ? 'Collection failed' : feed.status === 'partial' ? 'Partial collection' : 'Unknown'}</span><span>Last attempt: {timestamp(feed.attempted_at)}</span><span>Last accepted: {timestamp(feed.as_of)}{feed.record_count != null ? ` · ${feed.record_count} records` : ''}</span></li>)}</ul>
  </details>;
}
