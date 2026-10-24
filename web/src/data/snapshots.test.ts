import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { clearSnapshotCache, loadSnapshots, loadEvidence, type AppData } from './snapshots';
import { rowsForView } from './selectors';
import { DEFAULT_VIEW } from '../state/viewState';
import comparisonText from '../../public/data/comparison.json?raw';
const comparison = JSON.parse(comparisonText);
import detailsText from '../../public/data/details.json?raw';
const details = JSON.parse(detailsText);
import catalogText from '../../public/data/catalog.json?raw';
const catalog = JSON.parse(catalogText);
import resultsText from '../../public/data/results.json?raw';
const results = JSON.parse(resultsText);
import marketText from '../../public/data/market.json?raw';
const market = JSON.parse(marketText);
import manifestText from '../../public/data/manifest.json?raw';
const manifest = JSON.parse(manifestText);
beforeEach(() => { clearSnapshotCache(); });
afterEach(() => { vi.unstubAllGlobals(); });
const response = (value: unknown) => ({ ok: true, json: async () => value });
it('deduplicates startup and lazy evidence loads across navigation', async () => {
  const fetcher = vi.fn(async (url: string) => response(url.endsWith('comparison.json') ? comparison : details));
  vi.stubGlobal('fetch', fetcher);
  const [a,b] = await Promise.all([loadSnapshots('/test/'),loadSnapshots('/test/')]);
  expect(a).toBe(b); expect(fetcher).toHaveBeenCalledTimes(1);
  expect(a.details.sources).toEqual([]);
  const [full,again] = await Promise.all([loadEvidence(a),loadEvidence(a)]);
  expect(full).toBe(again); expect(full.details).toEqual(details);
  expect(fetcher).toHaveBeenLastCalledWith(`/test/data/${comparison.evidence_file}`);
  expect(fetcher).toHaveBeenCalledTimes(2);
  expect(await loadSnapshots('/test/')).toBe(a);
});
it('allows retry after failed startup or evidence requests', async () => {
  const fetcher = vi.fn().mockResolvedValueOnce({ok:false,status:503}).mockResolvedValueOnce(response(comparison))
    .mockResolvedValueOnce({ok:false,status:503}).mockResolvedValueOnce(response(details));
  vi.stubGlobal('fetch',fetcher);
  await expect(loadSnapshots('/retry/')).rejects.toThrow('503');
  const data = await loadSnapshots('/retry/');
  await expect(loadEvidence(data)).rejects.toThrow('503');
  expect((await loadEvidence(data)).details).toEqual(details);
});
it('compact data preserves every preset and evidence-sensitive filter result', async () => {
  vi.stubGlobal('fetch',vi.fn(async () => response(comparison)));
  const compact = await loadSnapshots('/parity/');
  const full = {catalog,results,details,market,manifest} as unknown as AppData;
  const filters = [{}, {comparableOnly:true}, {independentOnly:true}, {providerReportedAllowed:false}, {incompleteSetupAllowed:false}];
  for (const preset of full.catalog.presets) for (const filter of filters) {
    const view = {...structuredClone(DEFAULT_VIEW),presetId:preset.id,visibleColumnIds:preset.benchmark_ids ?? [],filters:{...DEFAULT_VIEW.filters,...filter}};
    const summarize = (data: AppData) => rowsForView(data,view,new Set()).map(row => ({id:row.id,count:row.reviewedCount,cells:[...row.observations]}));
    expect(summarize(compact)).toEqual(summarize(full));
  }
});

it('includes exact published report values and units before downloading evidence', () => {
  const records = new Map(comparison.observations.map((record: { id: string; value: number; unit: string }) => [record.id, record]));
  for (const report of details.observations) {
    expect(records.get(report.id)).toMatchObject({ value: report.value, unit: report.unit });
  }
});


it('loads route performance only with content-addressed evidence and keeps startup immutable', async () => {
  const fetcher = vi.fn(async (url: string) => response(url.endsWith('comparison.json') ? comparison : { ...details, route_performance: market.performance }));
  vi.stubGlobal('fetch', fetcher);
  const data = await loadSnapshots('/performance/');
  expect(data.market.performance).toEqual([]);
  expect(fetcher).toHaveBeenCalledTimes(1);
  const full = await loadEvidence(data);
  expect(full.market.performance).toEqual(market.performance);
  expect(full.market.performance.length).toBeGreaterThan(0);
  expect(data.market.performance).toEqual([]);
  expect(full.details).toEqual(details);
});
