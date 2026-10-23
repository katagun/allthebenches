import { queryRows } from './rowQuery';
import type { AppData } from './snapshots';
import type { ViewState } from '../state/viewState';

let dataset: AppData | null = null;
type WorkerRequest =
  | { type: 'initialize'; data: AppData }
  | { type: 'rows'; id: number; key: string; view: ViewState; expandedIds: string[]; asOf: number };
type WorkerResponse = { type: 'ready' } | { type: 'rows'; id: number; key: string; rows: unknown[] } | { type: 'error'; id: number; key: string; error: string };
const workerScope = self as unknown as {
  onmessage: ((event: MessageEvent<WorkerRequest>) => void) | null;
  postMessage: (message: WorkerResponse) => void;
};

workerScope.onmessage = event => {
  const message = event.data;
  if (message.type === 'initialize') {
    dataset = message.data;
    workerScope.postMessage({ type: 'ready' });
    return;
  }
  if (!dataset) {
    workerScope.postMessage({ type: 'error', id: message.id, key: message.key, error: 'Row worker is not initialized.' });
    return;
  }
  try {
    const rows = queryRows(dataset, message.view, new Set(message.expandedIds), message.asOf);
    workerScope.postMessage({ type: 'rows', id: message.id, key: message.key, rows });
  } catch (error) {
    workerScope.postMessage({ type: 'error', id: message.id, key: message.key, error: error instanceof Error ? error.message : 'Could not update table rows.' });
  }
};
