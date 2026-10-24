import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { FeedHealth } from './FeedHealth';
import type { AppData } from '../data/snapshots';

it('separates failed attempts from retained data and counts only fresh available route prices', () => {
  const data = { manifest: { feeds: [{ source_id: 'openrouter', status: 'stale', as_of: '2026-10-18T12:00:00Z', attempted_at: '2026-10-24T12:00:00Z' }] },
    catalog: { models: [{ id: 'a' }, { id: 'b' }] }, market: {
      routes: [{ id: 'r', model_id: 'a', availability: 'listed' }, { id: 's', model_id: 'b', availability: 'listed' }],
      prices: [ { route_id: 'r', observed_at: '2026-10-24T12:00:00Z', available: true, currency: 'USD', price_unit: 'USD per 1M tokens' }, { route_id: 's', observed_at: '2026-10-18T12:00:00Z', available: true, currency: 'USD', price_unit: 'USD per 1M tokens' } ],
    } } as unknown as AppData;
  const { rerender } = render(<FeedHealth data={data} asOf={Date.parse('2026-10-24T13:00:00Z')}/>);
  expect(screen.getByText(/1 feed needs attention/)).toBeTruthy();
  expect(screen.getByText(/Fresh available prices: 1 of 2 releases · 1 routes/)).toBeTruthy();
  expect(screen.getByText('Last attempt: 2026-10-24 12:00:00 UTC')).toBeTruthy();
  expect(screen.getByText('Last accepted: 2026-10-18 12:00:00 UTC')).toBeTruthy();
  rerender(<FeedHealth data={data} asOf={Date.parse('2026-10-26T12:00:00Z')}/>);
  expect(screen.getByText(/Fresh available prices: 0 of 2/)).toBeTruthy();
});

it('does not label absent collection metadata healthy', () => {
  const data = { manifest: { feeds: [] }, catalog: { models: [] }, market: { prices: [], routes: [] } } as unknown as AppData;
  render(<FeedHealth data={data} asOf={0}/>);
  expect(screen.getByText(/Collection status unknown/)).toBeTruthy();
});
