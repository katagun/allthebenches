import { render, screen, fireEvent } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { MobilePriceSummary, priceRangeLabel } from './ModelPrices';
import type { DisplayRow } from '../data/selectors';
import type { PriceObservation } from '../generated/dataset';

it('shows paired input/output ranges and opens prices without opening score evidence', () => {
  const onOpen = vi.fn();
  const row = { model: { name: 'Example' }, prices: [
    { route_id: 'a', input_price: '1', output_price: '6', observed_at: '2026-10-24T00:00:00Z' },
    { route_id: 'b', input_price: '2', output_price: '4', observed_at: '2026-10-24T00:00:00Z' },
  ] } as DisplayRow;
  render(<MobilePriceSummary row={row} asOf={Date.parse('2026-10-24T12:00:00Z')} onOpen={onOpen}/>);
  expect(screen.getByText('Input $1–$2 · Output $4–$6')).toBeTruthy();
  expect(screen.getByText(/USD \/ 1M tokens · 2 routes/)).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'API prices for Example' }));
  expect(onOpen).toHaveBeenCalledTimes(1);
});

it('distinguishes missing prices from explicitly free quotes and labels historical quotes', () => {
  const row = { model: { name: 'Example' }, prices: [] } as unknown as DisplayRow;
  const { rerender } = render(<MobilePriceSummary row={row} asOf={Date.parse('2026-10-24T12:00:00Z')} onOpen={() => {}}/>);
  expect(screen.getByText('No eligible API price')).toBeTruthy();
  row.prices = [{ route_id: 'a', input_price: '0', output_price: '0', observed_at: '2026-10-18T00:00:00Z' }] as PriceObservation[];
  rerender(<MobilePriceSummary row={row} asOf={Date.parse('2026-10-24T12:00:00Z')} onOpen={() => {}}/>);
  expect(screen.getByText('Input $0 · Output $0')).toBeTruthy();
  expect(screen.getByText(/Historical/)).toBeTruthy();
  expect(priceRangeLabel([{ input_price: null }] as PriceObservation[], 'input_price')).toBe('Unknown');
});
