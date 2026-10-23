"""Read-only diagnostics for the 2026-10-22 review; synthetic changes stay in memory."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import httpx  # noqa: E402
from pipeline.build import select_observations  # noqa: E402
from pipeline.collectors import collect  # noqa: E402
from pipeline.freshness import build_report  # noqa: E402
from pipeline.schema import Dataset  # noqa: E402

raw = json.loads((ROOT / 'data/curated/dataset.json').read_text())
clone = lambda: json.loads(json.dumps(raw))
report = {'as_of': '2026-10-22T14:30:00Z', 'counts': {
    k: len(v) for k, v in raw.items() if isinstance(v, list)}}
report['observation_states'] = dict(Counter(o['review_state'] for o in raw['observations']))
report['series_status'] = dict(Counter(s['comparability_status'] for s in raw['series']))
report['sources_with_field'] = {key: sum(bool(s.get(key)) for s in raw['sources'])
    for key in ('retrieved_at', 'published_at', 'content_sha256', 'license', 'method')}
report['observations_with_field'] = {key: sum(bool(o.get(key)) for o in raw['observations'])
    for key in ('reported_at', 'evaluated_at', 'uncertainty', 'supersedes')}
fresh = build_report(raw, datetime(2026, 10, 22, 14, 30, tzinfo=timezone.utc))
report['freshness'] = {kind: {'total': len(rows), 'stale': sum(r['stale'] for r in rows)}
    for kind, rows in fresh['mutable_data'].items()}
cells = select_observations(Dataset.model_validate(raw))
groups = defaultdict(list)
for cell in cells:
    groups[cell['configuration_id'], cell['benchmark_id']].append(cell)
report['display'] = {'cells': len(cells), 'states': dict(Counter(c['state'] for c in cells)),
    'configuration_benchmark_pairs': len(groups),
    'multi_series_pairs': sum(len(cs) > 1 for cs in groups.values()),
    'multi_series_all_individually_undisputed': sum(len(cs) > 1 and all(c['state'] != 'disputed' for c in cs) for cs in groups.values())}
report['payloads'] = {p.name: {'bytes': len(p.read_bytes()), 'gzip_bytes': len(gzip.compress(p.read_bytes()))}
    for p in sorted((ROOT / 'web/public/data').glob('*.json'))}
report['validation_probes'] = {}
for label, mutate in [
    ('blank_reviewed_provenance', lambda d: d['observations'][0].update(locator='', evaluator='', setup={})),
    ('self_supersession', lambda d: d['observations'][0].update(supersedes=[d['observations'][0]['id']])),
    ('non_http_source', lambda d: d['sources'][0].update(url='data:text/html,example')),
    ('mismatched_mapping', lambda d: d['external_mappings'].append({
        'id': 'review_bad_mapping', 'source_id': d['sources'][0]['id'], 'external_id': 'example',
        'internal_model_id': next(m['id'] for m in d['models'] if m['id'] != d['routes'][0]['model_id']),
        'route_id': d['routes'][0]['id'], 'status': 'reviewed'})),
]:
    sample = clone()
    mutate(sample)
    try:
        Dataset.model_validate(sample)
        report['validation_probes'][label] = 'accepted'
    except ValueError:
        report['validation_probes'][label] = 'rejected'
sample = clone()
old = sample['observations'][0]
sample['observations'].append({**old, 'id': 'review_correction', 'value': old['value'] - .1, 'supersedes': [old['id']]})
report['correction_cell'] = next(c for c in select_observations(Dataset.model_validate(sample))
    if 'review_correction' in c['observation_ids'])
sample = clone()
sample['observations'][0]['review_state'] = 'disputed'
report['explicit_disputed_is_published'] = any(sample['observations'][0]['id'] in c['observation_ids']
    for c in select_observations(Dataset.model_validate(sample)))
with tempfile.TemporaryDirectory() as temp:
    with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json={'data': [{'id': 'model-a'}]}))) as client:
        collect('openrouter', Path(temp), client)
    with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json={'data': []}))) as client:
        refreshed = collect('openrouter', Path(temp), client)
    report['empty_feed_refresh'] = {'status': refreshed['status'], 'row_counts': [len(f['data']['data']) for f in refreshed['feeds']]}
print(json.dumps(report, indent=2, sort_keys=True))
