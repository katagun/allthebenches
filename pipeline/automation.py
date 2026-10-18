"""Review-only benchmark collection with immutable evidence and offline replay."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from pipeline.merge_expansions import ALLOWED_TABLES, canonical_category
from pipeline.schema import Dataset

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / 'data/collection/sources.json').read_text())
SOURCES = tuple(REGISTRY['sources'])
HOSTS = {'epoch.ai', 'www.vals.ai', 'artificialanalysis.ai', 'huggingface.co', 'livebench.ai'}
REDIRECT_HOSTS = HOSTS | {'cdn-lfs.huggingface.co', 'cdn-lfs-us-1.huggingface.co',
                          'cas-bridge.xethub.hf.co', 'us.aws.cdn.hf.co', 'cdn-lfs.hf.co'}
MAX_BYTES = 64 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')
    temporary.replace(path)


class Archive:
    """Raw bytes are compressed deterministically; paths never come from the server."""

    def __init__(self, root: Path, work: Path, *, offline=False, client=None):
        self.root, self.work, self.offline = root, work, offline
        self.work.mkdir(parents=True, exist_ok=True)
        path = root / 'captures.json'
        self.previous = json.loads(path.read_text()) if path.exists() else {}
        self.captures = {}
        self.client = client

    def fetch(self, url: str) -> Path:
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:
            raise ValueError(f'Unapproved source URL: {url}')
        if url in self.captures:
            return self.work / self.captures[url]['sha256']
        old = self.previous.get(url)
        if self.offline:
            if not old:
                raise ValueError(f'No archived capture for {url}')
            sha = old['sha256']
            if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                raise ValueError('Invalid capture hash')
            with gzip.open(self.root / 'raw' / f'{sha}.gz', 'rb') as handle:
                raw = handle.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES or digest(raw) != sha:
                raise ValueError(f'Corrupt archived evidence: {url}')
            record = old
        else:
            raw, headers = self._download(url)
            sha = digest(raw)
            record = old if old and old['sha256'] == sha else {
                'url': url, 'sha256': sha, 'bytes': len(raw),
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'content_type': headers.get('content-type'),
            }
            path = self.root / 'raw' / f'{sha}.gz'
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(gzip.compress(raw, mtime=0))
        target = self.work / sha
        target.write_bytes(raw)
        self.captures[url] = record
        return target

    def _download(self, url):
        for attempt in range(3):
            try:
                current = url
                for _ in range(6):
                    parsed = urlparse(current)
                    if (parsed.scheme != 'https' or parsed.hostname not in REDIRECT_HOSTS
                            or parsed.username or parsed.password or parsed.port not in (None, 443)):
                        raise ValueError('Unapproved source redirect destination')
                    with self.client.stream('GET', current, follow_redirects=False) as response:
                        if response.is_redirect:
                            current = urljoin(current, response.headers['location'])
                            continue
                        response.raise_for_status()
                        raw = bytearray()
                        for chunk in response.iter_bytes():
                            raw.extend(chunk)
                            if len(raw) > MAX_BYTES:
                                raise ValueError(f'Source exceeds {MAX_BYTES} bytes: {url}')
                        return bytes(raw), response.headers
                raise ValueError('Too many source redirects')
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in (429, 500, 502, 503, 504):
                    raise
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        raise AssertionError('unreachable')

    def save(self):
        write_json(self.root / 'captures.json', self.previous | self.captures)


def assess(fragment: dict, dataset: dict) -> dict:
    """Validate candidates without promoting them; classify every proposed entity."""
    counts = {'new': 0, 'unchanged': 0, 'conflict': 0}
    conflicts = []
    merged = json.loads(json.dumps(dataset))
    if set(fragment) - ALLOWED_TABLES:
        raise ValueError('Unexpected fragment tables')
    for table, rows in fragment.items():
        kind = Dataset.model_fields[table].annotation.__args__[0]
        existing = {row['id']: kind.model_validate(row) for row in merged[table]}
        seen = set()
        for raw in rows:
            row = canonical_category(raw) if table == 'benchmarks' else dict(raw)
            item = kind.model_validate(row)
            if item.id in seen:
                raise ValueError(f'Duplicate {table} ID: {item.id}')
            seen.add(item.id)
            old = existing.get(item.id)
            comparable = item.model_copy(update={'review_state': old.review_state}) if old and table == 'observations' else item
            if old is None:
                counts['new'] += 1
                merged[table].append(row)
            elif comparable == old:
                counts['unchanged'] += 1
            else:
                counts['conflict'] += 1
                conflicts.append({'table': table, 'id': item.id,
                                  'changed_fields': sorted(k for k, v in comparable.model_dump().items()
                                                           if old.model_dump().get(k) != v)})
    # Validate cross-references for new entities against existing catalog.
    Dataset.model_validate(merged)
    return {'entities': counts, 'conflicts': conflicts, 'publication': 'review_required',
            'candidate_observations': len(fragment.get('observations', []))}


def run(source: str, output: Path, dataset_path: Path, *, offline=False) -> dict:
    from pipeline.source_adapters import collect_and_parse
    dataset = json.loads(dataset_path.read_text())
    Dataset.model_validate(dataset)
    with tempfile.TemporaryDirectory() as temp, httpx.Client(timeout=60, follow_redirects=True,
            headers={'User-Agent': 'allthebenches/1.0 (public benchmark evidence collector)'}) as client:
        archive = Archive(output, Path(temp), offline=offline, client=client)
        try:
            # Capture timestamps are stable for unchanged content. Adapters use the
            # raw manifest as authoritative evidence; replay is independent of clock.
            fragment, coverage = collect_and_parse(source, archive, '1970-01-01T00:00:00Z', dataset)
            retrieved = max(r['retrieved_at'] for r in archive.captures.values())
            fragment = json.loads(json.dumps(fragment).replace('1970-01-01T00:00:00Z', retrieved))
            coverage = json.loads(json.dumps(coverage).replace('1970-01-01T00:00:00Z', retrieved))
            for row in fragment.get('sources', []):
                capture = archive.captures.get(row.get('url'))
                if capture:
                    row['retrieved_at'] = capture['retrieved_at']
            report = assess(fragment, dataset)
            if not fragment.get('observations') and not (coverage.get('counts', {}).get('duplicate_existing') or coverage.get('counts', {}).get('duplicate_identical')):
                raise ValueError('No candidate or accounted existing observations; source requires investigation')
            report.update({'source': source, 'coverage': coverage, 'contract': REGISTRY['sources'][source],
                           'dataset_sha256': digest(dataset_path.read_bytes()),
                           'adapter_sha256': digest(b''.join(p.read_bytes() for p in sorted((ROOT / 'pipeline').glob('*.py')))),
                           'dependency_lock_sha256': digest((ROOT / 'uv.lock').read_bytes()),
                           'mapping_contract_sha256': digest(b''.join(p.read_bytes() for p in [
                               ROOT / 'data/collection/sources.json',
                               ROOT / 'data/mappings/epoch_models.json',
                               ROOT / 'data/expansion/vals-all-source-snapshot-2026-10-18.json'])),
                           'evidence_sha256': digest(json.dumps(archive.captures, sort_keys=True).encode()),
                           'latency_policy': REGISTRY['latency_policy']})
            candidate_bytes = (json.dumps(fragment, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()
            report['candidate_sha256'] = digest(candidate_bytes)
            output.mkdir(parents=True, exist_ok=True)
            (output / 'candidate.json').write_bytes(candidate_bytes)
            write_json(output / 'report.json', report)
            (output / 'REVIEW.md').write_text(f'# {source} source update\n\n'
                f"Candidate observations: {report['candidate_observations']}.\n\n"
                f"Entity changes: {report['entities']}.\n\n"
                'This PR stages evidence and candidates only. Merging it does not publish scores. '
                'Review report.json for coverage and conflicts, then explicitly promote an approved fragment. '
                'Never resolve conflicts by silently overwriting existing observations.\n')
            failure = output / 'failure.json'
            failure.unlink(missing_ok=True)
            return report
        except Exception as exc:
            write_json(output / 'failure.json', {'source': source, 'error': f'{type(exc).__name__}: {exc}'})
            raise
        finally:
            archive.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, choices=SOURCES)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/curated/dataset.json')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.output, args.dataset, offline=args.offline)['entities']))


if __name__ == '__main__':
    main()
