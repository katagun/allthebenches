import json
from pathlib import Path

import pytest

from pipeline import aa_import
from pipeline.aa_import import build_fragment, extract_flight_payload
from pipeline.merge_expansions import merge_fragments
from pipeline.schema import Dataset

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def stable_aa_registry(monkeypatch):
    """Keep adapter tests independent of integration changes to curated data."""
    model_ids = {
        "gpt-6-astra": "gpt6_astra",
        "mistral-large-4": "mistral_large4",
        "deepseek-r1": "deepseek_r1",
        "gpt-4": "gpt4",
    }
    existing_benchmarks = []
    for bench_id, name, metric in [
        ("terminal_bench_4", "Terminal-Bench 4.0", "pass@1"),
        ("terminal_bench_21", "Terminal-Bench 2.1", "mean pass@1"),
        ("terminal_science_01", "Terminal-Bench Science 0.1", "pass@1"),
        ("frontiercode_v11", "FrontierCode v1.1 Main", "task success rate"),
        ("harvey_lab_aa_v11", "Harvey LAB-AA v1.1", "hallucination-gated all-pass rate"),
    ]:
        existing_benchmarks.append({
            "id": bench_id, "family_id": bench_id, "name": name,
            "version": "fixture", "category": "test", "modality": "text",
            "metric_name": metric, "unit": "%", "lower_bound": 0,
            "upper_bound": 100, "direction": "higher",
        })
    monkeypatch.setattr(aa_import, "MODEL_IDS", model_ids)
    monkeypatch.setattr(aa_import, "_CANONICAL", {"benchmarks": existing_benchmarks})
    monkeypatch.setattr(aa_import, "CONFIGS_BY_MODEL", {
        model_id: [] for model_id in model_ids.values()
    })


def _load_fragment():
    return json.loads((ROOT / "data/expansion/aa-2026-10-18.json").read_text(encoding="utf-8"))


def test_staged_fragment_merges_idempotently_and_promotes_only_on_review():
    fragment = _load_fragment()
    assert all(o["review_state"] == "candidate" for o in fragment["observations"])
    fragment_benchmarks = {b["id"] for b in fragment["benchmarks"]}
    referenced_benchmarks = {o["benchmark_id"] for o in fragment["observations"]}
    existing_benchmark_ids = referenced_benchmarks - fragment_benchmarks
    existing_benchmarks = []
    for bench_id in existing_benchmark_ids:
        observation = next(o for o in fragment["observations"] if o["benchmark_id"] == bench_id)
        existing_benchmarks.append({
            "id": bench_id, "family_id": bench_id, "name": bench_id,
            "version": "fixture", "category": "test", "modality": "text",
            "metric_name": "fixture", "unit": observation["unit"],
            "direction": "higher",
        })
    model_ids = {config["model_id"] for config in fragment["configurations"]}
    fixture = Dataset(
        models=[{"id": mid, "lab_ids": [], "family_id": f"fixture_{mid}", "name": mid} for mid in model_ids],
        benchmarks=existing_benchmarks,
    ).model_dump(mode="json")
    merged = merge_fragments(fixture, [fragment], reviewed=True)
    assert len(merged["observations"]) == len(fragment["observations"])
    assert {o["review_state"] for o in merged["observations"]} == {"reviewed"}
    assert merge_fragments(merged, [fragment], reviewed=True) == merged


def test_aa_maps_documented_fields_with_independent_units_and_filtering():
    fragment = _load_fragment()
    assert len(fragment["observations"]) > 900
    by_field = {}
    for obs in fragment["observations"]:
        by_field.setdefault(obs["locator"].rsplit(".", 1)[-1], []).append(obs)
    # AA serializes these as fractions; the existing variants are percent.
    mistral_terminal = next(o for o in fragment["observations"] if o["configuration_id"] == "aa_mistral_large4_unknown" and o["benchmark_id"] == "terminal_bench_4")
    assert mistral_terminal["value"] == 0.267676767676768 * 100
    assert mistral_terminal["setup"]["source_field_value"] == 0.267676767676768
    assert mistral_terminal["setup"]["normalization"]["formula"] == "source fraction × 100"
    # Signed index and Elo retain their source units without percentage scaling.
    omni = next(o for o in fragment["observations"] if o["configuration_id"] == "aa_mistral_large4_unknown" and o["benchmark_id"] == "aa_omniscience_index")
    assert omni["value"] == -5.3 and omni["unit"] == "points"
    hle = next(o for o in fragment["observations"] if o["configuration_id"] == "aa_mistral_large4_unknown" and o["benchmark_id"] == "aa_hle_text")
    assert hle["unit"] == "%" and hle["value"] == 0.35032437442075995 * 100
    briefcase = next(o for o in fragment["observations"] if o["configuration_id"] == "aa_mistral_large4_unknown" and o["benchmark_id"] == "aa_briefcase_v11")
    assert briefcase["value"] == 1391.97 and briefcase["unit"] == "Elo"
    assert briefcase["uncertainty"] == {
        "type": "confidence_interval", "confidence_level": 0.95,
        "lower": 1381.46, "upper": 1402.29, "unit": "Elo",
    }
    assert "aa_gdpval_v21" in {o["benchmark_id"] for o in fragment["observations"]}
    assert "aa_omniscience_accuracy" in {o["benchmark_id"] for o in fragment["observations"]}
    assert "aa_omniscience_hallucination" in {o["benchmark_id"] for o in fragment["observations"]}
    omni_subsets = {b["id"]: b["subset"] for b in fragment["benchmarks"] if b["id"].startswith("aa_omniscience_")}
    assert omni_subsets == {
        "aa_omniscience_index": "Index",
        "aa_omniscience_accuracy": "Accuracy",
        "aa_omniscience_hallucination": "Hallucination rate",
    }
    assert "aa_scicode" in {o["benchmark_id"] for o in fragment["observations"]}
    assert "aa_ifbench" in {o["benchmark_id"] for o in fragment["observations"]}
    assert "aa_apex_agents" in {o["benchmark_id"] for o in fragment["observations"]}
    assert all(o["review_state"] == "candidate" for o in fragment["observations"])
    assert all(s["comparability_status"] == "unknown" for s in fragment["series"])
    scicode = next(o for o in fragment["observations"] if o["benchmark_id"] == "aa_scicode")
    assert scicode["setup"]["source_caveat"] == {
        "status": "Artificial Analysis marks SciCode under review",
        "reason": "Independent audit of the SciCode-Verified dataset.",
        "url": "https://artificialanalysis.ai/evaluations/scicode",
    }
    assert not any("Cost" in b["name"] or "Time" in b["name"] for b in fragment["benchmarks"])


def test_aa_adapter_omits_unknown_models_and_null_fields():
    raw = json.dumps({"slug": "unmapped-model", "id": "provider-id", "terminalBench40": 0.5}).encode()
    fragment = build_fragment(json.loads(raw), raw, "2026-10-18T14:22:00Z")
    assert fragment == {"sources": [], "benchmarks": [], "configurations": [], "series": [], "observations": []}


def test_aa_exact_release_alias_zero_null_signed_and_estimated_index_rules():
    raw = json.dumps({
        "slug": "display-label-differs", "id": "aa-r1", "release": {"slug": "deepseek-r1"},
        "effort": {"slug": "max"}, "intelligenceIndex": 0,
        "intelligenceIndexIsEstimated": False, "hle": 0,
        "omniscience": -100, "omniscienceAccuracy": 0,
        "omniscienceHallucinationRate": 1, "gpqa": None,
    }).encode()
    fragment = build_fragment(json.loads(raw), raw, "2026-10-18T14:22:00Z")
    by_bench = {o["benchmark_id"]: o for o in fragment["observations"]}
    assert by_bench["aa_intelligence_index_v432"]["value"] == 0
    assert by_bench["aa_hle_text"]["value"] == 0
    assert by_bench["aa_omniscience_index"]["value"] == -100
    assert by_bench["aa_omniscience_accuracy"]["value"] == 0
    assert by_bench["aa_omniscience_hallucination"]["value"] == 100
    assert next(b for b in fragment["benchmarks"] if b["id"] == "aa_omniscience_hallucination")["direction"] == "lower"
    assert "aa_gpqa_diamond" not in by_bench

    raw_estimated = json.dumps({
        "slug": "deepseek-r1", "id": "aa-r1-est", "release": {"slug": "deepseek-r1"},
        "effort": {"slug": "max"}, "intelligenceIndex": 10,
        "intelligenceIndexIsEstimated": True,
    }).encode()
    estimated = build_fragment(json.loads(raw_estimated), raw_estimated, "2026-10-18T14:22:00Z")
    assert "aa_intelligence_index_v432" not in {o["benchmark_id"] for o in estimated["observations"]}


def test_published_effort_creates_missing_config_and_unknown_setting_stays_unknown():
    raw = json.dumps({
        "slug": "deepseek-r1", "id": "aa-deepseek-r1-medium",
        "release": {"slug": "deepseek-r1"},
        "effort": {"slug": "medium", "label": "medium"}, "hle": 0.5,
    }).encode()
    fragment = build_fragment(json.loads(raw), raw, "2026-10-18T14:22:00Z")
    assert fragment["configurations"] == [{
        "id": "aa_deepseek_r1_medium", "model_id": "deepseek_r1",
        "reasoning_label": "medium", "reasoning_budget_tokens": None,
        "mode": "enabled", "precision": None,
    }]
    assert fragment["observations"][0]["configuration_id"] == "aa_deepseek_r1_medium"

    raw_unknown = json.dumps({"slug": "gpt-4", "id": "aa-gpt4", "release": {"slug": "gpt-4"}, "hle": 0.5}).encode()
    unknown = build_fragment(json.loads(raw_unknown), raw_unknown, "2026-10-18T14:22:00Z")
    assert unknown["configurations"] == [{
        "id": "aa_gpt4_unknown", "model_id": "gpt4", "reasoning_label": None,
        "reasoning_budget_tokens": None, "mode": "unknown", "precision": None,
    }]
    assert unknown["observations"][0]["configuration_id"] == "aa_gpt4_unknown"


def test_existing_source_specific_configuration_is_reused():
    config = {
        "id": "aa_deepseek_r1_medium", "model_id": "deepseek_r1",
        "reasoning_label": "medium", "reasoning_budget_tokens": None,
        "mode": "enabled", "precision": None,
    }
    aa_import.CONFIGS_BY_MODEL["deepseek_r1"].append(config)
    raw = json.dumps({
        "slug": "deepseek-r1-medium", "id": "aa-r1-medium",
        "release": {"slug": "deepseek-r1"}, "effort": {"slug": "medium"}, "hle": 0.5,
    }).encode()
    fragment = build_fragment(json.loads(raw), raw, "2026-10-18T14:22:00Z")
    assert fragment["configurations"] == []
    assert fragment["observations"][0]["configuration_id"] == config["id"]


def test_configuration_resolution_is_stable_across_duplicate_effort_labels():
    source_id = "aa_gpt6_astra_max"
    model_configs = aa_import.CONFIGS_BY_MODEL["gpt6_astra"]
    original = list(model_configs)
    try:
        model_configs.extend([
            {"id": "epoch_gpt6_astra_max_a", "model_id": "gpt6_astra", "reasoning_label": "max", "mode": "enabled"},
            {"id": "epoch_gpt6_astra_max_b", "model_id": "gpt6_astra", "reasoning_label": "max", "mode": "enabled"},
        ])
        row = {"release": {"slug": "gpt-6-astra"}, "effort": {"slug": "max"}}
        config_id, config = aa_import._resolve_configuration(row, "gpt6_astra")
        assert config_id == source_id
        assert config is not None and config["reasoning_label"] == "max"
    finally:
        model_configs[:] = original

    row_default = {"release": {"slug": "gpt-6-astra"}, "suffix": "Default Fallback"}
    config_id, config = aa_import._resolve_configuration(row_default, "gpt6_astra")
    assert config_id == "aa_gpt6_astra_default"
    assert config["mode"] == "default"
    row_none = {"release": {"slug": "gpt-6-astra"}, "effort": {"slug": "none"}}
    config_id, config = aa_import._resolve_configuration(row_none, "gpt6_astra")
    assert config_id == "aa_gpt6_astra_none"
    assert config["mode"] == "disabled"

    row = {
        "slug": "gpt-6-astra-max", "id": "aa-astra-max",
        "release": {"slug": "gpt-6-astra"}, "effort": {"slug": "max"}, "hle": 0.5,
    }
    raw = json.dumps(row).encode()
    first = build_fragment(row, raw, "2026-10-18T14:22:00Z")
    config = first["configurations"][0]
    model_configs = aa_import.CONFIGS_BY_MODEL["gpt6_astra"]
    original = list(model_configs)
    try:
        model_configs.append(config)
        rerun = build_fragment(row, raw, "2026-10-18T14:22:00Z")
        assert rerun["configurations"] == []
        assert rerun["observations"][0]["id"] == first["observations"][0]["id"]
        assert rerun["series"][0]["id"] == first["series"][0]["id"]
    finally:
        model_configs[:] = original


def test_aa_flight_extractor_combines_model_list_and_current_model():
    raw = (
        b'4:{"models":[{"id":"aa-one","slug":"gpt-6-astra",'
        b'"release":{"slug":"gpt-6-astra"},"effort":{"slug":"max"},'
        b'"terminalBench40":0.5}],"currentModel":{"id":"aa-two",'
        b'"slug":"mistral-large-4","terminalBench40":0.2}}'
    )
    rows = extract_flight_payload(raw)
    assert [row["id"] for row in rows] == ["aa-one", "aa-two"]
