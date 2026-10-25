"""A fresh null measurement must not inherit an older snapshot's metric."""
import json
import runpy
from pathlib import Path

from test_route_metrics import fixture

IMPORTER = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/import-route-metrics.py'))['import_route_metrics']


def test_null_current_performance_removes_old_snapshot_without_erasing_other_sources(tmp_path):
    data = fixture()
    data['sources'].append({'id': 'other', 'url': 'https://example.com', 'title': 'Other', 'publisher': 'Other'})
    data['performance'].append({**data['performance'][0], 'id': 'independent', 'source_id': 'other'})
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps(data))
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text(json.dumps({'endpoints': {'lab/model': {
        'status': 'ok', 'retrieved_at': '2026-10-18T13:00:00Z',
        'data': {'data': {'endpoints': [{'provider_name': 'Provider', 'tag': 'provider',
                                      'latency_last_30m': None, 'throughput_last_30m': None}]}}
    }}}))
    result = IMPORTER(path, snapshot)
    refreshed = json.loads(path.read_text())
    assert result['performance_rows'] == 0
    assert [row['id'] for row in refreshed['performance']] == ['independent']


def test_older_cached_evidence_cannot_replace_newer_curated_quote(tmp_path):
    data = fixture()
    data['sources'][0]['retrieved_at'] = '2026-01-01T00:00:00Z'
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps(data))
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text(json.dumps({'endpoints': {'lab/model': {
        'status': 'ok', 'retrieved_at': '2025-12-31T00:00:00Z',
        'data': {'data': {'endpoints': [{'provider_name': 'Provider', 'tag': 'provider',
                                      'pricing': {'prompt': '0.000099'}}]}}
    }}}))
    assert IMPORTER(path, snapshot)['quotes'] == 0
    refreshed = json.loads(path.read_text())
    assert sorted(refreshed['prices'], key=lambda p: p['id']) == sorted(data['prices'], key=lambda p: p['id'])
    assert refreshed['sources'] == data['sources']
    assert refreshed['performance'] == data['performance']
