import { useSyncExternalStore } from 'react';
export const NAVIGATION_EVENT = 'benches:navigation';
export function subscribeNavigation(callback: () => void) {
  window.addEventListener('popstate', callback);
  window.addEventListener('hashchange', callback);
  window.addEventListener(NAVIGATION_EVENT, callback);
  return () => { window.removeEventListener('popstate', callback); window.removeEventListener('hashchange', callback); window.removeEventListener(NAVIGATION_EVENT, callback); };
}
export const fragmentParams = () => new URLSearchParams(location.hash.split('?')[1] ?? '');
export function useCatalogState(kind: string) {
  const hash = useSyncExternalStore(subscribeNavigation, () => location.hash);
  const params = new URLSearchParams(hash.split('?')[1] ?? '');
  const prefix = kind === 'models' ? 'm' : 'b';
  const query = (params.get(prefix + 'q') ?? '').slice(0, 500);
  const filter = (params.get(prefix + 'f') ?? 'all').slice(0, 300);
  const rawOrder = params.get(prefix + 'o');
  const order = rawOrder === 'name' || (kind === 'models' && rawOrder === 'recent') ? rawOrder : 'coverage';
  const rawPage = Number(params.get(prefix + 'p'));
  const page = Number.isSafeInteger(rawPage) && rawPage >= 0 && rawPage < 10000 ? rawPage : 0;
  const update = (values: Partial<{ query: string; filter: string; order: string; page: number }>, push = false) => {
    const url = new URL(location.href); const next = fragmentParams();
    for (const [key, value] of Object.entries(values)) next.set(prefix + ({ query: 'q', filter: 'f', order: 'o', page: 'p' }[key]), String(value));
    url.hash = `${url.hash.split('?')[0].slice(1)}?${next}`;
    history[push ? 'pushState' : 'replaceState']({}, '', url);
    window.dispatchEvent(new Event(NAVIGATION_EVENT));
  };
  return { query, filter, order, page, update };
}
