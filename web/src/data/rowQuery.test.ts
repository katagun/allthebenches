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
  it('defaults all-model presets to newest releases first, with stable ties and unknown dates last', () => {
    const data = structuredClone({ catalog, details, manifest, market, results }) as unknown as AppData;
    // Deliberately avoid a hard-coded all-model preset ID.
    data.catalog.presets = [{ id: 'everything', version: '1', name: 'All models', model_configuration_ids: data.catalog.configurations.map(c => c.id), benchmark_ids: [] }];
    data.catalog.models.forEach((model, index) => { model.release_date = index === 0 ? null : index <= 2 ? '2026-10-18' : '2024-03-04'; });
    const view = { ...DEFAULT_VIEW, presetId: 'everything', includeUnbenchmarked: true, sort: null };
    const rows = queryRows(data, view, new Set());
    expect(rows.slice(0, 2).map(row => row.model.release_date)).toEqual(['2026-10-18', '2026-10-18']);
    expect(rows.at(-1)?.model.id).toBe(data.catalog.models[0].id);
    expect(rows.map(row => row.model.release_date ?? '')).toEqual(rows.map(row => row.model.release_date ?? '').sort().reverse());
    const tiedNames = rows.slice(0, 2).map(row => `${row.lab.name} ${row.model.name}`);
    expect(tiedNames).toEqual([...tiedNames].sort((a, b) => a.localeCompare(b)));
    const explicit = queryRows(data, { ...view, sort: { id: 'model', direction: 'asc' } }, new Set());
    const names = explicit.map(row => `${row.lab.name} ${row.model.name}`);
    expect(names).toEqual([...names].sort((a, b) => a.localeCompare(b)));
  });
  it('sorts the full result with zero intact and missing scores last in either direction', () => {
    const base = { catalog, details, manifest, market, results } as unknown as AppData;
    const selected = queryRows(base, DEFAULT_VIEW, new Set()).slice(0, 3);
    const data = structuredClone(base);
    const benchmarkId = data.catalog.benchmarks[0].id;
    data.catalog.presets = [{ id: DEFAULT_VIEW.presetId, version: 'test', name: 'Test', model_configuration_ids: selected.map(row => row.id), benchmark_ids: [benchmarkId] }];
    data.results.cells = selected.map((row, index) => ({ configuration_id: row.id, benchmark_id: benchmarkId, series_id: null, state: 'selected', value: [0, null, 3][index], unit: data.catalog.benchmarks[0].unit, observation_ids: [`test-${index}`] }));
    const ascending = { ...DEFAULT_VIEW, includeUnbenchmarked: true, sort: { id: benchmarkId, direction: 'asc' as const } };
    expect(queryRows(data, ascending, new Set()).map(row => row.id)).toEqual([selected[0].id, selected[2].id, selected[1].id]);
    expect(queryRows(data, { ...ascending, sort: { id: benchmarkId, direction: 'desc' } }, new Set()).map(row => row.id)).toEqual([selected[2].id, selected[0].id, selected[1].id]);
  });
});
