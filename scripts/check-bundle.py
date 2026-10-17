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
    errors = check_bundle(Path(__file__).resolve().parents[1] / 'web/dist/assets')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        raise SystemExit(1)
