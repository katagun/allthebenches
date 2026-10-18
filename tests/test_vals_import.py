import json
from pathlib import Path
from collections import defaultdict

from pipeline.schema import Dataset
from pipeline.vals_import import build_expansion


ROOT = Path(__file__).resolve().parents[1]


def _inputs():
    snapshot = json.loads((ROOT / "data/expansion/vals-all-source-snapshot-2026-10-18.json").read_text())
    curated = json.loads((ROOT / "data/curated/dataset.json").read_text())
    return snapshot, curated


def _idempotent_merge(curated, fragment):
    merged = {}
    for key, value in curated.items():
        if isinstance(value, list):
            by_id = {item["id"]: item for item in value}
            for item in fragment.get(key, []):
                by_id.setdefault(item["id"], item)
            merged[key] = list(by_id.values())
        else:
            merged[key] = value
    return merged


def test_vals_all_page_candidates_preserve_scores_settings_provenance_and_units():
    snapshot, curated = _inputs()
    fragment = build_expansion(snapshot, curated)
    assert len(snapshot["pages"]) == 45
    assert len(snapshot["rows"]) == 533
    assert len(fragment["observations"]) == 533
    assert all(row["model_id"] in {m["id"] for m in curated["models"]} for row in snapshot["rows"])
    assert len(snapshot["model_profiles"]) == 21
    assert all(profile["canonical_model_id"] in {m["id"] for m in curated["models"]}
               for profile in snapshot["model_profiles"].values())
    assert all(len(page["sha256"]) == 64 and page["status"] == 200 for page in snapshot["pages"])
    assert all(row["unit"] == "%" and row["value"] is not None for row in snapshot["rows"])
    assert all(row["setup"]["row_configuration_status"] == "unknown"
               and row["setup"]["profile_setting_application"] == "not established for this leaderboard row"
               for row in fragment["observations"])
    assert all(config["mode"] == "unknown" and config["reasoning_label"] is None
               for config in fragment["configurations"])
    assert all(row["uncertainty"] is None for row in fragment["observations"])
    by_page = defaultdict(list)
    for row in snapshot["rows"]:
        by_page[row["source_slug"]].append(row)
        assert row["cells"][row["headers"].index(row["score_header"])] == row["raw_score"]
    for rows in by_page.values():
        ranked = sorted(rows, key=lambda row: int(row["rank"]))
        assert all(float(a["value"]) >= float(b["value"])
                   for a, b in zip(ranked, ranked[1:], strict=False))


def test_vals_snapshot_accounts_for_every_displayed_model_row():
    snapshot, _ = _inputs()
    coverage = snapshot["coverage"]
    assert coverage["pages_seen"] == coverage["pages_fetched"] == 45
    assert coverage["rows_seen"] == 3177
    assert coverage["candidate_rows"] == coverage["imported_rows"] == 533
    assert coverage["unresolved_rows"] == 28
    assert coverage["excluded_rows"] == 2616
    assert coverage["rows_seen"] == coverage["candidate_rows"] + coverage["unresolved_rows"] + coverage["excluded_rows"]
    assert sum(sum(counts.values()) for counts in coverage["unresolved"].values()) == coverage["unresolved_rows"]
    assert sum(sum(counts.values()) for counts in coverage["excluded"].values()) == coverage["excluded_rows"]


def test_verified_profile_aliases_are_imported_and_ambiguous_variants_stay_out():
    snapshot, curated = _inputs()
    rows = snapshot["rows"]
    names = {r["model_label"] for r in rows}
    assert {"GLM 5.3", "GLM 5.3 Flash", "Qwen 3.8 Max", "Qwen 3.8 27B",
            "Wonder Full", "Muse Spark 1.3 Max", "DeepSeek R1"} <= names
    unresolved = {name for counts in snapshot["coverage"]["unresolved"].values() for name in counts}
    excluded = {name for counts in snapshot["coverage"]["excluded"].values() for name in counts}
    assert "Claude Fable 5" in excluded
    assert "DeepSeek V4" in excluded
    assert "Claude Opus 5.5 (CVP)" in unresolved
    assert all(row.get("profile_id") for row in rows)
    assert all(snapshot["model_profiles"][row["profile_id"]].get("mapping_evidence") for row in rows)


def test_vals_fragment_references_validate_after_idempotent_promotion_merge():
    snapshot, curated = _inputs()
    fragment = build_expansion(snapshot, curated)
    merged = _idempotent_merge(curated, fragment)
    Dataset.model_validate(merged)
    # Reapplying a fragment, including after candidate IDs have been promoted,
    # must not add duplicate IDs or replace the curated review state.
    twice = _idempotent_merge(merged, fragment)
    Dataset.model_validate(twice)
    for key in ("sources", "configurations", "benchmarks", "series", "observations"):
        assert len(twice[key]) == len(merged[key])
