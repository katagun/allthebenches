"""Source configuration identity must survive unrelated catalog additions."""
import json
from types import SimpleNamespace
import sys

import pytest

from pipeline.arena_import import build as arena_build, source_configuration_index
from pipeline.livebench_import import build as livebench_build


def dataset(evaluator):
    return {
        "models": [{"id": "model", "name": "Model"}],
        "configurations": [
            {"id": "epoch_model_high", "model_id": "model", "reasoning_label": "high"},
            {"id": "original_source_config", "model_id": "model", "reasoning_label": "high"},
        ],
        "benchmarks": [],
        "observations": [{"id": "prior", "configuration_id": "original_source_config",
            "benchmark_id": "old_benchmark", "evaluator": evaluator,
            "setup": {"upstream_model_id": "Model (High)", "reasoning_effort": "high"}}],
    }


def test_arena_reuses_reviewed_identity_not_first_matching_effort(monkeypatch, tmp_path):
    row = {"model_name": "Model (High)", "category": "overall", "leaderboard_publish_date": "2026-10-19",
           "rating": 1234, "rating_lower": 1200, "rating_upper": 1250, "vote_count": 100}
    parquet = SimpleNamespace(read_table=lambda _: SimpleNamespace(to_pylist=lambda: [row]))
    monkeypatch.setitem(sys.modules, "pyarrow", SimpleNamespace(parquet=parquet))
    monkeypatch.setitem(sys.modules, "pyarrow.parquet", parquet)
    data = dataset("Arena")
    fragment, _ = arena_build(data, {"text": tmp_path / "capture"}, [{"path": "text/latest-file", "sha256": "a" * 64}])
    assert fragment["observations"][0]["configuration_id"] == "original_source_config"
    data["observations"].extend(fragment["observations"])
    replay, coverage = arena_build(data, {"text": tmp_path / "capture"}, [{"path": "text/latest-file", "sha256": "a" * 64}])
    assert replay["observations"] == []
    assert coverage["counts"]["duplicate_identical"] == 1
    row["vote_count"] = 101
    changed, _ = arena_build(data, {"text": tmp_path / "capture"}, [{"path": "text/latest-file", "sha256": "b" * 64}])
    assert len(changed["observations"]) == 1
    data["observations"] = []
    fragment, _ = arena_build(data, {"text": tmp_path / "capture"}, [{"path": "text/latest-file", "sha256": "a" * 64}])
    assert fragment["observations"][0]["configuration_id"] == "arena_hf_model_high"


def test_livebench_reuses_identity_and_keeps_new_source_setup_separate(tmp_path):
    paths = []
    for name, value in {
        "v1.csv": "model,task\nModel (High),50\n",
        "v2.csv": "model,task\nModel (High),51\n",
        "cats1.json": {"Reasoning": ["task"]},
        "cats2.json": {"Reasoning": ["task"]},
        "breakdown.json": {},
        "frontend.json": {"v2_models": {"Model (High)": {"display_name": "Model", "effort": "high"}}},
    }.items():
        path = tmp_path / name
        path.write_text(value if isinstance(value, str) else json.dumps(value))
        paths.append(path)
    data = dataset("LiveBench")
    fragment, _ = livebench_build(data, *paths)
    assert {o["configuration_id"] for o in fragment["observations"]} == {"original_source_config"}
    data["observations"] = []
    fragment, _ = livebench_build(data, *paths)
    assert {o["configuration_id"] for o in fragment["observations"]} == {"livebench_model_high"}


def test_ambiguous_source_identity_fails_closed():
    data = dataset("Arena")
    data["observations"].append({**data["observations"][0], "configuration_id": "epoch_model_high"})
    with pytest.raises(ValueError, match="Ambiguous Arena"):
        source_configuration_index(data, "Arena")
