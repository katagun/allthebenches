"""Regression tests that prove quality gates fail on broken artifacts."""
import importlib.util
from pathlib import Path
import random
import shutil

from pipeline.build import build, export_schema, load_dataset

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_gate_catches_stale_types_and_data(tmp_path):
    shutil.copytree(ROOT / 'data/curated', tmp_path / 'data/curated')
    build(load_dataset(tmp_path / 'data/curated/dataset.json'), tmp_path / 'web/public/data')
    export_schema(tmp_path)
    check = load_script('check-generated').check_generated
    assert check(tmp_path) == []
    for relative in ('web/src/generated/dataset.ts', 'web/public/data/results.json'):
        with (tmp_path / relative).open('a') as file:
            file.write(' ')
    assert set(check(tmp_path)) == {'web/src/generated/dataset.ts', 'web/public/data/results.json'}


def test_bundle_gate_rejects_missing_and_oversized_assets(tmp_path):
    check = load_script('check-bundle').check_bundle
    assert len(check(tmp_path)) == 2
    (tmp_path / 'app.js').write_text('export {}')
    (tmp_path / 'app.css').write_text('body {}')
    assert check(tmp_path) == []
    (tmp_path / 'app.js').write_bytes(random.Random(42).randbytes(250 * 1024))
    assert any('budget exceeded' in error for error in check(tmp_path))
