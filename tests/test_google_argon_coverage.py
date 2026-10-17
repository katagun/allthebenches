import json
from pathlib import Path

from pipeline.schema import Dataset


DATA = Path(__file__).parents[1] / "data/curated/dataset.json"
REQUIRED = {
    "vals_index_reported", "automationbench_reported", "vals_finance_agent_v2",
    "harvey_legal_agent_reported", "deepswe_v11", "frontierswe_v2",
    "vibe_code_bench_reported", "terminal_bench_4", "posttrainbench_v11",
    "terminal_science_01", "labbench_2", "riemannbench_reported",
    "graphwalks_up_to_128k_bfs_f1", "graphwalks_256k_to_1m_bfs_f1",
    "agents_last_exam_binary", "osworld_20_offline_partial",
    "chartography_reported", "lvbench_reported", "cwe_bench_v1",
}
CONFIGS = {
    "gemini4_argon_max", "gpt6_astra_google_reported",
    "claude_fable51_google_reported", "claude_opus55_google_reported",
}


def test_google_argon_frontier_minimum_coverage_and_missingness():
    raw = json.loads(DATA.read_text())
    data = Dataset.model_validate(raw)
    frontier = next(p for p in data.presets if p.id == "frontier_oct2026")
    all_models = next(p for p in data.presets if p.id == "all_models_oct2026")
    assert REQUIRED <= set(frontier.benchmark_ids)
    assert REQUIRED <= set(all_models.benchmark_ids)
    assert {b.id for b in data.benchmarks} <= set(all_models.benchmark_ids)
    assert {c.id for c in data.configurations} <= set(all_models.model_configuration_ids)

    table_rows = {
        "vals_index_reported": [68.9, 63.1, 65.8, 67.0],
        "automationbench_reported": [51.3, 41.4, 31.4, 42.5],
        "vals_finance_agent_v2": [65.4, 53.5, 58.9, 58.6],
        "harvey_legal_agent_reported": [19.6, 5.4, 6.7, 3.8],
        "deepswe_v11": [77.9, 74.1, 67.4, 74.2],
        "frontierswe_v2": [55.0, 65.5, 56.3, 62.3],
        "vibe_code_bench_reported": [91.9, 89.6, 90.3, 90.3],
        "terminal_bench_4": [57.4, 58.2, 57.9, 66.4],
        "posttrainbench_v11": [45.3, 44.3, 40.2, 49.3],
        "terminal_science_01": [57.6, 68.1, 52.6, 63.3],
        "labbench_2": [88.8, 85.4, 68.6, 73.1],
        "riemannbench_reported": [76.0, 72.0, 65.6, 69.6],
        "graphwalks_up_to_128k_bfs_f1": [99.7, 98.7, 91.4, 90.6],
        "graphwalks_256k_to_1m_bfs_f1": [84.2, 71.8, 65.0, 66.8],
        "agents_last_exam_binary": [39.5, 34.2, None, 38.2],
        "osworld_20_offline_partial": [69.2, 72.6, None, None],
        "chartography_reported": [71.6, 71.0, 46.2, 66.3],
        "lvbench_reported": [91.7, 87.5, 79.7, 83.7],
        "cwe_bench_v1": [68.0, 68.0, 58.0, 67.0],
    }
    config_order = ["gemini4_argon_max", "gpt6_astra_google_reported",
                    "claude_fable51_google_reported", "claude_opus55_google_reported"]
    for benchmark_id, expected in table_rows.items():
        rows = {o.configuration_id: o for o in data.observations
                if o.benchmark_id == benchmark_id and o.source_id == "google_card"}
        missing = {(m.configuration_id, m.benchmark_id) for m in data.missing_cells}
        for config_id, value in zip(config_order, expected, strict=True):
            if value is None:
                assert config_id not in rows
                assert (config_id, benchmark_id) in missing
            else:
                assert rows[config_id].value == value
                assert rows[config_id].unit == "%"
                assert rows[config_id].review_state == "reviewed"
        assert all(c in CONFIGS for c in rows)


def test_google_reported_peer_effort_is_not_invented():
    raw = json.loads(DATA.read_text())
    for config in raw["configurations"]:
        if config["id"] in CONFIGS - {"gemini4_argon_max"}:
            assert "unresolved" in config["reasoning_label"]
    for obs in raw["observations"]:
        if obs["source_id"] == "google_card" and obs["configuration_id"] in CONFIGS - {"gemini4_argon_max"}:
            note = obs["setup"]["reasoning"]
            assert "not published" in note or "not stated" in note or "does not report" in note


def test_google_own_evaluations_do_not_count_as_independent():
    data = Dataset.model_validate_json(DATA.read_text())
    self_computed = {"posttrainbench_v11", "labbench_2", "graphwalks_up_to_128k_bfs_f1",
                     "graphwalks_256k_to_1m_bfs_f1", "lvbench_reported"}
    rows = [o for o in data.observations if o.source_id == "google_card"
            and o.configuration_id == "gemini4_argon_max" and o.benchmark_id in self_computed]
    assert {o.benchmark_id for o in rows} == self_computed
    assert all(o.reporting_relationship == "self_report" for o in rows)
