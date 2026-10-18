"""Apply only the source fragments whose hashes were approved in a review manifest.

Run from the repository root:
  uv run python scripts/import-reviewed-snapshots.py data/expansion/reviewed-source-imports-2026-10-18.json
Then rebuild the static dataset with `uv run benches build --offline`.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.merge_expansions import merge_fragments  # noqa: E402
from pipeline.schema import Dataset  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    path = ROOT / 'data/curated/dataset.json'
    data = json.loads(path.read_text())
    presets = []
    for entry in manifest['imports']:
        payload = (ROOT / entry['path']).read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry['sha256']:
            raise ValueError(f'Fragment changed since review: {entry["path"]}')
        fragment = json.loads(payload)
        data = merge_fragments(data, [fragment], reviewed=True)
        observations = fragment.get('observations', [])
        presets.append({
            'id': entry['preset_id'], 'name': entry['name'], 'version': '1.0.0',
            'reviewed_at': manifest['reviewed_at'], 'saturation_policy_version': 'manual-v1',
            'model_configuration_ids': sorted({o['configuration_id'] for o in observations}),
            'benchmark_ids': sorted({o['benchmark_id'] for o in observations}),
            'reason': entry['scope'],
        })
    for preset in presets:
        data['presets'] = [p for p in data['presets'] if p['id'] != preset['id']] + [preset]
    all_models = next(p for p in data['presets'] if p['id'] == 'all_models_oct2026')
    all_models['benchmark_ids'] = sorted(b['id'] for b in data['benchmarks'])
    all_models['model_configuration_ids'] = sorted(c['id'] for c in data['configurations'])
    all_models['reviewed_at'] = manifest['reviewed_at']
    removed = set(manifest.get('resolved_gap_ids', []))
    updates = {g['id']: g for g in manifest.get('coverage_updates', [])}
    data['coverage_gaps'] = [updates.get(g['id'], g) for g in data['coverage_gaps'] if g['id'] not in removed]
    data['generated_at'] = manifest['integrated_at']
    Dataset.model_validate(data)
    # Validation and hash checks all complete before the first write.
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    for preset in [all_models, *presets]:
        (ROOT / f'data/presets/{preset["id"]}.json').write_text(json.dumps(preset, indent=2, ensure_ascii=False) + '\n')
    print(f'Integrated {len(manifest["imports"])} reviewed source snapshots; {len(data["observations"])} total observations.')


if __name__ == '__main__':
    main()
