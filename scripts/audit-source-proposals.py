"""Reconcile the first five proposals against published observations, without promotion."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.automation import Archive, digest, write_json  # noqa: E402
from pipeline.schema import Dataset  # noqa: E402
from pipeline.source_adapters import collect_and_parse  # noqa: E402


def audit() -> dict:
    dataset = json.loads((ROOT / 'data/curated/dataset.json').read_text())
    kind = Dataset.model_fields['observations'].annotation.__args__[0]
    existing = {o['id']: kind.model_validate(o).model_dump() for o in dataset['observations']}
    results = {}
    for source in ('epoch', 'vals', 'aa', 'arena', 'livebench'):
        proposal = ROOT / 'data/automation' / source
        original = (proposal / 'candidate.json').read_bytes()
        original_report = json.loads((proposal / 'report.json').read_text())
        if digest(original) != original_report['candidate_sha256']:
            raise ValueError(f'{source}: candidate hash does not match the reviewed proposal')
        with tempfile.TemporaryDirectory() as temp:
            archive = Archive(proposal, Path(temp), offline=True)
            fragment, coverage = collect_and_parse(source, archive, '2026-10-18T00:00:00Z', dataset)
        matched = []
        for row in fragment['observations']:
            record = kind.model_validate(row).model_dump()
            previous = existing.get(row['id'])
            if previous is None:
                raise ValueError(f'{source}: unreviewed new observation {row["id"]}')
            record['review_state'] = previous['review_state']
            # Epoch's ZIP hash changes when unrelated CSV members change. The
            # exact admitted source rows, metric and value must remain identical.
            if source == 'epoch':
                expected_hash = archive.captures['https://epoch.ai/data/benchmark_data.zip']['sha256']
                if record['setup'].get('archive_sha256') != expected_hash:
                    raise ValueError('Epoch evidence hash mismatch')
                record['setup']['archive_sha256'] = previous['setup']['archive_sha256']
            if record != previous:
                raise ValueError(f'{source}: changed observation requires review: {row["id"]}')
            matched.append(row['id'])
        counts = coverage.get('counts', {})
        duplicate_count = counts.get('duplicate_existing', 0) + counts.get('duplicate_identical', 0)
        decisions = Counter(d['status'] for d in coverage.get('decisions', []))
        results[source] = {
            'original_candidate_sha256': digest(original),
            'verified_existing_results': len(matched) + duplicate_count,
            'new_results': 0, 'changed_scores': 0,
            'original_proposed_observations': original_report['candidate_observations'],
            'replayed_candidate_observations': len(matched),
            'coverage_counts': counts, 'decision_counts': dict(decisions),
            'denominators': coverage.get('denominators'),
            'raw_captures_verified': len(archive.captures),
            'captures_sha256': hashlib.sha256((proposal / 'captures.json').read_bytes()).hexdigest(),
        }
        print(f'{source}: {len(matched) + duplicate_count} verified existing results; no new scores')
    expected = {'epoch': 925, 'vals': 533, 'aa': 1082, 'arena': 2564, 'livebench': 586}
    if {s: r['verified_existing_results'] for s, r in results.items()} != expected:
        raise ValueError('Reviewed snapshot coverage changed; investigate before publishing')
    return {'review_date': '2026-10-18', 'sources': results,
            'verified_existing_results': sum(expected.values()), 'new_results': 0,
            'published_observations': len(dataset['observations']),
            'decision': 'Preserve all published scores; fix collector identity and source links; archive review evidence.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, audit())
