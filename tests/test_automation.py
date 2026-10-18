import gzip
import json
from pathlib import Path

import httpx
import pytest

from pipeline.automation import Archive, assess, digest


def test_archive_roundtrip_preserves_bytes_and_timestamp(tmp_path):
    calls = []
    def respond(request):
        calls.append(request.url)
        return httpx.Response(200, content=b'original source evidence', headers={'content-type': 'text/plain'})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        archive = Archive(tmp_path / 'archive', tmp_path / 'work', client=client)
        first = archive.fetch('https://epoch.ai/data/example')
        archive.save()
        captures = archive.captures.copy()
        assert archive.fetch('https://epoch.ai/data/example') == first
        assert len(calls) == 1
        retry = Archive(archive.root, tmp_path / 'retry', client=client)
        assert retry.fetch('https://epoch.ai/data/example').read_bytes() == first.read_bytes()
        assert retry.captures == captures
        replay = Archive(archive.root, tmp_path / 'replay', offline=True)
        assert replay.fetch('https://epoch.ai/data/example').read_bytes() == first.read_bytes()
        assert replay.captures == captures


def test_archive_rejects_corruption_and_missing_capture(tmp_path):
    root = tmp_path / 'archive'
    (root / 'raw').mkdir(parents=True)
    sha = digest(b'correct')
    (root / 'captures.json').write_text(json.dumps({'https://epoch.ai/data/x': {'sha256': sha}}))
    (root / 'raw' / f'{sha}.gz').write_bytes(gzip.compress(b'wrong'))
    archive = Archive(root, tmp_path / 'work', offline=True)
    with pytest.raises(ValueError, match='Corrupt'):
        archive.fetch('https://epoch.ai/data/x')
    with pytest.raises(ValueError, match='No archived'):
        archive.fetch('https://epoch.ai/data/missing')
    with pytest.raises(ValueError, match='Unapproved'):
        archive.fetch('http://localhost/secrets')


def test_failed_fetch_never_replaces_good_capture(tmp_path):
    root = tmp_path / 'archive'
    root.mkdir()
    prior = {'https://epoch.ai/x': {'sha256': digest(b'old')}}
    (root / 'captures.json').write_text(json.dumps(prior))
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(404))) as client:
        archive = Archive(root, tmp_path / 'work', client=client)
        with pytest.raises(httpx.HTTPStatusError):
            archive.fetch('https://epoch.ai/x')
        assert json.loads((root / 'captures.json').read_text()) == prior


def test_assessment_detects_conflicts_without_mutation():
    dataset = json.loads(Path('data/curated/dataset.json').read_text())
    row = dict(dataset['observations'][0])
    row['review_state'] = 'candidate'
    assert assess({'observations': [row]}, dataset)['entities']['unchanged'] == 1
    row['value'] += 0.001
    result = assess({'observations': [row]}, dataset)
    assert result['entities']['conflict'] == 1
    assert dataset['observations'][0]['value'] != row['value']
    with pytest.raises(ValueError, match='Duplicate'):
        assess({'observations': [row, row]}, dataset)


def test_promotion_requires_matching_approval_and_current_catalog(tmp_path):
    from pipeline.promote_candidate import promote
    dataset = tmp_path / 'dataset.json'
    dataset.write_bytes(Path('data/curated/dataset.json').read_bytes())
    candidate = tmp_path / 'candidate.json'
    candidate.write_text('{"observations": []}')
    sha = digest(candidate.read_bytes())
    report = {'candidate_sha256': sha, 'dataset_sha256': digest(dataset.read_bytes())}
    (tmp_path / 'report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='changed since approval'):
        promote(tmp_path, dataset, 'wrong')
    dataset.write_text(dataset.read_text() + '\n')
    with pytest.raises(ValueError, match='Catalog changed'):
        promote(tmp_path, dataset, sha)


def test_source_registry_matches_workflow():
    from pipeline.automation import SOURCES
    workflow = Path('.github/workflows/benchmark-refresh.yml').read_text()
    assert f"source: [{', '.join(SOURCES)}]" in workflow
    assert 'uv run --frozen --group collectors' in workflow
    assert 'gh workflow run checks.yml' in workflow


def test_retry_is_bounded_and_replays_good_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr('pipeline.automation.time.sleep', lambda delay: None)
    calls = []
    def respond(request):
        calls.append(request.url)
        return httpx.Response(503 if len(calls) < 3 else 200, content=b'ok')
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        archive = Archive(tmp_path / 'archive', tmp_path / 'work', client=client)
        assert archive.fetch('https://epoch.ai/x').read_bytes() == b'ok'
        assert len(calls) == 3


def test_payload_limit(tmp_path, monkeypatch):
    monkeypatch.setattr('pipeline.automation.MAX_BYTES', 2)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b'large'))) as client:
        archive = Archive(tmp_path / 'archive', tmp_path / 'work', client=client)
        with pytest.raises(ValueError, match='exceeds'):
            archive.fetch('https://epoch.ai/x')
        assert not archive.captures


def test_redirect_cannot_escape_approved_hosts(tmp_path):
    calls = []
    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={'location': 'http://127.0.0.1/private'})
    with httpx.Client(transport=httpx.MockTransport(respond), follow_redirects=True) as client:
        archive = Archive(tmp_path / 'archive', tmp_path / 'work', client=client)
        with pytest.raises(ValueError, match='Unapproved source redirect'):
            archive.fetch('https://epoch.ai/x')
        assert calls == ['https://epoch.ai/x']
