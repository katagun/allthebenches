"""Regression tests that prove quality gates fail on broken artifacts."""
import importlib.util
import json
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


def test_generated_gate_catches_and_offline_build_repairs_manifest_drift(tmp_path, monkeypatch):
    from pipeline.cli import main

    shutil.copytree(ROOT / 'data/curated', tmp_path / 'data/curated')
    public = tmp_path / 'web/public/data'
    feeds = [{'source_id': 'test', 'status': 'ok'}]
    build(load_dataset(tmp_path / 'data/curated/dataset.json'), public, feeds)
    export_schema(tmp_path)
    # Reproduce the deployment failure: comparison has lost the published feeds.
    comparison = json.loads((public / 'comparison.json').read_text())
    comparison['manifest']['feeds'] = []
    (public / 'comparison.json').write_text(json.dumps(comparison))
    check = load_script('check-generated').check_generated
    assert check(tmp_path) == ['web/public/data/comparison.json']
    monkeypatch.chdir(tmp_path)
    assert main(['build', '--offline']) == 0
    assert check(tmp_path) == []
    manifest = json.loads((public / 'manifest.json').read_text())
    assert manifest['feeds'] == feeds
    assert json.loads((public / 'comparison.json').read_text())['manifest'] == manifest


def test_bundle_gate_rejects_missing_and_oversized_assets(tmp_path):
    check = load_script('check-bundle').check_bundle
    assert len(check(tmp_path)) == 2
    (tmp_path / 'app.js').write_text('export {}')
    (tmp_path / 'app.css').write_text('body {}')
    assert check(tmp_path) == []
    (tmp_path / 'app.js').write_bytes(random.Random(42).randbytes(250 * 1024))
    assert any('budget exceeded' in error for error in check(tmp_path))
