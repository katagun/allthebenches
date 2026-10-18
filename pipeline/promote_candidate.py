"""Explicitly approve a hash-identified candidate; conflicts always require review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.automation import assess, digest, write_json
from pipeline.merge_expansions import merge_fragments
from pipeline.schema import Dataset


def promote(proposal: Path, dataset_path: Path, approved_sha256: str) -> None:
    payload = (proposal / 'candidate.json').read_bytes()
    report = json.loads((proposal / 'report.json').read_text())
    if digest(payload) != approved_sha256 or report['candidate_sha256'] != approved_sha256:
        raise ValueError('Candidate changed since approval')
    if digest(dataset_path.read_bytes()) != report['dataset_sha256']:
        raise ValueError('Catalog changed; regenerate the proposal before approval')
    fragment = json.loads(payload)
    dataset = json.loads(dataset_path.read_text())
    if assess(fragment, dataset)['conflicts']:
        raise ValueError('Resolve conflicting IDs before promotion; existing evidence cannot be overwritten')
    merged = merge_fragments(dataset, [fragment], reviewed=True)
    Dataset.model_validate(merged)
    write_json(dataset_path, merged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('proposal', type=Path)
    parser.add_argument('--dataset', type=Path, default=Path('data/curated/dataset.json'))
    parser.add_argument('--approve-sha256', required=True)
    args = parser.parse_args()
    promote(args.proposal, args.dataset, args.approve_sha256)


if __name__ == '__main__':
    main()
