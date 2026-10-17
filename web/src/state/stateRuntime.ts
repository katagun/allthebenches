import { DEFAULT_VIEW, decodeViewState, encodeViewState, readSavedView, storageKey, writeSavedView, forgetSavedView, type ViewState, type ValidationContext } from './viewState';
export const QUERY_KEY = 'v';
export type InitialState = { view: ViewState; source: 'url' | 'saved' | 'default'; notice?: string; unresolved: string[]; remembered: boolean; key: string };
export function loadInitialState(location: Location, storage: Storage, baseUrl: string, ctx: ValidationContext = {}): InitialState {
  const key = storageKey(baseUrl);
  const params = new URLSearchParams(location.search);
  if (params.has(QUERY_KEY)) {
    const parsed = decodeViewState(params.get(QUERY_KEY) ?? '', ctx);
    if (!parsed.ok) return { view: structuredClone(DEFAULT_VIEW), source: 'default', notice: 'This shared view is invalid or out of date. Showing the default view.', unresolved: [], remembered: false, key };
    return { view: parsed.value, source: 'url', unresolved: parsed.unresolved, remembered: false, key };
  }
  const saved = readSavedView(storage, key, ctx);
  if (saved.ok) return { view: saved.value, source: 'saved', unresolved: saved.unresolved, remembered: true, key };
  if (saved.reason !== 'No saved view') return { view: structuredClone(DEFAULT_VIEW), source: 'default', notice: 'The saved view could not be restored. Showing the default view.', unresolved: [], remembered: false, key };
  return { view: structuredClone(DEFAULT_VIEW), source: 'default', unresolved: [], remembered: false, key };
}
export function writeUrl(view: ViewState, mode: 'push' | 'replace' = 'push'): void {
  const url = new URL(location.href);
  url.searchParams.set(QUERY_KEY, encodeViewState(view));
  history[mode === 'push' ? 'pushState' : 'replaceState']({ viewVersion: 1 }, '', url);
}
export function saveView(storage: Storage, key: string, view: ViewState): boolean { return writeSavedView(storage, key, view); }
export function forgetView(storage: Storage, key: string): boolean { return forgetSavedView(storage, key); }
export function validatedUrlView(location: Location, ctx: ValidationContext = {}): { view: ViewState; unresolved: string[] } | null {
  const value = new URLSearchParams(location.search).get(QUERY_KEY);
  if (value === null) return null;
  const parsed = decodeViewState(value, ctx);
  return parsed.ok ? { view: parsed.value, unresolved: parsed.unresolved } : { view: structuredClone(DEFAULT_VIEW), unresolved: [] };
}
