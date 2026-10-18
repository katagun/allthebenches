import type { AppData } from '../data/snapshots';
export function comparisonFixture(input: unknown) {
  const data = input as AppData;
  return { catalog: data.catalog, market: data.market, manifest: data.manifest,
    cells: data.results.cells, observations: data.details.observations, series: data.details.series, evidence_file: 'evidence-test.json' };
}
