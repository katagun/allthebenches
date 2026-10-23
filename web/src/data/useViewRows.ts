import { PRICE_MAX_AGE_MS } from './prices';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { ViewState } from '../state/viewState';
import type { AppData } from './snapshots';
import { RowWorkerClient, type RowRequestResult } from './rowWorkerClient';
import type { DisplayRow } from './selectors';

type RowState = { data: AppData; key: string; rows: DisplayRow[]; error: string | null };
export const EMPTY_ROWS: DisplayRow[] = [];

/** Only fields consumed by row selection and ordering belong in this key.
 * Visible benchmarks also determine the primary configuration, even without search.
 */
function rowQueryKey(view: ViewState, expandedIds: string[], asOf: number) {
  const { presetId, categoryId, search, sort, compare, includeUnbenchmarked, filters } = view;
  return JSON.stringify({
    presetId, categoryId, search, sort, compare, includeUnbenchmarked, filters,
    visibleColumnIds: view.visibleColumnIds,
    selectedConfigurationIds: compare ? view.selectedConfigurationIds : [],
    expandedIds, asOf,
  });
}
export function useViewRows(data: AppData | null, view: ViewState | null, expanded: Set<string>) {
  const [asOf, setAsOf] = useState(Date.now);
  useEffect(() => { setAsOf(Date.now()); }, [data]);
  // Requery at each freshness boundary, and after returning from a suspended tab.
  useEffect(() => {
    const now = Date.now();
    const transitions = data?.market.prices.flatMap(price => {
      const observed = Date.parse(price.observed_at);
      return [observed, observed + PRICE_MAX_AGE_MS];
    }).filter(time => Number.isFinite(time) && time > now) ?? [];
    const refresh = () => setAsOf(Date.now());
    const timer = transitions.length ? window.setTimeout(refresh, Math.min(Math.min(...transitions) - now, 2_147_483_647)) : undefined;
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => { window.clearTimeout(timer); window.removeEventListener('focus', refresh); document.removeEventListener('visibilitychange', refresh); };
  }, [data, asOf]);
  const client = useRef<{ data: AppData; instance: RowWorkerClient } | null>(null);
  const [result, setResult] = useState<RowState | null>(null);
  const expandedIds = useMemo(() => [...expanded].sort(), [expanded]);
  const queryViewRef = useRef(view);
  queryViewRef.current = view;
  const requestKey = useMemo(() => view ? rowQueryKey(view, expandedIds, asOf) : '', [view, expandedIds, asOf]);

  useEffect(() => {
    if (!data) return;
    const instance = new RowWorkerClient(data);
    client.current = { data, instance };
    return () => { instance.close(); if (client.current?.instance === instance) client.current = null; };
  }, [data]);

  useEffect(() => {
    if (!data || !requestKey) return;
    const instance = client.current?.data === data ? client.current.instance : null;
    if (!instance) return;
    const queryView = queryViewRef.current;
    if (!queryView) return;
    let active = true;
    void instance.request(queryView, expandedIds, requestKey, asOf).then((response: RowRequestResult | null) => {
      if (!active || !response || response.key !== requestKey) return;
      setResult({ data, key: requestKey, rows: 'rows' in response ? response.rows : [], error: 'error' in response ? response.error : null });
    });
    return () => { active = false; };
  }, [data, requestKey, expandedIds, asOf]);

  const current = result?.data === data && result.key === requestKey ? result : null;
  return { rows: current?.rows ?? EMPTY_ROWS, busy: !!data && !!view && current === null, error: current?.error ?? null, asOf };
}
