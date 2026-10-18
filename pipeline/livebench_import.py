"""Build reviewable LiveBench v1/v2 candidate fragments from pinned CSV captures.

No scores are averaged across suites. Run with:
  python3 pipeline/livebench_import.py --v1 data/expansion/livebench-v1-20260625.csv \
      --v2 data/expansion/livebench-v2-20260902.csv --config data/expansion/livebench-frontend-config.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_DATE = "2026-06-25"
V2_KEY = "2026-09-02"
V2_DISPLAY_DATE = "2026-10-14"
FRONTEND_URL = "https://livebench.ai/static/js/main.38b3cf3c.js"
V1_URL = f"https://livebench.ai/v1/table_{V1_DATE}.csv"
V2_URL = f"https://livebench.ai/table_{V2_KEY}.csv"
V1_CATEGORIES_URL = f"https://livebench.ai/v1/categories_{V1_DATE}.json"
V2_CATEGORIES_URL = f"https://livebench.ai/categories_{V2_KEY}.json"
V2_BREAKDOWN_URL = f"https://livebench.ai/breakdown_{V2_KEY}.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "model" not in rows[0]:
        raise ValueError(f"{path} is not a LiveBench score table")
    return rows


def extract_frontend_models(js: str) -> dict[str, dict[str, str]]:
    """Extract the exact v2 leaderboard model key/display name/effort triples."""
    start = js.find("Ye={")
    end = js.find("},Qt={},Wt={}", start)
    if start < 0 or end < 0:
        raise ValueError("Could not locate the LiveBench model metadata object")
    block = js[start + len("Ye={"):end + 1]
    result: dict[str, dict[str, str]] = {}
    pattern = re.compile(r'"?([a-zA-Z0-9._-]+)"?:\{[^{}]*?displayName:"([^"]+)"[^{}]*?effort:"([^"]+)"[^{}]*?\}')
    for key, display, effort in pattern.findall(block):
        result[key] = {"display_name": display, "effort": effort}
    return result


def canonical_model_lookup(dataset: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for model in dataset["models"]:
        for label in [model["name"], *(model.get("aliases") or [])]:
            key = norm(label)
            if key:
                if key in result and result[key] != model["id"]:
                    raise ValueError(f"ambiguous canonical model alias: {label}")
                result[key] = model["id"]
    # The captured LiveBench frontend key/display pair identifies Meta's base
    # Muse Wonder release. Meta publishes Muse Wonder and Wonder Full separately.
    if "muse_wonder" in {m["id"] for m in dataset["models"]}:
        result[norm("Muse Wonder 1.0")] = "muse_wonder"
    return result


def effort_from_v1(name: str) -> tuple[str, str] | None:
    """Return (base model slug, exact effort) only for explicit source suffixes."""
    match = re.search(r"-(max|xhigh|high|medium|low|minimal|none)-effort$", name, re.I)
    if match:
        return name[:match.start()], match.group(1).lower()
    match = re.search(r"-(max|xhigh|high|medium|low|minimal)$", name, re.I)
    if match:
        return name[:match.start()], match.group(1).lower()
    # LiveBench v1 contains model keys whose high setting is part of the upstream ID.
    match = re.search(r"-(high|xhigh|medium|low)$", name, re.I)
    if match:
        return name[:match.start()], match.group(1).lower()
    return name, "unknown"


def config_lookup(dataset: dict) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for config in dataset["configurations"]:
        if "_arc_" in config["id"]:
            continue
        model = config["model_id"]
        effort = (config.get("reasoning_label") or "unknown").casefold()
        key = (model, effort)
        # Prefer the non-report, explicitly named canonical configuration if duplicate labels exist.
        if key not in result:
            result[key] = config["id"]
    return result


def build(dataset: dict, v1_path: Path, v2_path: Path, categories_v1_path: Path,
          categories_v2_path: Path, breakdown_v2_path: Path, frontend_config_path: Path,
          retrieved_at: str = "2026-10-18T00:00:00Z") -> tuple[dict, dict]:
    model_lookup = canonical_model_lookup(dataset)
    configs = config_lookup(dataset)
    frontend_capture = json.loads(frontend_config_path.read_text(encoding="utf-8"))
    frontend = frontend_capture["v2_models"]
    v1_categories = json.loads(categories_v1_path.read_text(encoding="utf-8"))
    v2_categories = json.loads(categories_v2_path.read_text(encoding="utf-8"))
    breakdown = json.loads(breakdown_v2_path.read_text(encoding="utf-8"))
    fragment = {key: [] for key in ("sources", "configurations", "benchmarks", "series", "observations", "external_mappings")}
    created_configs: dict[tuple[str, str], dict] = {}
    coverage = {"source": "LiveBench", "snapshot": {"v1_key": V1_DATE, "v2_key": V2_KEY,
        "v2_display_date": V2_DISPLAY_DATE, "retrieved_at": retrieved_at}, "captures": [],
        "denominators": {}, "counts": {}, "unresolved_aliases": [], "unresolved_configurations": [],
        "decisions": [],
        "identity_policy": "Only exact normalized canonical names/aliases from the source display metadata are mapped; unresolved rows remain queued.",
        "configuration_policy": "Use an explicit source effort label when published; create source-specific exact-effort configurations when no matching canonical configuration exists; use unknown only when the source omits effort.",
        "release_policy": "Keep v1 and v2 as distinct suites; v2 release key 2026-09-02 is reported with frontend display date 2026-10-14.",
        "metric_policy": "Preserve each published task/suite score on its 0–100 scale. Do not reconstruct suite scores from breakdowns or average across suites/categories. No interval is supplied by these CSV captures.",
        "explicit_source_aliases": [{"display_name": "Muse Wonder 1.0", "upstream_key": "muse-wonder-1.0", "model_id": "muse_wonder",
            "identity_basis": "Captured frontend key/display metadata identifies Muse Wonder 1.0; Meta's official release page names Muse Wonder and Muse Wonder Full as distinct models, so the key maps to Muse Wonder only.",
            "evidence_url": "https://dev.meta.ai/models/muse-wonder"}]}

    for generation, path, table_url, cats, release_key, display_date in (
        ("v1", v1_path, V1_URL, v1_categories, V1_DATE, V1_DATE),
        ("v2", v2_path, V2_URL, v2_categories, V2_KEY, V2_DISPLAY_DATE),
    ):
        rows = read_csv(path)
        cat_for_column = {column: category for category, columns in cats.items() for column in columns}
        if set(rows[0]) - {"model"} - set(cat_for_column):
            raise ValueError(f"Unclassified {generation} columns: {set(rows[0]) - {'model'} - set(cat_for_column)}")
        capture_id = f"livebench_{generation}_{release_key.replace('-', '')}"
        source_id = capture_id
        fragment["sources"].append({"id": source_id, "url": table_url, "title": f"LiveBench {generation.upper()} dated score table ({display_date})",
            "publisher": "LiveBench", "original_evaluator": "LiveBench", "retrieved_at": retrieved_at,
            "published_at": display_date + "T00:00:00Z", "version": f"{generation.upper()} release key {release_key}; display date {display_date}",
            "content_sha256": sha256(path), "license": "Apache-2.0", "attribution": "LiveBench; https://livebench.ai and https://github.com/LiveBench/LiveBench",
            "method": "Deterministic import of the official dated CSV; source values remain on the 0–100 scale.",
            "locator": f"CSV header and all model rows; categories from {V1_CATEGORIES_URL if generation == 'v1' else V2_CATEGORIES_URL}"})
        # Every numeric cell in the full source snapshot is in the denominator.
        available_cells = sum(1 for row in rows for col in row if col != "model" and row[col].strip() not in ("", "-", "n/a", "N/A"))
        coverage["captures"].append({"generation": generation, "release_key": release_key,
            "display_date": display_date, "table_url": table_url, "sha256": sha256(path),
            "rows": len(rows), "columns": len(rows[0]) - 1, "numeric_cells": available_cells,
            "categories_url": V1_CATEGORIES_URL if generation == "v1" else V2_CATEGORIES_URL,
            "categories_sha256": sha256(categories_v1_path if generation == "v1" else categories_v2_path),
            "breakdown_url": None if generation == "v1" else V2_BREAKDOWN_URL,
            "breakdown_sha256": None if generation == "v1" else sha256(breakdown_v2_path),
            "frontend_config_sha256": sha256(frontend_config_path)})
        coverage["denominators"][generation] = {"source_rows": len(rows), "numeric_score_cells": available_cells}
        for column in rows[0]:
            if column == "model":
                continue
            category = cat_for_column[column]
            version = f"LiveBench {generation.upper()} {release_key}"
            benchmark_id = f"livebench_{generation}_{release_key.replace('-', '')}_{re.sub(r'[^a-z0-9]+', '_', column.lower()).strip('_')}"
            pretty = column.replace("_", " ")
            if column == "design_layout": pretty = "Design"
            metric_label = "task mean score" if generation == "v1" else "suite score"
            modality = "code, tools" if category in {"Coding", "Agentic Coding"} else "text, tools" if category == "Browser" else "text"
            parts = breakdown.get(pretty, {}).get("parts", []) if generation == "v2" else []
            fragment["benchmarks"].append({"id": benchmark_id, "family_id": f"livebench_{generation}_{column}",
                "name": f"LiveBench {generation.upper()} · {pretty}", "version": version,
                "subset": column if generation == "v1" else json.dumps(parts, ensure_ascii=False, separators=(",", ":")) if parts else None,
                "category": category.lower(), "modality": modality,
                "metric_name": metric_label, "unit": "%", "lower_bound": 0, "upper_bound": 100,
                "direction": "higher", "owner": "LiveBench",
                "task": "Historical v1 task score; no suite averages inferred." if generation == "v1" else f"LiveBench 2.0 suite score for {pretty}; the published value is source-reported, not reconstructed from breakdowns.",
                "documentation_url": "https://livebench.ai/methodology"})
            series_id = benchmark_id + "_series"
            fragment["series"].append({"id": series_id, "benchmark_id": benchmark_id, "evaluator": "LiveBench",
                "protocol": "LiveBench public dated table; task mean score on 0–100 scale.", "protocol_version": version,
                "comparability_status": "comparable", "comparability": "Compare only within this LiveBench release and category/task; v1 and 2.0 are distinct suites."})
            for row in rows:
                raw = row[column].strip()
                if raw in ("", "-", "n/a", "N/A"):
                    coverage["decisions"].append({"source_row": row["model"], "column": column, "release": release_key, "status": "no_score", "reason": "source cell is blank or n/a"})
                    continue
                value = float(raw)
                if not 0 <= value <= 100:
                    raise ValueError(f"out-of-range LiveBench score {row['model']} {column}={raw}")
                external_name = row["model"].strip()
                effort = "unknown"
                if generation == "v2":
                    meta = frontend.get(external_name)
                    if meta is None:
                        base_name = external_name
                    else:
                        effort = meta["effort"].casefold()
                        base_name = meta["display_name"]
                else:
                    base_name, effort = effort_from_v1(external_name)
                    # Prefer frontend's explicit metadata if the exact raw key is listed there.
                    meta = frontend.get(external_name)
                    if meta:
                        base_name = meta["display_name"]
                        effort = meta.get("effort", effort).casefold()
                    else:
                        base_name = re.sub(r"[-_]", " ", base_name)
                model_id = model_lookup.get(norm(base_name))
                if model_id is None:
                    decision = {"source_row": external_name, "column": column, "release": release_key, "status": "unresolved_alias", "canonical_candidate": None}
                    coverage["decisions"].append(decision)
                    queued = next((x for x in coverage["unresolved_aliases"] if x["generation"] == generation and x["source_model"] == external_name), None)
                    if queued is None:
                        queued = {"generation": generation, "source_model": external_name, "normalized_display": norm(base_name), "numeric_cells": 0, "columns": []}
                        coverage["unresolved_aliases"].append(queued)
                    queued["numeric_cells"] += 1
                    queued["columns"].append(column)
                    continue
                config_id = configs.get((model_id, effort))
                if not config_id and effort == "unknown":
                    unknown_configs = [c for c in dataset["configurations"] if c["model_id"] == model_id and (c.get("reasoning_label") or "unknown").casefold() == "unknown"]
                    if len(unknown_configs) == 1:
                        config_id = unknown_configs[0]["id"]
                if config_id is None:
                    key = (model_id, effort)
                    if key not in created_configs:
                        suffix = effort if effort != "unknown" else "unknown"
                        cid = f"livebench_{model_id}_{suffix}"
                        mode = "unknown" if effort == "unknown" else "default" if effort == "default" else "disabled" if effort == "none" else "enabled"
                        created_configs[key] = {"id": cid, "model_id": model_id, "reasoning_label": None if effort == "unknown" else effort, "mode": mode}
                    config_id = created_configs[key]["id"]
                duplicate = next((o for o in dataset["observations"] if o["configuration_id"] == config_id and o["benchmark_id"] == benchmark_id and str(o.get("reported_at") or "").startswith(display_date)), None)
                if duplicate:
                    coverage["decisions"].append({"source_row": external_name, "column": column, "release": release_key, "status": "duplicate_existing", "existing_observation_id": duplicate["id"], "same_value": float(duplicate["value"]) == value})
                    continue
                oid = f"o_{benchmark_id}_{config_id}"
                obs = {"id": oid, "configuration_id": config_id, "benchmark_id": benchmark_id, "series_id": series_id,
                    "value": value, "unit": "%", "source_id": source_id, "locator": f"CSV row model={external_name}; column={column}; raw={raw}",
                    "evaluator": "LiveBench", "reporting_relationship": "evaluator_measurement", "reported_at": display_date + "T00:00:00Z",
                    "setup": {"upstream_model_id": external_name, "reasoning_effort": effort,
                        "release_key": release_key, "display_date": display_date, "category": category,
                        "effort_metadata_source": FRONTEND_URL if generation == "v2" or external_name in frontend else None,
                        "effort_metadata_sha256": frontend_capture.get("frontend_sha256") if generation == "v2" or external_name in frontend else None,
                        "metric_scope": "single task" if generation == "v1" else "suite score; not an average of suite categories"},
                    "review_state": "candidate"}
                fragment["observations"].append(obs)
                fragment["external_mappings"].append({"id": f"livebench_{generation}_{re.sub(r'[^a-z0-9]+','_',external_name.lower()).strip('_')}", "source_id": source_id,
                    "external_id": external_name, "internal_model_id": model_id, "status": "reviewed",
                    "evidence": "LiveBench frontend key muse-wonder-1.0 and display name Muse Wonder 1.0 map to Meta's Muse Wonder API release; Meta identifies Muse Wonder and Muse Wonder Full as distinct models. Effort is taken from LiveBench metadata." if norm(base_name) == norm("Muse Wonder 1.0") else f"LiveBench {generation} row identity; exact model label/display metadata and effort {effort}."})
                coverage["decisions"].append({"source_row": external_name, "column": column, "release": release_key, "status": "candidate_import", "observation_id": oid})
    fragment["configurations"] = list(created_configs.values())
    coverage["unresolved_configurations"] = []
    # The pinned CSVs are the row-level audit trail; summarize every cell outcome compactly.
    status_counts: dict[str, dict[str, int]] = {}
    for decision in coverage["decisions"]:
        release = decision["release"]
        bucket = status_counts.setdefault(release, {})
        bucket[decision["status"]] = bucket.get(decision["status"], 0) + 1
    coverage["status_counts_by_release"] = status_counts
    coverage["decisions"] = [d for d in coverage["decisions"] if d["status"] in {"duplicate_existing", "unresolved_configuration"}]
    # Remove repeated reviewed mapping ids while preserving first-seen order.
    fragment["external_mappings"] = list({x["id"]: x for x in fragment["external_mappings"]}.values())
    coverage["counts"] = {
        "candidate_observations": len(fragment["observations"]),
        "duplicate_existing": sum(x.get("duplicate_existing", 0) for x in status_counts.values()),
        "unresolved_alias_cells": sum(x.get("unresolved_alias", 0) for x in status_counts.values()),
        "unresolved_configuration_cells": sum(x.get("unresolved_configuration", 0) for x in status_counts.values()),
        "source_specific_configurations": len(fragment["configurations"]),
        "no_score_cells": sum(x.get("no_score", 0) for x in status_counts.values()),
    }
    return fragment, coverage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/curated/dataset.json")
    parser.add_argument("--v1", type=Path, required=True)
    parser.add_argument("--v2", type=Path, required=True)
    parser.add_argument("--categories-v1", type=Path, required=True)
    parser.add_argument("--categories-v2", type=Path, required=True)
    parser.add_argument("--breakdown-v2", type=Path, required=True)
    parser.add_argument("--frontend-config", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "data/expansion/livebench.json")
    parser.add_argument("--coverage", type=Path, default=ROOT / "data/expansion/livebench-coverage.json")
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    fragment, coverage = build(dataset, args.v1, args.v2, args.categories_v1, args.categories_v2, args.breakdown_v2, args.frontend_config)
    args.out.write_text(json.dumps(fragment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.coverage.write_text(json.dumps(coverage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
