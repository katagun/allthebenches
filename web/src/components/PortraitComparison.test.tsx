import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';
import type { BenchmarkVariant } from '../generated/dataset';
import type { DisplayRow } from '../data/selectors';
import { PortraitComparison } from './PortraitComparison';

afterEach(cleanup);

const benchmark = (direction: 'higher' | 'lower' = 'higher') => ({ id: 'bench', name: 'Test benchmark', version: 'v1', category: 'text', metric_name: 'Accuracy', unit: '%', direction } as BenchmarkVariant);
function row(id: string, value: number | null, state: 'selected' | 'agreed' | 'disputed' = 'selected', observationIds = ['observation'], benchmarkId = 'bench'): DisplayRow {
  const observations = value === null && state !== 'disputed' ? new Map() : new Map([[benchmarkId, { configuration_id: id, benchmark_id: benchmarkId, state, value, unit: '%', observation_ids: observationIds }]]);
  return { id, model: { id, name: id }, lab: { name: 'Lab' }, configuration: { id, reasoning_label: 'default' }, observations } as unknown as DisplayRow;
}
function renderComparison(rows: DisplayRow[], selected = benchmark()) {
  return render(<PortraitComparison rows={rows} benchmarks={[selected]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null}
    renderModel={item => <button className="model-link">{item.id}</button>} renderScore={item => <span>{item.id}</span>} />);
}

it('ranks unambiguous scores by benchmark direction and leaves disputed, multiple, and missing scores last', () => {
  const { container, rerender } = renderComparison([row('Low', 20), row('Missing', null), row('High', 90), row('Disputed', null, 'disputed', ['a', 'b']), row('Multiple', 99, 'selected', ['a', 'b'])]);
  const ids = () => [...container.querySelectorAll('.portrait-model-card .model-link')].map(item => item.textContent);
  expect(ids()).toEqual(['High', 'Low', 'Disputed', 'Missing', 'Multiple']);

  rerender(<PortraitComparison rows={[row('Low', 20), row('Missing', null), row('High', 90)]} benchmarks={[benchmark('lower')]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null} renderModel={item => <button className="model-link">{item.id}</button>} renderScore={item => <span>{item.id}</span>} />);
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
  const props = { rows, benchmarks: [sparse, covered], onBenchmarkChange: () => {}, hideEmpty: false, busy: false, error: null, renderModel: (item: DisplayRow) => <button className="model-link">{item.id}</button>, renderScore: (item: DisplayRow) => <span>{item.id}</span>, onScoreOpen: () => {} };
  const { rerender } = render(<PortraitComparison {...props} selectedBenchmarkId={null} />);
  expect(screen.getByRole('button', { name: 'Choose benchmark' }).textContent).toContain('Covered benchmark');
  rerender(<PortraitComparison {...props} selectedBenchmarkId="sparse" />);
  expect(screen.getByRole('button', { name: 'Choose benchmark' }).textContent).toContain('Sparse benchmark');
});

it('uses a shared percentage scale and never draws missing or disputed scores as numeric bars', () => {
  const { container } = renderComparison([row('High', 80), row('Low', 20), row('Zero', 0), row('Missing', null), row('Disputed', 90, 'disputed')]);
  const widths = [...container.querySelectorAll<HTMLElement>('.mobile-score-bar')].map(bar => bar.style.width);
  expect(widths).toEqual(['80%', '20%', '0%']);
});

it('uses the reporting row for the score, bar, ranking, winner range, and evidence target', () => {
  const opened: string[] = [];
  const primary = row('Primary', null);
  const reporting = { ...row('Reporting', 70), model: primary.model };
  const rows = [primary, row('Other', 60)];
  const { container } = render(<PortraitComparison rows={rows} benchmarks={[benchmark()]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null}
    rowsForBenchmark={() => [reporting, rows[1]]}
    renderModel={item => <button className="model-link">{item.model.name}</button>}
    renderScore={(item, bench, range) => <button className="score-button" data-best={item.observations.get(bench.id)?.value === range?.max || undefined} onClick={() => opened.push(item.configuration.id)}>{item.observations.get(bench.id)?.value ?? '—'}</button>} />);
  const cards = [...container.querySelectorAll('.portrait-model-card')];
  expect(cards.map(card => card.querySelector('.model-link')?.textContent)).toEqual(['Primary', 'Other']);
  expect(cards[0].querySelector('.score-button')?.textContent).toBe('70');
  expect(cards[0].querySelector<HTMLElement>('.mobile-score-bar')?.style.width).toBe('70%');
  expect(cards[0].querySelector('.score-button')?.getAttribute('data-best')).toBe('true');
  fireEvent.click(cards[0].querySelector('.score-button')!);
  expect(opened).toEqual(['Reporting']);
});

it('waits for row selection before showing scores for the default benchmark', () => {
  const sparse = { ...benchmark(), id: 'sparse', name: 'Sparse' };
  const covered = { ...benchmark(), id: 'covered', name: 'Covered' };
  const rows = [row('A', 10, 'selected', ['a'], 'covered'), row('B', 20, 'selected', ['b'], 'covered')];
  const queried: string[] = [];
  const props = {
    benchmarks: [sparse, covered], selectedBenchmarkId: null, onBenchmarkChange: () => {}, hideEmpty: false, error: null,
    rowsForBenchmark: (id: string) => { queried.push(id); return rows; },
    renderModel: (item: DisplayRow) => <span>{item.model.name}</span>, renderScore: (item: DisplayRow) => <span>{item.id}</span>,
  };
  const { container, rerender } = render(<PortraitComparison {...props} rows={[]} busy />);
  expect(container.querySelectorAll('.portrait-model-card')).toHaveLength(0);
  expect(queried).toEqual([]);
  expect(screen.queryByText('No configurations match these filters.')).toBeNull();
  rerender(<PortraitComparison {...props} rows={rows} busy={false} />);
  expect(queried).toEqual(['covered']);
  expect(container.querySelectorAll('.portrait-model-card')).toHaveLength(2);
});

it('labels the setup only when several cards share one model', () => {
  const shared = (id: string, reasoning: string, value: number): DisplayRow => ({
    id, model: { id: 'same', name: 'Same Model' }, lab: { name: 'Lab' }, configuration: { id, reasoning_label: reasoning },
    observations: new Map([['bench', { configuration_id: id, benchmark_id: 'bench', state: 'selected', value, unit: '%', observation_ids: ['o'] }]]),
  } as unknown as DisplayRow);
  const { container } = render(<PortraitComparison rows={[shared('a', 'low', 70), row('Solo', 10), shared('b', 'high', 80)]} benchmarks={[benchmark()]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null}
    renderModel={item => <button className="model-link">{item.id}</button>} renderScore={item => <span>{item.id}</span>} />);
  const cards = [...container.querySelectorAll('.portrait-model-card')];
  expect(cards).toHaveLength(3);
  expect(cards[0].querySelector('.mobile-model-setup')?.textContent).toBe('Reasoning: high');
  expect(cards[1].querySelector('.mobile-model-setup')?.textContent).toBe('Reasoning: low');
  expect(cards[2].querySelector('.mobile-model-setup')).toBeNull();
});

it('uses the eligibility resolver for bars and ranking when a score is excluded by filters', () => {
  const { container } = render(<PortraitComparison rows={[row('Eligible', 20), row('Excluded', 99)]} benchmarks={[benchmark()]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null}
    renderModel={item => <button className="model-link">{item.id}</button>} renderScore={item => <span>{item.id}</span>} score={item => item.id === 'Eligible' ? 20 : null} />);
  const cards = [...container.querySelectorAll('.portrait-model-card')];
  expect(cards.map(card => card.querySelector('.model-link')?.textContent)).toEqual(['Eligible', 'Excluded']);
  expect(cards[1].querySelector('.mobile-score-bar')).toBeNull();
});

it('keeps disputed scores visible as disputed while sorting them last without bars', () => {
  const { container } = render(<PortraitComparison rows={[row('Scored', 10), row('Contested', null, 'disputed', ['a', 'b'])]} benchmarks={[benchmark()]} selectedBenchmarkId="bench" onBenchmarkChange={() => {}} hideEmpty={false} busy={false} error={null}
    renderModel={item => <button className="model-link">{item.id}</button>} renderScore={item => <span className="preview">{item.id}</span>} />);
  const cards = [...container.querySelectorAll('.portrait-model-card')];
  expect(cards.map(card => card.querySelector('.model-link')?.textContent)).toEqual(['Scored', 'Contested']);
  expect(cards[1].querySelector('.preview')).not.toBeNull();
  expect(cards[1].querySelector('.score-button.missing')).toBeNull();
  expect(cards[1].querySelector('.mobile-score-bar')).toBeNull();
});

it('preserves the bar scale across result pages', () => {
  const rows = Array.from({ length: 21 }, (_, index) => row(`Model ${index}`, index + 1));
  const { container } = renderComparison(rows, { ...benchmark(), unit: 'points' });
  expect(container.querySelector<HTMLElement>('.mobile-score-bar')?.style.width).toBe('100%');
  fireEvent.click(screen.getByRole('button', { name: 'Next model cards' }));
  expect(parseFloat(container.querySelector<HTMLElement>('.mobile-score-bar')!.style.width)).toBeCloseTo(100 / 21);
});
