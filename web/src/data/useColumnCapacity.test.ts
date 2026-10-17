import { describe, expect, it } from 'vitest';
import { columnCapacity } from './useColumnCapacity';

describe('responsive column budget', () => {
  it('reserves room for the model, optional market columns, borders, and readable cells', () => {
    expect(columnCapacity(2122)).toBe(10);
    expect(columnCapacity(2121)).toBe(9);
    expect(columnCapacity(2122, 2)).toBe(8);
    expect(columnCapacity(4200)).toBe(21);
  });
  it('fits more model columns in benchmark-row orientation', () => {
    expect(columnCapacity(1360, 0, true)).toBe(7);
    expect(columnCapacity(1360)).toBe(5);
    expect(columnCapacity(10000, 0, true)).toBe(24);
  });
  it('keeps narrow screens navigable and extreme screens bounded', () => {
    expect(columnCapacity(320, 2)).toBe(1);
    expect(columnCapacity(366, 0, true)).toBe(3);
    expect(columnCapacity(744)).toBe(3);
    expect(columnCapacity(10000)).toBe(24);
  });
});
