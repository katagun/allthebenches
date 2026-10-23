import { describe, expect, it } from 'vitest';
import { scoreColor, isBestScore } from './heatmap';

describe('benchmark heatmap', () => {
  it('identifies directional winners and ties without rounding scores', () => {
    const range = { min: 0, max: 99.1234 };
    expect(isBestScore(99.1234, range, 'higher')).toBe(true);
    expect(isBestScore(99.1233, range, 'higher')).toBe(false);
    expect(isBestScore(0, range, 'lower')).toBe(true);
    expect(isBestScore(99.1234, range, 'lower')).toBe(false);
    expect(isBestScore(7, { min: 7, max: 7 }, 'higher')).toBe(true);
    expect(isBestScore(NaN, range, 'higher')).toBe(false);
    expect(isBestScore(7, undefined, 'higher')).toBe(false);
  });
  it('reverses lower-is-better metrics, including zero', () => {
    const range = { min: 0, max: 100 };
    expect(scoreColor(0, range, 'lower')).toBe(scoreColor(100, range, 'higher'));
    expect(scoreColor(100, range, 'lower')).toBe(scoreColor(0, range, 'higher'));
    expect(scoreColor(50, range, 'lower')).toBe(scoreColor(50, range, 'higher'));
  });
  it('tints ties and solitary values while leaving invalid numbers uncolored', () => {
    expect(scoreColor(42, { min: 42, max: 42 }, 'higher')).toBe(scoreColor(50, { min: 0, max: 100 }, 'higher'));
    expect(scoreColor(42, undefined, 'higher')).toBeUndefined();
    expect(scoreColor(NaN, { min: 0, max: 100 }, 'higher')).toBeUndefined();
  });
});
