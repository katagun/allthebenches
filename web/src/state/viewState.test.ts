import { describe, expect, it } from 'vitest';
import { DEFAULT_VIEW, decodeViewState, encodeViewState, forgetSavedView, parseViewState, readSavedView, storageKey, writeSavedView } from './viewState';

describe('versioned view state', () => {
  it('shares the selected portrait benchmark and accepts older links', () => {
    const view = { ...structuredClone(DEFAULT_VIEW), portraitBenchmarkId: 'arc_agi_2_semi_private' };
    expect(decodeViewState(encodeViewState(view))).toMatchObject({ ok: true, value: { portraitBenchmarkId: view.portraitBenchmarkId } });
    expect(parseViewState({ ...view, portraitBenchmarkId: undefined })).toMatchObject({ ok: true, value: { portraitBenchmarkId: null } });
    expect(parseViewState({ ...view, portraitBenchmarkId: 1 }).ok).toBe(false);
    expect(parseViewState(view, { knownBenchmarkIds: new Set() })).toMatchObject({ ok: true, unresolved: ['portrait benchmark: arc_agi_2_semi_private'] });
  });
  it('persists orientation and defaults older links to benchmark rows', () => {
    const view = { ...structuredClone(DEFAULT_VIEW), orientation: 'benchmarks-rows' as const };
    expect(decodeViewState(encodeViewState(view))).toMatchObject({ ok: true, value: { orientation: 'benchmarks-rows' } });
    expect(parseViewState({ ...view, orientation: undefined })).toMatchObject({ ok: true, value: { orientation: 'benchmarks-rows' } });
    expect(parseViewState({ ...view, orientation: 'invalid' }).ok).toBe(false);
  });
  it('round trips a complete view without changing stable IDs', () => {
    const view = { ...structuredClone(DEFAULT_VIEW), selectedConfigurationIds: ['cfg-a'], visibleColumnIds: ['bench-a'], filters: { ...DEFAULT_VIEW.filters, scoreConditions: [{ benchmarkId: 'bench-a', operator: '>=' as const, value: 0 }], includeEstimates: true } };
    const decoded = decodeViewState(encodeViewState(view));
    expect(decoded.ok && decoded.value).toEqual(view);
  });
  it('uses URL-safe UTF-8 base64 and retains legacy JSON links', () => {
    const view = { ...structuredClone(DEFAULT_VIEW), search: '日本語 café 🧠 + / &' };
    const encoded = encodeViewState(view);
    expect(encoded).toMatch(/^b1\.[A-Za-z0-9_-]+$/);
    expect(decodeViewState(encoded)).toMatchObject({ ok: true, value: view });
    expect(decodeViewState(JSON.stringify(view))).toMatchObject({ ok: true, value: view });
  });
  it('rejects invalid encodings and bounds decoding work', () => {
    for (const input of ['b1.', 'b1.A', 'b1.%%%%', 'b1._w', 'b2.e30', 'b1.' + 'A'.repeat(44000), ' '.repeat(32769)]) {
      expect(decodeViewState(input).ok).toBe(false);
    }
    expect(() => encodeViewState({ ...DEFAULT_VIEW, search: 'a'.repeat(32769) })).toThrow('too large');
  });
  it('strips unknown properties before sharing or saving', () => {
    const result = parseViewState({ ...structuredClone(DEFAULT_VIEW), remember: true, filters: { ...DEFAULT_VIEW.filters, hiddenSecret: 'x' } });
    expect(result.ok && 'remember' in result.value).toBe(false);
    expect(result.ok && 'hiddenSecret' in result.value.filters).toBe(false);
  });
  it('loads old links with the page-empty option off and rejects a non-boolean value', () => {
    const oldView = structuredClone(DEFAULT_VIEW) as Record<string, unknown>;
    delete oldView.hideEmptyPageRows;
    expect(parseViewState(oldView)).toMatchObject({ ok: true, value: { hideEmptyPageRows: false } });
    expect(parseViewState({ ...oldView, hideEmptyPageRows: 'true' })).toMatchObject({ ok: false });
  });
  it('rejects malformed and obsolete versions', () => {
    expect(decodeViewState('{')).toMatchObject({ ok: false });
    expect(parseViewState({ ...DEFAULT_VIEW, version: 2 })).toMatchObject({ ok: false });
    expect(parseViewState(DEFAULT_VIEW, { knownPresetIds: new Set(['other']) })).toMatchObject({ ok: false });
  });
  it('retains restrictive IDs that disappeared from the current dataset', () => {
    const result = parseViewState({ ...structuredClone(DEFAULT_VIEW), filters: { ...DEFAULT_VIEW.filters, benchmarkIds: ['removed-benchmark'] } }, { knownBenchmarkIds: new Set() });
    expect(result.ok && result.unresolved).toContain('benchmark: removed-benchmark');
    expect(result.ok && result.value.filters.benchmarkIds).toEqual(['removed-benchmark']);
  });
});

describe('saved views', () => {
  it('namespaces by normalized deployment base and supports explicit forgetting', () => {
    const store = new Map<string, string>();
    const storage = { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => { store.set(k, v); }, removeItem: (k: string) => { store.delete(k); } } as unknown as Storage;
    const key = storageKey('https://example.test/allthebenches/');
    expect(key).toBe('allthebenches:/allthebenches/:saved-view');
    expect(writeSavedView(storage, key, DEFAULT_VIEW)).toBe(true);
    expect(readSavedView(storage, key)).toMatchObject({ ok: true, value: DEFAULT_VIEW });
    expect(forgetSavedView(storage, key)).toBe(true);
    expect(readSavedView(storage, key)).toMatchObject({ ok: false, reason: 'No saved view' });
  });
  it('does not report success when storage writes fail', () => {
    const storage = { setItem: () => { throw new Error('blocked'); } } as unknown as Storage;
    expect(writeSavedView(storage, 'k', DEFAULT_VIEW)).toBe(false);
  });
});
