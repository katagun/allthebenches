#!/usr/bin/env python3
"""Apply an explicit reviewed price crosswalk; never infer identity from similarity."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.schema import Dataset  # noqa: E402


def apply_mappings(dataset: dict, catalog: dict, provenance: dict, decisions: list[dict]) -> int:
    source_id = 'openrouter_price_coverage_catalog_2026_10_24'
    models = {m['id']: m for m in dataset['models']}
    records = {r['id']: r for r in catalog['data']}
    if len(records) != len(catalog['data']):
        raise ValueError('duplicate catalog identity')
    additions = []
    seen = set()
    existing = dataset.get('external_mappings', [])
    for decision in decisions:
        ext, mid = decision['external_id'], decision['model_id']
        if ext in seen:
            raise ValueError('duplicate reviewed identity')
        seen.add(ext)
        model, record = models.get(mid), records.get(ext)
        if not model or model['name'] != decision['curated_name']:
            raise ValueError('curated identity changed')
        if not record or any(record.get(k) != decision.get(expected) for k, expected in [('name', 'catalog_name'), ('canonical_slug', 'canonical_slug'), ('hugging_face_id', 'hugging_face_id')]):
            raise ValueError('catalog identity changed; review required')
        if not decision.get('evidence'):
            raise ValueError('missing review evidence')
        if any(r.get('external_id') == ext and r.get('status') == 'reviewed' and r.get('internal_model_id') != mid for r in existing):
            raise ValueError('conflicting reviewed identity')
        additions.append({'id': 'price_mapping_' + hashlib.sha256(ext.encode()).hexdigest()[:16], 'source_id': source_id,
                          'external_id': ext, 'internal_model_id': mid, 'status': 'reviewed', 'evidence': decision['evidence']})
    source = {'id': source_id, 'url': provenance['url'], 'title': 'OpenRouter catalog: reviewed price coverage identities (2026-10-24)',
              'publisher': 'OpenRouter', 'retrieved_at': provenance['retrieved_at'], 'content_sha256': provenance['content_sha256'],
              'method': 'Exact catalog IDs, names, canonical release slugs and weight IDs reviewed against curated releases.',
              'locator': 'data[]; explicit crosswalk in price-coverage-reviewed-mappings-2026-10-24.json'}
    dataset['sources'] = [s for s in dataset['sources'] if s['id'] != source_id] + [source]
    by_id = {r['id']: r for r in existing}
    by_id.update({r['id']: r for r in additions})
    dataset['external_mappings'] = list(by_id.values())
    Dataset.model_validate(dataset)
    return len(additions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/curated/dataset.json')
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    args = parser.parse_args()
    raw = args.catalog.read_bytes()
    provenance = json.loads(args.provenance.read_text())
    if provenance['url'] != 'https://openrouter.ai/api/v1/models' or hashlib.sha256(raw).hexdigest() != provenance['content_sha256']:
        raise ValueError('catalog provenance mismatch')
    dataset = json.loads(args.dataset.read_text())
    count = apply_mappings(dataset, json.loads(raw), provenance, json.loads(args.decisions.read_text()))
    args.dataset.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + '\n')
    print(f'{count} reviewed price mappings applied')


if __name__ == '__main__':
    main()
