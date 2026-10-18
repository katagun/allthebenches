import json
from pathlib import Path

import pytest

from pipeline.merge_expansions import merge_fragments


def test_merge_is_explicit_idempotent_and_rejects_conflicting_scores():
    data = json.loads(Path('data/curated/dataset.json').read_text())
    observation = dict(data['observations'][0], id='test_candidate', review_state='candidate')
    fragment = {'observations': [observation]}
    staged = merge_fragments(data, [fragment])
    assert staged['observations'][-1]['review_state'] == 'candidate'
    merged = merge_fragments(data, [fragment], reviewed=True)
    assert merged['observations'][-1]['review_state'] == 'reviewed'
    assert merged == merge_fragments(merged, [fragment], reviewed=True)
    assert len(data['observations']) + 1 == len(merged['observations'])
    with pytest.raises(ValueError, match='Conflicting observations ID'):
        merge_fragments(merged, [{'observations': [dict(observation, value=observation['value'] + 1)]}], reviewed=True)


def test_source_categories_use_shared_navigation_without_losing_variants():
    from pipeline.merge_expansions import canonical_category
    benchmark = {'id': 'arena_style', 'name': 'Text Arena Style Control · Math', 'category': 'text style control', 'subset': 'Math'}
    normalized = canonical_category(benchmark)
    assert normalized == dict(benchmark, category='text')
    assert benchmark['category'] == 'text style control'
    assert canonical_category(normalized) == normalized


def test_reviewed_snapshot_manifest_matches_production_and_presets():
    import hashlib
    manifest = json.loads(Path('data/expansion/reviewed-source-imports-2026-10-18.json').read_text())
    data = json.loads(Path('data/curated/dataset.json').read_text())
    observations = {o['id']: o for o in data['observations']}
    presets = {p['id']: p for p in data['presets']}
    fragments = []
    for entry in manifest['imports']:
        payload = Path(entry['path']).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == entry['sha256']
        fragment = json.loads(payload)
        fragments.append(fragment)
        assert len(fragment['observations']) == entry['observations']
        preset = presets[entry['preset_id']]
        for candidate in fragment['observations']:
            published = observations[candidate['id']]
            assert published['review_state'] == 'reviewed'
            assert published['value'] == candidate['value']
            assert published['unit'] == candidate['unit']
            assert published['source_id'] == candidate['source_id']
            assert published['benchmark_id'] in preset['benchmark_ids']
            assert published['configuration_id'] in preset['model_configuration_ids']
    assert merge_fragments(data, fragments, reviewed=True) == data
