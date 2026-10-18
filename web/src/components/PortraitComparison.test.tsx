import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';
import type { BenchmarkVariant } from '../generated/dataset';
import type { DisplayRow } from '../data/selectors';
import { PortraitComparison } from './PortraitComparison';

afterEach(cleanup);

const benchmark = (direction: 'higher' | 'lower' = 'higher') => ({ id: 'bench', name: 'Test benchmark', version: 'v1', category: 'text', metric_name: 'Accuracy', unit: '%', direction } as BenchmarkVariant);
function row(id: string, value: number | null, state: 'selected' | 'agreed' | 'disputed' = 'selected', observationIds = ['observation'], benchmarkId = 'bench'): DisplayRow {
  const observations = value === null && state !== 'disputed' ? new Map() : new Map([[benchmarkId, { configuration_id: id, benchmark_id: benchmarkId, state, value, unit: '%', observation_ids: observationIds }]]);
  return { id, model: { name: id }, lab: { name: 'Lab' }, observations } as unknown as DisplayRow;
}
function renderComparison(rows: DisplayRow[], selected = benchmark()) {
  return render(<PortraitComparison rows={rows} benchmarks={[selected]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null} onMatrix={() => {}}
    renderModel={id => <button className="model-link">{id}</button>} renderScore={item => <span>{item.id}</span>} />);
}

it('ranks unambiguous scores by benchmark direction and leaves disputed, multiple, and missing scores last', () => {
  const { container, rerender } = renderComparison([row('Low', 20), row('Missing', null), row('High', 90), row('Disputed', null, 'disputed', ['a', 'b']), row('Multiple', 99, 'selected', ['a', 'b'])]);
  const ids = () => [...container.querySelectorAll('.portrait-model-card .model-link')].map(item => item.textContent);
  expect(ids()).toEqual(['High', 'Low', 'Disputed', 'Missing', 'Multiple']);

  rerender(<PortraitComparison rows={[row('Low', 20), row('Missing', null), row('High', 90)]} benchmarks={[benchmark('lower')]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null} onMatrix={() => {}} renderModel={id => <button className="model-link">{id}</button>} renderScore={item => <span>{item.id}</span>} />);
  expect(ids()).toEqual(['Low', 'High', 'Missing']);
});

it('renders at most twenty cards per page and pages through the remaining models', () => {
  const rows = Array.from({ length: 25 }, (_, index) => row(`Model ${String(index + 1).padStart(2, '0')}`, index + 1));
  const { container } = renderComparison(rows);
  expect(container.querySelectorAll('.portrait-model-card')).toHaveLength(20);
  fireEvent.click(screen.getByRole('button', { name: 'Next model cards' }));
  expect(container.querySelectorAll('.portrait-model-card')).toHaveLength(5);
  expect(within(container).getByText('Page 2 of 2')).toBeTruthy();
});

it('chooses the most covered visible benchmark by default but preserves an explicit selection', () => {
  const sparse = { ...benchmark(), id: 'sparse', name: 'Sparse benchmark' };
  const covered = { ...benchmark(), id: 'covered', name: 'Covered benchmark' };
  const rows = [row('A', 10, 'selected', ['a'], 'sparse'), row('B', 20, 'selected', ['b'], 'covered'), row('C', 30, 'selected', ['c'], 'covered')];
  const props = { rows, benchmarks: [sparse, covered], onBenchmarkChange: () => {}, hideEmpty: false, busy: false, error: null, onMatrix: () => {}, renderModel: (id: string) => <button className="model-link">{id}</button>, renderScore: (item: DisplayRow) => <span>{item.id}</span> };
  const { rerender } = render(<PortraitComparison {...props} selectedBenchmarkId={null} />);
  expect(screen.getByRole('button', { name: 'Choose benchmark' }).textContent).toContain('Covered benchmark');
  rerender(<PortraitComparison {...props} selectedBenchmarkId="sparse" />);
  expect(screen.getByRole('button', { name: 'Choose benchmark' }).textContent).toContain('Sparse benchmark');
});
