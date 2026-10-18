const ordinary = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });
const small = new Intl.NumberFormat(undefined, { maximumSignificantDigits: 4 });
/** Presentation only: evidence, sorting, heatmaps and exports keep source precision. */
export function compactScore(value: number): string {
  return Math.abs(value) > 0 && Math.abs(value) < 1 ? small.format(value) : ordinary.format(value);
}

/** Detail cards round to two decimals, without turning tiny nonzero scores into zero. */
export function detailScore(value: number): string {
  return value !== 0 && Math.abs(value) < .005 ? value.toExponential(2) : ordinary.format(value);
}
