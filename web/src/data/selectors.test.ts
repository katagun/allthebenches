import { describe, expect, it } from 'vitest';
import { hasResultOnBenchmarks, numericScoreCount, orderColumnsByModelCoverage, rowsForView } from './selectors';
import type { AppData } from './snapshots';
import { DEFAULT_VIEW } from '../state/viewState';

function dataset(values: Record<string, Record<string, number | null>>, routes: unknown[] = [], prices: unknown[] = []): AppData {
  const configurations = Object.keys(values).map(id => ({ id, model_id: 'model', reasoning_label: id, mode: 'enabled' as const }));
  const cells = Object.entries(values).flatMap(([configuration_id, scores]) => Object.entries(scores).filter(([, value]) => value !== null).map(([benchmark_id, value]) => ({ configuration_id, benchmark_id, series_id: null, state: 'selected' as const, value: value!, unit: '%', observation_ids: [`o-${configuration_id}-${benchmark_id}`] })));
  return {
    catalog: {
      schema_version: '1', data_version: 'test', generated_at: null,
      labs: [{ id: 'lab', name: 'Lab', hq_country_codes: ['US'] }],
      models: [{ id: 'model', lab_ids: ['lab'], family_id: 'family', name: 'Model', access_state: 'available', weights_state: 'closed', modalities: ['text'] }],
      configurations,
      benchmarks: [{ id: 'b1', family_id: 'f1', name: 'Benchmark 1', version: '1', category: 'coding', modality: 'text', metric_name: 'score', unit: '%', direction: 'higher' }, { id: 'b2', family_id: 'f2', name: 'Benchmark 2', version: '1', category: 'math', modality: 'text', metric_name: 'score', unit: '%', direction: 'higher' }],
      presets: [{ id: 'frontier_oct2026', version: '1', name: 'Frontier', model_configuration_ids: ['c1'], benchmark_ids: ['b1','b2'] }],
      coverage_gaps: [], metadata_claims: [], missing_cells: [], saturation: [],
    },
    results: { schema_version: '1', observations: [], cells },
    details: { schema_version: '1', sources: [], series: [], observations: [], external_mappings: [], metadata_claims: [] },
    market: { schema_version: '1', routes, prices, usage: [] },
    manifest: { schema_version: '1', data_version: 'test', snapshot_id: 'test-snapshot', generated_at: null, files: {}, coverage: { models: 1, benchmarked_models: 1, observations: cells.length, display_cells: cells.length, benchmarks: 2 }, feeds: [] },
  } as unknown as AppData;
}

describe('table row selectors', () => {
  it('chooses one highest-coverage configuration for the all-model primary row, counting zero', () => {
    const data = dataset({ c1: { b1: 90 }, c2: { b1: 10, b2: 0 } });
    const view = { ...structuredClone(DEFAULT_VIEW), visibleColumnIds: ['b1', 'b2'] };
    expect(rowsForView(data, view, new Set()).map(row => row.configuration.id)).toEqual(['c2']);
    expect(rowsForView(data, view, new Set(['model'])).map(row => row.configuration.id)).toEqual(['c2', 'c1']);
  });
  it('orders benchmark columns by distinct model coverage with stable ties', () => {
    const data = dataset({ c1: { b1: 90, b2: 80 } });
    data.catalog.models.push({ ...data.catalog.models[0], id: 'model-2', name: 'Model 2' });
    data.catalog.configurations.push({ id: 'c2', model_id: 'model-2' });
    data.results.cells.push({ configuration_id: 'c2', benchmark_id: 'b1', state: 'selected', value: 0, unit: '%', observation_ids: ['zero'] } as never);
    expect(orderColumnsByModelCoverage(data, ['b2', 'b1'])).toEqual(['b1', 'b2']);
    expect(orderColumnsByModelCoverage(data, ['b2', 'unknown'])).toEqual(['b2', 'unknown']);
  });
  it('counts unique numeric scores across all benchmarks and only the current page subset', () => {
    const data = dataset({ c1: { b1: 0, b2: 80 } });
    const row = rowsForView(data, structuredClone(DEFAULT_VIEW), new Set())[0];
    expect(numericScoreCount(row)).toBe(2);
    expect(numericScoreCount(row, ['b1'])).toBe(1);
    expect(hasResultOnBenchmarks(row, ['missing'])).toBe(false);
    expect(hasResultOnBenchmarks(row, ['b1'])).toBe(true);
    row.observations.set('b2', { ...row.observations.get('b2')!, state: 'disputed', value: null });
    expect(numericScoreCount(row)).toBe(1);
    expect(hasResultOnBenchmarks(row, ['b2'])).toBe(true);
  });
  it('retains a curated preset configuration even when another configuration has broader coverage', () => {
    const data = dataset({ c1: { b1: 90 }, c2: { b1: 10, b2: 0 } });
    data.catalog.models.push({ ...data.catalog.models[0], id: 'model-2', name: 'Other model' });
    data.catalog.presets[0].model_configuration_ids = ['c1'];
    const view = { ...structuredClone(DEFAULT_VIEW), visibleColumnIds: ['b1', 'b2'] };
    expect(rowsForView(data, view, new Set()).map(row => row.configuration.id)).toEqual(['c1']);
  });
  it('requires compound score thresholds on one exact configuration', () => {
    const data = dataset({ c1: { b1: 90, b2: 40 }, c2: { b1: 40, b2: 95 } });
    const view = { ...structuredClone(DEFAULT_VIEW), filters: { ...DEFAULT_VIEW.filters, scoreConditions: [{ benchmarkId: 'b1', operator: '>=' as const, value: 80 }, { benchmarkId: 'b2', operator: '>=' as const, value: 80 }] } };
    expect(rowsForView(data, view, new Set())).toEqual([]);
  });
  it('can surface an alternate configuration that satisfies all conditions while collapsed', () => {
    const data = dataset({ c1: { b1: 90, b2: 40 }, c2: { b1: 85, b2: 95 } });
    const view = { ...structuredClone(DEFAULT_VIEW), filters: { ...DEFAULT_VIEW.filters, scoreConditions: [{ benchmarkId: 'b1', operator: '>=' as const, value: 80 }, { benchmarkId: 'b2', operator: '>=' as const, value: 80 }] } };
    expect(rowsForView(data, view, new Set()).map(row => row.configuration.id)).toEqual(['c2']);
  });
  it('applies input and output limits to the same route', () => {
    const routes = [{ id: 'route-a', model_id: 'model', provider: 'A' }, { id: 'route-b', model_id: 'model', provider: 'B' }];
    const prices = [{ id: 'p-a', route_id: 'route-a', currency: 'USD', input_price: '1', output_price: '100', price_unit: 'USD / 1M tokens', observed_at: '2026-10-01', source_id: 's' }, { id: 'p-b', route_id: 'route-b', currency: 'USD', input_price: '10', output_price: '10', price_unit: 'USD / 1M tokens', observed_at: '2026-10-01', source_id: 's' }];
    const data = dataset({ c1: { b1: 90 } }, routes, prices);
    const view = { ...structuredClone(DEFAULT_VIEW), filters: { ...DEFAULT_VIEW.filters, maxInputPricePerMillion: 5, maxOutputPricePerMillion: 20 } };
    expect(rowsForView(data, view, new Set())).toEqual([]);
    const updated = { ...data, market: {
      ...data.market,
      prices: [...data.market.prices, { ...prices[0], id: 'p-c', route_id: 'route-c', input_price: '4', output_price: '15' }],
      routes: [...data.market.routes, { id: 'route-c', model_id: 'model', provider: 'C' } as never],
    } } as AppData;
    expect(rowsForView(updated, view, new Set()).map(row => row.configuration.id)).toEqual(['c1']);
  });
  it('fails closed on an obsolete preset', () => {
    const data = dataset({ c1: { b1: 90 } });
    expect(rowsForView(data, { ...structuredClone(DEFAULT_VIEW), presetId: 'removed-preset' }, new Set())).toEqual([]);
  });
  it('compares multiple selected configurations from the same model', () => {
    const data = dataset({ c1: { b1: 90 }, c2: { b1: 85 } });
    const view = { ...structuredClone(DEFAULT_VIEW), compare: true, selectedConfigurationIds: ['c1', 'c2'] };
    expect(rowsForView(data, view, new Set()).map(row => row.configuration.id)).toEqual(['c1', 'c2']);
  });
  it('uses distinct total and active parameter claims', () => {
    const data = dataset({ c1: { b1: 90 } });
    data.catalog.metadata_claims.push(
      { id: 'total', entity_type: 'model', entity_id: 'model', field: 'total_parameters', value: 70, unit: 'B parameters', basis: 'disclosed', confidence_rationale: 'source', selected: true },
      { id: 'active', entity_type: 'model', entity_id: 'model', field: 'active_parameters', value: 8, unit: 'B parameters', basis: 'measured', confidence_rationale: 'source', selected: true },
    );
    const base = structuredClone(DEFAULT_VIEW);
    expect(rowsForView(data, { ...base, filters: { ...base.filters, minTotalParametersB: 60 } }, new Set())).toHaveLength(1);
    expect(rowsForView(data, { ...base, filters: { ...base.filters, minActiveParametersB: 10 } }, new Set())).toHaveLength(0);
  });
  it('excludes estimated parameter claims unless estimates are enabled', () => {
    const data = dataset({ c1: { b1: 90 } });
    data.catalog.metadata_claims.push({ id: 'estimate', entity_type: 'model', entity_id: 'model', field: 'total_parameters', value: 70, unit: 'B parameters', basis: 'third_party_estimate', confidence_rationale: 'estimate', selected: true });
    const base = structuredClone(DEFAULT_VIEW);
    expect(rowsForView(data, { ...base, filters: { ...base.filters, minTotalParametersB: 60, includeEstimates: false } }, new Set())).toHaveLength(0);
    expect(rowsForView(data, { ...base, filters: { ...base.filters, minTotalParametersB: 60, includeEstimates: true } }, new Set())).toHaveLength(1);
  });
  it('does not pass evidence filters when a configuration has no reviewed evidence', () => {
    const data = dataset({ c1: { b1: 90 } });
    const base = structuredClone(DEFAULT_VIEW);
    expect(rowsForView(data, { ...base, filters: { ...base.filters, independentOnly: true } }, new Set())).toHaveLength(0);
    expect(rowsForView(data, { ...base, filters: { ...base.filters, incompleteSetupAllowed: false } }, new Set())).toHaveLength(0);
  });
  it('reuses sparse dataset indexes across views and rebuilds them for a new AppData object', () => {
    const source = dataset({ c1: { b1: 90 } });
    let resultsReads = 0;
    let marketReads = 0;
    const data = new Proxy(source, { get(target, property, receiver) {
      if (property === 'results') resultsReads += 1;
      if (property === 'market') marketReads += 1;
      return Reflect.get(target, property, receiver);
    } });
    expect(rowsForView(data, structuredClone(DEFAULT_VIEW), new Set())).toHaveLength(1);
    const categoryView = { ...structuredClone(DEFAULT_VIEW), categoryId: 'math' };
    expect(rowsForView(data, categoryView, new Set())).toHaveLength(0);
    expect(resultsReads).toBe(1);
    expect(marketReads).toBe(1);

    const changed = dataset({ c1: { b1: 42 } });
    expect(rowsForView(changed, structuredClone(DEFAULT_VIEW), new Set())[0].observations.get('b1')?.value).toBe(42);
  });
  it('preserves disputed display cells when multiple series exist for one configuration and benchmark', () => {
    const data = dataset({ c1: { b1: 90 } });
    data.results.cells.push({ configuration_id: 'c1', benchmark_id: 'b1', series_id: 'other-series', state: 'selected', value: 91, unit: '%', observation_ids: ['second-observation'] });
    const cell = rowsForView(data, structuredClone(DEFAULT_VIEW), new Set())[0].observations.get('b1');
    expect(cell?.state).toBe('disputed');
    expect(cell?.value).toBeNull();
    expect(cell?.observation_ids).toEqual(['o-c1-b1', 'second-observation']);
  });
  it('preserves the existing equality join for usage with missing upstream IDs', () => {
    const data = dataset({ c1: { b1: 90 } }, [{ id: 'route', model_id: 'model', provider: 'Provider' }]);
    data.market.usage.push({ id: 'usage', platform: 'openrouter', upstream_route_id: undefined, total: 5 } as never);
    expect(rowsForView(data, structuredClone(DEFAULT_VIEW), new Set())[0].usage.map(item => item.id)).toEqual(['usage']);
  });
});
