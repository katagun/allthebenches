import type { DisplayRow } from './selectors';

export type ScoreRange = { min: number; max: number };
/** Only cells displaying a single finite score participate; zero is valid. */
export function scoreRanges(rows: DisplayRow[]): Map<string, ScoreRange> {
  const ranges = new Map<string, ScoreRange>();
  for (const row of rows) for (const [id, cell] of row.observations) {
    if (cell.state === 'disputed' || cell.observation_ids.length !== 1 || cell.value === null) continue;
    const value = Number(cell.value);
    if (!Number.isFinite(value)) continue;
    const range = ranges.get(id);
    if (range) { range.min = Math.min(range.min, value); range.max = Math.max(range.max, value); }
    else ranges.set(id, { min: value, max: value });
  }
  return ranges;
}

/** Pale amber → pale teal, independently normalized for each exact benchmark. */
export function scoreColor(value: number, range: ScoreRange | undefined, direction: string): string | undefined {
  if (!range || range.min === range.max || !Number.isFinite(value)) return undefined;
  const position = Math.max(0, Math.min(1, (value - range.min) / (range.max - range.min)));
  const quality = direction === 'lower' ? 1 - position : position;
  const low = [250, 231, 206], high = [187, 225, 211];
  return `rgb(${low.map((channel, i) => Math.round(channel + (high[i] - channel) * quality)).join(', ')})`;
}

/** Includes exact ties; a sole reported score is also the best available score. */
export function isBestScore(value: number, range: ScoreRange | undefined, direction: string): boolean {
  return !!range && Number.isFinite(value) && value === (direction === 'lower' ? range.min : range.max);
}
