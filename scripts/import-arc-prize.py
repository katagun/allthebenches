"""Import reviewed ARC Prize score-table snapshots; never infer missing scores or harnesses.

Input: data/expansion/arc-prize-scores.json (exact visible Verified scores tables).
Run: uv run python scripts/import-arc-prize.py && uv run benches build --offline
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {
    'ARC-AGI-1': ('arc_agi_1_semi_private', '1', 'ARC-AGI-1', 'static puzzle evaluation'),
    'ARC-AGI-2': ('arc_agi_2_semi_private', '2', 'ARC-AGI-2', 'static puzzle evaluation'),
    'ARC-AGI-3 (Standard harness)': ('arc_agi_3_standard', '3', 'ARC-AGI-3 · Standard', 'Standard'),
    'ARC-AGI-3 (Provider Adapter harness)': ('arc_agi_3_provider_adapter', '3', 'ARC-AGI-3 · Provider Adapter', 'Provider Adapter'),
    'ARC-AGI-3': ('arc_agi_3_unspecified', '3', 'ARC-AGI-3 · Harness unspecified', 'Not specified in result table'),
}


def score(value):
    if value in ('—', '–', '-'):
        return None
    if not value.endswith('%'):
        raise ValueError(f'Unexpected score: {value}')
    number = float(value[:-1])
    if not 0 <= number <= 100:
        raise ValueError(f'Out-of-range score: {value}')
    return number


def upsert(rows, item):
    rows[:] = [row for row in rows if row['id'] != item['id']] + [item]


def main():
    path = ROOT / 'data/curated/dataset.json'
    data = json.loads(path.read_text())
    snapshots = json.loads((ROOT / 'data/expansion/arc-prize-scores.json').read_text())
    models = {m['id']: m for m in data['models']}
    configuration_ids = []
    for bid, version, name, harness in HEADERS.values():
        upsert(data['benchmarks'], dict(id=bid, family_id='arc_agi_'+version, name=name,
            version=version, split='semi-private', category='reasoning', modality='interactive' if version == '3' else 'text',
            metric_name='human-normalized efficiency score' if version == '3' else 'task accuracy',
            unit='%', direction='higher', lower_bound=0, upper_bound=100, owner='ARC Prize Foundation',
            documentation_url='https://arcprize.org/arc-agi/'+version))
        upsert(data['series'], dict(id=bid+'_verified', benchmark_id=bid, evaluator='ARC Prize Foundation',
            protocol='Verified leaderboard; semi-private evaluation. Public task replays are a separate split.',
            tools=harness, comparability_status='unknown', comparability='Published runs may differ in effort and budget; inspect source settings.'))
    for entry in snapshots:
        mid = entry['model_id']
        model = models[mid]
        sid = 'arc_prize_'+mid
        upsert(data['sources'], dict(id=sid, url=entry['url'], title=model['name']+' — ARC Prize verified results',
            publisher='ARC Prize Foundation', retrieved_at=entry['retrieved_at'], content_sha256=entry['sha256'],
            method='Reviewed extraction of visible Verified scores table', locator='Verified scores (not public task replay tables)'))
        headers = entry['table'][0][1:]
        if set(headers) - HEADERS.keys():
            raise ValueError('Unknown ARC column')
        for row in entry['table'][1:]:
            if len(row) != len(headers)+1:
                raise ValueError('Score row width mismatch')
            effort = row[0].lower()
            if effort not in {'max', 'xhigh', 'high', 'medium', 'low', 'none'}:
                raise ValueError('Unknown reasoning effort')
            mode = 'disabled' if effort == 'none' else 'enabled'
            candidates = [c for c in data['configurations'] if c['model_id']==mid and c.get('reasoning_label')==effort and c['mode']==mode]
            cid = candidates[0]['id'] if candidates else mid+'_arc_'+effort
            if not candidates:
                data['configurations'].append(dict(id=cid, model_id=mid, mode=mode, reasoning_label=effort))
            if cid not in configuration_ids:
                configuration_ids.append(cid)
            for header, raw in zip(headers, row[1:], strict=True):
                value = score(raw)
                if value is None:
                    continue
                bid, version, _, harness = HEADERS[header]
                upsert(data['observations'], dict(id='o_arc_'+mid+'_'+effort+'_'+bid, configuration_id=cid,
                    benchmark_id=bid, series_id=bid+'_verified', value=value, unit='%', source_id=sid,
                    locator=f'Verified scores: {row[0]} row, {header} column', evaluator='ARC Prize Foundation',
                    reporting_relationship='evaluator_measurement', review_state='reviewed',
                    setup={'split':'semi-private', 'reasoning_effort':effort, 'harness':harness,
                           'score_precision':'As displayed by the source; no extra precision inferred.',
                           'policy_url':'https://arcprize.org/policy'}))
    bids = [item[0] for item in HEADERS.values()]
    preset = dict(id='arc_agi', version='1.0.0', name='ARC-AGI · Verified', model_configuration_ids=configuration_ids,
        benchmark_ids=bids, reason='ARC-AGI 1, 2 and 3; semi-private results, separated by harness. Missing scores are not zero.', reviewed_at='2026-10-17')
    upsert(data['presets'], preset)
    for item in data['presets']:
        if item['id'] in {'frontier_oct2026', 'all_models_oct2026'}:
            item['benchmark_ids'] = list(dict.fromkeys(item['benchmark_ids']+bids))
            item['model_configuration_ids'] = list(dict.fromkeys(item['model_configuration_ids']+configuration_ids))
        if item['id'] in {'arc_agi', 'frontier_oct2026', 'all_models_oct2026'}:
            (ROOT / ('data/presets/'+item['id']+'.json')).write_text(json.dumps(item,indent=2,ensure_ascii=False)+'\n')
    upsert(data['coverage_gaps'], dict(id='arc_agi_coverage', scope='ARC-AGI benchmark series',
        reason='All three current ARC-AGI versions are represented. This snapshot covers nine catalog models; other models, public splits, competition systems and the retired ARC-AGI-3 Preview are not yet imported. Unlabeled ARC-AGI-3 harness results remain separate.',
        source_ids=['arc_prize_'+s['model_id'] for s in snapshots]))
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


if __name__ == '__main__':
    main()
