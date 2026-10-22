import type { AppData, ObservationIndex } from './snapshots';
import type { Configuration, DisplayCell, Lab, ModelRelease, Observation, PriceObservation, ServingRoute, UsageObservation } from '../generated/dataset';
import type { ViewState } from '../state/viewState';
export type DisplayRow = { id: string; configuration: Configuration; model: ModelRelease; lab: Lab; labs: Lab[]; expanded: boolean; observations: Map<string, DisplayCell>; prices: PriceObservation[]; routes: ServingRoute[]; usage: UsageObservation[]; reviewedCount: number };
const list = <T,>(v: T[] | undefined): T[] => v ?? [];
const isComparable = (status?: string | null) => status === 'comparable';
const number = (x: unknown) => { const parsed = typeof x === 'number' ? x : typeof x === 'string' && x.trim() !== '' ? Number(x) : NaN; return Number.isFinite(parsed) ? parsed : null; };
type ParameterField = 'total_parameters' | 'active_parameters';
type SelectorIndexes = {
  presetsById: Map<string, AppData['catalog']['presets'][number]>;
  configurationsById: Map<string, Configuration>;
  configurationsByModel: Map<string, Configuration[]>;
  configurationOrder: Map<string, number>;
  modelsById: Map<string, ModelRelease>;
  labsById: Map<string, Lab>;
  seriesById: Map<string, AppData['details']['series'][number]>;
  categoryBenchmarkIds: Map<string, string[]>;
  knownConfigurationIds: Set<string>;
  cellsByConfiguration: Map<string, Map<string, DisplayCell>>;
  reviewedObservationsByConfiguration: Map<string, ObservationIndex[]>;
  reviewedCountByConfiguration: Map<string, number>;
  observationsById: Map<string, ObservationIndex>;
  observationSeriesStatus: Map<string, string | null | undefined>;
  parameterClaims: Map<string, AppData['catalog']['metadata_claims'][number]>;
  routesByModel: Map<string, ServingRoute[]>;
  pricesByRoute: Map<string, PriceObservation[]>;
  pricesByModel: Map<string, PriceObservation[]>;
  usageByModel: Map<string, UsageObservation[]>;
  priceOrder: Map<string, number>;
  usageOrder: Map<string, number>;
};
const indexesByData = new WeakMap<AppData, SelectorIndexes>();
const claimKey = (modelId: string, field: ParameterField) => `${modelId}\u0000${field}`;

/** Sort all-model benchmark columns by the number of distinct releases with numeric scores. */
export function orderColumnsByModelCoverage(data: AppData, ids: string[]): string[] {
  const indexes = selectorIndexes(data);
  const coverage = new Map(ids.map(id => [id, new Set<string>()]));
  for (const [configurationId, cells] of indexes.cellsByConfiguration) {
    const modelId = indexes.configurationsById.get(configurationId)?.model_id;
    if (!modelId) continue;
    for (const [benchmarkId, cell] of cells) {
      const models = coverage.get(benchmarkId);
      if (models && cell.state !== 'disputed' && cell.value !== null && Number.isFinite(Number(cell.value))) models.add(modelId);
    }
  }
  const originalOrder = new Map(ids.map((id, index) => [id, index]));
  return [...ids].sort((a, b) => (coverage.get(b)?.size ?? 0) - (coverage.get(a)?.size ?? 0) || (originalOrder.get(a) ?? 0) - (originalOrder.get(b) ?? 0));
}

function selectorIndexes(data: AppData): SelectorIndexes {
  const cached = indexesByData.get(data);
  if (cached) return cached;

  const { catalog, results, details, market } = data;
  const indexes: SelectorIndexes = {
    presetsById: new Map(list(catalog.presets).map(preset => [preset.id, preset])),
    configurationsById: new Map(list(catalog.configurations).map(configuration => [configuration.id, configuration])),
    configurationsByModel: new Map(),
    configurationOrder: new Map(),
    modelsById: new Map(list(catalog.models).map(model => [model.id, model])),
    labsById: new Map(list(catalog.labs).map(lab => [lab.id, lab])),
    seriesById: new Map(list(details.series).map(series => [series.id, series])),
    categoryBenchmarkIds: new Map(),
    knownConfigurationIds: new Set(),
    cellsByConfiguration: new Map(),
    reviewedObservationsByConfiguration: new Map(),
    reviewedCountByConfiguration: new Map(),
    observationsById: new Map(list(details.observations).map(record => [record.id, record])),
    observationSeriesStatus: new Map(),
    parameterClaims: new Map(),
    routesByModel: new Map(),
    pricesByRoute: new Map(),
    pricesByModel: new Map(),
    usageByModel: new Map(),
    priceOrder: new Map(),
    usageOrder: new Map(),
  };

  for (const [index, configuration] of list(catalog.configurations).entries()) {
    indexes.configurationOrder.set(configuration.id, index);
    const group = indexes.configurationsByModel.get(configuration.model_id);
    if (group) group.push(configuration); else indexes.configurationsByModel.set(configuration.model_id, [configuration]);
  }
  for (const benchmark of list(catalog.benchmarks)) {
    const group = indexes.categoryBenchmarkIds.get(benchmark.category);
    if (group) group.push(benchmark.id); else indexes.categoryBenchmarkIds.set(benchmark.category, [benchmark.id]);
  }
  for (const observation of list(results.observations)) {
    if (observation.review_state === 'reviewed') indexes.knownConfigurationIds.add(observation.configuration_id);
    if (observation.review_state === 'reviewed') indexes.reviewedCountByConfiguration.set(observation.configuration_id, (indexes.reviewedCountByConfiguration.get(observation.configuration_id) ?? 0) + 1);
  }
  for (const cell of list(results.cells)) {
    if (cell.value !== null) indexes.knownConfigurationIds.add(cell.configuration_id);
    let byBenchmark = indexes.cellsByConfiguration.get(cell.configuration_id);
    if (!byBenchmark) indexes.cellsByConfiguration.set(cell.configuration_id, byBenchmark = new Map());
    const found = byBenchmark.get(cell.benchmark_id);
    if (!found) byBenchmark.set(cell.benchmark_id, cell);
    else if (found.state !== 'disputed') byBenchmark.set(cell.benchmark_id, {
      ...found,
      state: 'disputed',
      value: null,
      observation_ids: [...found.observation_ids, ...cell.observation_ids],
    });
    else byBenchmark.set(cell.benchmark_id, {
      ...found,
      observation_ids: [...found.observation_ids, ...cell.observation_ids],
    });
  }
  const benchmarkOrder = new Map(list(catalog.benchmarks).map((benchmark, index) => [benchmark.id, index]));
  for (const byBenchmark of indexes.cellsByConfiguration.values()) {
    const sorted = [...byBenchmark].sort(([a], [b]) => (benchmarkOrder.get(a) ?? Number.MAX_SAFE_INTEGER) - (benchmarkOrder.get(b) ?? Number.MAX_SAFE_INTEGER));
    byBenchmark.clear();
    for (const [id, cell] of sorted) byBenchmark.set(id, cell);
  }
  for (const observation of list(details.observations)) {
    const status = indexes.seriesById.get(observation.series_id ?? '')?.comparability_status;
    indexes.observationSeriesStatus.set(observation.id, status);
    if (observation.review_state !== 'reviewed') continue;
    const group = indexes.reviewedObservationsByConfiguration.get(observation.configuration_id);
    if (group) group.push(observation); else indexes.reviewedObservationsByConfiguration.set(observation.configuration_id, [observation]);
  }
  for (const claim of list(catalog.metadata_claims)) {
    if (claim.entity_type !== 'model' || !claim.selected || !['total_parameters', 'active_parameters'].includes(claim.field)) continue;
    const key = claimKey(claim.entity_id, claim.field as ParameterField);
    const previous = indexes.parameterClaims.get(key);
    if (!previous || (claim.claimed_at ?? '').localeCompare(previous.claimed_at ?? '') >= 0) indexes.parameterClaims.set(key, claim);
  }
  const usageByUpstreamRoute = new Map<string | null | undefined, UsageObservation[]>();
  for (const [index, usage] of list(market.usage).entries()) {
    indexes.usageOrder.set(usage.id, index);
    const group = usageByUpstreamRoute.get(usage.upstream_route_id);
    if (group) group.push(usage); else usageByUpstreamRoute.set(usage.upstream_route_id, [usage]);
  }
  for (const [index, price] of list(market.prices).entries()) {
    indexes.priceOrder.set(price.id, index);
    if (price.route_id == null) continue;
    const group = indexes.pricesByRoute.get(price.route_id);
    if (group) group.push(price); else indexes.pricesByRoute.set(price.route_id, [price]);
  }
  for (const route of list(market.routes)) {
    const group = indexes.routesByModel.get(route.model_id);
    if (group) group.push(route); else indexes.routesByModel.set(route.model_id, [route]);
  }
  for (const [modelId, routes] of indexes.routesByModel) {
    const modelPrices: PriceObservation[] = [];
    const modelUsage = new Map<string, UsageObservation>();
    for (const route of routes) {
      modelPrices.push(...list(indexes.pricesByRoute.get(route.id)));
      for (const usage of [...list(usageByUpstreamRoute.get(route.upstream_model_id)), ...list(usageByUpstreamRoute.get(route.id))]) modelUsage.set(usage.id, usage);
    }
    indexes.pricesByModel.set(modelId, modelPrices.sort((a, b) => (indexes.priceOrder.get(a.id) ?? 0) - (indexes.priceOrder.get(b.id) ?? 0)));
    indexes.usageByModel.set(modelId, [...modelUsage.values()].sort((a, b) => (indexes.usageOrder.get(a.id) ?? 0) - (indexes.usageOrder.get(b.id) ?? 0)));
  }

  indexesByData.set(data, indexes);
  return indexes;
}

function parameterClaims(indexes: SelectorIndexes, modelId: string, field: ParameterField) {
  return indexes.parameterClaims.get(claimKey(modelId, field));
}
function parameterRange(indexes: SelectorIndexes, modelId: string, field: ParameterField, includeEstimates: boolean): [number, number] | null {
  const claim = parameterClaims(indexes, modelId, field); if (!claim || (!includeEstimates && !['disclosed', 'measured'].includes(claim.basis))) return null;
  const value = claim.value;
  if (typeof value === 'number') return [value, value];
  if (Array.isArray(value) && value.length === 2) { const lo = number(value[0]); const hi = number(value[1]); if (lo !== null && hi !== null) return [lo, hi]; }
  if (value && typeof value === 'object') { const lo = number((value as { min?: unknown }).min); const hi = number((value as { max?: unknown }).max); if (lo !== null && hi !== null) return [lo, hi]; }
  return null;
}
function completeSetup(o: ObservationIndex, seriesComparability?: string | null): boolean {
  const setup = o.setup ?? {};
  const required = ['tools', 'harness', 'reasoning', 'pass_k', 'task_count', 'prompt_protocol', 'grader', 'fallback_models', 'resource_budget'];
  const known = (key: string) => Object.entries(setup).some(([k, value]) => (k === key || (key === 'pass_k' && ['sampling', 'passk'].includes(k)) || (key === 'resource_budget' && ['budget', 'limits'].includes(k))) && value !== null && value !== undefined && value !== 'unknown' && value !== 'not reported' && value !== 'not stated');
  const seriesDeclared = seriesComparability === 'comparable';
  return required.filter(known).length >= 4 && seriesDeclared && Object.values(setup).every(value => value !== null && value !== undefined && value !== 'unknown' && value !== 'not reported' && value !== 'not stated');
}
export type OutsideViewBenchmarkMatch = { benchmarkId: string; name: string; presetIds: string[] };
export type OutsideViewSearch = {
  totalCount: number;
  matches: OutsideViewBenchmarkMatch[];
  suggestedPreset: { id: string; name: string; matchedBenchmarkIds: string[] } | null;
};

/** Benchmarks matching the query across the whole catalog but hidden by the current view. */
export function benchmarkMatchesOutsideView(data: AppData, view: ViewState, limit = 5): OutsideViewSearch {
  const empty: OutsideViewSearch = { totalCount: 0, matches: [], suggestedPreset: null };
  const query = view.search.trim().toLowerCase();
  if (!query) return empty;
  const preset = data.catalog.presets.find(item => item.id === view.presetId);
  const visibleIds = new Set(view.visibleColumnIds.length ? view.visibleColumnIds : list(preset?.benchmark_ids));
  const matches = list(data.catalog.benchmarks).filter(item =>
    !visibleIds.has(item.id)
    && (view.categoryId === null || item.category === view.categoryId)
    && (!view.filters.saturationStates.length || data.catalog.saturation.some(state => state.benchmark_id === item.id && view.filters.saturationStates.includes(state.state)))
    && `${item.name} ${item.version ?? ''} ${item.metric_name} ${item.subset ?? ''}`.toLowerCase().includes(query));
  if (!matches.length) return empty;
  const limited = matches.slice(0, Math.max(0, limit));
  const withPresets: OutsideViewBenchmarkMatch[] = limited.map(item => ({
    benchmarkId: item.id,
    name: item.name,
    presetIds: list(data.catalog.presets).filter(candidate => candidate.id !== view.presetId && list(candidate.benchmark_ids).includes(item.id)).map(candidate => candidate.id),
  }));
  const matchedIds = new Set(matches.map(item => item.id));
  const suggested = list(data.catalog.presets)
    .filter(candidate => candidate.id !== view.presetId)
    .map(candidate => ({ candidate, matched: list(candidate.benchmark_ids).filter(id => matchedIds.has(id)) }))
    .filter(entry => entry.matched.length > 0)
    .sort((a, b) => b.matched.length - a.matched.length || list(a.candidate.benchmark_ids).length - list(b.candidate.benchmark_ids).length || a.candidate.name.localeCompare(b.candidate.name))[0];
  return {
    totalCount: matches.length,
    matches: withPresets,
    suggestedPreset: suggested ? { id: suggested.candidate.id, name: suggested.candidate.name, matchedBenchmarkIds: suggested.matched } : null,
  };
}

/** Search benchmark metadata within the current view without changing saved column selections. */
export function benchmarkSearchForView(data: AppData, view: ViewState) {
  const preset = data.catalog.presets.find(item => item.id === view.presetId);
  const ids = view.visibleColumnIds.length ? view.visibleColumnIds : list(preset?.benchmark_ids);
  const byId = new Map(data.catalog.benchmarks.map(item => [item.id, item]));
  const benchmarks = ids.map(id => byId.get(id)).filter((item): item is AppData['catalog']['benchmarks'][number] => !!item
    && (view.categoryId === null || item.category === view.categoryId)
    && (!view.filters.saturationStates.length || data.catalog.saturation.some(state => state.benchmark_id === item.id && view.filters.saturationStates.includes(state.state))));
  const query = view.search.trim().toLowerCase();
  const matches = query ? benchmarks.filter(item => `${item.name} ${item.version ?? ''} ${item.metric_name} ${item.subset ?? ''}`.toLowerCase().includes(query)) : [];
  return { benchmarks: matches.length ? matches : benchmarks, matchesBenchmark: matches.length > 0 };
}

function applyFilters(indexes: SelectorIndexes, row: DisplayRow, view: ViewState, matchesBenchmark: boolean): boolean {
  const f = view.filters;
  if (view.compare && !view.selectedConfigurationIds.includes(row.configuration.id)) return false;
  if (view.search.trim() && !matchesBenchmark && !`${row.model.name} ${row.model.version ?? ''} ${row.labs.map(lab => lab.name).join(' ')} ${row.configuration.reasoning_label ?? ''}`.toLowerCase().includes(view.search.trim().toLowerCase())) return false;
  if (f.labIds.length && !f.labIds.some(id => row.labs.some(lab => lab.id === id))) return false;
  if (f.countryCodes.length && !f.countryCodes.some(code => row.labs.some(lab => list(lab.hq_country_codes).includes(code)))) return false;
  if (f.releaseYears.length && !f.releaseYears.includes(Number(row.model.release_date?.slice(0, 4)))) return false;
  if (f.accessStates.length && !f.accessStates.includes(row.model.access_state ?? 'unknown')) return false;
  if (f.weightsAvailable !== null && (row.model.weights_state === 'available') !== f.weightsAvailable) return false;
  if (f.modalities.length && !f.modalities.some(x => list(row.model.modalities).includes(x))) return false;
  if (f.architectureIds.length) return false; // The current canonical model contract has no architecture field.
  if (f.reasoningModes.length && !f.reasoningModes.includes(row.configuration.reasoning_label ?? row.configuration.mode ?? 'unknown')) return false;
  if (f.benchmarkIds.length && !f.benchmarkIds.some(id => { const cell = row.observations.get(id); return cell && cell.state !== 'disputed' && cell.value !== null; })) return false;
  if (view.categoryId && !list(indexes.categoryBenchmarkIds.get(view.categoryId)).some(id => row.observations.get(id)?.value != null && row.observations.get(id)?.state !== 'disputed')) return false;
  for (const condition of f.scoreConditions) { const cell = row.observations.get(condition.benchmarkId); if (!cell || cell.value === null || cell.state === 'disputed') return false; const v = cell.value; const c = condition.value; if (!(condition.operator === '>=' ? v >= c : condition.operator === '<=' ? v <= c : condition.operator === '>' ? v > c : condition.operator === '<' ? v < c : v === c)) return false; }
  if (f.comparableOnly) {
    const comparable = [...row.observations.values()].some(cell => cell.state !== 'disputed' && cell.observation_ids.some(id => isComparable(indexes.observationSeriesStatus.get(id))));
    if (!comparable) return false;
  }
  const selectedObs = list(indexes.reviewedObservationsByConfiguration.get(row.configuration.id));
  if ((!f.providerReportedAllowed || f.independentOnly || !f.incompleteSetupAllowed) && selectedObs.length === 0) return false;
  if (!f.providerReportedAllowed && selectedObs.some(o => o.reporting_relationship === 'self_report' || o.reporting_relationship === 'quoted_result')) return false;
  if (f.independentOnly && selectedObs.some(o => !['evaluator_measurement', 'third_party_reproduction'].includes(o.reporting_relationship))) return false;
  if (!f.incompleteSetupAllowed && selectedObs.some(o => !completeSetup(o, indexes.observationSeriesStatus.get(o.id)))) return false;
  const sizeConditions = [f.minTotalParametersB, f.maxTotalParametersB, f.minActiveParametersB, f.maxActiveParametersB].some(x => x !== null);
  if (sizeConditions) {
    const total = parameterRange(indexes, row.model.id, 'total_parameters', f.includeEstimates); const active = parameterRange(indexes, row.model.id, 'active_parameters', f.includeEstimates);
    if (f.maxTotalParametersB !== null && (!total || total[1] > f.maxTotalParametersB)) return false;
    if (f.minTotalParametersB !== null && (!total || total[0] < f.minTotalParametersB)) return false;
    if (f.maxActiveParametersB !== null && (!active || active[1] > f.maxActiveParametersB)) return false;
    if (f.minActiveParametersB !== null && (!active || active[0] < f.minActiveParametersB)) return false;
  }
  if (f.maxInputPricePerMillion !== null || f.maxOutputPricePerMillion !== null || f.routeIds.length) {
    const candidates = row.prices.filter(p => (!f.routeIds.length || f.routeIds.includes(p.route_id ?? '')) && p.available !== false && (f.includeFreeRoutes || !(number(p.input_price) === 0 && number(p.output_price) === 0)));
    if (!candidates.some(p => (f.maxInputPricePerMillion === null || number(p.input_price) !== null && number(p.input_price)! <= f.maxInputPricePerMillion) && (f.maxOutputPricePerMillion === null || number(p.output_price) !== null && number(p.output_price)! <= f.maxOutputPricePerMillion))) return false;
  }
  if (!f.includeFreeRoutes && row.prices.length && !row.prices.some(p => !(number(p.input_price) === 0 && number(p.output_price) === 0))) return false;
  if (f.openRouterUsageAvailable !== null) {
    const available = row.usage.some(u => u.platform.toLowerCase() === 'openrouter' && u.total !== null && u.total !== undefined);
    if (available !== f.openRouterUsageAvailable) return false;
  }
  return true;
}
export function rowsForView(data: AppData, view: ViewState, expandedIds: Set<string>): DisplayRow[] {
  const indexes = selectorIndexes(data);
  const preset = indexes.presetsById.get(view.presetId);
  if (!preset) return [];
  const presetConfigIds = new Set(list(preset.model_configuration_ids));
  const allModelPreset = presetIncludesAllModels(data, preset.id);
  const modelIds = new Set([...presetConfigIds].map(id => indexes.configurationsById.get(id)?.model_id).filter((x): x is string => !!x));
  if (!presetConfigIds.size || !modelIds.size) return [];
  let configurations = [...modelIds].flatMap(modelId => list(indexes.configurationsByModel.get(modelId)))
    .sort((a, b) => (indexes.configurationOrder.get(a.id) ?? 0) - (indexes.configurationOrder.get(b.id) ?? 0));
  if (!view.includeUnbenchmarked) configurations = configurations.filter(c => indexes.knownConfigurationIds.has(c.id));
  const configurationsByModel = new Map<string, Configuration[]>();
  for (const configuration of configurations) {
    const group = configurationsByModel.get(configuration.model_id);
    if (group) group.push(configuration); else configurationsByModel.set(configuration.model_id, [configuration]);
  }
  const benchmarkSearch = benchmarkSearchForView(data, view);
  const candidates: DisplayRow[] = configurations.map(configuration => {
    const model = indexes.modelsById.get(configuration.model_id)!; const labs = model.lab_ids.map(id => indexes.labsById.get(id)).filter((x): x is Lab => !!x); const lab = labs[0]!;
    const routes = list(indexes.routesByModel.get(model.id));
    return { id: configuration.id, configuration, model, lab, labs, expanded: expandedIds.has(model.id), observations: indexes.cellsByConfiguration.get(configuration.id) ?? new Map(), prices: list(indexes.pricesByModel.get(model.id)), routes, usage: list(indexes.usageByModel.get(model.id)), reviewedCount: indexes.reviewedCountByConfiguration.get(configuration.id) ?? 0 };
  }).filter(row => !!row.model && !!row.lab && applyFilters(indexes, row, view, benchmarkSearch.matchesBenchmark));
  const byModel = new Map<string, DisplayRow[]>();
  for (const row of candidates) { const group = byModel.get(row.model.id); if (group) group.push(row); else byModel.set(row.model.id, [row]); }
  const output: DisplayRow[] = [];
  if (view.compare) return candidates.filter(row => view.selectedConfigurationIds.includes(row.configuration.id));
  const selectedBenchmarks = benchmarkSearch.benchmarks.map(benchmark => benchmark.id);
  for (const [modelId, matched] of byModel) {
    const allConfigIds = new Set(list(configurationsByModel.get(modelId)).map(c => c.id));
    const matchedOptions = matched.filter(row => allConfigIds.has(row.configuration.id));
    const primary = allModelPreset
      ? [...matchedOptions].sort((a, b) => {
        const coverage = (row: DisplayRow) => selectedBenchmarks.reduce((count, id) => { const cell = row.observations.get(id); return count + Number(!!cell && cell.state !== 'disputed' && cell.value !== null && Number.isFinite(Number(cell.value))); }, 0);
        return coverage(b) - coverage(a) || (indexes.configurationOrder.get(a.configuration.id) ?? 0) - (indexes.configurationOrder.get(b.configuration.id) ?? 0);
      })[0]
      : matchedOptions.find(row => presetConfigIds.has(row.configuration.id)) ?? [...matchedOptions].sort((a,b) => b.reviewedCount - a.reviewedCount || (a.configuration.reasoning_label ?? '').localeCompare(b.configuration.reasoning_label ?? ''))[0];
    if (!primary) continue;
    output.push(primary);
    if (expandedIds.has(modelId)) output.push(...matchedOptions.filter(row => row.id !== primary.id));
  }
  return output;
}
/** Detect broad presets by membership rather than a date-specific preset ID. */
export function presetIncludesAllModels(data: AppData, presetId: string): boolean {
  const indexes = selectorIndexes(data);
  const preset = indexes.presetsById.get(presetId);
  const included = new Set(list(preset?.model_configuration_ids).map(id => indexes.configurationsById.get(id)?.model_id));
  return data.catalog.models.length > 0 && data.catalog.models.every(model => included.has(model.id));
}
export function setupComplete(o: Observation): boolean { return completeSetup(o); }
export function numeric(value: number | string | null | undefined): number | null { if (value === null || value === undefined) return null; const n = Number(value); return Number.isFinite(n) ? n : null; }
export function valueForCell(row: DisplayRow, benchmarkId: string): DisplayCell | undefined { return row.observations.get(benchmarkId); }
/** A disputed cell still has reported evidence and keeps its row visible. */
export function hasResultOnBenchmarks(row: DisplayRow, benchmarkIds: readonly string[]): boolean {
  return benchmarkIds.some(id => { const cell = row.observations.get(id); return !!cell && (cell.state === 'disputed' || cell.value !== null && Number.isFinite(Number(cell.value))); });
}
/** The single unambiguous reported value on one exact configuration. Disputed, multi-report, and missing cells never qualify. */
export function singleReportedValue(row: DisplayRow, benchmarkId: string): number | null {
  const cell = row.observations.get(benchmarkId);
  if (!cell || cell.state === 'disputed' || cell.observation_ids.length !== 1) return null;
  return numeric(cell.value);
}
/** Whether this cell is hidden by the selected saturation filter (shown as missing). Mirrors the matrix score button. */
export function isSaturationExcluded(data: AppData, benchmarkId: string, cell: DisplayCell, saturationStates: string[]): boolean {
  return saturationStates.length > 0 && !cell.observation_ids.some(id => {
    const observation = data.details.observations.find(o => o.id === id);
    return data.catalog.saturation.some(a => a.benchmark_id === benchmarkId && a.series_id === (observation?.series_id ?? null) && saturationStates.includes(a.state));
  });
}
/** The number a portrait card shows and ranks by: the single reported value, else the midpoint of a multi-report range or of other-configuration previews, else null. Only portrait cards rank by this preview value so the displayed order matches; matrix and table sorting stay on the exact configuration. */
export function previewScore(data: AppData, row: DisplayRow, benchmarkId: string, saturationStates: string[]): number | null {
  // Midpoints mirror scoreRangeMidpoint in heatmap.ts (kept separate to avoid a module cycle); inputs below are pre-sorted.
  const midpoint = (values: number[]) => values.length ? (values[0]! + values[values.length - 1]!) / 2 : NaN;
  const cell = row.observations.get(benchmarkId);
  // Alternate setups preview only when this configuration has no cell at all, mirroring the matrix score button.
  if (!cell) {
    // Midpoints mirror scoreRangeMidpoint in heatmap.ts (kept separate to avoid a module cycle); inputs below are pre-sorted.
    const mid = midpoint(otherConfigurationScores(data, row, benchmarkId));
    return Number.isFinite(mid) ? mid : null;
  }
  if (cell.state === 'disputed' || isSaturationExcluded(data, benchmarkId, cell, saturationStates)) return null;
  const direct = singleReportedValue(row, benchmarkId);
  if (direct !== null) return direct;
  if (cell.observation_ids.length > 1) {
    const mid = midpoint(reportedCellScores(data, cell, data.catalog.benchmarks.find(b => b.id === benchmarkId)?.unit ?? cell.unit ?? ''));
    return Number.isFinite(mid) ? mid : null;
  }
  return null;
}
/** Compact configuration label shared by the desktop badge and portrait cards. */
export function shortReasoning(row: DisplayRow): string {
  const label = row.configuration.reasoning_label;
  return label && /^(none|off|on|low|medium|high|xhigh|max|minimal|default|auto)$/i.test(label) ? label : row.configuration.mode === 'not_applicable' ? 'n/a' : row.configuration.mode ?? 'unknown';
}
export function numericScoreCount(row: DisplayRow, benchmarkIds?: readonly string[]): number {
  const ids = benchmarkIds ? new Set(benchmarkIds) : null;
  let count = 0;
  for (const [id, cell] of row.observations) if ((!ids || ids.has(id)) && cell.state !== 'disputed' && cell.value !== null && Number.isFinite(Number(cell.value))) count++;
  return count;
}
export function categoryLabels(benchmarks: AppData['catalog']['benchmarks']): string[] { return [...new Set(benchmarks.map(b => b.category))]; }

/** Exact benchmark only; alternative setups remain explicitly labeled. */
export function otherConfigurationResults(data: AppData, row: DisplayRow, benchmarkId: string): string[] {
  const index = selectorIndexes(data);
  return list(index.configurationsByModel.get(row.model.id)).filter(configuration => {
    if (configuration.id === row.configuration.id) return false;
    return !!index.cellsByConfiguration.get(configuration.id)?.get(benchmarkId)?.observation_ids.length;
  }).map(configuration => configuration.id);
}

/** Numeric preview only; matrix and table sorting and winner highlighting stay on the exact configuration. Portrait cards are the deliberate exception: they rank by previewScore so the displayed order matches what is shown. */
export function otherConfigurationScores(data: AppData, row: DisplayRow, benchmarkId: string): number[] {
  const ids = otherConfigurationResults(data, row, benchmarkId);
  const index = selectorIndexes(data);
  const unit = data.catalog.benchmarks.find(benchmark => benchmark.id === benchmarkId)?.unit;
  return [...new Set(ids.flatMap(id => {
    const cell = index.cellsByConfiguration.get(id)?.get(benchmarkId);
    return cell ? [cell] : [];
  }).filter(cell => cell.unit === unit && cell.state !== 'disputed'
    && cell.observation_ids.length === 1 && cell.value !== null && Number.isFinite(cell.value))
    .map(cell => cell.value!))].sort((a, b) => a - b);
}

/** Summarize only the published reports attached to this exact cell, in its benchmark unit. */
export function reportedCellScores(data: AppData, cell: DisplayCell, unit: string): number[] {
  const index = selectorIndexes(data);
  const reports = cell.observation_ids.map(id => index.observationsById.get(id));
  // An incomplete or mixed-unit set cannot truthfully be presented as a complete range.
  if (!reports.length || reports.some(record => !record || record.configuration_id !== cell.configuration_id
    || record.benchmark_id !== cell.benchmark_id || record.unit !== unit || !Number.isFinite(record.value)
    || !['reviewed', 'disputed'].includes(record.review_state ?? ''))) return [];
  return [...new Set(reports.map(record => record!.value))].sort((a, b) => a - b);
}
