"""Bound shipped assets after a production build; deliberately no timing threshold."""
import gzip
from pathlib import Path
import sys

# Current baseline: ~148 KiB JS including worker; ~8 KiB CSS, gzip.
BUDGETS = {'.js': 200 * 1024, '.css': 16 * 1024}


def check_bundle(assets: Path) -> list[str]:
    failures = []
    for extension, budget in BUDGETS.items():
        files = list(assets.rglob('*' + extension))
        size = sum(len(gzip.compress(path.read_bytes(), mtime=0)) for path in files)
        print(f'{extension}: {size:,} gzip bytes / {budget:,} budget ({len(files)} files)')
        if not files:
            failures.append(f'No {extension} assets; run the production build first')
        elif size > budget:
            failures.append(f'{extension} gzip budget exceeded: {size} > {budget}')
    return failures


if __name__ == '__main__':
    dist = Path(__file__).resolve().parents[1] / 'web/dist'
    errors = check_bundle(dist / 'assets')
    startup = (dist / 'data/comparison.json').read_bytes()
    compressed = len(gzip.compress(startup, mtime=0))
    print(f'Comparison startup: {len(startup):,} decoded bytes; {compressed:,} gzip bytes')
    if len(startup) > 9 * 1024 * 1024 or compressed > 450 * 1024:
        errors.append('Comparison startup exceeds its 9 MiB decoded / 450 KiB gzip budget')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        raise SystemExit(1)
