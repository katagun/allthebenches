import { routeHref } from '../state/stateRuntime';
import { useState, type ReactNode, type CSSProperties } from 'react';
import type { BenchmarkVariant } from '../generated/dataset';
import type { DisplayRow } from '../data/selectors';
import { hasResultOnBenchmarks } from '../data/selectors';
import { ArrowDown, ArrowUp, ArrowDownUp } from 'lucide-react';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { COMPACT_MODEL_WIDTH, BENCHMARK_LABEL_WIDTH } from '../data/useColumnCapacity';

type Props = {
  rows: DisplayRow[]; benchmarks: BenchmarkVariant[]; capacity: number; hideEmpty: boolean;
  marketIds: string[]; renderModel: (id: string) => ReactNode;
  renderScore: (row: DisplayRow, benchmark: BenchmarkVariant) => ReactNode;
  renderMarket: (id: string, metric: string) => ReactNode;
  sort: { id: string; direction: 'asc' | 'desc' } | null;
  onSort: (benchmark: BenchmarkVariant) => void;
};

export function TransposedTable({ rows, benchmarks, capacity, hideEmpty, marketIds, renderModel, renderScore, renderMarket, onSort, sort }: Props) {
  const [modelPage, setModelPage] = useState(0);
  const [metricPage, setMetricPage] = useState(0);
  const modelPages = Math.max(1, Math.ceil(rows.length / capacity));
  const safeModelPage = Math.min(modelPage, modelPages - 1);
  const models = rows.slice(safeModelPage * capacity, (safeModelPage + 1) * capacity);
  const metrics = hideEmpty ? benchmarks.filter(b => models.some(row => hasResultOnBenchmarks(row, [b.id]))) : benchmarks;
  const metricPages = Math.max(1, Math.ceil(metrics.length / 50));
  const safeMetricPage = Math.min(metricPage, metricPages - 1);
  const shownMetrics = metrics.slice(safeMetricPage * 50, (safeMetricPage + 1) * 50);
  return <>
    <div className="transpose-pagination">
      <nav aria-label="Model column pages"><Button size="sm" variant="outline" disabled={safeModelPage === 0} onClick={() => { setModelPage(safeModelPage - 1); setMetricPage(0); }} aria-label="Previous models"><span className="pagination-full">Previous models</span><span className="pagination-short" aria-hidden="true">←</span></Button><span>Models {rows.length ? safeModelPage * capacity + 1 : 0}–{Math.min((safeModelPage + 1) * capacity, rows.length)} of {rows.length}</span><Button size="sm" variant="outline" disabled={safeModelPage + 1 >= modelPages} onClick={() => { setModelPage(safeModelPage + 1); setMetricPage(0); }} aria-label="Next models"><span className="pagination-full">Next models</span><span className="pagination-short" aria-hidden="true">→</span></Button></nav>
      <nav aria-label="Benchmark row pages" className={metricPages === 1 ? 'single-page' : undefined}><Button size="sm" variant="outline" disabled={safeMetricPage === 0} onClick={() => setMetricPage(safeMetricPage - 1)} aria-label="Previous benchmarks"><span className="pagination-full">Previous benchmarks</span><span className="pagination-short" aria-hidden="true">←</span></Button><span>Benchmarks {metrics.length ? safeMetricPage * 50 + 1 : 0}–{Math.min((safeMetricPage + 1) * 50, metrics.length)} of {metrics.length}{hideEmpty && ` · ${benchmarks.length - metrics.length} empty hidden`}</span><Button size="sm" variant="outline" disabled={safeMetricPage + 1 >= metricPages} onClick={() => setMetricPage(safeMetricPage + 1)} aria-label="Next benchmarks"><span className="pagination-full">Next benchmarks</span><span className="pagination-short" aria-hidden="true">→</span></Button></nav>
    </div>
    <Table containerClassName="transposed-scroll" className="benchmark-table transposed-table" aria-label="Benchmark results, benchmarks in rows" style={{ minWidth: BENCHMARK_LABEL_WIDTH + COMPACT_MODEL_WIDTH * models.length, '--mobile-columns': models.length } as CSSProperties}>
      <TableHeader><TableRow><TableHead className="sticky-model-head">Benchmark & metric</TableHead>{models.map(row => <TableHead key={row.id} aria-label={`${row.model.name}, ${row.configuration.reasoning_label ?? row.lab.name}`}>{renderModel(row.id)}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{shownMetrics.map(benchmark => <TableRow key={benchmark.id}><TableCell className="sticky-model-cell"><button className="header-button" onClick={() => onSort(benchmark)} title={`Sort model columns by this benchmark · ${benchmark.version} · ${benchmark.subset ?? benchmark.metric_name} · ${benchmark.direction} is better`}><div className="bench-heading"><span>{benchmark.name}</span><small>{benchmark.version !== 'unversioned-as-reported' && benchmark.version.length < 20 && <>{benchmark.version} · </>}{benchmark.unit} · <span aria-label={`${benchmark.direction} is better`}>{benchmark.direction === 'higher' ? '↑' : '↓'} better</span>{benchmark.subset && <span className="benchmark-subset">{benchmark.subset}</span>}</small></div>{sort?.id === benchmark.id ? (sort.direction === 'desc' ? <ArrowDown/> : <ArrowUp/>) : <ArrowDownUp className="sort-idle"/>}</button><a className="benchmark-detail-link" aria-label={`About ${benchmark.name}`} href={routeHref(`/benchmarks/${encodeURIComponent(benchmark.id)}`)}>About benchmark</a></TableCell>{models.map(row => <TableCell key={row.id}>{renderScore(row, benchmark)}</TableCell>)}</TableRow>)}{marketIds.map(id => <TableRow key={id}><TableCell className="sticky-model-cell">{id === 'price' ? 'API price ranges by route' : 'OpenRouter public token volume'}</TableCell>{models.map(row => <TableCell key={row.id}>{renderMarket(row.id, id)}</TableCell>)}</TableRow>)}</TableBody>
    </Table>
    {!metrics.length && !marketIds.length && <p className="empty-state">No benchmarks have results for the models on this page. Change model pages or turn off the empty-row filter.</p>}
  </>;
}
