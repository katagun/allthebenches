import { urlState } from '../state/stateRuntime';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import EntityPage from './EntityPage';
import { decodeViewState } from '../state/viewState';
import type { AppData } from '../data/snapshots';

const records = [
  { id: 'report-a', value: 70, review_state: 'reviewed', source_id: 'a' },
  { id: 'report-b', value: 71, review_state: 'reviewed', source_id: 'b' },
  { id: 'unpublished', value: 999, review_state: 'candidate', source_id: 'c' },
].map(item => ({ ...item, configuration_id: 'config', benchmark_id: 'bench', unit: '%', locator: 'Table 1', evaluator: 'Lab', reporting_relationship: 'self_report' }));
const fixture = {
  catalog: { models: [{ id: 'model', name: 'Test model', lab_ids: ['lab'] }], labs: [{ id: 'lab', name: 'Lab' }], configurations: [{ id: 'config', model_id: 'model', reasoning_label: 'high' }], benchmarks: [{ id: 'bench', name: 'Test benchmark', version: 'v1', category: 'math', unit: '%', metric_name: 'Accuracy', direction: 'higher' }], presets: [{ id: 'all', model_configuration_ids: ['config'] }] },
  results: { cells: [{ configuration_id: 'config', benchmark_id: 'bench', state: 'disputed', value: null, observation_ids: ['report-a', 'report-b'] }] },
  details: { observations: records, sources: ['a', 'b', 'c'].map(id => ({ id, title: `Source ${id}`, publisher: 'Lab', url: `https://example.org/${id}` })), metadata_claims: [], series: [] },
  market: {
    routes: [{ id: 'route', model_id: 'model', provider: 'Provider', routing_variant: 'standard', availability: 'available' }],
    prices: [{ id: 'price', route_id: 'route', input_price: 2.4, output_price: 8, cache_write_1h_price: 4, discount_fraction: 0.2, currency: 'USD', price_unit: 'USD per 1M tokens', observed_at: '2026-10-17T00:00:00Z', source_id: 'a', additional_charges: [{ name: 'web_search', amount: '0.008', unit: 'USD per web search' }] }],
    performance: [
      { id: 'latency', route_id: 'route', metric: 'latency', percentile: 'p50', value: 0.6545, unit: 'seconds', source_value: 654.5, source_unit: 'source_reported', normalization_basis: 'inferred_ms_scale', sample_window_seconds: 1800, observed_at: '2026-10-17T00:00:00Z', source_id: 'a' },
      { id: 'throughput', route_id: 'route', metric: 'throughput', percentile: 'p50', value: 70, unit: 'tokens_per_second', sample_window_seconds: 1800, observed_at: '2026-10-17T00:00:00Z', source_id: 'a' },
    ],
  }, manifest: { snapshot_id: 'fixture' },
} as unknown as AppData;

vi.mock('../data/snapshots', () => ({ loadSnapshots: () => Promise.resolve(fixture) }));
afterEach(cleanup);

it('keeps conflicting published reports separate and excludes unpublished candidates', async () => {
  const { container } = render(<EntityPage route={{ kind: 'models', id: 'model' }}/>);
  await screen.findByRole('heading', { name: 'Test model', level: 1 });
  expect(container.querySelectorAll('.entity-score')).toHaveLength(2);
  expect(screen.getAllByText('Disputed result — conflicting evidence retained')).toHaveLength(2);
  expect(container.textContent).not.toContain('999');
  expect(screen.queryByText('Source c')).toBeNull();
  const link = screen.getByRole('link', { name: 'View this model in the matrix →' });
  const encoded = urlState(new URL(link.getAttribute('href')!, 'https://example.org'))!;
  const decoded = decodeViewState(encoded);
  expect(decoded.ok).toBe(true);
  if (decoded.ok) {
    expect(decoded.value.selectedConfigurationIds).toEqual(['config']);
    expect(decoded.value.visibleColumnIds).toEqual(['bench']);
    expect(decoded.value.compare).toBe(true);
  }
});

it('summarizes routes and shows converted latency, stale age, and discounted typed prices in details', async () => {
  render(<EntityPage route={{ kind: 'models', id: 'model' }}/>);
  await screen.findByRole('heading', { name: 'Test model', level: 1 });
  fireEvent.click(screen.getByText('Model metadata & serving routes'));
  expect(screen.getByText(/p50 latency ≈0\.65 s \(unit inferred\)/)).toBeTruthy();
  expect(screen.getByText(/after 20% endpoint discount/)).toBeTruthy();
  expect(screen.getByText(/1-hour cache write 4 USD per 1M tokens/)).toBeTruthy();
  expect(screen.getByText(/web search: 0\.008 USD per web search/)).toBeTruthy();
  expect(screen.getByText(/source 654\.5 \(API-reported unit\)/)).toBeTruthy();
  expect(screen.getAllByText(/stale: snapshot is older than its 30-minute sample window/)).toHaveLength(2);
});
