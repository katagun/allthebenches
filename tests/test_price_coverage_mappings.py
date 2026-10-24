import copy
import json
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).parents[1]
APPLY = runpy.run_path(str(ROOT / 'scripts/import-reviewed-price-mappings.py'))['apply_mappings']


def inputs():
    return (json.loads((ROOT / 'data/curated/dataset.json').read_text()),
            json.loads((ROOT / 'data/expansion/openrouter-price-coverage-catalog-2026-10-24.json').read_text()),
            json.loads((ROOT / 'data/expansion/openrouter-price-coverage-catalog-2026-10-24-provenance.json').read_text()),
            json.loads((ROOT / 'data/expansion/price-coverage-reviewed-mappings-2026-10-24.json').read_text()))


def test_reviewed_crosswalk_is_idempotent_and_excludes_variant_guesses():
    data, catalog, provenance, decisions = inputs()
    assert APPLY(data, catalog, provenance, decisions) == 16
    before = copy.deepcopy(data)
    APPLY(data, catalog, provenance, decisions)
    assert data == before
    mapped = {r['model_id']: r['external_id'] for r in decisions}
    assert mapped['gpt4o'] == 'openai/gpt-4o-2024-05-13'
    assert mapped['deepseek_v4_1_flash'] == 'deepseek/deepseek-v4.1-flash'
    for ambiguous in ['muse_wonder_full', 'qwen38_max', 'qwen3_8b_base', 'deepseek_r1', 'grok3']:
        assert ambiguous not in mapped


@pytest.mark.parametrize('change', ['canonical_slug', 'name', 'hugging_face_id', 'missing', 'duplicate', 'curated_name'])
def test_changed_identity_requires_review_without_partial_mutation(change):
    data, catalog, provenance, decisions = inputs()
    before = copy.deepcopy(data)
    record = next(r for r in catalog['data'] if r['id'] == decisions[0]['external_id'])
    if change in ['canonical_slug', 'name', 'hugging_face_id']:
        record[change] = 'different variant'
    elif change == 'missing':
        catalog['data'].remove(record)
    elif change == 'duplicate':
        decisions.append(decisions[0])
    else:
        decisions[0]['curated_name'] = 'Different release'
    with pytest.raises(ValueError):
        APPLY(data, catalog, provenance, decisions)
    assert data == before


def test_direct_price_preserves_region_units_and_nonzero_token_rates():
    raw = json.loads((ROOT / 'data/expansion/alibaba-qwen38-max-reviewed-price-2026-10-24.json').read_text())
    data = json.loads((ROOT / 'data/curated/dataset.json').read_text())
    assert raw['route'] in data['routes']
    assert raw['price'] in data['prices']
    assert raw['route']['upstream_model_id'] == 'qwen3.8-max'
    assert 'Singapore' in raw['route']['routing_variant']
    assert raw['price']['price_unit'] == 'USD per 1M tokens'
    assert (raw['price']['input_price'], raw['price']['output_price']) == ('2', '6')
    assert raw['source']['content_sha256']


def test_audit_accounts_for_every_original_gap_and_only_fills_verified_models():
    audit = json.loads((ROOT / 'data/expansion/price-coverage-audit-2026-10-24.json').read_text())['releases']
    data, _, _, decisions = inputs()
    assert len(audit) == len({r['model_id'] for r in audit}) == 39
    assert all(r['reason'] and r['sources'] for r in audit)
    filled = {r['model_id'] for r in audit if r['decision'] == 'filled'}
    assert filled == {r['model_id'] for r in decisions} | {'qwen38_max'}
    unavailable = {r['model_id'] for r in audit if r['decision'] != 'filled'}
    # No historical/base/replacement evidence was promoted by this audit.
    new_routes = [r for r in data['routes'] if any(s in r['source_ids'] for s in ['alibaba_qwen38_max_pricing_2026_10_24']) or r.get('upstream_model_id') in {d['external_id'] for d in decisions}]
    assert not unavailable.intersection(r['model_id'] for r in new_routes)
