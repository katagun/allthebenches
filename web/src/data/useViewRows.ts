import { useEffect, useMemo, useRef, useState } from 'react';
import type { ViewState } from '../state/viewState';
import type { AppData } from './snapshots';
import { RowWorkerClient, type RowRequestResult } from './rowWorkerClient';
import type { DisplayRow } from './selectors';

type RowState = { data: AppData; key: string; rows: DisplayRow[]; error: string | null };
export const EMPTY_ROWS: DisplayRow[] = [];

/** Only fields consumed by row selection and ordering belong in this key.
 * Column visibility affects benchmark searches; ordinary checkbox selections do not re-run a query.
 */
function rowQueryKey(view: ViewState, expandedIds: string[]) {
  const { presetId, categoryId, search, sort, compare, includeUnbenchmarked, filters } = view;
  return JSON.stringify({
    presetId, categoryId, search, sort, compare, includeUnbenchmarked, filters,
    searchBenchmarkIds: search.trim() ? view.visibleColumnIds : [],
    selectedConfigurationIds: compare ? view.selectedConfigurationIds : [],
    expandedIds,
  });
}
export function useViewRows(data: AppData | null, view: ViewState | null, expanded: Set<string>) {
  const client = useRef<{ data: AppData; instance: RowWorkerClient } | null>(null);
  const [result, setResult] = useState<RowState | null>(null);
  const expandedIds = useMemo(() => [...expanded].sort(), [expanded]);
  const queryViewRef = useRef(view);
  queryViewRef.current = view;
  const requestKey = useMemo(() => view ? rowQueryKey(view, expandedIds) : '', [view, expandedIds]);

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
    void instance.request(queryView, expandedIds, requestKey).then((response: RowRequestResult | null) => {
      if (!active || !response || response.key !== requestKey) return;
      setResult({ data, key: requestKey, rows: 'rows' in response ? response.rows : [], error: 'error' in response ? response.error : null });
    });
    return () => { active = false; };
  }, [data, requestKey, expandedIds]);

  const current = result?.data === data && result.key === requestKey ? result : null;
  return { rows: current?.rows ?? EMPTY_ROWS, busy: !!data && !!view && current === null, error: current?.error ?? null };
}
