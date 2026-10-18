import { urlState } from './state/stateRuntime';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { Profiler, StrictMode } from 'react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import catalog from '../public/data/catalog.json';
import details from '../public/data/details.json';
import manifest from '../public/data/manifest.json';
import market from '../public/data/market.json';
import results from '../public/data/results.json';
import App from './App';
import { clearSnapshotCache, type AppData } from './data/snapshots';
import { comparisonFixture } from './test/comparisonFixture';
import { decodeViewState, DEFAULT_VIEW } from './state/viewState';

const fixture: AppData = { catalog, details, manifest, market, results } as unknown as AppData;
const files = { catalog, details, manifest, market, results } as const;
const allModels = fixture.catalog.presets.find(p => p.id === 'all_models_oct2026')!;
const frontier = fixture.catalog.presets.find(p => p.id === 'frontier_oct2026')!;
const selectedBenchmarkIds = allModels.benchmark_ids ?? [];
const selectedConfigurationIds = allModels.model_configuration_ids ?? [];
const state = { ...structuredClone(DEFAULT_VIEW), orientation: 'models-rows' as const, presetId: allModels.id, visibleColumnIds: selectedBenchmarkIds };
let activeFiles: typeof files = files;
beforeEach(() => {
  clearSnapshotCache();
  activeFiles = files;
  window.history.replaceState({}, '', `/?v=${encodeURIComponent(JSON.stringify(state))}`);
  window.localStorage.clear();
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const key = String(input).split('/').pop()?.replace('.json', '') as string;
    return { ok: true, status: 200, json: async () => (key === 'comparison' ? comparisonFixture(activeFiles) : key.startsWith('evidence-') ? activeFiles.details : activeFiles[key as keyof typeof activeFiles]) } as Response;
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe('wide table rendering', () => {
  it('adapts to container width without unbounded rendering or resize loops', async () => {
    let width = 2500;
    let resized: () => void = () => undefined;
    vi.spyOn(Element.prototype, 'clientWidth', 'get').mockImplementation(() => width);
    vi.stubGlobal('ResizeObserver', class {
      constructor(callback: () => void) { resized = callback; }
      observe() {}
      disconnect() {}
    });
    let commits = 0;
    const { container } = render(<StrictMode><Profiler id="responsive" onRender={() => { commits++; }}><App/></Profiler></StrictMode>);
    await waitFor(() => expect(container.querySelectorAll('thead th').length).toBe(13));
    expect(screen.queryByText('Compare the work.')).toBeNull();
    expect(screen.queryByText('MODEL EVALUATIONS')).toBeNull();
    width = 4200;
    resized();
    await waitFor(() => expect(container.querySelectorAll('thead th').length).toBe(22));
    width = 10000;
    resized();
    await waitFor(() => expect(container.querySelectorAll('thead th').length).toBe(25));
    expect(container.querySelectorAll('tbody td').length).toBeLessThanOrEqual(50 * 25);
    const settled = commits;
    for (let i = 0; i < 30; i++) resized();
    await new Promise(resolve => setTimeout(resolve, 80));
    expect(commits - settled).toBeLessThanOrEqual(2);
    width = 1100;
    resized();
    await waitFor(() => expect(container.querySelectorAll('thead th').length).toBe(5));
  });

  it('bounds DOM columns while retaining navigable columns and full table metadata', async () => {
    const started = performance.now();
    const { container } = render(<App/>);
    await screen.findByRole('button', { name: 'All models' });
    await waitFor(() => expect(container.querySelectorAll('tbody tr').length).toBeGreaterThan(0));
    const elapsed = performance.now() - started;
    const bodyRowCount = container.querySelectorAll('tbody tr').length;
    const bodyCellCount = container.querySelectorAll('tbody td').length;
    const headerCellCount = container.querySelectorAll('thead th').length;
    const nodeCount = container.querySelectorAll('*').length;
    const table = container.querySelector('table[aria-label="Benchmark results"]');
    console.log(JSON.stringify({ selectedColumns: selectedBenchmarkIds.length, modelConfigurations: selectedConfigurationIds.length, bodyRowCount, bodyCellCount, headerCellCount, totalTableCells: bodyCellCount + headerCellCount, nodeCount, renderMs: Math.round(elapsed) }));

    expect(screen.getByText(`Showing benchmarks 1–10 of ${selectedBenchmarkIds.length}`)).toBeTruthy();
    expect(table?.getAttribute('aria-colcount')).toBe(String(selectedBenchmarkIds.length + 1));
    expect(container.querySelectorAll('thead th').length).toBeLessThanOrEqual(11);
    expect(bodyCellCount).toBeLessThanOrEqual(bodyRowCount * 11);
    expect(screen.getByRole('button', { name: 'Previous benchmark columns' })).toHaveProperty('disabled', true);

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Next benchmark columns' }));
    await waitFor(() => expect(screen.getByText(`Showing benchmarks 11–20 of ${selectedBenchmarkIds.length}`)).toBeTruthy());
    expect(container.querySelector('thead th[aria-colindex="12"]')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Previous benchmark columns' })).toHaveProperty('disabled', false);

    const benchmark = fixture.catalog.benchmarks.find(item => item.id === selectedBenchmarkIds[10])!;
    const header = screen.getByRole('columnheader', { name: new RegExp(benchmark.name) });
    await user.click(header.querySelector('button')!);
    await waitFor(() => {
      const encoded = urlState(window.location);
      expect(encoded).toBeTruthy();
      const decoded = decodeViewState(encoded!);
      expect(decoded.ok && decoded.value.sort?.id).toBe(benchmark.id);
    });
  }, 30_000);

  it('pages configuration rows with a synthetic large preset and keeps selection across pages', async () => {
    const expanded = structuredClone(files) as any;
    const preset = expanded.catalog.presets.find((item: any) => item.id === 'all_models_oct2026');
    const modelTemplate = expanded.catalog.models[0];
    const configurationTemplate = expanded.catalog.configurations[0];
    for (let index = 0; index < 70; index++) {
      const modelId = `synthetic_scale_model_${index}`;
      const configurationId = `synthetic_scale_config_${index}`;
      expanded.catalog.models.push({ ...modelTemplate, id: modelId, family_id: modelId, name: `Synthetic Scale Model ${index}`, source_ids: [] });
      expanded.catalog.configurations.push({ ...configurationTemplate, id: configurationId, model_id: modelId, reasoning_label: 'default' });
      preset.model_configuration_ids.push(configurationId);
    }
    activeFiles = expanded;
    window.history.replaceState({}, '', `/?v=${encodeURIComponent(JSON.stringify({ ...state, includeUnbenchmarked: true }))}`);
    const user = userEvent.setup();
    const { container } = render(<App/>);
    await waitFor(() => expect(screen.getByRole('navigation', { name: 'Table row pages' })).toBeTruthy(), { timeout: 20_000 });
    const rowStatus = screen.getByRole('navigation', { name: 'Table row pages' }).querySelector('[aria-live="polite"]')?.textContent ?? '';
    const totalRows = Number(rowStatus.match(/of (\d+)$/)?.[1]);
    expect(rowStatus).toMatch(/^Showing rows 1–50 of \d+$/);
    expect(totalRows).toBeGreaterThan(50);
    expect(container.querySelectorAll('tbody tr').length).toBe(50);
    expect(container.querySelectorAll('tbody td').length).toBeLessThanOrEqual(50 * 11);
    const selectedRow = container.querySelector('tbody tr')!;
    const selectBox = selectedRow.querySelector('[role="checkbox"]') as HTMLElement;
    await user.click(selectBox);
    const selectedId = decodeViewState(urlState(window.location)!);
    expect(selectedId.ok && selectedId.value.selectedConfigurationIds).toHaveLength(1);

    await user.click(screen.getByRole('button', { name: 'Next table rows' }));
    await waitFor(() => expect(screen.getByRole('navigation', { name: 'Table row pages' }).querySelector('[aria-live="polite"]')?.textContent).toMatch(new RegExp(`^Showing rows 51–\\d+ of ${totalRows}$`)));
    const secondPageCheckbox = container.querySelector('tbody tr [role="checkbox"]') as HTMLElement;
    await user.click(secondPageCheckbox);
    expect(screen.getByRole('navigation', { name: 'Table row pages' }).querySelector('[aria-live="polite"]')?.textContent).toMatch(new RegExp(`^Showing rows 51–\\d+ of ${totalRows}$`));
    const afterPage = decodeViewState(urlState(window.location)!);
    expect(afterPage.ok && afterPage.value.selectedConfigurationIds).toHaveLength(2);
  }, 30_000);

  it('settles after a wide-preset switch under StrictMode and records React render cost', async () => {
    window.history.replaceState({}, '', `/?v=${encodeURIComponent(JSON.stringify({ ...structuredClone(DEFAULT_VIEW), orientation: 'models-rows' as const, presetId: frontier.id, visibleColumnIds: frontier.benchmark_ids ?? [] }))}`);
    let commits = 0;
    let actualDurationMs = 0;
    const onRender: React.ProfilerOnRenderCallback = (_id, _phase, actualDuration) => {
      commits += 1;
      actualDurationMs += actualDuration;
    };
    const user = userEvent.setup();
    const { container } = render(<StrictMode><Profiler id="app" onRender={onRender}><App/></Profiler></StrictMode>);
    await waitFor(() => expect(container.querySelectorAll('tbody tr').length).toBeGreaterThan(0), { timeout: 20_000 });
    const startCommits = commits;
    const startDuration = actualDurationMs;
    await user.click(screen.getByRole('button', { name: 'All models' }));
    await waitFor(() => expect(container.querySelector('table[aria-label="Benchmark results"]')?.getAttribute('aria-busy')).toBe('false'), { timeout: 20_000 });
    await new Promise(resolve => window.setTimeout(resolve, 120));
    const presetCommits = commits - startCommits;
    const presetDuration = actualDurationMs - startDuration;
    console.log(JSON.stringify({ presetSwitchCommits: presetCommits, presetSwitchReactActualDurationMs: Math.round(presetDuration) }));
    expect(presetCommits).toBeLessThanOrEqual(8);
    expect(container.querySelectorAll('tbody tr').length).toBeGreaterThan(0);

    const reverseStartCommits = commits;
    await user.click(screen.getByRole('button', { name: 'Frontier' }));
    await waitFor(() => expect(container.querySelector('table[aria-label="Benchmark results"]')?.getAttribute('aria-busy')).toBe('false'), { timeout: 20_000 });
    await new Promise(resolve => window.setTimeout(resolve, 120));
    const reverseCommits = commits - reverseStartCommits;
    expect(reverseCommits).toBeLessThanOrEqual(8);
    expect(container.querySelectorAll('tbody tr').length).toBeGreaterThan(0);
    const settledCommits = commits;
    await new Promise(resolve => window.setTimeout(resolve, 150));
    expect(commits).toBe(settledCommits);
  }, 30_000);
});
