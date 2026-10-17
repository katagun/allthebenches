import type { CatalogSnapshot, DetailsSnapshot, ManifestSnapshot, MarketSnapshot, ResultsSnapshot } from '../generated/dataset';
export type AppData = { catalog: CatalogSnapshot; results: ResultsSnapshot; details: DetailsSnapshot; market: MarketSnapshot; manifest: ManifestSnapshot };
export async function loadSnapshots(base = import.meta.env.BASE_URL): Promise<AppData> {
  const root = `${base.endsWith('/') ? base : `${base}/`}data/`;
  const names = ['catalog', 'results', 'details', 'market', 'manifest'] as const;
  const responses = await Promise.all(names.map(name => fetch(`${root}${name}.json`)));
  const failed = responses.findIndex(response => !response.ok);
  if (failed >= 0) throw new Error(`Could not load ${names[failed]} data (${responses[failed].status})`);
  const [catalog, results, details, market, manifest] = await Promise.all(responses.map(response => response.json()));
  return { catalog, results, details, market, manifest } as AppData;
}
