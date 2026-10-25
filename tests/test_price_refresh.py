import json
from pathlib import Path

import httpx
import pytest

from pipeline.price_refresh import ALIBABA_URL, alibaba_prices, refresh, reviewed_ids
from pipeline.reconcile import candidate_openrouter_ids
from pipeline.feed_health import feed_health

ROOT = Path(__file__).parents[1]
HTML = (ROOT / 'tests/fixtures/alibaba-qwen38-pricing.html').read_text()


def test_every_reviewed_id_is_collected_without_discovery_catalogs(tmp_path):
    path = ROOT / 'data/curated/dataset.json'
    dataset = json.loads(path.read_text())
    ids = reviewed_ids(dataset)
    decisions = json.loads((ROOT / 'data/expansion/price-coverage-reviewed-mappings-2026-10-24.json').read_text())
    assert len(ids) == 25
    assert set(ids) <= set(candidate_openrouter_ids(path, tmp_path))
    # Specifically cover dated GPT-4o and all newly reviewed model identities.
    assert 'openai/gpt-4o-2024-05-13' in ids
    assert 'deepseek/deepseek-v4.1-flash' in ids
    assert {d['external_id'] for d in decisions} <= set(ids)


def test_alibaba_exact_region_and_units():
    assert alibaba_prices(HTML) == {'input_price': '2', 'output_price': '6', 'cache_read_price': '0.25'}
    assert alibaba_prices(HTML.replace('<p>2</p>', '<p>3</p>'))['input_price'] == '3'


@pytest.mark.parametrize('old,new', [
    ('<p>qwen3.8-max</p>', '<p>qwen3.8-max-0902</p>'),
    ('Scope: International', 'Scope: Global'),
    ('Price (USD)', 'Price (CNY)'),
    ('Per 1M tokens', 'Per 1K tokens'),
    ('<p>2</p>', '<p>NaN</p>'),
    ('Input(Implicit Cache)', 'Input(Explicit Cache)'),
])
def test_changed_alibaba_identity_or_schema_is_rejected(old, new):
    with pytest.raises((ValueError, ArithmeticError)):
        alibaba_prices(HTML.replace(old, new))


def test_refresh_replays_last_good_without_redating_or_discovering_routes(tmp_path):
    original = json.loads((ROOT / 'data/curated/dataset.json').read_text())
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps(original))
    seen = []
    def handler(request):
        seen.append(str(request.url))
        if str(request.url) == ALIBABA_URL:
            return httpx.Response(200, text=HTML)
        model = str(request.url).split('/models/')[1].removesuffix('/endpoints')
        endpoints = []
        for route in original['routes']:
            if route.get('upstream_model_id') == model:
                endpoints.append({'model_id': model, 'provider_name': route['provider'],
                                  'tag': route['id'].split(':')[-2], 'status': 0,
                                  'pricing': {'prompt': '0.000003', 'completion': '0.000004'}})
        return httpx.Response(200, json={'data': {'id': model, 'endpoints': endpoints}})
    staging = tmp_path / 'cache'
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = refresh(path, staging, client)
    assert report['alibaba'] == 'ok'
    assert len(seen) == 26
    fresh = json.loads(path.read_text())
    assert fresh['routes'] == original['routes']
    assert fresh['observations'] == original['observations']
    assert any(p['observed_at'] > '2026-10-24T17:35:16' for p in fresh['prices'])
    # New runner starts from committed data; replay cached evidence then fail all requests.
    path.write_text(json.dumps(original))
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))) as client:
        report = refresh(path, staging, client)
    retained = json.loads(path.read_text())
    assert retained['prices'] == fresh['prices']
    assert report['alibaba'] == 'stale'
    assert all(row['status'] == 'stale' for row in report['attempts'])
    assert all(f['status'] == 'stale' for f in feed_health(staging) if f['source_id'] in ('alibaba', 'openrouter-endpoints'))
    # Changed table or empty endpoints also cannot advance observation dates.
    def rejected(request):
        if str(request.url) == ALIBABA_URL:
            return httpx.Response(200, text=HTML.replace('Price (USD)', 'Price (CNY)'))
        model = str(request.url).split('/models/')[1].removesuffix('/endpoints')
        return httpx.Response(200, json={'data': {'id': model, 'endpoints': []}})
    with httpx.Client(transport=httpx.MockTransport(rejected)) as client:
        refresh(path, staging, client)
    assert json.loads(path.read_text())['prices'] == fresh['prices']


def test_daily_publication_is_wired_after_deterministic_checks():
    workflow = (ROOT / '.github/workflows/pages.yml').read_text()
    assert "cron: '47 6 * * *'" in workflow
    assert 'python -m pipeline.price_refresh --output web/public/data' in workflow
    assert workflow.index('pnpm test:layout') < workflow.index('python -m pipeline.price_refresh')
    assert workflow.index('python -m pipeline.price_refresh') < workflow.index('name: Build refreshed application')
    assert workflow.index('name: Smoke test refreshed publication') < workflow.index('uses: actions/upload-pages-artifact')


def test_cold_cache_failures_preserve_curated_prices_and_observation_dates(tmp_path):
    original = json.loads((ROOT / 'data/curated/dataset.json').read_text())
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps(original))
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))) as client:
        report = refresh(path, tmp_path / 'cache', client)
    result = json.loads(path.read_text())
    assert {p['id']: p for p in result['prices']} == {p['id']: p for p in original['prices']}
    assert report['alibaba'] == 'stale'
