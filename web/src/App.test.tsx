import { urlState } from './state/stateRuntime';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import catalog from '../public/data/catalog.json';
import details from '../public/data/details.json';
import manifest from '../public/data/manifest.json';
import market from '../public/data/market.json';
import results from '../public/data/results.json';
import App from './App';
import type { AppData } from './data/snapshots';
import { storageKey, decodeViewState } from './state/viewState';
import { DEFAULT_VIEW, type ViewState } from './state/viewState';

const fixture: AppData = { catalog, details, manifest, market, results } as unknown as AppData;
const dataFiles = { catalog, details, manifest, market, results } as const;
const originalStorageDescriptor = Object.getOwnPropertyDescriptor(window, 'localStorage');

function response(body: unknown, ok = true, status = 200) {
  return { ok, status, json: async () => body } as Response;
}
function mockSuccessfulFetch() {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const name = String(input).split('/').pop()?.replace('.json', '') as keyof typeof dataFiles;
    return response(dataFiles[name]);
  }));
}
function viewWith(overrides: Partial<ViewState> = {}): ViewState {
  return {
    ...structuredClone(DEFAULT_VIEW), orientation: 'models-rows' as const,
    presetId: fixture.catalog.presets[0]?.id ?? DEFAULT_VIEW.presetId,
    visibleColumnIds: fixture.catalog.presets[0]?.benchmark_ids?.slice(0, 2) ?? [],
    ...overrides,
  };
}
function setSharedUrl(view: ViewState) {
  const url = new URL(window.location.href);
  url.hash = '';
  url.searchParams.set('v', JSON.stringify(view));
  window.history.replaceState({}, '', url);
}
function savedEnvelope(view: ViewState) {
  return JSON.stringify({ format_version: 1, saved_at: '2026-10-17T00:00:00Z', view });
}

beforeEach(() => {
  if (originalStorageDescriptor) Object.defineProperty(window, 'localStorage', originalStorageDescriptor);
  window.history.replaceState({}, '', '/');
  window.localStorage.clear();
  mockSuccessfulFetch();
});
afterEach(() => {
  cleanup();
  if (originalStorageDescriptor) Object.defineProperty(window, 'localStorage', originalStorageDescriptor);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('App view workflows', () => {
  it('renders the same evidence in the transposed orientation with bounded model columns', async () => {
    const view = viewWith({ orientation: 'benchmarks-rows' });
    setSharedUrl(view);
    render(<App />);
    const table = await screen.findByRole('table', { name: 'Benchmark results, benchmarks in rows' });
    await waitFor(() => expect(within(table).getAllByRole('columnheader').length).toBeGreaterThan(1));
    expect(within(table).getAllByRole('columnheader').length).toBeLessThanOrEqual(11);
    expect(within(table).getAllByRole('row').length).toBeLessThanOrEqual(51);
    const evidence = within(table).getAllByRole('button', { name: /show evidence/ })[0];
    await userEvent.setup().click(evidence);
    expect(await screen.findByRole('dialog')).toBeTruthy();
    expect(decodeViewState(urlState(window.location)!)).toMatchObject({ ok: true, value: { orientation: 'benchmarks-rows', visibleColumnIds: view.visibleColumnIds } });
  });
  it('shares a base64url link that restores the complete view', async () => {
    const view = viewWith({ search: 'café 🧠' });
    setSharedUrl(view); // Existing JSON links must still load.
    const user = userEvent.setup();
    const clipboard = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue();
    render(<App />);
    await screen.findByRole('searchbox', { name: 'Search models' });
    await user.click(screen.getByRole('button', { name: 'Share' }));
    const shared = new URLSearchParams(new URL(clipboard.mock.calls[0][0]).hash.split('?')[1]).get('v')!;
    expect(shared).toMatch(/^b1\.[A-Za-z0-9_-]+$/);
    expect(decodeViewState(shared)).toMatchObject({ ok: true, value: view });
    cleanup();
    window.history.replaceState({}, '', '#/?' + new URLSearchParams({ v: shared }));
    render(<App />);
    expect((await screen.findByRole('searchbox', { name: 'Search models' }) as HTMLInputElement).value).toBe(view.search);
  });

  it('preserves reported decimal precision in table cells and evidence', async () => {
    const preciseFiles: Record<string, any> = JSON.parse(JSON.stringify(dataFiles));
    const checks = [
      { benchmarkId: 'terminal_bench_4', value: 0.983 },
      { benchmarkId: 'deepswe_v11', value: 0.5282 },
      { benchmarkId: 'automationbench_reported', value: 1.691 },
    ];
    for (const check of checks) {
      const cell = preciseFiles.results.cells.find((item: any) => item.configuration_id === 'gpt6_astra_google_reported' && item.benchmark_id === check.benchmarkId);
      expect(cell).toBeDefined();
      cell.value = check.value;
      for (const id of cell.observation_ids) {
        const observation = preciseFiles.details.observations.find((item: any) => item.id === id);
        expect(observation).toBeDefined();
        observation.value = check.value;
      }
    }
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const name = String(input).split('/').pop()?.replace('.json', '') ?? '';
      return response(preciseFiles[name]);
    }));
    setSharedUrl(viewWith({ presetId: 'frontier_oct2026', visibleColumnIds: checks.map(check => check.benchmarkId) }));

    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole('searchbox', { name: 'Search models' });
    const row = await screen.findByRole('row', { name: /GPT-6 Astra/ });
    for (const check of checks) {
      const benchmark = fixture.catalog.benchmarks.find(item => item.id === check.benchmarkId);
      expect(benchmark).toBeDefined();
      const formatted = String(check.value);
      const score = within(row).getByRole('button', { name: new RegExp(`GPT-6 Astra, ${benchmark!.name}:`) });
      expect(score.textContent).toContain(formatted);
      await user.click(score);
      const dialog = await screen.findByRole('dialog');
      expect(within(dialog).getAllByText(new RegExp(formatted.replace('.', '\\.'))).length).toBeGreaterThan(0);
      await user.keyboard('{Escape}');
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    }
  });

  it('discards filter draft on Cancel and writes it only when Apply is chosen', async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole('searchbox', { name: 'Search models' });
    const before = window.location.href;
    await user.click(screen.getByRole('button', { name: /Filters/ }));
    const dialog = await screen.findByRole('dialog');
    const lab = fixture.catalog.labs[0];
    const labCheckbox = within(dialog).getByRole('checkbox', { name: lab.name });
    await user.click(labCheckbox);
    await user.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(window.location.href).toBe(before);
    expect(screen.getByRole('button', { name: /Filters/ }).textContent).not.toContain('1');

    await user.click(screen.getByRole('button', { name: /Filters/ }));
    const nextDialog = await screen.findByRole('dialog');
    await user.click(within(nextDialog).getByRole('checkbox', { name: lab.name }));
    await user.click(within(nextDialog).getByRole('button', { name: 'Apply filters' }));
    await waitFor(() => expect(decodeViewState(urlState(window.location)!)).toMatchObject({ ok: true, value: { filters: { labIds: [lab.id] } } }));
    expect(screen.getByRole('button', { name: /Filters/ }).textContent).toContain('1');
  }, 15_000);

  it('restores the prior applied view when the browser emits popstate', async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole('searchbox', { name: 'Search models' });
    await user.click(screen.getByRole('button', { name: 'All models' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'All models' }).getAttribute('aria-pressed')).toBe('true'));
    expect(decodeViewState(urlState(window.location)!)).toMatchObject({ ok: true, value: { presetId: 'all_models_oct2026' } });
    window.history.replaceState({}, '', '/');
    window.dispatchEvent(new PopStateEvent('popstate'));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Frontier' }).getAttribute('aria-pressed')).toBe('true'));
  }, 15_000);

  it('gives a shared URL precedence over a saved view without replacing the saved view', async () => {
    const saved = viewWith({ search: 'saved-only-query' });
    const shared = viewWith({ search: 'shared-only-query' });
    const key = storageKey('/');
    window.localStorage.setItem(key, savedEnvelope(saved));
    setSharedUrl(shared);
    const before = window.localStorage.getItem(key);

    render(<App />);
    expect((await screen.findByRole('searchbox', { name: 'Search models' }) as HTMLInputElement).value).toBe('shared-only-query');
    expect(window.localStorage.getItem(key)).toBe(before);
    await userEvent.setup().click(screen.getByRole('button', { name: /Filters/ }));
    expect(await screen.findByText(/Save this view on this device/)).not.toBeNull();
  });

  it('uses the shared URL when localStorage access is blocked', async () => {
    const shared = viewWith({ search: 'url-still-works' });
    setSharedUrl(shared);
    Object.defineProperty(window, 'localStorage', { configurable: true, get: () => { throw new Error('blocked'); } });

    render(<App />);
    expect((await screen.findByRole('searchbox', { name: 'Search models' }) as HTMLInputElement).value).toBe('url-still-works');
    expect(urlState(window.location)).toContain('url-still-works');

    setSharedUrl(viewWith({ search: 'url-back-forward-still-works' }));
    window.dispatchEvent(new PopStateEvent('popstate'));
    await waitFor(() => expect((screen.getByRole('searchbox', { name: 'Search models' }) as HTMLInputElement).value).toBe('url-back-forward-still-works'));
  });

  it('shows a recoverable load error and retries the snapshot request', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({}, false, 503))
      .mockImplementation(async (input: RequestInfo | URL) => {
        const name = String(input).split('/').pop()?.replace('.json', '') as keyof typeof dataFiles;
        return response(dataFiles[name]);
      });
    vi.stubGlobal('fetch', fetchMock);

    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByText('Could not load catalog data (503)')).not.toBeNull();
    const callsBeforeRetry = fetchMock.mock.calls.length;
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('searchbox', { name: 'Search models' })).not.toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeRetry + 5);
  });
});
