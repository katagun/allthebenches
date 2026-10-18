import { expect, it } from 'vitest';
import { coverageIndex } from './coverage';
import type { AppData } from './snapshots';
it('deduplicates release coverage and excludes disputed or missing scores', () => {
  const data = { catalog: { configurations: [{ id: 'a', model_id: 'm' }, { id: 'b', model_id: 'm' }] }, results: { cells: [
    { configuration_id: 'a', benchmark_id: 'x', value: 0, state: 'selected', observation_ids: ['one'] },
    { configuration_id: 'b', benchmark_id: 'x', value: 5, state: 'selected', observation_ids: ['two'] },
    { configuration_id: 'a', benchmark_id: 'y', value: 6, state: 'disputed', observation_ids: ['conflict'] },
    { configuration_id: 'a', benchmark_id: 'z', value: null, state: 'missing', observation_ids: [] },
  ] } } as unknown as AppData;
  const index = coverageIndex(data);
  expect([...index.models.get('m')!]).toEqual(['x']);
  expect([...index.benchmarks.get('x')!]).toEqual(['m']);
  expect(index.observations.size).toBe(3);
});
