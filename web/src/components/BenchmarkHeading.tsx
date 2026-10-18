import { ArrowDown, ArrowDownUp, ArrowUp } from 'lucide-react';
import type { BenchmarkVariant } from '../generated/dataset';
import { routeHref } from '../state/stateRuntime';
import { HeaderTooltip } from './HeaderTooltip';

/** A linked name and a separate sort control, shared by both matrix orientations. */
export function BenchmarkHeading({ benchmark, direction, onSort }: {
  benchmark: BenchmarkVariant;
  direction: 'asc' | 'desc' | false;
  onSort: () => void;
}) {
  const version = benchmark.version !== 'unversioned-as-reported'
    && !benchmark.name.toLowerCase().includes(benchmark.version.toLowerCase()) ? benchmark.version : '';
  const details = [benchmark.name, version, benchmark.metric_name, benchmark.unit,
    `${benchmark.direction} is better`, benchmark.subset, benchmark.split].filter(Boolean).join(' · ');
  return <HeaderTooltip text={details}><div className="benchmark-heading-compact">
    <a className="benchmark-detail-link" href={routeHref(`/benchmarks/${encodeURIComponent(benchmark.id)}`)}>
      <span>{benchmark.name}{version && version.length < 20 ? ` ${version}` : ''}</span>
      {benchmark.subset && <small className="benchmark-variant-label">{benchmark.subset}</small>}
    </a>
    <button className="benchmark-sort" aria-label={`Sort by ${benchmark.name}`}
      title={`Sort by ${benchmark.name} · ${benchmark.direction} is better`} onClick={onSort}>
      {direction === 'desc' ? <ArrowDown/> : direction === 'asc' ? <ArrowUp/> : <ArrowDownUp className="sort-idle"/>}
    </button>
  </div></HeaderTooltip>;
}
