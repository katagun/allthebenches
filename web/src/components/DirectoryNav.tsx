import { routeHref } from '../state/stateRuntime';
export function DirectoryNav({ active }: { active?: string }) {
  return <nav className="directory-nav" aria-label="Browse catalog"><a href={routeHref('/')}>Matrix</a>{['models', 'benchmarks', 'evidence'].map(id => <a key={id} href={routeHref(`/${id}`)} aria-current={active === id ? 'page' : undefined}>{id === 'evidence' ? 'Coverage & evidence' : id[0].toUpperCase() + id.slice(1)}</a>)}</nav>;
}
