"""Replay only changed review proposals; historical merged captures remain immutable."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.automation import SOURCES, run  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true')
    args = parser.parse_args()
    baseline = 'HEAD^' if os.getenv('GITHUB_EVENT_NAME') == 'push' else 'origin/main'
    diff = ['--cached'] if args.staged else [baseline]
    paths = subprocess.check_output(['git', 'diff', '--name-only', '-z', *diff, '--', 'data/automation']).decode().split('\0')
    sources = sorted({p.split('/')[2] for p in paths if len(p.split('/')) > 3})
    for source in sources:
        if source not in SOURCES:
            raise ValueError(f'Unknown proposal source: {source}')
        proposal = ROOT / 'data/automation' / source
        if not proposal.exists():
            raise ValueError(f'Proposal evidence removed: {source}')
        before = [(proposal / name).read_bytes() for name in ('candidate.json', 'report.json')]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / source
            shutil.copytree(proposal, target)
            run(source, target, ROOT / 'data/curated/dataset.json', offline=True)
            after = [(target / name).read_bytes() for name in ('candidate.json', 'report.json')]
            if before != after:
                raise ValueError(f'{source}: proposal differs from offline replay; regenerate and review it')
        print(f'{source}: candidate and report match archived evidence')
    print(f'Checked {len(sources)} changed source proposals.')


if __name__ == '__main__':
    main()
