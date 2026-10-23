import { exactScore, type DisplayRow } from './selectors';
import type { AppData } from './snapshots';

export type ScoreRange = { min: number; max: number };
/** Only exact eligible values contribute to the displayed scale and winners. */
export function displayedScoreRanges(data: AppData, rows: DisplayRow[], benchmarkIds: string[], saturationStates: string[] = []): Map<string, ScoreRange> {
  const ranges = new Map<string, ScoreRange>();
  for (const id of benchmarkIds) {
    const values = rows.map(row => exactScore(data, row, id, saturationStates)).filter((value): value is number => value !== null);
    if (values.length) ranges.set(id, { min: Math.min(...values), max: Math.max(...values) });
  }
  return ranges;
}

/** Pale amber → pale teal, independently normalized for each exact benchmark. */
export function scoreColor(value: number, range: ScoreRange | undefined, direction: string): string | undefined {
  if (!range || !Number.isFinite(value)) return undefined;
  const position = range.min === range.max ? 0.5 : Math.max(0, Math.min(1, (value - range.min) / (range.max - range.min)));
  const quality = direction === 'lower' ? 1 - position : position;
  const low = [250, 231, 206], high = [187, 225, 211];
  return `rgb(${low.map((channel, i) => Math.round(channel + (high[i] - channel) * quality)).join(', ')})`;
}

/** Includes exact ties; a sole reported score is also the best available score. */
export function isBestScore(value: number, range: ScoreRange | undefined, direction: string): boolean {
  return !!range && Number.isFinite(value) && value === (direction === 'lower' ? range.min : range.max);
}
