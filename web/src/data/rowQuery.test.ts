import { describe, expect, it } from 'vitest';
import catalog from '../../public/data/catalog.json';
import details from '../../public/data/details.json';
import manifest from '../../public/data/manifest.json';
import market from '../../public/data/market.json';
import results from '../../public/data/results.json';
import type { AppData } from './snapshots';
import { queryRows } from './rowQuery';
import { DEFAULT_VIEW } from '../state/viewState';

describe('worker row ordering', () => {
  it('sorts the full result with zero intact and missing scores last in either direction', () => {
    const base = { catalog, details, manifest, market, results } as unknown as AppData;
    const selected = queryRows(base, DEFAULT_VIEW, new Set()).slice(0, 3);
    const data = structuredClone(base);
    const benchmarkId = data.catalog.benchmarks[0].id;
    data.catalog.presets = [{ id: DEFAULT_VIEW.presetId, version: 'test', name: 'Test', model_configuration_ids: selected.map(row => row.id), benchmark_ids: [benchmarkId] }];
    data.results.cells = selected.map((row, index) => ({ configuration_id: row.id, benchmark_id: benchmarkId, series_id: null, state: 'selected', value: [0, null, 3][index], unit: '%', observation_ids: [] }));
    const ascending = { ...DEFAULT_VIEW, includeUnbenchmarked: true, sort: { id: benchmarkId, direction: 'asc' as const } };
    expect(queryRows(data, ascending, new Set()).map(row => row.id)).toEqual([selected[0].id, selected[2].id, selected[1].id]);
    expect(queryRows(data, { ...ascending, sort: { id: benchmarkId, direction: 'desc' } }, new Set()).map(row => row.id)).toEqual([selected[2].id, selected[0].id, selected[1].id]);
  });
});
