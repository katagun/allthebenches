import type { CatalogSnapshot, DetailsSnapshot, ManifestSnapshot, MarketSnapshot, Observation, ResultsSnapshot } from '../generated/dataset';
export type ObservationIndex = Pick<Observation, 'id' | 'configuration_id' | 'benchmark_id' | 'series_id' | 'review_state' | 'reporting_relationship' | 'setup'>;
export type AppData = { catalog: CatalogSnapshot; results: Omit<ResultsSnapshot, 'observations'> & { observations: ObservationIndex[] }; details: Omit<DetailsSnapshot, 'observations'> & { observations: ObservationIndex[] }; market: MarketSnapshot; manifest: ManifestSnapshot };
export type FullAppData = Omit<AppData, 'details' | 'results'> & { details: DetailsSnapshot; results: ResultsSnapshot };
type ComparisonPayload = Pick<AppData, 'catalog' | 'market' | 'manifest'> & { cells: ResultsSnapshot['cells']; observations: ObservationIndex[]; series: DetailsSnapshot['series']; evidence_file: string };
const pending = new Map<string, Promise<AppData>>();
const fullPending = new WeakMap<AppData, Promise<FullAppData>>();
const evidenceUrls = new WeakMap<AppData, string>();
async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load published data (${response.status})`);
  return response.json() as Promise<T>;
}
/** Reuse one immutable snapshot across StrictMode mounts and client-side navigation. */
export function loadSnapshots(base = import.meta.env.BASE_URL): Promise<AppData> {
  const root = `${base.endsWith('/') ? base : `${base}/`}data/`;
  const cached = pending.get(root);
  if (cached) return cached;
  const request = readJson<ComparisonPayload>(`${root}comparison.json`).then(payload => {
    const schema_version = payload.manifest.schema_version;
    const data: AppData = { catalog: payload.catalog, market: payload.market, manifest: payload.manifest,
      results: { schema_version, cells: payload.cells, observations: payload.observations.filter(record => record.review_state === 'reviewed') },
      details: { schema_version, observations: payload.observations, series: payload.series, sources: [], external_mappings: [], metadata_claims: payload.catalog.metadata_claims } };
    evidenceUrls.set(data, `${root}${payload.evidence_file}`);
    return data;
  }).catch(error => { pending.delete(root); throw error; });
  pending.set(root, request);
  return request;
}
/** Evidence never blocks the matrix. Content-addressing prevents mixing snapshot versions. */
export function loadEvidence(data: AppData): Promise<FullAppData> {
  const url = evidenceUrls.get(data);
  if (!url) return Promise.reject(new Error('Evidence location is unavailable. Reload the snapshot.'));
  const cached = fullPending.get(data);
  if (cached) return cached;
  const request = readJson<DetailsSnapshot>(url).then(details => ({ ...data, details,
    results: { ...data.results, observations: details.observations.filter(record => record.review_state === 'reviewed') },
  })).catch(error => { fullPending.delete(data); throw error; });
  fullPending.set(data, request);
  return request;
}
export async function loadFullSnapshots(base = import.meta.env.BASE_URL): Promise<FullAppData> {
  return loadEvidence(await loadSnapshots(base));
}

export function clearSnapshotCache(): void { pending.clear(); }
