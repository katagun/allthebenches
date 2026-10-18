import { lazy, Suspense, useEffect, useSyncExternalStore } from 'react';
import App from './App';
import { subscribeNavigation } from './state/catalogState';
import type { EntityRoute } from './components/EntityPage';
const CatalogPage = lazy(() => import('./components/CatalogPage'));
const EntityPage = lazy(() => import('./components/EntityPage'));
export function parseEntityRoute(hash: string): EntityRoute | null {
  const match = /^#\/(models|benchmarks)\/([^/]+)$/.exec(hash.split('?')[0]);
  if (!match) return null;
  try { return { kind: match[1] as EntityRoute['kind'], id: decodeURIComponent(match[2]) }; } catch { return null; }
}
export default function Router() {
  const hash = useSyncExternalStore(subscribeNavigation, () => window.location.hash.split('?')[0]);
  useEffect(() => { window.scrollTo(0, 0); }, [hash]);
  const path = hash.split('?')[0];
  if (path === '#/models' || path === '#/benchmarks' || path === '#/evidence') return <Suspense fallback={<main className="state-page">Loading catalog…</main>}><CatalogPage kind={path.slice(2) as 'models' | 'benchmarks' | 'evidence'}/></Suspense>;
  return !hash || hash === '#' || hash.split('?')[0] === '#/' ? <App/> : <Suspense fallback={<main className="state-page">Loading details…</main>}><EntityPage key={hash} route={parseEntityRoute(hash)}/></Suspense>;
}
