import type { DisplayRow } from './selectors';
import { queryRows } from './rowQuery';
import type { AppData } from './snapshots';
import type { ViewState } from '../state/viewState';

export type RowRequestResult = { id: number; key: string; rows: DisplayRow[] } | { id: number; key: string; error: string };
type WorkerMessage = { type: 'ready' } | { type: 'rows'; id: number; key: string; rows: DisplayRow[] } | { type: 'error'; id: number; key: string; error: string };
type WorkerRequest = { type: 'initialize'; data: AppData } | { type: 'rows'; id: number; key: string; view: ViewState; expandedIds: string[] };
export interface WorkerTransport {
  onmessage: ((event: MessageEvent<WorkerMessage>) => void) | null;
  onerror: ((event: ErrorEvent) => void) | null;
  postMessage(message: WorkerRequest): void;
  terminate(): void;
}
type QueuedRequest = { id: number; key: string; view: ViewState; expandedIds: string[]; resolve: (result: RowRequestResult | null) => void };

function createModuleWorker(): WorkerTransport | null {
  if (typeof Worker === 'undefined') return null;
  try { return new Worker(new URL('./rows.worker.ts', import.meta.url), { type: 'module' }) as unknown as WorkerTransport; }
  catch { return null; }
}

/** One in-flight computation and one replaceable latest request bound the worker queue. */
export class RowWorkerClient {
  private worker: WorkerTransport | null;
  private ready: boolean;
  private nextId = 0;
  private latestId = 0;
  private active: QueuedRequest | null = null;
  private queued: QueuedRequest | null = null;
  private closed = false;
  private cache = new Map<string, DisplayRow[]>();

  constructor(private readonly data: AppData, workerFactory: () => WorkerTransport | null = createModuleWorker) {
    try { this.worker = workerFactory(); } catch { this.worker = null; }
    this.ready = !this.worker;
    if (this.worker) {
      this.worker.onmessage = event => this.onMessage(event.data);
      this.worker.onerror = () => this.recoverToFallback();
      try { this.worker.postMessage({ type: 'initialize', data }); }
      catch { this.recoverToFallback(); }
    }
  }

  request(view: ViewState, expandedIds: string[], key: string): Promise<RowRequestResult | null> {
    if (this.closed) return Promise.resolve(null);
    const id = ++this.nextId;
    this.latestId = id;
    const cached = this.cache.get(key);
    if (cached) {
      this.queued?.resolve(null);
      this.queued = null;
      this.touchCache(key, cached);
      return Promise.resolve({ id, key, rows: cached });
    }
    return new Promise(resolve => {
      if (this.closed) { resolve(null); return; }
      if (this.queued) this.queued.resolve(null);
      this.queued = { id, key, view, expandedIds: [...expandedIds], resolve };
      this.drain();
    });
  }

  close(): void {
    this.closed = true;
    this.worker?.terminate();
    this.worker = null;
    this.active?.resolve(null);
    this.queued?.resolve(null);
    this.active = null;
    this.queued = null;
    this.cache.clear();
  }

  private onMessage(message: WorkerMessage): void {
    if (message.type === 'ready') { this.ready = true; this.drain(); return; }
    if (!this.active || message.id !== this.active.id) return;
    const completed = this.active;
    this.active = null;
    if (completed.id === this.latestId) {
      if (message.type === 'rows') {
        this.touchCache(message.key, message.rows);
        completed.resolve({ id: message.id, key: message.key, rows: message.rows });
      } else {
        // Retry worker-side computation failures through the bounded fallback.
        this.queued = { ...completed, id: this.latestId };
        this.recoverToFallback();
        return;
      }
    } else completed.resolve(null);
    this.drain();
  }

  private drain(): void {
    if (this.closed || !this.ready || this.active || !this.queued) return;
    const next = this.queued;
    this.queued = null;
    this.active = next;
    if (this.worker) {
      try { this.worker.postMessage({ type: 'rows', id: next.id, key: next.key, view: next.view, expandedIds: next.expandedIds }); }
      catch { this.recoverToFallback(); }
      return;
    }
    window.setTimeout(() => {
      if (this.active !== next || this.closed) return;
      try {
        const rows = queryRows(this.data, next.view, new Set(next.expandedIds));
        this.touchCache(next.key, rows);
        if (next.id === this.latestId) next.resolve({ id: next.id, key: next.key, rows });
        else next.resolve(null);
      } catch (error) {
        next.resolve({ id: next.id, key: next.key, error: error instanceof Error ? error.message : 'Could not update table rows.' });
      }
      this.active = null;
      this.drain();
    });
  }

  private recoverToFallback(): void {
    this.worker?.terminate();
    this.worker = null;
    this.ready = true;
    const current = this.active;
    if (current && this.queued) current.resolve(null);
    this.active = null;
    if (current && !this.queued) this.queued = current;
    this.drain();
  }

  private touchCache(key: string, rows: DisplayRow[]): void {
    this.cache.delete(key);
    this.cache.set(key, rows);
    while (this.cache.size > 5) this.cache.delete(this.cache.keys().next().value!);
  }
}
