import { numeric, presetIncludesAllModels, rowsForView, type DisplayRow } from './selectors';
import type { AppData } from './snapshots';
import type { ViewState } from '../state/viewState';

/** Applies the full view on the worker, including TanStack-equivalent null-last sorting. */
export function queryRows(data: AppData, view: ViewState, expandedIds: Set<string>): DisplayRow[] {
  const rows = rowsForView(data, view, expandedIds);
  const sort = view.sort;
  if (!sort) {
    const newestFirst = !view.compare && presetIncludesAllModels(data, view.presetId);
    return rows.sort((a, b) => {
      // ISO release dates sort chronologically; absent dates belong after known releases.
      const releaseOrder = newestFirst ? (b.model.release_date ?? '').localeCompare(a.model.release_date ?? '') : 0;
      return releaseOrder || a.lab.name.localeCompare(b.lab.name) || a.model.name.localeCompare(b.model.name) || (a.configuration.reasoning_label ?? '').localeCompare(b.configuration.reasoning_label ?? '');
    });
  }
  const valueFor = (row: DisplayRow): string | number | null => {
    if (sort.id === 'model') return `${row.lab.name} ${row.model.name}`;
    if (sort.id === 'price') return row.prices.length === 1 ? numeric(row.prices[0].input_price) : null;
    if (sort.id === 'usage') return row.usage[0]?.total ?? null;
    const cell = row.observations.get(sort.id);
    return !cell || cell.state === 'disputed' ? null : cell.value;
  };
  const direction = sort.direction === 'desc' ? -1 : 1;
  return rows.sort((left, right) => {
    const a = valueFor(left); const b = valueFor(right);
    if (a === null || a === undefined) return b === null || b === undefined ? 0 : 1;
    if (b === null || b === undefined) return -1;
    const compared = typeof a === 'number' && typeof b === 'number' ? a - b : String(a).localeCompare(String(b));
    return compared * direction;
  });
}
