import { afterEach, describe, expect, it } from 'vitest';
import { DEFAULT_VIEW, encodeViewState } from './viewState';
import { clearUrlState, loadInitialState, routeHref, urlState, viewUrl, writeUrl } from './stateRuntime';
import { parseEntityRoute } from '../Router';

afterEach(() => { history.replaceState({}, '', '/'); localStorage.clear(); });
describe('fragment shared URLs', () => {
  it('removes legacy and fragment state while preserving the base path and unrelated query parameters', () => {
    history.replaceState({}, '', '/project/?v=old&keep=yes#/?v=shared&mq=old');
    clearUrlState();
    expect(location.pathname + location.search + location.hash).toBe('/project/?keep=yes');
    expect(urlState(location)).toBeNull();
  });
  it('keeps large state out of HTTP requests and restores it exactly', () => {
    const view = { ...structuredClone(DEFAULT_VIEW), compare: true, selectedConfigurationIds: Array.from({ length: 100 }, (_, i) => `model-configuration-${i}`), visibleColumnIds: Array.from({ length: 300 }, (_, i) => `benchmark-variant-${i}`) };
    const url = viewUrl(view, 'https://example.com/project/?v=legacy&keep=yes');
    expect(url.hash.length).toBeGreaterThan(8000);
    expect(url.pathname + url.search).toBe('/project/?keep=yes');
    history.replaceState({}, '', url.pathname + url.search + url.hash);
    expect(loadInitialState(location, localStorage, '/project/').view).toEqual(view);
    const detail = routeHref('/models/example');
    history.replaceState({}, '', detail);
    expect(parseEntityRoute(location.hash)).toEqual({ kind: 'models', id: 'example' });
    expect(urlState(location)).toBe(encodeViewState(view));
    history.replaceState({}, '', routeHref('/'));
    expect(loadInitialState(location, localStorage, '/project/').view).toEqual(view);
  });
  it('reads legacy query links and migrates on the next update', () => {
    history.replaceState({}, '', '/?v=' + encodeURIComponent(JSON.stringify(DEFAULT_VIEW)));
    expect(loadInitialState(location, localStorage, '/').view).toEqual(DEFAULT_VIEW);
    writeUrl(DEFAULT_VIEW, 'replace');
    expect(location.search).toBe('');
    expect(location.hash).toMatch(/^#\/\?v=b1\./);
  });
});
