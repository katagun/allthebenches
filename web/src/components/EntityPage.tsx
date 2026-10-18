import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { loadSnapshots, type AppData } from '../data/snapshots';
import { DEFAULT_VIEW, encodeViewState } from '../state/viewState';
import { ModelIdentity } from './ModelIdentity';
import { Button } from './ui/button';
import { Input } from './ui/input';

export type EntityRoute = { kind: 'models' | 'benchmarks'; id: string };
const versionLabel = (version?: string) => version === 'unversioned-as-reported' ? 'Version not specified' : version ?? 'Version unknown';
export const entityHref = (kind: EntityRoute['kind'], id: string) => `#/${kind}/${encodeURIComponent(id)}`;

export default function EntityPage({ route }: { route: EntityRoute | null }) {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => { let active = true; loadSnapshots().then(value => { if (active) setData(value); }).catch(() => { if (active) setError(true); }); return () => { active = false; }; }, []);
  return <main className="entity-page"><a className="entity-back" href="#"><ArrowLeft size={16}/>Back to comparison matrix</a>{error ? <><h1>Unable to load this page</h1><p>The published dataset could not be loaded. Reload to try again.</p></> : !data ? <p role="status">Loading details…</p> : <EntityContent data={data} route={route}/>}</main>;
}

function EntityContent({ data, route }: { data: AppData; route: EntityRoute | null }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const model = route?.kind === 'models' ? data.catalog.models.find(item => item.id === route.id) : undefined;
  const benchmark = route?.kind === 'benchmarks' ? data.catalog.benchmarks.find(item => item.id === route.id) : undefined;
  const title = model?.name ?? benchmark?.name ?? 'Page not found';
  useEffect(() => { document.title = `${title} · All the Benches`; return () => { document.title = 'All the Benches · Model evaluations'; }; }, [title]);
  const configs = useMemo(() => new Map(data.catalog.configurations.map(item => [item.id, item])), [data]);
  const models = useMemo(() => new Map(data.catalog.models.map(item => [item.id, item])), [data]);
  const benchmarks = useMemo(() => new Map(data.catalog.benchmarks.map(item => [item.id, item])), [data]);
  const sources = useMemo(() => new Map(data.details.sources.map(item => [item.id, item])), [data]);
  // Use only observations backing published cells, retaining conflicting reports individually.
  const records = useMemo(() => {
    const ids = new Set(data.results.cells.filter(cell => model ? configs.get(cell.configuration_id)?.model_id === model.id : benchmark && cell.benchmark_id === benchmark.id).flatMap(cell => cell.observation_ids));
    return data.details.observations.filter(item => ids.has(item.id));
  }, [data, configs, model, benchmark]);
  const matching = records.filter(item => `${models.get(configs.get(item.configuration_id)?.model_id ?? '')?.name} ${benchmarks.get(item.benchmark_id)?.name} ${configs.get(item.configuration_id)?.reasoning_label ?? ''}`.toLowerCase().includes(query.toLowerCase()));
  const pages = Math.max(1, Math.ceil(matching.length / 25));
  const currentPage = Math.min(page, pages - 1);
  const sourceIds = [...new Set([...(model?.source_ids ?? []), ...data.details.metadata_claims.filter(claim => claim.entity_id === model?.id).flatMap(claim => claim.source_ids ?? []), ...records.map(item => item.source_id)])];
  const labs = data.catalog.labs.filter(lab => model?.lab_ids.includes(lab.id));
  const allPreset = data.catalog.presets.find(preset => data.catalog.models.every(item => preset.model_configuration_ids?.some(id => configs.get(id)?.model_id === item.id)));
  const primaryConfiguration = model ? data.catalog.configurations.filter(config => config.model_id === model.id).sort((a, b) => records.filter(record => record.configuration_id === b.id).length - records.filter(record => record.configuration_id === a.id).length)[0] : undefined;
  const disputed = new Set(data.results.cells.filter(cell => cell.state === 'disputed').flatMap(cell => cell.observation_ids));
  const matrixView = { ...structuredClone(DEFAULT_VIEW), presetId: allPreset?.id ?? DEFAULT_VIEW.presetId, selectedConfigurationIds: primaryConfiguration ? [primaryConfiguration.id] : [], compare: !!primaryConfiguration, includeUnbenchmarked: true, visibleColumnIds: model ? [...new Set(records.map(item => item.benchmark_id))] : benchmark ? [benchmark.id] : [], orientation: 'benchmarks-rows' as const };
  if (!model && !benchmark) return <><h1>Page not found</h1><p>This model or benchmark is not in the current snapshot.</p></>;
  return <>
    <header className="entity-heading"><span className="entity-kind">{model ? 'Model release' : 'Benchmark variant'}</span><h1>{model ? <ModelIdentity name={title} labId={labs[0]?.id} labName={labs[0]?.name}/> : title}</h1><p>{model ? `${labs.map(lab => lab.name).join(' · ')} · ${model.release_date ?? 'Release date unknown'}` : `${benchmark!.category} · ${versionLabel(benchmark!.version)} · ${benchmark!.metric_name}`}</p><a className="entity-matrix-link" href={`${import.meta.env.BASE_URL}?v=${encodeURIComponent(encodeViewState(matrixView))}`}>View {model ? 'this model' : 'this benchmark'} in the matrix →</a></header>
    <dl className="entity-facts">{model ? <><div><dt>Access</dt><dd>{model.access_state ?? 'Unknown'}</dd></div><div><dt>Weights</dt><dd>{model.weights_state ?? 'Unknown'}</dd></div><div><dt>Modalities</dt><dd>{model.modalities?.join(', ') || 'Unknown'}</dd></div></> : <><div><dt>Metric</dt><dd>{benchmark!.metric_name} ({benchmark!.unit})</dd></div><div><dt>Direction</dt><dd>{benchmark!.direction} is better</dd></div><div><dt>Subset / split</dt><dd>{[benchmark!.subset, benchmark!.split].filter(Boolean).join(' · ') || 'Not specified'}</dd></div></>}<div><dt>Published observations</dt><dd>{records.length}</dd></div></dl>
    {benchmark?.documentation_url && <a className="entity-documentation" href={benchmark.documentation_url} target="_blank" rel="noreferrer">Official benchmark documentation <ExternalLink size={14}/></a>}
    <section aria-labelledby="entity-scores"><div className="entity-section-heading"><h2 id="entity-scores">Scores</h2><Input aria-label="Search scores" type="search" placeholder={model ? 'Find a benchmark…' : 'Find a model…'} value={query} onChange={event => { setQuery(event.target.value); setPage(0); }}/></div><p className="entity-note">Each published observation keeps its exact configuration and source. Reports may use different evaluation setups; missing results are not zero.</p>
      <div className="entity-scores">{matching.slice(currentPage * 25, (currentPage + 1) * 25).map(record => { const config = configs.get(record.configuration_id); const release = models.get(config?.model_id ?? ''); const metric = benchmarks.get(record.benchmark_id); const source = sources.get(record.source_id); const series = data.details.series.find(item => item.id === record.series_id); return <article className="entity-score" key={record.id}>
        <div className="entity-score-title"><a href={entityHref(model ? 'benchmarks' : 'models', model ? record.benchmark_id : config?.model_id ?? '')}>{model ? metric?.name : <ModelIdentity name={release?.name ?? 'Unknown model'} labId={release?.lab_ids[0]} labName={data.catalog.labs.find(lab => lab.id === release?.lab_ids[0])?.name}/>}</a><strong>{record.value.toLocaleString(undefined, { maximumFractionDigits: 20 })} <small>{record.unit}</small></strong></div>
        {disputed.has(record.id) && <p className="entity-disputed">Disputed result — conflicting evidence retained</p>}<p>{config?.reasoning_label ?? config?.mode ?? 'Unknown reasoning'}{model && ` · ${versionLabel(metric?.version)}`}</p>
        {source && <a className="entity-source-link" href={source.url} target="_blank" rel="noreferrer">{source.title} <ExternalLink size={12}/></a>}
        <details><summary>Evidence & evaluation setup</summary><dl><div><dt>Evaluator</dt><dd>{record.evaluator} · {record.reporting_relationship.replaceAll('_', ' ')}</dd></div><div><dt>Review status</dt><dd>{record.review_state ?? 'Not specified'}</dd></div><div><dt>Reported / evaluated</dt><dd>{record.reported_at ?? 'Unknown'} / {record.evaluated_at ?? 'Unknown'}</dd></div><div><dt>Source locator</dt><dd>{record.locator || 'Not specified'}</dd></div><div><dt>Protocol</dt><dd>{series?.protocol ?? 'Not specified'} · {series?.comparability_status ?? 'Comparability unknown'}</dd></div>{Object.entries(record.setup ?? {}).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{typeof value === 'string' ? value : JSON.stringify(value)}</dd></div>)}</dl></details>
      </article>; })}</div>{matching.length === 0 && <p>{records.length ? 'No scores match your search.' : 'No published scores are available for this entry in the current snapshot.'}</p>}
      {pages > 1 && <nav className="entity-pagination" aria-label="Score pages"><Button variant="outline" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</Button><span>{currentPage + 1} / {pages}</span><Button variant="outline" disabled={currentPage + 1 === pages} onClick={() => setPage(currentPage + 1)}>Next</Button></nav>}
    </section>
    {model && <details className="entity-metadata"><summary>Model metadata & serving routes</summary><dl className="entity-facts"><div><dt>Version</dt><dd>{model.version ?? 'Not specified'}</dd></div><div><dt>Developer headquarters</dt><dd>{labs.flatMap(lab => lab.hq_country_codes ?? []).join(', ') || 'Unknown'}</dd></div><div><dt>Configurations</dt><dd>{data.catalog.configurations.filter(config => config.model_id === model.id).map(config => config.reasoning_label ?? config.mode ?? 'Unknown').join(' · ')}</dd></div></dl><h3>Size claims</h3>{data.details.metadata_claims.filter(claim => claim.entity_id === model.id && claim.field.includes('parameter')).map(claim => <p key={claim.id}>{claim.field}: {JSON.stringify(claim.value)} {claim.unit} · {claim.basis.replaceAll('_', ' ')} · {claim.confidence_rationale}</p>)}<p>Only recorded claims are shown; an absent size is unknown.</p><h3>Serving routes</h3>{data.market.routes.filter(route => route.model_id === model.id).map(route => <div key={route.id}><strong>{route.provider}</strong> · {route.availability} · {route.quantization ?? 'Quantization unknown'}{data.market.prices.filter(price => price.route_id === route.id).map(price => <p key={price.id}>Input {price.input_price ?? 'unknown'} / output {price.output_price ?? 'unknown'} {price.currency} {price.price_unit} · {price.observed_at} <a href={sources.get(price.source_id)?.url}>Source</a></p>)}</div>)}</details>}
    <section className="entity-sources"><h2>Sources</h2>{sourceIds.length === 0 ? <p>No source records are attached.</p> : <ul>{sourceIds.map(id => { const source = sources.get(id); return source && <li key={id}><a href={source.url} target="_blank" rel="noreferrer">{source.title} <ExternalLink size={12}/></a><small>{source.publisher}{source.attribution ? ` · ${source.attribution}` : ''}</small></li>; })}</ul>}</section>
    <footer className="entity-footer">Snapshot {data.manifest.snapshot_id} · <a href="#">Back to comparison matrix</a></footer>
  </>;
}
