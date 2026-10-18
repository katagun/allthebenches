import { urlState } from './state/stateRuntime';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import catalogJson from '../public/data/catalog.json';
import detailsJson from '../public/data/details.json';
import manifestJson from '../public/data/manifest.json';
import marketJson from '../public/data/market.json';
import resultsJson from '../public/data/results.json';
import App, { makeDefault } from './App';
import type { AppData } from './data/snapshots';
import { DEFAULT_VIEW, decodeViewState, encodeViewState, storageKey } from './state/viewState';

const targetCell = resultsJson.cells.find(cell => cell.value !== null);
const targetConfiguration = catalogJson.configurations.find(config => config.id === targetCell?.configuration_id);
const targetModel = catalogJson.models.find(model => model.id === targetConfiguration?.model_id);
const targetBenchmark = catalogJson.benchmarks.find(benchmark => benchmark.id === targetCell?.benchmark_id);
const historicalPreset = {
  id: 'historical', version: '1', name: 'Historical releases',
  model_configuration_ids: targetConfiguration ? [targetConfiguration.id] : [],
  benchmark_ids: targetCell ? [targetCell.benchmark_id] : [],
};
const fixture = structuredClone({ catalog: catalogJson, details: detailsJson, manifest: manifestJson, market: marketJson, results: resultsJson }) as unknown as AppData;
fixture.catalog.presets = [...fixture.catalog.presets.filter(p => p.id !== historicalPreset.id), historicalPreset];
const files = { catalog: fixture.catalog, details: fixture.details, manifest: fixture.manifest, market: fixture.market, results: fixture.results };

beforeEach(() => {
  Object.defineProperties(HTMLElement.prototype, {
    hasPointerCapture: { configurable: true, value: () => false },
    setPointerCapture: { configurable: true, value: () => undefined },
    releasePointerCapture: { configurable: true, value: () => undefined },
    scrollIntoView: { configurable: true, value: () => undefined },
  });
  window.history.replaceState({}, '', '/');
  window.localStorage.clear();
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const name = String(input).split('/').pop()?.replace('.json', '') as keyof typeof files;
    return { ok: true, status: 200, json: async () => files[name] } as Response;
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe('curated preset switching', () => {
  it('clears shared and saved filters, removes URL state and restores the same default on reload', async () => {
    const filtered = { ...structuredClone(DEFAULT_VIEW), search: 'Mistral' };
    localStorage.setItem(storageKey('/'), JSON.stringify(filtered));
    history.replaceState({}, '', '/?v=' + encodeURIComponent(encodeViewState(filtered)));
    const user = userEvent.setup();
    render(<App/>);
    await screen.findByDisplayValue('Mistral');
    await user.click(screen.getAllByRole('button', { name: 'Clear filters' })[0]);
    expect(location.search).toBe('');
    expect(location.hash).toBe('');
    expect(localStorage.getItem(storageKey('/'))).toBeNull();
    expect((screen.getByRole('searchbox', { name: 'Search models' }) as HTMLInputElement).value).toBe('');
    cleanup();
    render(<App/>);
    await screen.findByRole('button', { name: 'Frontier' });
    expect((screen.getByRole('searchbox', { name: 'Search models' }) as HTMLInputElement).value).toBe('');
  });
  it('keeps the full all-model benchmark selection within the shared-view URL bound', () => {
    const preset = fixture.catalog.presets.find(item => item.name.toLowerCase().includes('all models') && (item.benchmark_ids?.length ?? 0) >= 300);
    expect(preset).toBeTruthy();
    if (!preset) return;
    const encoded = encodeViewState({ ...structuredClone(DEFAULT_VIEW), orientation: 'models-rows' as const, presetId: preset.id, visibleColumnIds: preset.benchmark_ids ?? [], compare: true, selectedConfigurationIds: fixture.catalog.configurations.map(config => config.id) });
    expect(decodeViewState(encoded).ok).toBe(true);
  });
  it('keeps every curated frontier column in the default view, including later pages', () => {
    const data = structuredClone(fixture);
    const frontier = data.catalog.presets.find(p => p.id === 'frontier_oct2026')!;
    // More than one page ensures the default cannot silently truncate the preset.
    frontier.benchmark_ids = data.catalog.benchmarks.slice(0, 22).map(b => b.id);
    expect(makeDefault(data).orientation).toBe('benchmarks-rows');
    expect(makeDefault(data).visibleColumnIds).toEqual(frontier.benchmark_ids);
    const removed = frontier.benchmark_ids[0];
    data.catalog.benchmarks = data.catalog.benchmarks.filter(b => b.id !== removed);
    expect(makeDefault(data).visibleColumnIds).toEqual(frontier.benchmark_ids.slice(1));
  });

  it('switches to a data-defined historical preset, uses its columns, and restores it from the URL', async () => {
    expect(targetCell && targetConfiguration && targetModel && targetBenchmark).toBeTruthy();
    if (!targetCell || !targetConfiguration || !targetModel || !targetBenchmark) return;
    const frontier = fixture.catalog.presets.find(p => p.id === 'frontier_oct2026');
    const selectedConfigurationId = frontier?.model_configuration_ids?.[0];
    expect(selectedConfigurationId).toBeTruthy();
    if (!frontier || !selectedConfigurationId) return;
    const priorView = { ...structuredClone(DEFAULT_VIEW), orientation: 'models-rows' as const, presetId: frontier.id, compare: true, selectedConfigurationIds: [selectedConfigurationId] };
    const url = new URL(window.location.href);
    url.hash = '';
  url.searchParams.set('v', JSON.stringify(priorView));
    window.history.replaceState({}, '', url);
    const user = userEvent.setup();
    const first = render(<App/>);
    await screen.findByRole('searchbox', { name: 'Search models' });
    await user.click(screen.getByRole('combobox', { name: 'More model sets' }));
    await user.click(await screen.findByRole('option', { name: historicalPreset.name }));

    await waitFor(() => {
      const encoded = urlState(window.location);
      expect(encoded).toBeTruthy();
      const parsed = decodeViewState(encoded!);
      expect(parsed.ok).toBe(true);
      if (!parsed.ok) throw new Error(parsed.reason);
      const state = parsed.value;
      expect(state.presetId).toBe(historicalPreset.id);
      expect(state.visibleColumnIds).toEqual([targetCell.benchmark_id]);
      expect(state.compare).toBe(false);
      expect(state.selectedConfigurationIds).toEqual([]);
    });
    expect(await screen.findByText(targetModel.name)).toBeTruthy();
    first.unmount();
    render(<App/>);
    expect(await screen.findByText(targetModel.name)).toBeTruthy();
    expect(await screen.findByText(targetBenchmark.name)).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Choose benchmarks' }));
    expect(await screen.findByText(/observed price quotes across/)).toBeTruthy();
    expect(screen.getByText(/No public token-volume records in this snapshot/)).toBeTruthy();
    await user.click(screen.getAllByRole('checkbox', { checked: true })[0]);
    await user.click(screen.getByRole('button', { name: 'Use preset benchmarks' }));
    await waitFor(() => {
      const parsed = decodeViewState(urlState(window.location)!);
      if (!parsed.ok) throw new Error(parsed.reason);
      const state = parsed.value;
      expect(state.visibleColumnIds).toEqual(historicalPreset.benchmark_ids);
    });
  });
});
