import json
from copy import deepcopy
from pathlib import Path

from pipeline.livebench_import import build

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "data/expansion/source-snapshots/livebench"


def dataset_before_staged_import(dataset):
    """Remove integrated LiveBench records to make importer coverage deterministic."""
    base = deepcopy(dataset)
    fragment = json.loads((ROOT / "data/expansion/livebench.json").read_text())
    for table, records in fragment.items():
        ids = {item["id"] for item in records}
        base[table] = [item for item in base[table] if item["id"] not in ids]
    return base


def test_livebench_import_preserves_releases_categories_and_known_effort():
    dataset = dataset_before_staged_import(json.loads((ROOT / "data/curated/dataset.json").read_text()))
    fragment, coverage = build(
        dataset,
        CAPTURE / "table_v1_2026_06_25.csv",
        CAPTURE / "table_2026_09_02.csv",
        CAPTURE / "categories_v1_2026_06_25.json",
        CAPTURE / "categories_v2_2026_09_02.json",
        CAPTURE / "breakdown_v2_2026_09_02.json",
        CAPTURE / "frontend_config.json",
    )
    mistral = [o for o in fragment["observations"] if o["setup"]["upstream_model_id"].startswith("mistral-large-4")]
    assert len(mistral) == 30
    wonder = [o for o in fragment["observations"] if o["setup"]["upstream_model_id"].startswith("muse-wonder-1.0")]
    assert len(wonder) == 30
    assert {o["configuration_id"] for o in wonder} == {"muse_wonder_max"}
    assert all(o["configuration_id"] != "muse_wonder_full_max" for o in wonder)
    v2 = [o for o in mistral if o["setup"]["release_key"] == "2026-09-02"]
    assert len(v2) == 7
    assert {o["setup"]["reasoning_effort"] for o in mistral} == {"high"}
    assert {o["setup"]["display_date"] for o in v2} == {"2026-10-14"}
    assert {b["category"] for b in fragment["benchmarks"] if b["id"].startswith("livebench_v2_")} == {
        "design", "research", "browser", "coding", "long-horizon", "data analysis", "reasoning"
    }
    design = next(b for b in fragment["benchmarks"] if b["id"] == "livebench_v2_20260902_design_layout")
    assert "Documents (DOCX)" in design["subset"]
    assert coverage["snapshot"]["v2_key"] == "2026-09-02"
    assert coverage["snapshot"]["v2_display_date"] == "2026-10-14"
    assert coverage["counts"]["source_specific_configurations"] == len(fragment["configurations"])
    assert fragment["configurations"]
    assert coverage["counts"]["unresolved_configuration_cells"] == 0
    total = sum(section["numeric_cells"] for section in coverage["captures"])
    decided = sum(coverage["counts"][key] for key in (
        "candidate_observations", "duplicate_existing", "unresolved_alias_cells", "unresolved_configuration_cells"
    ))
    assert total == decided

    # Re-importing the exact same captured records against the merged dataset reuses
    # the existing observations and does not create a second set of candidates.
    merged = deepcopy(dataset)
    for table, records in fragment.items():
        existing_ids = {item["id"] for item in merged[table]}
        merged[table].extend(item for item in records if item["id"] not in existing_ids)
    repeated, repeated_coverage = build(
        merged,
        CAPTURE / "table_v1_2026_06_25.csv",
        CAPTURE / "table_2026_09_02.csv",
        CAPTURE / "categories_v1_2026_06_25.json",
        CAPTURE / "categories_v2_2026_09_02.json",
        CAPTURE / "breakdown_v2_2026_09_02.json",
        CAPTURE / "frontend_config.json",
    )
    assert repeated["observations"] == []
    assert repeated_coverage["counts"]["duplicate_existing"] == len(fragment["observations"])
