from datetime import date
import json

import pytest
from pydantic import ValidationError

from pipeline.build import assess_saturation, build, select_observations
from pipeline.cli import main
from pipeline.schema import Dataset


def sample(value=0):
    return Dataset.model_validate({
        "sources": [{"id":"s","url":"https://example.test/report","title":"Report","publisher":"Lab"}],
        "labs": [{"id":"lab","name":"Lab"}],
        "models": [{"id":"m","lab_ids":["lab"],"family_id":"f","name":"Model","release_date":"2026-01-02","release_date_precision":"day","first_seen_at":"2026-02-01T00:00:00Z"}],
        "configurations": [{"id":"c","model_id":"m","mode":"unknown"}],
        "benchmarks": [{"id":"b","family_id":"bf","name":"Test","version":"1","category":"coding","modality":"text","metric_name":"score","unit":"%","lower_bound":0,"upper_bound":100,"direction":"higher"}],
        "series": [{"id":"e","benchmark_id":"b","protocol":"official"}],
        "observations": [{"id":"o","configuration_id":"c","benchmark_id":"b","series_id":"e","value":value,"unit":"%","source_id":"s","locator":"Table 1","evaluator":"Lab","reporting_relationship":"self_report","review_state":"reviewed"}],
        "prices": [{"id":"p","currency":"USD","input_price":"0","price_unit":"USD per million tokens","observed_at":"2026-01-02T00:00:00Z","source_id":"s"}],
    })


def test_zero_is_valid_and_build_keeps_it(tmp_path):
    data = sample(0)
    build(data, tmp_path)
    results = json.loads((tmp_path / "results.json").read_text())
    assert results["observations"][0]["value"] == 0
    assert json.loads((tmp_path / "market.json").read_text())["prices"][0]["input_price"] == "0"


def test_rebuild_preserves_feeds_unless_explicitly_replaced(tmp_path):
    feeds = [{"source_id": "test", "status": "ok", "as_of": "2026-10-17T00:00:00Z"}]
    build(sample(), tmp_path, feeds)
    build(sample(10), tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    comparison = json.loads((tmp_path / "comparison.json").read_text())
    assert manifest["feeds"] == feeds
    assert comparison["manifest"] == manifest
    assert comparison["observations"][0]["value"] == 10
    build(sample(10), tmp_path, [])
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["feeds"] == []
    assert json.loads((tmp_path / "comparison.json").read_text())["manifest"] == manifest


@pytest.mark.parametrize("with_staging", [False, True])
def test_offline_cli_rebuild_is_identical_with_or_without_staging(tmp_path, monkeypatch, with_staging):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "dataset.json"
    source.write_text(sample().model_dump_json())
    output = tmp_path / "web/public/data"
    feeds = [{"source_id": "test", "status": "ok"}]
    build(sample(), output, feeds)
    before = {p.name: p.read_bytes() for p in output.iterdir() if p.is_file()}
    if with_staging:
        staging = tmp_path / "data/staging"
        staging.mkdir(parents=True)
        (staging / "test.json").write_text(json.dumps({"source": "test", "status": "stale"}))
    assert main(["build", "--offline", "--input", str(source)]) == 0
    assert {p.name: p.read_bytes() for p in output.iterdir() if p.is_file()} == before
    if with_staging:
        assert main(["build", "--input", str(source)]) == 0
        manifest = json.loads((output / "manifest.json").read_text())
        assert manifest["feeds"][0]["status"] == "stale"
        assert json.loads((output / "comparison.json").read_text())["manifest"] == manifest


def test_foreign_key_unit_and_bounds_reject_publication():
    raw = sample().model_dump(mode="json")
    raw["observations"][0]["source_id"] = "missing"
    with pytest.raises(ValidationError): Dataset.model_validate(raw)
    raw = sample().model_dump(mode="json")
    raw["observations"][0]["unit"] = "points"
    with pytest.raises(ValidationError): Dataset.model_validate(raw)
    raw = sample().model_dump(mode="json")
    raw["observations"][0]["value"] = 101
    with pytest.raises(ValidationError): Dataset.model_validate(raw)


def test_duplicate_ids_and_conflicting_missingness_reject():
    raw = sample().model_dump(mode="json")
    raw["models"].append(raw["models"][0])
    with pytest.raises(ValidationError): Dataset.model_validate(raw)
    raw = sample().model_dump(mode="json")
    raw["missing_cells"] = [{"id":"mc","configuration_id":"c","benchmark_id":"b","reason":"not_reported"}]
    with pytest.raises(ValidationError): Dataset.model_validate(raw)


def test_release_date_and_catalog_first_seen_are_separate():
    model = sample().models[0]
    assert model.release_date == date(2026, 1, 2)
    assert model.first_seen_at.date() == date(2026, 2, 1)


def test_selection_excludes_candidates_and_exposes_conflicts_without_winner():
    raw = sample().model_dump(mode="json")
    candidate = dict(raw["observations"][0], id="candidate", review_state="candidate")
    conflict = dict(raw["observations"][0], id="conflict", value=10)
    raw["observations"] += [candidate, conflict]
    cells = select_observations(Dataset.model_validate(raw))
    assert len(cells) == 1
    assert cells[0]["state"] == "disputed"
    assert cells[0]["value"] is None
    assert cells[0]["observation_ids"] == ["conflict", "o"]


def test_saturation_counts_releases_once_and_requires_two_labs_in_one_series():
    raw = sample(97).model_dump(mode="json")
    raw["series"][0]["comparability_status"] = "comparable"
    raw["labs"].append({"id":"lab2","name":"Lab 2"})
    raw["models"].extend([
        {"id":"m2","lab_ids":["lab2"],"family_id":"f2","name":"Model 2"},
        {"id":"m3","lab_ids":["lab2"],"family_id":"f3","name":"Model 3"},
    ])
    raw["configurations"].extend([
        {"id":"c2","model_id":"m2"},{"id":"c3","model_id":"m3"},
        {"id":"c-alt","model_id":"m"},
    ])
    raw["observations"].extend([
        {"id":"o2","configuration_id":"c2","benchmark_id":"b","series_id":"e","value":98,"unit":"%","source_id":"s","locator":"Table 1","evaluator":"Lab","reporting_relationship":"self_report","review_state":"reviewed"},
        {"id":"o3","configuration_id":"c3","benchmark_id":"b","series_id":"e","value":99,"unit":"%","source_id":"s","locator":"Table 1","evaluator":"Lab","reporting_relationship":"self_report","review_state":"reviewed"},
        {"id":"o-alt","configuration_id":"c-alt","benchmark_id":"b","series_id":"e","value":99,"unit":"%","source_id":"s","locator":"Table 1","evaluator":"Lab","reporting_relationship":"self_report","review_state":"reviewed"},
    ])
    assessment = assess_saturation(Dataset.model_validate(raw))[0]
    assert assessment["state"] == "saturated"
    assert assessment["distinct_model_count"] == 3
    assert assessment["distinct_lab_count"] == 2
    assert len(assessment["models_at_threshold"]) == 3

    # Three qualifying releases from one lab are not sufficient, even when a
    # lower-scoring fourth release supplies a second lab.
    raw["models"][1]["lab_ids"] = ["lab"]
    raw["models"][2]["lab_ids"] = ["lab"]
    raw["models"].append({"id":"m4","lab_ids":["lab2"],"family_id":"f4","name":"Model 4"})
    raw["configurations"].append({"id":"c4","model_id":"m4"})
    raw["observations"].append({"id":"o4","configuration_id":"c4","benchmark_id":"b","series_id":"e","value":94,"unit":"%","source_id":"s","locator":"Table 1","evaluator":"Lab","reporting_relationship":"self_report","review_state":"reviewed"})
    assessment = assess_saturation(Dataset.model_validate(raw))[0]
    assert assessment["state"] == "not_saturated"
    assert assessment["high_lab_count"] == 1

    raw["observations"] = [o for o in raw["observations"] if o["configuration_id"] in ("c","c-alt")]
    assessment = assess_saturation(Dataset.model_validate(raw))[0]
    assert assessment["state"] == "unknown"
    assert assessment["distinct_model_count"] == 1


def test_saturation_unknown_without_matched_series_and_excludes_zero_width():
    raw = sample(99).model_dump(mode="json")
    assessment = assess_saturation(Dataset.model_validate(raw))[0]
    assert assessment["state"] == "unknown"
    raw["benchmarks"][0]["upper_bound"] = 0
    raw["benchmarks"][0]["lower_bound"] = 0
    raw["observations"][0]["value"] = 0
    assessment = assess_saturation(Dataset.model_validate(raw))[0]
    assert assessment["state"] == "ineligible"
    assert "metric bounds have no positive range" in assessment["ineligible_reasons"]
