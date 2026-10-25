"""Refresh only reviewed price identities for deployment; never discover routes."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import runpy
import tempfile

import httpx

from .collectors import collect_openrouter_endpoints
from .schema import Dataset

ROOT = Path(__file__).resolve().parents[1]
ALIBABA_ROUTE = 'alibaba:qwen3.8-max:singapore:international'
ALIBABA_URL = 'https://www.alibabacloud.com/help/en/model-studio/qwen3-8-max'


def reviewed_ids(dataset: dict) -> list[str]:
    return sorted({r['upstream_model_id'] for r in dataset['routes']
                   if r['id'].startswith('openrouter:') and r.get('upstream_model_id')})


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(' '.join(data.split()))


def alibaba_prices(html: str) -> dict[str, str]:
    """Fail closed on changed model, section, currency, units or table shape."""
    parser = TextParser()
    parser.feed(html)
    text = '\n'.join(parser.parts).split('Snapshot Versions')[0]
    if 'parameter):\nqwen3.8-max\nModel Capabilities' not in text:
        raise ValueError('Unexpected Alibaba model identity')
    sections = text.split('\nPricing\n')
    if len(sections) != 2:
        raise ValueError('Ambiguous Alibaba pricing section')
    section = sections[1].split('\nRate Limits\n')[0]
    tables = section.split('\nSingapore\nScope: International\n')
    if len(tables) != 2:
        raise ValueError('Missing Singapore International pricing')
    table = tables[1].split('\nGermany (Frankfurt)\n')[0].splitlines()
    expected = ['Input', 'Output', 'Input(Implicit Cache)', 'Explicit Cache Creation', 'Explicit Cache Read']
    if table[:3] != ['Billing Item', 'Price (USD)', 'Unit'] or len(table) != 18:
        raise ValueError('Unexpected Alibaba pricing table')
    values = []
    for index, label in enumerate(expected):
        name, value, unit = table[3 + index * 3:6 + index * 3]
        if name != label or unit != 'Per 1M tokens':
            raise ValueError('Unexpected Alibaba pricing unit or billing item')
        amount = Decimal(value)
        if not amount.is_finite() or amount < 0:
            raise ValueError('Invalid Alibaba price')
        values.append(str(amount))
    return dict(zip(('input_price', 'output_price', 'cache_read_price'), values[:3], strict=True))


def apply_alibaba(dataset: dict, evidence: dict) -> None:
    route = next((r for r in dataset['routes'] if r['id'] == ALIBABA_ROUTE), None)
    if not route or route['upstream_model_id'] != 'qwen3.8-max' or route['model_id'] != 'qwen38_max':
        raise ValueError('Alibaba route is not reviewed')
    quote = next(p for p in dataset['prices'] if p.get('route_id') == ALIBABA_ROUTE)
    source = next(s for s in dataset['sources'] if s['id'] == quote['source_id'])
    if source['url'] != ALIBABA_URL or evidence['url'] != ALIBABA_URL:
        raise ValueError('Unexpected Alibaba source')
    values = alibaba_prices(evidence['html'])
    observed = evidence['retrieved_at']
    if datetime.fromisoformat(observed) < datetime.fromisoformat(quote['observed_at']):
        return
    quote.update(values, observed_at=observed)
    source.update(retrieved_at=observed, content_sha256=hashlib.sha256(evidence['html'].encode()).hexdigest())


def refresh(dataset_path: Path, staging: Path, client: httpx.Client | None = None) -> dict:
    """Replay last accepted evidence, fetch again, and publish validated data."""
    original = json.loads(dataset_path.read_text())
    Dataset.model_validate(original)
    staging.mkdir(parents=True, exist_ok=True)
    importer = runpy.run_path(str(ROOT / 'scripts/import-route-metrics.py'))['import_route_metrics']
    endpoint_path = staging / 'openrouter-endpoints.json'
    alibaba_path = staging / 'alibaba-prices.json'
    if not endpoint_path.exists():
        # Cold runners still need the reviewed baseline for collapse protection.
        seeded = {}
        for name in ('openrouter-endpoints-current-2026-10-24.json',
                     'openrouter-price-coverage-endpoints-2026-10-24.json'):
            seeded.update(json.loads((ROOT / 'data/expansion' / name).read_text())['endpoints'])
        endpoint_path.write_text(json.dumps({'endpoints': seeded}))
    with tempfile.TemporaryDirectory() as temporary:
        working = Path(temporary) / 'dataset.json'
        working.write_text(json.dumps(original))
        # Retained payloads retain their original observation dates. Cache cannot
        # add routes or override newer curated quotes.
        if endpoint_path.exists():
            old = json.loads(endpoint_path.read_text())
            replay = deepcopy(old)
            for envelope in replay.get('endpoints', {}).values():
                if envelope.get('data') and envelope.get('retrieved_at'):
                    envelope['status'] = 'ok'
            replay_path = Path(temporary) / 'replay.json'
            replay_path.write_text(json.dumps(replay))
            importer(working, replay_path)
        result = collect_openrouter_endpoints(reviewed_ids(original), staging, client)
        importer(working, endpoint_path)
        updated = json.loads(working.read_text())
        baseline_quote = next(p for p in original['prices'] if p.get('route_id') == ALIBABA_ROUTE)
        previous = json.loads(alibaba_path.read_text()) if alibaba_path.exists() else {
            'url': ALIBABA_URL, 'retrieved_at': baseline_quote['observed_at']}
        if previous.get('html'):
            apply_alibaba(updated, previous)
        attempted = datetime.now(timezone.utc).isoformat()
        try:
            if client is None:
                with httpx.Client(timeout=30, follow_redirects=True) as http:
                    response = http.get(ALIBABA_URL)
            else:
                response = client.get(ALIBABA_URL)
            response.raise_for_status()
            evidence = {'url': ALIBABA_URL, 'html': response.text, 'retrieved_at': attempted,
                        'attempted_at': attempted, 'status': 'ok', 'record_count': 1}
            apply_alibaba(updated, evidence)
        except (httpx.HTTPError, ValueError, ArithmeticError):
            evidence = {**previous, 'url': ALIBABA_URL, 'attempted_at': attempted,
                        'status': 'stale' if previous.get('retrieved_at') else 'error'}
        alibaba_path.write_text(json.dumps(evidence))
        (staging / 'alibaba.json').write_text(json.dumps({'feeds': [
            {k: v for k, v in evidence.items() if k != 'html'}]}))
        # Restore newer curated observations if a cache payload predates them.
        originals = {p['id']: p for p in original['prices']}
        for i, price in enumerate(updated['prices']):
            prior = originals.get(price['id'])
            if prior and datetime.fromisoformat(prior['observed_at']) > datetime.fromisoformat(price['observed_at']):
                updated['prices'][i] = prior
        Dataset.model_validate(updated)
        dataset_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n')
    report = {'reviewed_openrouter_ids': reviewed_ids(original), 'attempts': result['attempts'],
              'alibaba': evidence['status']}
    (staging / 'price-refresh-report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('data/curated/dataset.json'))
    parser.add_argument('--staging', type=Path, default=Path('data/cache/price-refresh'))
    parser.add_argument('--output', type=Path, help='Build deployment data with refreshed feed health')
    args = parser.parse_args()
    report = refresh(args.dataset, args.staging)
    if args.output:
        from .build import build, load_dataset
        from .feed_health import feed_health
        manifest = json.loads((args.output / 'manifest.json').read_text())
        feeds = [f for f in manifest['feeds'] if f['source_id'] not in ('openrouter-endpoints', 'alibaba')]
        feeds += [f for f in feed_health(args.staging) if f['source_id'] in ('openrouter-endpoints', 'alibaba')]
        build(load_dataset(args.dataset), args.output, feeds)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
