import { useEffect, useMemo, useState } from 'react';
import { loadFullSnapshots, type FullAppData as AppData } from '../data/snapshots';
import { coverageIndex } from '../data/coverage';
import { useCatalogState } from '../state/catalogState';
import { DEFAULT_VIEW } from '../state/viewState';
import { routeHref, viewUrl } from '../state/stateRuntime';
import { ModelIdentity } from './ModelIdentity';
import { DirectoryNav } from './DirectoryNav';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from './ui/select';
export type CatalogKind = 'models' | 'benchmarks' | 'evidence';
export default function CatalogPage({ kind }: { kind: CatalogKind }) {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => { let active = true; loadFullSnapshots().then(d => { if (active) setData(d); }).catch(() => { if (active) setError(true); }); return () => { active = false; }; }, []);
  useEffect(() => { document.title = `${kind === 'evidence' ? 'Coverage & evidence' : kind[0].toUpperCase() + kind.slice(1)} · All the Benches`; return () => { document.title = 'All the Benches · Model evaluations'; }; }, [kind]);
  return <main className="entity-page catalog-page"><DirectoryNav active={kind}/>{error ? <p role="alert">Could not load the catalog. Reload to retry.</p> : data ? <CatalogContent key={kind} data={data} kind={kind}/> : <p role="status">Loading catalog…</p>}</main>;
}
function CatalogContent({ data, kind }: { data: AppData; kind: CatalogKind }) {
  const { query, filter, order, page, update } = useCatalogState(kind);
  useEffect(() => { window.scrollTo(0, 0); }, [page]);
  const coverage = useMemo(() => coverageIndex(data), [data]);
  const labs = new Map(data.catalog.labs.map(l => [l.id, l]));
  const models = kind === 'models';
  const categories = [...new Set(data.catalog.benchmarks.map(b => b.category))].sort();
  const entries = models ? data.catalog.models.filter(m => (filter === 'all' || m.lab_ids.includes(filter)) && `${m.name} ${m.lab_ids.map(id => labs.get(id)?.name).join(' ')}`.toLowerCase().includes(query.toLowerCase())).map(m => ({ id: m.id, name: m.name, date: m.release_date ?? '', count: coverage.models.get(m.id)?.size ?? 0, model: m, benchmark: undefined })) : data.catalog.benchmarks.filter(b => (filter === 'all' || b.category === filter) && `${b.name} ${b.version} ${b.family_id} ${b.metric_name}`.toLowerCase().includes(query.toLowerCase())).map(b => ({ id: b.id, name: b.name, date: '', count: coverage.benchmarks.get(b.id)?.size ?? 0, model: undefined, benchmark: b }));
  entries.sort((a, b) => (order === 'coverage' ? b.count - a.count : order === 'recent' ? b.date.localeCompare(a.date) : 0) || a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
  const pages = Math.max(1, Math.ceil(entries.length / 24));
  const currentPage = Math.min(page, pages - 1);
  const allPreset = data.catalog.presets.find(p => p.id.startsWith('all_models'));
  if (kind === 'evidence') return <Evidence data={data} coverage={coverage}/>;
  return <>
    <header className="catalog-heading"><h1>{models ? 'Models' : 'Benchmark variants'}</h1><p>{models ? 'Find a release, inspect its evidence, then compare exact reasoning configurations.' : 'Find the exact version and metric. Coverage counts describe this snapshot, not the whole field.'}</p></header>
    <div className="catalog-tools"><Input type="search" aria-label="Search catalog" placeholder={models ? 'Search models or labs…' : 'Search benchmarks, families or versions…'} value={query} onChange={e => { update({ query: e.target.value, page: 0 }); }}/><Select value={filter} onValueChange={v => { update({ filter: v, page: 0 }); }}><SelectTrigger aria-label={models ? 'Filter by lab' : 'Filter by category'}><SelectValue/></SelectTrigger><SelectContent><SelectItem value="all">{models ? 'All labs' : 'All categories'}</SelectItem>{(models ? data.catalog.labs.map(l => ({ id: l.id, name: l.name })) : categories.map(c => ({ id: c, name: c }))).map(x => <SelectItem value={x.id} key={x.id}>{x.name}</SelectItem>)}</SelectContent></Select><Select value={order} onValueChange={v => { update({ order: v, page: 0 }); }}><SelectTrigger aria-label="Sort catalog"><SelectValue/></SelectTrigger><SelectContent><SelectItem value="coverage">Most coverage</SelectItem><SelectItem value="name">Name A–Z</SelectItem>{models && <SelectItem value="recent">Newest release</SelectItem>}</SelectContent></Select></div>
    <p className="catalog-count" role="status">{entries.length} {models ? 'releases' : 'variants'} · Coverage counts unique {models ? 'benchmark variants' : 'model releases'} with numeric, undisputed results.</p>
    <div className="catalog-grid">{entries.slice(currentPage * 24, (currentPage + 1) * 24).map(entry => {
      const m = entry.model; const b = entry.benchmark;
      const view = { ...structuredClone(DEFAULT_VIEW), presetId: allPreset?.id ?? DEFAULT_VIEW.presetId, visibleColumnIds: b ? [b.id] : [...(coverage.models.get(entry.id) ?? [])], filters: { ...structuredClone(DEFAULT_VIEW.filters) } };
      if (m) { view.compare = true; view.selectedConfigurationIds = data.catalog.configurations.filter(c => c.model_id === m.id).map(c => c.id); }
      return <article className="catalog-card" key={entry.id}><h2><a href={routeHref(`/${kind}/${encodeURIComponent(entry.id)}`)}>{m ? <ModelIdentity name={m.name} labId={m.lab_ids[0]} labName={labs.get(m.lab_ids[0])?.name}/> : entry.name}</a></h2><p>{m ? `${m.lab_ids.map(id => labs.get(id)?.name ?? id).join(' · ')} · ${m.release_date ?? 'Release date unknown'}` : `${b!.category} · ${b!.version === 'unversioned-as-reported' ? 'Version not specified' : b!.version}`}</p><p>{m ? `${m.access_state ?? 'Access unknown'} · weights ${m.weights_state ?? 'unknown'}` : `${b!.metric_name} · ${b!.unit} · ${b!.direction} is better`}</p>{b?.subset && <p>{b.subset}</p>}<div className="catalog-card-bottom"><span><strong>{entry.count}</strong> {models ? 'variants scored' : `of ${data.catalog.models.length} releases scored`}</span><a href={viewUrl(view).toString()}>Open matrix →</a></div></article>;
    })}</div>
    {!entries.length && <div className="catalog-empty"><p>No matches. Try a broader search or reset the filters.</p><Button variant="outline" onClick={() => { update({ query: '', filter: 'all', page: 0 }); }}>Reset filters</Button></div>}
    {pages > 1 && <nav className="entity-pagination" aria-label="Catalog pages"><Button variant="outline" disabled={currentPage === 0} onClick={() => update({ page: currentPage - 1 }, true)}>Previous</Button><span>{currentPage + 1} / {pages}</span><Button variant="outline" disabled={currentPage + 1 >= pages} onClick={() => update({ page: currentPage + 1 }, true)}>Next</Button></nav>}
    <p className="entity-footer">Snapshot generated {data.manifest.generated_at?.slice(0,10) ?? 'Unknown'} · <a href={routeHref('/evidence')}>Coverage, sources & limitations</a></p>
  </>;
}
function Evidence({ data, coverage }: { data: AppData; coverage: ReturnType<typeof coverageIndex> }) {
  const records = data.details.observations.filter(o => coverage.observations.has(o.id));
  const relationships = new Map<string, number>();
  for (const record of records) relationships.set(record.reporting_relationship, (relationships.get(record.reporting_relationship) ?? 0) + 1);
  const sources = new Map(data.details.sources.map(s => [s.id, s]));
  return <>
    <header className="catalog-heading"><h1>Coverage & evidence</h1><p>A published snapshot of reported evaluations. Missing scores are unknown, not zero.</p></header>
    <dl className="entity-facts"><div><dt>Model releases</dt><dd>{data.catalog.models.length}</dd></div><div><dt>Benchmark variants</dt><dd>{data.catalog.benchmarks.length}</dd></div><div><dt>Published observations</dt><dd>{records.length}</dd></div><div><dt>Snapshot generated</dt><dd>{data.manifest.generated_at?.slice(0,10) ?? 'Unknown'}</dd></div></dl>
    <section className="evidence-section"><h2>Read a comparison correctly</h2><ul><li>Each model configuration keeps its reasoning setting and evaluation setup. A release can have several configurations.</li><li>Versions, metrics, splits and harnesses can change the meaning of a score. Matching benchmark names alone does not establish comparability.</li><li>Color and bold scores describe the selected comparison set, including other pages, not statistical significance or a universal model ranking. Open a score to inspect its source and setup.</li><li>Provider reports, evaluator measurements, quoted results and reproductions are labeled separately. “Reviewed” means curated evidence, not an independently rerun evaluation.</li><li>Disputed reports remain available in evidence panels. Unknown or missing values never become zero; historical and saturated variants remain available.</li></ul><a href="https://github.com/katagun/allthebenches/blob/main/docs/DATA_MODEL.md" target="_blank" rel="noreferrer">Data contract and review rules ↗</a></section>
    <section className="evidence-section"><h2>Where the results come from</h2><div className="evidence-breakdown">{[...relationships].map(([key, count]) => <div key={key}><strong>{count}</strong><span>{key.replaceAll('_', ' ')}</span></div>)}</div><p>Counts include published conflicting observations. Catalog coverage counts exclude disputed scores and deduplicate releases and variants.</p></section>
    <section className="evidence-section"><h2>Known collection gaps ({data.catalog.coverage_gaps.length})</h2><p>These are curation notes, not claims that a result does not exist elsewhere.</p><div className="gap-list">{data.catalog.coverage_gaps.map(gap => <details key={gap.id}><summary>{gap.scope}</summary><p>{gap.reason}</p>{(gap.source_ids ?? []).map(id => { const source = sources.get(id); return source && <a key={id} href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a>; })}</details>)}</div></section>
    <section className="evidence-section"><h2>Reproduce or correct this snapshot</h2><p>Snapshot <code>{data.manifest.snapshot_id}</code>. Source claims and dates are preserved in the downloadable data. Feed fetch dates are not the dates of every benchmark result.</p><div className="directory-nav">{['catalog','results','details','market','manifest'].map(name => <a key={name} href={`${import.meta.env.BASE_URL}data/${name}.json`} download>{name}.json ↓</a>)}</div><p><a href="https://github.com/katagun/allthebenches/issues/new?title=Data%20correction&amp;body=Model%20or%20benchmark%3A%0ASource%20URL%3A%0AExact%20configuration%20and%20score%3A%0A" target="_blank" rel="noreferrer">Suggest a correction or missing source ↗</a> · <a href="https://github.com/katagun/allthebenches/blob/main/CONTRIBUTING.md" target="_blank" rel="noreferrer">Contributing guide ↗</a></p></section>
  </>;
}
