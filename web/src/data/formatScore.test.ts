import { describe, expect, it } from 'vitest';
import { compactScore } from './formatScore';

describe('compact matrix scores', () => {
  it('bounds rating precision and floating-point artifacts without changing signs or zero', () => {
    expect(compactScore(1608.0365495299)).toBe('1,608.04');
    expect(compactScore(88.80000000000001)).toBe('88.8');
    expect(compactScore(-5.3)).toBe('-5.3');
    expect(compactScore(0)).toBe('0');
  });
  it('does not round small nonzero source-scale values to zero', () => {
    expect(compactScore(.000001234567)).toBe('0.000001235');
    expect(compactScore(-.000001234567)).toBe('-0.000001235');
  });
});
