import json
import sys
import types
from copy import deepcopy
from pathlib import Path

from pipeline import arena_import

ROOT = Path(__file__).resolve().parents[1]


def dataset_before_staged_import(dataset, fragment_name):
    """Remove this importer’s integrated records to create a stable pre-import base."""
    base = deepcopy(dataset)
    fragment = json.loads((ROOT / f"data/expansion/{fragment_name}.json").read_text())
    for table, records in fragment.items():
        ids = {item["id"] for item in records}
        base[table] = [item for item in base[table] if item["id"] not in ids]
    return base


def test_arena_import_pins_revision_and_keeps_explicit_effort():
    assert arena_import.REVISION == "0ebb411abf001fa30ad48fc7e49c5cd5891d5f8a"
    assert arena_import.parse_label("GPT-6 Astra (Max)") == ("GPT-6 Astra", "max")
    assert arena_import.parse_label("GPT-6 Astra") == ("GPT-6 Astra", "unknown")
    assert arena_import.parse_label("GPT-6 Astra (Future)") == ("GPT-6 Astra (Future)", "unknown")


def test_arena_import_accounts_duplicate_and_new_exact_configuration(monkeypatch, tmp_path):
    integrated = json.loads((ROOT / "data/curated/dataset.json").read_text())
    dataset = dataset_before_staged_import(integrated, "arena-hf")
    # Make this fixture's reviewed source identity explicit. Generic equal-effort
    # configurations from other evaluators must not establish source identity.
    prior = next(o for o in dataset["observations"]
                 if o["id"] == "arena_gpt6_astra_max_text_overall_20261015")
    prior["setup"].update(upstream_model_id="GPT-6 Astra (Max)", reasoning_effort="max")
    rows = [
        {"model_name": "GPT-6 Astra (Max)", "organization": "openai", "license": "Proprietary",
         "rating": 1500.5, "rating_lower": 1498.0, "rating_upper": 1503.0, "variance": 1.5,
         "vote_count": 1234, "rank": 1, "category": "overall", "leaderboard_publish_date": "2026-10-15"},
        {"model_name": "GPT-6 Astra (High)", "organization": "openai", "license": "Proprietary",
         "rating": 1490.5, "rating_lower": 1488.0, "rating_upper": 1493.0, "variance": 1.5,
         "vote_count": 567, "rank": 2, "category": "overall", "leaderboard_publish_date": "2026-10-15"},
        {"model_name": "Uncatalogued Model (High)", "organization": "unknown", "license": "unknown",
         "rating": 1400.0, "rating_lower": 1390.0, "rating_upper": 1410.0, "variance": 2.0,
         "vote_count": 10, "rank": 3, "category": "overall", "leaderboard_publish_date": "2026-10-15"},
        {"model_name": "Claude Opus 5.5 (High)", "organization": "anthropic", "license": "Proprietary",
         "rating": 1475.0, "rating_lower": 1470.0, "rating_upper": 1480.0, "variance": 1.0,
         "vote_count": 42, "rank": 4, "category": "overall", "leaderboard_publish_date": "2026-10-15"},
    ]
    path = tmp_path / "text/latest-00000-of-00001.parquet"
    path.parent.mkdir()
    path.write_bytes(b"fixture")
    fake_parquet = types.ModuleType("pyarrow.parquet")
    fake_parquet.read_table = lambda _: types.SimpleNamespace(to_pylist=lambda: rows)
    fake_pyarrow = types.ModuleType("pyarrow")
    fake_pyarrow.parquet = fake_parquet
    monkeypatch.setitem(sys.modules, "pyarrow", fake_pyarrow)
    monkeypatch.setitem(sys.modules, "pyarrow.parquet", fake_parquet)
    manifest = [{"path": "text/latest-00000-of-00001.parquet", "sha256": arena_import.sha256(path),
                 "lfs": {"oid": arena_import.sha256(path)}}]
    fragment, coverage = arena_import.build(dataset, {"text": path}, manifest)
    assert len(fragment["observations"]) == 3
    imported = next(o for o in fragment["observations"] if o["configuration_id"] == "arena_hf_gpt6_astra_high")
    assert imported["configuration_id"] == "arena_hf_gpt6_astra_high"
    assert imported["setup"]["reasoning_effort"] == "high"
    assert imported["uncertainty"]["lower_bound"] == 1488.0
    assert imported["setup"]["source_count"] == 567
    assert {d["status"] for d in coverage["decisions"]} == {"preserved_alternate_source_snapshot"}
    assert coverage["status_counts_by_partition"]["text"]["candidate_import"] == 2
    assert coverage["status_counts_by_partition"]["text"]["unresolved_alias"] == 1
    preserved = next(d for d in coverage["decisions"] if d["status"] == "preserved_alternate_source_snapshot")
    assert preserved["same_value"] is False
    assert preserved["source_value"] == 1500.5
    assert coverage["denominators"]["scored_records"] == 4
    assert any(c["id"] == "arena_hf_claude_opus55_high" for c in fragment["configurations"])
    assert any(o["configuration_id"] == "arena_hf_claude_opus55_high" for o in fragment["observations"])


def test_arena_snapshot_reuse_requires_exact_date_and_ips_metrics_keep_signed_direction():
    assert arena_import.category_name("text", "overall", "2026-10-14") == "arena_hf_text_overall_20261014"
    assert arena_import.category_name("text", "overall", "2026-10-15") == "arena_text_overall_bt_20261015"
    staged = json.loads((ROOT / "data/expansion/arena-hf.json").read_text())
    agent_benchmarks = {b["id"]: b for b in staged["benchmarks"] if b["id"].startswith("arena_hf_agent_")}
    assert agent_benchmarks
    assert {b["direction"] for b in agent_benchmarks.values()} == {"higher"}
    hallucination = next(b for b in agent_benchmarks.values() if "tool_hallucination" in b["id"])
    obs = next(o for o in staged["observations"] if o["benchmark_id"] == hallucination["id"])
    assert obs["value"] == obs["setup"]["source_value"]
    assert obs["unit"] == "IPS score"
    assert obs["uncertainty"]["confidence_level"] == 95
    model_lookup, _ = arena_import.indexes(json.loads((ROOT / "data/curated/dataset.json").read_text()))
    assert arena_import.resolve_source_model("Qwen3.8-Max", model_lookup)[2] == "qwen38_max"
    assert arena_import.resolve_source_model("Qwen 3.8 27B", model_lookup)[2] == "qwen38_27b"
    dated = arena_import.resolve_source_model("Claude 3.5 Sonnet 20240620", model_lookup)
    assert dated[2] == "claude35_sonnet_june"
    deepseek = arena_import.resolve_source_model("DeepSeek-V4-Pro (High, 20260813)", model_lookup)
    assert deepseek[2:3] == ("deepseek_v4_pro_0813",)
    assert deepseek[1] == "high"
    assert arena_import.resolve_source_model("deepseek-r1-0528", model_lookup)[2] is None
    assert arena_import.resolve_source_model("GLM-5.2 (Max)", model_lookup)[2] is None
