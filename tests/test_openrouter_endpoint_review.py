import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "openrouter_endpoint_review", ROOT / "scripts/review-openrouter-endpoints.py"
)
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


def load_inputs(snapshot_name="openrouter-endpoints-2026-10-18.json"):
    dataset = json.loads((ROOT / "data/curated/dataset.json").read_text())
    snapshot = json.loads((ROOT / "data/expansion" / snapshot_name).read_text())
    raw_catalog = (ROOT / "data/expansion/openrouter-model-catalog-2026-10-18.json").read_bytes()
    catalog = json.loads(raw_catalog)
    catalog_rows = {row["id"]: row for row in catalog["data"]}
    return dataset, snapshot, catalog_rows


def test_review_rejects_changed_crosswalk_model_name_and_response_id():
    dataset, snapshot, catalog_rows = load_inputs()
    dataset = copy.deepcopy(dataset)
    next(row for row in dataset["models"] if row["id"] == "deepseek_r1")["name"] = "DeepSeek R1 0528"
    with pytest.raises(ValueError, match="Curated model name changed"):
        reviewer.review(dataset, snapshot, catalog_rows, "catalog")

    dataset, snapshot, catalog_rows = load_inputs()
    snapshot = copy.deepcopy(snapshot)
    snapshot["endpoints"]["deepseek/deepseek-r1"]["data"]["data"]["id"] = "deepseek/deepseek-r1-0528"
    with pytest.raises(ValueError, match="identity mismatch"):
        reviewer.review(dataset, snapshot, catalog_rows, "catalog")


def test_review_rejects_wrong_endpoint_url():
    dataset, snapshot, catalog_rows = load_inputs()
    snapshot = copy.deepcopy(snapshot)
    snapshot["endpoints"]["deepseek/deepseek-r1"]["url"] = "https://example.com/fake"
    with pytest.raises(ValueError, match="Unexpected endpoint URL"):
        reviewer.review(dataset, snapshot, catalog_rows, "catalog")


@pytest.mark.parametrize("damage", ["hash", "parsed_body"])
def test_review_rejects_raw_response_hash_or_parsed_data_mismatch(damage):
    dataset, snapshot, catalog_rows = load_inputs("openrouter-endpoints-current-2026-10-18.json")
    snapshot = copy.deepcopy(snapshot)
    envelope = snapshot["endpoints"]["deepseek/deepseek-r1"]
    if damage == "hash":
        envelope["sha256"] = "0" * 64
    else:
        envelope["data"]["data"]["name"] = "mutated parsed data"
    with pytest.raises(ValueError, match="hash mismatch|differs from parsed"):
        reviewer.review(dataset, snapshot, catalog_rows, "catalog", refresh_existing=True)


def test_review_rejects_duplicate_route_identity_in_snapshot():
    dataset, snapshot, catalog_rows = load_inputs()
    snapshot = copy.deepcopy(snapshot)
    endpoints = snapshot["endpoints"]["deepseek/deepseek-v4-pro-0813"]["data"]["data"]["endpoints"]
    endpoints.append(copy.deepcopy(endpoints[0]))
    with pytest.raises(ValueError, match="Duplicate endpoint route identity"):
        reviewer.review(dataset, snapshot, catalog_rows, "catalog")


def test_review_is_idempotent_after_import():
    dataset, snapshot, catalog_rows = load_inputs()
    dataset = copy.deepcopy(dataset)
    additions, sources, _ = reviewer.review(dataset, snapshot, catalog_rows, "catalog")
    dataset["routes"].extend(additions)
    dataset["sources"].extend(sources)
    additions_again, sources_again, rows_again = reviewer.review(dataset, snapshot, catalog_rows, "catalog")
    assert additions_again == []
    assert sources_again == []
    assert len(rows_again) == 86
    assert {row["classification"] for row in rows_again} == {"already_curated"}


def test_check_mode_does_not_write_dataset_or_audit(tmp_path, monkeypatch):
    dataset_path = tmp_path / "dataset.json"
    audit_path = tmp_path / "audit.md"
    original = (ROOT / "data/curated/dataset.json").read_bytes()
    dataset_path.write_bytes(original)
    monkeypatch.setattr(sys, "argv", [
        "review-openrouter-endpoints.py",
        "--dataset", str(dataset_path),
        "--snapshot", str(ROOT / "data/expansion/openrouter-endpoints-2026-10-18.json"),
        "--catalog", str(ROOT / "data/expansion/openrouter-model-catalog-2026-10-18.json"),
        "--catalog-provenance", str(ROOT / "data/expansion/openrouter-model-catalog-provenance-2026-10-18.json"),
        "--audit", str(audit_path),
        "--check",
    ])
    assert reviewer.main() == 0
    assert dataset_path.read_bytes() == original
    assert not audit_path.exists()


def test_refresh_marks_missing_route_unknown_but_retains_failed_model():
    dataset, snapshot, catalog = load_inputs('openrouter-endpoints-current-2026-10-24.json')
    missing = {'id': 'openrouter:moonshotai/kimi-k3:Removed:removed:default', 'upstream_model_id': 'moonshotai/kimi-k3', 'model_id': 'kimi_k3', 'provider': 'Removed', 'availability': 'listed', 'source_ids': []}
    dataset['routes'].append(missing)
    failed_routes = [r.copy() for r in dataset['routes'] if r.get('upstream_model_id') == 'deepseek/deepseek-r1']
    reviewer.review(dataset, snapshot, catalog, 'catalog', refresh_existing=True)
    assert missing['availability'] == 'unknown'
    assert [r for r in dataset['routes'] if r.get('upstream_model_id') == 'deepseek/deepseek-r1'] == failed_routes


def test_review_rejects_empty_healthy_endpoint_before_import():
    dataset, snapshot, catalog = load_inputs()
    snapshot['endpoints']['deepseek/deepseek-r1']['data']['data']['endpoints'] = []
    with pytest.raises(ValueError, match='empty'):
        reviewer.review(dataset, snapshot, catalog, 'catalog')
