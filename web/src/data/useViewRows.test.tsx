import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import catalog from '../../public/data/catalog.json';
import details from '../../public/data/details.json';
import manifest from '../../public/data/manifest.json';
import market from '../../public/data/market.json';
import results from '../../public/data/results.json';
import { queryRows } from './rowQuery';
import { useViewRows } from './useViewRows';
import { DEFAULT_VIEW } from '../state/viewState';
import type { AppData } from './snapshots';
import type { WorkerTransport } from './rowWorkerClient';
import { PRICE_MAX_AGE_MS } from './prices';
const data = { catalog, details, manifest, market, results } as unknown as AppData;
const expanded = new Set<string>();
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

class ComputingWorker implements WorkerTransport {
  onmessage: WorkerTransport['onmessage'] = null;
  onerror: WorkerTransport['onerror'] = null;
  data!: AppData;
  postMessage(message: Parameters<WorkerTransport['postMessage']>[0]) {
    if (message.type === 'initialize') { this.data = message.data; queueMicrotask(() => this.onmessage?.({ data: { type: 'ready' } } as MessageEvent)); }
    else queueMicrotask(() => this.onmessage?.({ data: { type: 'rows', id: message.id, key: message.key, rows: queryRows(this.data, message.view, new Set(message.expandedIds), message.asOf) } } as MessageEvent));
  }
  terminate() { this.onmessage = null; }
}
for (const worker of [false, true]) {
  it(`reselects configurations on column changes without search, including a cached return (${worker ? 'worker' : 'fallback'})`, async () => {
    vi.stubGlobal('Worker', worker ? ComputingWorker : undefined);
    const preset = catalog.presets.find(p => p.id === 'all_models_oct2026')!;
    const before = { ...structuredClone(DEFAULT_VIEW), presetId: preset.id, visibleColumnIds: preset.benchmark_ids };
    const after = { ...before, visibleColumnIds: ['terminal_bench_4'] };
    const initial = queryRows(data, before, expanded).map(row => row.id);
    const expected = queryRows(data, after, expanded).map(row => row.id);
    expect(expected).not.toEqual(initial);
    const hook = renderHook(({ view }) => useViewRows(data, view, expanded), { initialProps: { view: before } });
    await waitFor(() => expect(hook.result.current.busy).toBe(false));
    expect(hook.result.current.rows.map(row => row.id)).toEqual(initial);
    hook.rerender({ view: after });
    await waitFor(() => expect(hook.result.current.busy).toBe(false));
    expect(hook.result.current.rows.map(row => row.id)).toEqual(expected);
    hook.rerender({ view: before });
    await waitFor(() => expect(hook.result.current.busy).toBe(false));
    expect(hook.result.current.rows.map(row => row.id)).toEqual(initial);
  });
  it(`expires quotes in an open page and restores them only with historical opt-in (${worker ? 'worker' : 'fallback'})`, async () => {
    vi.useFakeTimers();
    vi.stubGlobal('Worker', worker ? ComputingWorker : undefined);
    const now = Date.parse('2026-10-22T12:00:00Z');
    vi.setSystemTime(now);
    const fixture = structuredClone(data);
    fixture.market.prices = [{ ...fixture.market.prices[0], observed_at: new Date(now - PRICE_MAX_AGE_MS + 1000).toISOString() }];
    const view = { ...structuredClone(DEFAULT_VIEW), presetId: 'all_models_oct2026', filters: { ...DEFAULT_VIEW.filters, maxInputPricePerMillion: 10 } };
    const hook = renderHook(({ view }) => useViewRows(fixture, view, expanded), { initialProps: { view } });
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(hook.result.current.rows).toHaveLength(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(1001); });
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(hook.result.current.busy).toBe(false);
    expect(hook.result.current.rows).toEqual([]);
    hook.rerender({ view: { ...view, filters: { ...view.filters, includeStalePrices: true } } });
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(hook.result.current.rows).toHaveLength(1);
  });
}
