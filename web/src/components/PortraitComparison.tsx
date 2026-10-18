import { useEffect, useMemo, useState, type ReactNode } from 'react';
import type { BenchmarkVariant } from '../generated/dataset';
import type { DisplayRow } from '../data/selectors';
import { hasResultOnBenchmarks } from '../data/selectors';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from './ui/sheet';

const PAGE_SIZE = 20;
const versionLabel = (value: string) => value === 'unversioned-as-reported' || value === 'reported' ? '' : value;

type Props = {
  rows: DisplayRow[];
  benchmarks: BenchmarkVariant[];
  selectedBenchmarkId: string | null;
  onBenchmarkChange: (id: string) => void;
  hideEmpty: boolean;
  busy: boolean;
  error: string | null;
  renderModel: (id: string) => ReactNode;
  renderScore: (row: DisplayRow, benchmark: BenchmarkVariant) => ReactNode;
  onMatrix: () => void;
};

export function PortraitComparison({ rows, benchmarks, selectedBenchmarkId, onBenchmarkChange, hideEmpty, busy, error, renderModel, renderScore, onMatrix }: Props) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const selected = useMemo(() => {
    const explicit = benchmarks.find(item => item.id === selectedBenchmarkId);
    if (explicit) return explicit;
    return benchmarks.reduce<BenchmarkVariant | undefined>((best, item) => {
      const coverage = rows.reduce((count, row) => {
        const cell = row.observations.get(item.id);
        return count + Number(!!cell && cell.state !== 'disputed' && cell.observation_ids.length === 1 && cell.value !== null && Number.isFinite(Number(cell.value)));
      }, 0);
      if (!best) return item;
      const bestCoverage = rows.reduce((count, row) => {
        const cell = row.observations.get(best.id);
        return count + Number(!!cell && cell.state !== 'disputed' && cell.observation_ids.length === 1 && cell.value !== null && Number.isFinite(Number(cell.value)));
      }, 0);
      return coverage > bestCoverage ? item : best;
    }, undefined);
  }, [benchmarks, rows, selectedBenchmarkId]);
  const matchingBenchmarks = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (!normalized) return benchmarks;
    return benchmarks.filter(item => `${item.name} ${item.version} ${item.metric_name} ${item.unit} ${item.category}`.toLocaleLowerCase().includes(normalized));
  }, [benchmarks, query]);

  useEffect(() => setPage(0), [selected?.id, rows.length]);
  const candidates = useMemo(() => {
    if (!selected) return [];
    const compareScore = (row: DisplayRow) => {
      const cell = row.observations.get(selected.id);
      return cell && cell.state !== 'disputed' && cell.observation_ids.length === 1 && cell.value !== null && Number.isFinite(Number(cell.value)) ? Number(cell.value) : null;
    };
    return [...(hideEmpty ? rows.filter(row => hasResultOnBenchmarks(row, [selected.id])) : rows)].sort((a, b) => {
      const left = compareScore(a);
      const right = compareScore(b);
      if (left === null || right === null) return left === right ? a.model.name.localeCompare(b.model.name) : left === null ? 1 : -1;
      return selected.direction === 'higher' ? right - left || a.model.name.localeCompare(b.model.name) : left - right || a.model.name.localeCompare(b.model.name);
    });
  }, [rows, selected, hideEmpty]);
  const pageCount = Math.max(1, Math.ceil(candidates.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const shownRows = candidates.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);
  const metricLabel = (item: BenchmarkVariant) => `${item.metric_name} · ${item.unit}`;

  return <section className="portrait-comparison" aria-label="Portrait benchmark comparison">
    <div className="portrait-comparison-head">
      <Button className="portrait-benchmark-picker" variant="outline" aria-label="Choose benchmark" onClick={() => { setQuery(''); setPickerOpen(true); }} disabled={!benchmarks.length}>
        <span className="portrait-benchmark-picker-copy"><strong>{selected?.name ?? 'No benchmark available'}</strong><small>{selected ? `${versionLabel(selected.version) ? `${versionLabel(selected.version)} · ` : ''}${metricLabel(selected)}` : 'Change filters to show benchmarks'}</small></span>
        <span aria-hidden="true">⌄</span>
      </Button>
      <Button variant="outline" size="sm" onClick={onMatrix}>Matrix view</Button>
    </div>
    {selected && <div className="portrait-benchmark-summary"><span>{selected.category}</span><span>{selected.direction === 'higher' ? 'Higher' : 'Lower'} is better</span></div>}
    <div className="portrait-results-toolbar" aria-live="polite">
      <span>{candidates.length} configurations · showing {candidates.length ? safePage * PAGE_SIZE + 1 : 0}–{Math.min((safePage + 1) * PAGE_SIZE, candidates.length)}</span>
      {pageCount > 1 && <div><Button variant="outline" size="sm" aria-label="Previous model cards" disabled={safePage === 0} onClick={() => setPage(safePage - 1)}>Previous</Button><span>Page {safePage + 1} of {pageCount}</span><Button variant="outline" size="sm" aria-label="Next model cards" disabled={safePage + 1 >= pageCount} onClick={() => setPage(safePage + 1)}>Next</Button></div>}
    </div>
    {busy && <p className="portrait-status" role="status">Updating comparison…</p>}
    {error && <p className="portrait-status portrait-error" role="alert">{error}</p>}
    <div className="portrait-model-list">
      {selected && shownRows.map(row => <article className="portrait-model-card" key={row.id}>
        <div className="portrait-model-identity">{renderModel(row.id)}</div>
        <div className="portrait-model-score">{renderScore(row, selected)}</div>
      </article>)}
      {selected && !shownRows.length && <p className="portrait-empty">No configurations match these filters.</p>}
    </div>
    <p className="portrait-evidence-hint">Tap a score for its sources and evaluation setup. A dash means no reviewed score is available.</p>
    <Sheet open={pickerOpen} onOpenChange={setPickerOpen}>
      <SheetContent side="bottom" className="portrait-benchmark-sheet">
        <SheetHeader><SheetTitle>Choose a benchmark</SheetTitle><SheetDescription>Search by benchmark, version, metric, unit, or category.</SheetDescription></SheetHeader>
        <div className="portrait-benchmark-search"><Input autoFocus type="search" aria-label="Search benchmarks" placeholder="Search benchmarks" value={query} onChange={event => setQuery(event.target.value)} /></div>
        <div className="portrait-benchmark-options" role="listbox" aria-label="Benchmarks">
          {matchingBenchmarks.map(item => <button type="button" role="option" aria-selected={selected?.id === item.id} className="portrait-benchmark-option" key={item.id} onClick={() => { onBenchmarkChange(item.id); setPickerOpen(false); }}>
            <strong>{item.name}</strong><span>{versionLabel(item.version) ? `${versionLabel(item.version)} · ` : ''}{metricLabel(item)}</span><small>{item.category} · {item.direction === 'higher' ? 'Higher' : 'Lower'} is better</small>
          </button>)}
          {!matchingBenchmarks.length && <p className="portrait-empty">No benchmarks match this search.</p>}
        </div>
      </SheetContent>
    </Sheet>
  </section>;
}
