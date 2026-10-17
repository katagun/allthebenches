"""Fail on stale generated contracts/data without modifying the working tree."""
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory

from pipeline.build import build, export_schema, load_dataset


def check_generated(root: Path) -> list[str]:
    dataset = load_dataset(root / 'data/curated/dataset.json')
    public = root / 'web/public/data'
    manifest = json.loads((public / 'manifest.json').read_text())
    with TemporaryDirectory(prefix='benches-generated-') as directory:
        temporary = Path(directory)
        # Feed health is captured at collection time, not re-fetched by this check.
        build(dataset, temporary / 'web/public/data', manifest.get('feeds', []))
        export_schema(temporary)
        return [str(path.relative_to(temporary)) for path in temporary.rglob('*')
                if path.is_file() and (not (root / path.relative_to(temporary)).is_file()
                or path.read_bytes() != (root / path.relative_to(temporary)).read_bytes())]


if __name__ == '__main__':
    stale = check_generated(Path(__file__).resolve().parents[1])
    if stale:
        print('Stale generated files: ' + ', '.join(sorted(stale)), file=sys.stderr)
        print('Run uv run benches build --offline and stage the outputs.', file=sys.stderr)
        raise SystemExit(1)
    print('Generated contracts and static snapshots match curated data.')
