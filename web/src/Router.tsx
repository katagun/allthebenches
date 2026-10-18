import { lazy, Suspense, useEffect, useSyncExternalStore } from 'react';
import App from './App';
import type { EntityRoute } from './components/EntityPage';
const EntityPage = lazy(() => import('./components/EntityPage'));
function subscribe(callback: () => void) { window.addEventListener('hashchange', callback); return () => window.removeEventListener('hashchange', callback); }
export function parseEntityRoute(hash: string): EntityRoute | null {
  const match = /^#\/(models|benchmarks)\/([^/]+)$/.exec(hash.split('?')[0]);
  if (!match) return null;
  try { return { kind: match[1] as EntityRoute['kind'], id: decodeURIComponent(match[2]) }; } catch { return null; }
}
export default function Router() {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash);
  useEffect(() => { window.scrollTo(0, 0); }, [hash]);
  return !hash || hash === '#' || hash.split('?')[0] === '#/' ? <App/> : <Suspense fallback={<main className="state-page">Loading details…</main>}><EntityPage key={hash} route={parseEntityRoute(hash)}/></Suspense>;
}
