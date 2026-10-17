import { describe, expect, it } from 'vitest';
import catalog from '../../public/data/catalog.json';
import details from '../../public/data/details.json';
import manifest from '../../public/data/manifest.json';
import market from '../../public/data/market.json';
import results from '../../public/data/results.json';
import type { AppData } from './snapshots';
import { RowWorkerClient, type WorkerTransport } from './rowWorkerClient';
import { DEFAULT_VIEW } from '../state/viewState';

const data: AppData = { catalog, details, manifest, market, results } as unknown as AppData;

class FakeWorker implements WorkerTransport {
  onmessage: WorkerTransport['onmessage'] = null;
  onerror: WorkerTransport['onerror'] = null;
  requests: Extract<Parameters<WorkerTransport['postMessage']>[0], { type: 'rows' }>[] = [];
  terminated = false;
  postMessage(message: Parameters<WorkerTransport['postMessage']>[0]) {
    if (message.type === 'initialize') this.onmessage?.({ data: { type: 'ready' } } as MessageEvent);
    else this.requests.push(message);
  }
  terminate() { this.terminated = true; }
  respond(data: { type: 'rows'; id: number; key: string; rows: [] } | { type: 'error'; id: number; key: string; error: string }) {
    this.onmessage?.({ data } as MessageEvent);
  }
}

describe('row worker client', () => {
  it('keeps one active request and replaces queued work with the latest query', async () => {
    const worker = new FakeWorker();
    const client = new RowWorkerClient(data, () => worker);
    const first = client.request(DEFAULT_VIEW, [], 'first');
    const replaced = client.request(DEFAULT_VIEW, [], 'replaced');
    const latest = client.request(DEFAULT_VIEW, [], 'latest');
    expect(worker.requests.map(request => request.key)).toEqual(['first']);
    worker.respond({ type: 'rows', id: worker.requests[0].id, key: 'first', rows: [] });
    expect(await first).toBeNull();
    expect(await replaced).toBeNull();
    expect(worker.requests.map(request => request.key)).toEqual(['first', 'latest']);
    worker.respond({ type: 'rows', id: worker.requests[1].id, key: 'latest', rows: [] });
    expect(await latest).toMatchObject({ key: 'latest', rows: [] });
    client.close();
  });

  it('uses the main-thread fallback when workers are unavailable and after worker errors', async () => {
    const fallbackClient = new RowWorkerClient(data, () => null);
    const fallback = await fallbackClient.request(DEFAULT_VIEW, [], 'fallback');
    expect(fallback && 'rows' in fallback && fallback.rows.length).toBeGreaterThan(0);
    fallbackClient.close();

    const worker = new FakeWorker();
    const recoveringClient = new RowWorkerClient(data, () => worker);
    const recovered = recoveringClient.request(DEFAULT_VIEW, [], 'recover');
    worker.respond({ type: 'error', id: worker.requests[0].id, key: 'recover', error: 'worker failed' });
    const response = await recovered;
    expect(response && 'rows' in response && response.rows.length).toBeGreaterThan(0);
    expect(worker.terminated).toBe(true);
    recoveringClient.close();
  });
});
