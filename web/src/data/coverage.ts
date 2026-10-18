import type { AppData } from './snapshots';
/** Count distinct published coverage, never unreviewed candidate observations. */
export function coverageIndex(data: AppData) {
  const configModels = new Map(data.catalog.configurations.map(c => [c.id, c.model_id]));
  const models = new Map<string, Set<string>>();
  const benchmarks = new Map<string, Set<string>>();
  const observations = new Set<string>();
  for (const cell of data.results.cells) {
    for (const id of cell.observation_ids) observations.add(id);
    if (cell.value == null || cell.state === 'disputed') continue;
    const model = configModels.get(cell.configuration_id);
    if (!model) continue;
    if (!models.has(model)) models.set(model, new Set());
    if (!benchmarks.has(cell.benchmark_id)) benchmarks.set(cell.benchmark_id, new Set());
    models.get(model)!.add(cell.benchmark_id);
    benchmarks.get(cell.benchmark_id)!.add(model);
  }
  return { models, benchmarks, observations };
}
