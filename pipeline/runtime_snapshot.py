"""Compact comparison payload; full provenance remains available on demand."""
import hashlib
import json
from pathlib import Path


def write_runtime_snapshot(output: Path, payloads: dict, manifest: dict) -> None:
    def compact(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

    details = payloads['details.json']
    # Keep every setup key and unknown marker: filtering semantics must match full evidence.
    def summary(observation):
        fields = ('id', 'configuration_id', 'benchmark_id', 'series_id', 'review_state', 'reporting_relationship', 'value', 'unit')
        record = {key: observation[key] for key in fields if key in observation}
        record['setup'] = {key: value if value is None or isinstance(value, str) and value in ('unknown', 'not reported', 'not stated') else True
                           for key, value in observation.get('setup', {}).items()}
        return record

    # Performance is used only on model detail pages, which already load evidence.
    evidence = compact({**details, "route_performance": payloads["market.json"]["performance"]})
    filename = f"evidence-{hashlib.sha256(evidence).hexdigest()[:16]}.json"
    for old in output.glob('evidence-*.json'):
        if old.name != filename:
            old.unlink()
    (output / filename).write_bytes(evidence)
    catalog = dict(payloads['catalog.json'])
    # Per-model saturation evidence is archival; the UI uses the assessment summary.
    catalog['saturation'] = [{**assessment, 'evidence': []} for assessment in catalog['saturation']]
    runtime = {'catalog': catalog, 'cells': payloads['results.json']['cells'],
               'observations': [summary(record) for record in details['observations']],
               'series': details['series'], 'market': {**payloads['market.json'], 'performance': []},
               'manifest': manifest, 'evidence_file': filename}
    (output / 'comparison.json').write_bytes(compact(runtime))
