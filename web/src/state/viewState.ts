/** Versioned, allowlisted client view state shared by URL and browser storage. */
export const VIEW_VERSION = 1 as const;
export type SortDirection = 'asc' | 'desc';
export type ScoreCondition = { benchmarkId: string; operator: '>=' | '<=' | '>' | '<' | '='; value: number };
export type ViewState = {
  version: typeof VIEW_VERSION;
  presetId: string;
  categoryId: string | null;
  search: string;
  visibleColumnIds: string[];
  sort: { id: string; direction: SortDirection } | null;
  selectedConfigurationIds: string[];
  compare: boolean;
  includeUnbenchmarked: boolean;
  hideEmptyPageRows: boolean;
  orientation: 'models-rows' | 'benchmarks-rows';
  portraitBenchmarkId: string | null;
  filters: {
    labIds: string[]; countryCodes: string[]; releaseYears: number[];
    accessStates: string[]; weightsAvailable: boolean | null; modalities: string[];
    architectureIds: string[]; reasoningModes: string[];
    minTotalParametersB: number | null; maxTotalParametersB: number | null;
    minActiveParametersB: number | null; maxActiveParametersB: number | null;
    includeEstimates: boolean;
    benchmarkIds: string[]; saturationStates: string[]; scoreConditions: ScoreCondition[];
    comparableOnly: boolean; providerReportedAllowed: boolean; independentOnly: boolean;
    incompleteSetupAllowed: boolean;
    maxInputPricePerMillion: number | null; maxOutputPricePerMillion: number | null;
    routeIds: string[]; includeFreeRoutes: boolean; includeStalePrices: boolean; openRouterUsageAvailable: boolean | null;
  };
};
export type SavedEnvelope = { format_version: 1; saved_at: string; view: ViewState };

export const DEFAULT_VIEW: ViewState = {
  version: 1, presetId: 'frontier_oct2026', categoryId: null, search: '',
  visibleColumnIds: [], sort: null, selectedConfigurationIds: [], compare: false, includeUnbenchmarked: false, hideEmptyPageRows: false, orientation: 'benchmarks-rows', portraitBenchmarkId: null,
  filters: {
    labIds: [], countryCodes: [], releaseYears: [], accessStates: [], weightsAvailable: null,
    modalities: [], architectureIds: [], reasoningModes: [], minTotalParametersB: null,
    maxTotalParametersB: null, minActiveParametersB: null, maxActiveParametersB: null,
    includeEstimates: false, benchmarkIds: [], saturationStates: [], scoreConditions: [],
    comparableOnly: false, providerReportedAllowed: true, independentOnly: false,
    incompleteSetupAllowed: true, maxInputPricePerMillion: null, maxOutputPricePerMillion: null,
    routeIds: [], includeFreeRoutes: true, includeStalePrices: false, openRouterUsageAvailable: null,
  },
};

export type ValidationContext = { knownPresetIds?: ReadonlySet<string>; knownCategoryIds?: ReadonlySet<string>; knownColumnIds?: ReadonlySet<string>; knownConfigurationIds?: ReadonlySet<string>; knownBenchmarkIds?: ReadonlySet<string> };
export type ParseResult = { ok: true; value: ViewState; unresolved: string[] } | { ok: false; reason: string };
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const str = (v: unknown): v is string => typeof v === 'string' && v.length > 0 && v.length <= 300;
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.length <= 1024 && v.every(str);
const nullableNumber = (v: unknown): v is number | null => v === null || (typeof v === 'number' && Number.isFinite(v));
const bool = (v: unknown): v is boolean => typeof v === 'boolean';

/** Strict shape validation; unknown restrictive IDs are retained and reported, never discarded. */
export function parseViewState(raw: unknown, ctx: ValidationContext = {}): ParseResult {
  if (!object(raw) || raw.version !== VIEW_VERSION) return { ok: false, reason: 'Unsupported or invalid view version' };
  if (raw.orientation !== undefined && raw.orientation !== 'models-rows' && raw.orientation !== 'benchmarks-rows') return { ok: false, reason: 'Invalid orientation' };
  if (raw.portraitBenchmarkId !== undefined && raw.portraitBenchmarkId !== null && !str(raw.portraitBenchmarkId)) return { ok: false, reason: 'Invalid portrait benchmark' };
  const f = raw.filters;
  if (!object(f) || !str(raw.presetId) || !(raw.categoryId === null || str(raw.categoryId)) || typeof raw.search !== 'string' || raw.search.length > 500 || !strings(raw.visibleColumnIds) || !strings(raw.selectedConfigurationIds) || !bool(raw.compare) || !bool(raw.includeUnbenchmarked) || (raw.hideEmptyPageRows !== undefined && !bool(raw.hideEmptyPageRows))) return { ok: false, reason: 'Invalid view fields' };
  const stringKeys = ['labIds','countryCodes','accessStates','modalities','architectureIds','reasoningModes','benchmarkIds','saturationStates','routeIds'] as const;
  for (const k of stringKeys) if (!strings(f[k])) return { ok: false, reason: `Invalid ${k}` };
  if (!Array.isArray(f.releaseYears) || f.releaseYears.length > 300 || !f.releaseYears.every(x => Number.isInteger(x) && x >= 1900 && x <= 2200)) return { ok: false, reason: 'Invalid release years' };
  const numberKeys = ['minTotalParametersB','maxTotalParametersB','minActiveParametersB','maxActiveParametersB','maxInputPricePerMillion','maxOutputPricePerMillion'] as const;
  for (const k of numberKeys) if (!nullableNumber(f[k]) || (f[k] !== null && f[k] < 0)) return { ok: false, reason: `Invalid ${k}` };
  const boolKeys = ['includeEstimates','comparableOnly','providerReportedAllowed','independentOnly','incompleteSetupAllowed','includeFreeRoutes'] as const;
  for (const k of boolKeys) if (!bool(f[k])) return { ok: false, reason: `Invalid ${k}` };
  if (f.includeStalePrices !== undefined && !bool(f.includeStalePrices)) return { ok: false, reason: 'Invalid includeStalePrices' };
  if (f.weightsAvailable !== null && !bool(f.weightsAvailable)) return { ok: false, reason: 'Invalid weightsAvailable' };
  if (f.openRouterUsageAvailable !== null && !bool(f.openRouterUsageAvailable)) return { ok: false, reason: 'Invalid openRouterUsageAvailable' };
  if (!Array.isArray(f.scoreConditions) || f.scoreConditions.length > 100 || !f.scoreConditions.every(x => object(x) && str(x.benchmarkId) && ['>=','<=','>','<','='].includes(String(x.operator)) && typeof x.value === 'number' && Number.isFinite(x.value))) return { ok: false, reason: 'Invalid score conditions' };
  const sort = raw.sort;
  if (!(sort === null || (object(sort) && str(sort.id) && (sort.direction === 'asc' || sort.direction === 'desc')))) return { ok: false, reason: 'Invalid sort' };
  if (ctx.knownPresetIds && !ctx.knownPresetIds.has(raw.presetId)) return { ok: false, reason: `Unknown preset: ${raw.presetId}` };
  const cleanFilters: ViewState['filters'] = {
    labIds: [...f.labIds as string[]], countryCodes: [...f.countryCodes as string[]], releaseYears: [...f.releaseYears as number[]], accessStates: [...f.accessStates as string[]], weightsAvailable: f.weightsAvailable as boolean | null,
    modalities: [...f.modalities as string[]], architectureIds: [...f.architectureIds as string[]], reasoningModes: [...f.reasoningModes as string[]],
    minTotalParametersB: f.minTotalParametersB as number | null, maxTotalParametersB: f.maxTotalParametersB as number | null, minActiveParametersB: f.minActiveParametersB as number | null, maxActiveParametersB: f.maxActiveParametersB as number | null, includeEstimates: f.includeEstimates as boolean,
    benchmarkIds: [...f.benchmarkIds as string[]], saturationStates: [...f.saturationStates as string[]], scoreConditions: (f.scoreConditions as ScoreCondition[]).map(x => ({ benchmarkId: x.benchmarkId, operator: x.operator, value: x.value })),
    comparableOnly: f.comparableOnly as boolean, providerReportedAllowed: f.providerReportedAllowed as boolean, independentOnly: f.independentOnly as boolean, incompleteSetupAllowed: f.incompleteSetupAllowed as boolean,
    maxInputPricePerMillion: f.maxInputPricePerMillion as number | null, maxOutputPricePerMillion: f.maxOutputPricePerMillion as number | null, routeIds: [...f.routeIds as string[]], includeFreeRoutes: f.includeFreeRoutes as boolean, includeStalePrices: f.includeStalePrices === true, openRouterUsageAvailable: f.openRouterUsageAvailable as boolean | null,
  };
  const value: ViewState = { version: VIEW_VERSION, presetId: raw.presetId, categoryId: raw.categoryId as string | null, search: raw.search, visibleColumnIds: [...raw.visibleColumnIds as string[]], sort: sort === null ? null : { id: (sort as {id:string}).id, direction: (sort as {direction:SortDirection}).direction }, selectedConfigurationIds: [...raw.selectedConfigurationIds as string[]], compare: raw.compare, includeUnbenchmarked: raw.includeUnbenchmarked, hideEmptyPageRows: raw.hideEmptyPageRows === true, orientation: raw.orientation === 'models-rows' ? 'models-rows' : 'benchmarks-rows', portraitBenchmarkId: typeof raw.portraitBenchmarkId === 'string' ? raw.portraitBenchmarkId : null, filters: cleanFilters };
  const unresolved: string[] = [];
  const checkIds = (name: string, ids: string[], known?: ReadonlySet<string>) => { if (known) for (const id of ids) if (!known.has(id)) unresolved.push(`${name}: ${id}`); };
  if (value.portraitBenchmarkId) checkIds('portrait benchmark', [value.portraitBenchmarkId], ctx.knownBenchmarkIds);
  if (value.categoryId) checkIds('category', [value.categoryId], ctx.knownCategoryIds);
  checkIds('column', value.visibleColumnIds, ctx.knownColumnIds);
  checkIds('configuration', value.selectedConfigurationIds, ctx.knownConfigurationIds);
  checkIds('benchmark', [...cleanFilters.benchmarkIds, ...cleanFilters.scoreConditions.map(x => x.benchmarkId)], ctx.knownBenchmarkIds);
  return { ok: true, value, unresolved };
}
// b1 identifies the UTF-8 base64url transport; the JSON has its own schema version.
const URL_PREFIX = 'b1.';
const MAX_STATE_BYTES = 32768;
export function encodeViewState(view: ViewState): string {
  const bytes = new TextEncoder().encode(JSON.stringify(view));
  if (bytes.length > MAX_STATE_BYTES) throw new Error('Shared view is too large');
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return URL_PREFIX + btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
export function decodeViewState(encoded: string, ctx?: ValidationContext): ParseResult {
  try {
    let json: string;
    if (encoded.startsWith(URL_PREFIX)) {
      if (encoded.length > URL_PREFIX.length + Math.ceil(MAX_STATE_BYTES * 4 / 3)) return { ok: false, reason: 'Shared view is too large' };
      const payload = encoded.slice(URL_PREFIX.length);
      if (!/^[A-Za-z0-9_-]+$/.test(payload) || payload.length % 4 === 1) throw new Error('Invalid base64url');
      const binary = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      if (binary.length > MAX_STATE_BYTES) return { ok: false, reason: 'Shared view is too large' };
      json = new TextDecoder('utf-8', { fatal: true }).decode(Uint8Array.from(binary, c => c.charCodeAt(0)));
    } else {
      // Retain links created before base64url sharing was introduced.
      if (encoded.length > MAX_STATE_BYTES || new TextEncoder().encode(encoded).length > MAX_STATE_BYTES) return { ok: false, reason: 'Shared view is too large' };
      json = encoded;
    }
    return parseViewState(JSON.parse(json), ctx);
  } catch { return { ok: false, reason: 'Malformed shared view' }; }
}
export function storageKey(baseUrl: string): string { const path = new URL(baseUrl, location.origin).pathname.replace(/\/+$/, '') || '/'; return `allthebenches:${path}/:saved-view`; }
export function readSavedView(storage: Storage, key: string, ctx?: ValidationContext): ParseResult | { ok: false; reason: string } {
  try { const raw = storage.getItem(key); if (!raw) return { ok: false, reason: 'No saved view' }; const envelope: unknown = JSON.parse(raw); if (!object(envelope) || envelope.format_version !== 1 || typeof envelope.saved_at !== 'string') return { ok: false, reason: 'Invalid saved view record' }; return parseViewState(envelope.view, ctx); } catch { return { ok: false, reason: 'Saved view could not be read' }; }
}
export function writeSavedView(storage: Storage, key: string, view: ViewState, now = new Date()): boolean {
  try { const parsed = parseViewState(view); if (!parsed.ok) return false; const envelope: SavedEnvelope = { format_version: 1, saved_at: now.toISOString(), view: parsed.value }; storage.setItem(key, JSON.stringify(envelope)); return true; } catch { return false; }
}
export function forgetSavedView(storage: Storage, key: string): boolean { try { storage.removeItem(key); return true; } catch { return false; } }
