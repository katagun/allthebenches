import json
from pathlib import Path

from pipeline.schema import Dataset

ROOT = Path(__file__).resolve().parents[1]


def test_arena_snapshot_keeps_ratings_and_agent_signals_distinct():
    raw = json.loads((ROOT / "data/curated/dataset.json").read_text(encoding="utf-8"))
    dataset = Dataset.model_validate(raw)
    benchmarks = {b.id: b for b in dataset.benchmarks}
    observations = {o.id: o for o in dataset.observations}

    text = benchmarks["arena_text_overall_bt_20261015"]
    assert text.unit == "Arena rating points"
    assert text.direction == "higher"
    assert text.lower_bound is None and text.upper_bound is None

    net = benchmarks["arena_agent_net_improvement_20261016"]
    assert net.unit == "percent"
    assert net.lower_bound is None and net.upper_bound is None
    assert net.direction == "higher"

    hallucination = benchmarks["arena_agent_tool_hallucination_20261016"]
    assert hallucination.direction == "lower"
    assert all(observations[o.id].unit == hallucination.unit for o in dataset.observations if o.benchmark_id == hallucination.id)


def test_arena_observations_use_only_exact_curated_configurations_and_sources():
    raw = json.loads((ROOT / "data/expansion/arena.json").read_text(encoding="utf-8"))
    source_ids = {s["id"] for s in raw["sources"]}
    allowed_configs = {"claude_opus55_max", "gpt6_astra_max", "claude_fable51_max", "gpt61_sol_max", "muse_wonder_max", "muse_spark13_max", "grok47_xhigh"}
    assert len(raw["benchmarks"]) == 10
    assert all(o["configuration_id"] in allowed_configs for o in raw["observations"])
    assert all(o["source_id"] in source_ids for o in raw["observations"])
    assert all(o["evaluated_at"] is None for o in raw["observations"])
    assert all(o["uncertainty"]["confidence_level"] is None for o in raw["observations"])

    preset = json.loads((ROOT / "data/presets/arena_oct2026.json").read_text(encoding="utf-8"))
    assert set(preset["benchmark_ids"]) == {b["id"] for b in raw["benchmarks"]}
    assert set(preset["model_configuration_ids"]) == allowed_configs
