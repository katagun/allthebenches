import { urlState } from '../state/stateRuntime';
import { cleanup, render, screen } from '@testing-library/react';
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
  market: { routes: [], prices: [], performance: [] }, manifest: { snapshot_id: 'fixture' },
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
