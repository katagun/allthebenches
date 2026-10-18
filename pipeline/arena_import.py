"""Build a reviewable Arena candidate fragment from the pinned official HF dataset.

The importer reads the latest Parquet file for each Arena subset at an immutable
repository revision. It needs PyArrow only when reading/downloading the snapshot:
  uv run --with pyarrow python pipeline/arena_import.py --download
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = "lmarena-ai/leaderboard-dataset"
REVISION = "0ebb411abf001fa30ad48fc7e49c5cd5891d5f8a"
REPO_URL = f"https://huggingface.co/datasets/{DATASET}"
TREE_URL = f"https://huggingface.co/api/datasets/{DATASET}/tree/{REVISION}?recursive=true&expand=false"
DATA_URL = f"{REPO_URL}/resolve/{REVISION}/"
RETRIEVED_AT = "2026-10-18T00:00:00Z"

EFFORTS = {"max": "max", "xhigh": "xhigh", "extra high": "xhigh", "high": "high",
           "medium": "medium", "low": "low", "minimal": "minimal", "none": "none",
           "default": "default", "thinking": "reasoning"}
BASE_CONFIG = {
    "text": "Text Arena Overall", "text_style_control": "Text Arena Style Control Overall",
    "vision": "Vision Arena Overall", "vision_style_control": "Vision Arena Style Control Overall",
    "search": "Search Arena Overall", "search_factuality": "Search Arena Factuality Overall",
    "search_style_control": "Search Arena Style Control Overall", "document": "Document Arena Overall",
    "document_style_control": "Document Arena Style Control Overall", "webdev": "Code Arena WebDev Overall",
    "text_to_image": "Text-to-Image Arena Overall", "image_edit": "Image Edit Arena Overall",
    "text_to_video": "Text-to-Video Arena Overall", "image_to_video": "Image-to-Video Arena Overall",
    "video_edit": "Video Edit Arena Overall", "agent": "Agent Arena Overall IPS Score",
    "agent_bash_recovery_steps": "Agent Arena Bash Recovery Steps",
    "agent_bash_reliability": "Agent Arena Bash Reliability",
    "agent_bash_reliability_no_prereq": "Agent Arena Bash Reliability (No Prerequisites)",
    "agent_praise_complaint": "Agent Arena Praise vs Complaint",
    "agent_steerability": "Agent Arena Steerability",
    "agent_task_outcome_explicit": "Agent Arena Confirmed Success",
    "agent_tool_hallucination": "Agent Arena Tool Hallucination",
}
KNOWN_IDS = {"text": "arena_text_overall_bt_20261015", "vision": "arena_vision_overall_bt_20261009",
             "search": "arena_search_overall_bt_20261013", "webdev": "arena_webdev_overall_bt_20261016"}
def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_manifest() -> list[dict]:
    with urllib.request.urlopen(TREE_URL, timeout=60) as response:
        listing = json.load(response)
    return [entry for entry in listing if entry.get("type") == "file" and "/latest-" in entry.get("path", "")]


def source_files(cache_dir: Path, download: bool) -> tuple[list[dict], dict[str, Path]]:
    entries = fetch_manifest()
    selected: dict[str, Path] = {}
    for entry in entries:
        path = cache_dir / entry["path"]
        if download or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(DATA_URL + entry["path"], path)
        actual = sha256(path)
        expected = (entry.get("lfs") or {}).get("oid")
        if expected and actual != expected:
            raise ValueError(f"SHA-256 mismatch for {entry['path']}: expected {expected}, got {actual}")
        selected[entry["path"].split("/", 1)[0]] = path
        entry["sha256"] = actual
    return entries, selected


def parse_label(label: str) -> tuple[str, str]:
    """Split only the explicit trailing effort label; do not fuzzy-match model names."""
    match = re.search(r"\s*\((Max|xHigh|Extra High|High|Medium|Low|Minimal|None|Default|Thinking)\)$", label, re.I)
    if match:
        effort = EFFORTS[match.group(1).casefold()]
        return label[:match.start()].strip(), effort
    match = re.search(r"[-_](max|xhigh|high|medium|low|minimal|none|thinking)$", label, re.I)
    if match:
        effort = EFFORTS[match.group(1).casefold()]
        return label[:match.start()].strip(), effort
    return label.strip(), "unknown"


def indexes(dataset: dict) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    model_lookup: dict[str, str] = {}
    for model in dataset["models"]:
        for label in [model["name"], *(model.get("aliases") or [])]:
            key = norm(label)
            if key in model_lookup and model_lookup[key] != model["id"]:
                raise ValueError(f"ambiguous local model alias: {label}")
            model_lookup[key] = model["id"]
    config_lookup: dict[tuple[str, str], str] = {}
    for config in dataset["configurations"]:
        if "_arc_" in config["id"]:
            continue
        effort = (config.get("reasoning_label") or "unknown").casefold()
        key = (config["model_id"], effort)
        if key not in config_lookup:
            config_lookup[key] = config["id"]
    return model_lookup, config_lookup


def category_name(partition: str, category: str, publish_date: str) -> str:
    expected_snapshot_dates = {"text": "2026-10-15", "vision": "2026-10-09",
                               "search": "2026-10-13", "webdev": "2026-10-16"}
    if partition in KNOWN_IDS and category == "overall" and publish_date == expected_snapshot_dates[partition]:
        return KNOWN_IDS[partition]
    # HF Agent Arena values are signed IPS estimates. Keep them as source-specific
    # measures rather than reusing the manually captured, differently scaled signals.
    token = re.sub(r"[^a-z0-9]+", "_", category.lower()).strip("_") or "overall"
    return f"arena_hf_{partition}_{token}_{publish_date.replace('-', '')}"


# These are exact source labels with independently verified one-to-one catalog
# identities. Keep this list explicit: version similarity is not an identity rule.
EXPLICIT_SOURCE_ALIASES = {
    norm("Qwen 3.8 27B"): ("qwen38_27b", "unknown", "Punctuation/spacing variant of canonical Qwen3.8-27B; digits and parameter size match exactly."),
    norm("Claude 3 Opus 20240229"): ("claude3_opus", "unknown", "Exact dated source slug for canonical Claude 3 Opus release."),
    norm("Claude 3 Sonnet 20240229"): ("claude3_sonnet", "unknown", "Exact dated source slug for canonical Claude 3 Sonnet release."),
    norm("Claude 3 Haiku 20240307"): ("claude3_haiku", "unknown", "Exact dated source slug for canonical Claude 3 Haiku release."),
    norm("Claude 3.5 Sonnet 20240620"): ("claude35_sonnet_june", "unknown", "Exact dated source slug for canonical June 2024 Claude 3.5 Sonnet report checkpoint."),
    norm("DeepSeek-V4-Pro (High, 20260813)"): ("deepseek_v4_pro_0813", "high", "Exact 20260813 model-date tag matches canonical V4 Pro 0813; OpenRouter catalog audit distinguishes this release."),
    norm("DeepSeek V4 Pro (High) (0813)"): ("deepseek_v4_pro_0813", "high", "Exact 0813 model-date tag matches canonical V4 Pro 0813; OpenRouter catalog audit distinguishes this release."),
    norm("deepseek-v4-pro-high-20260813"): ("deepseek_v4_pro_0813", "high", "Exact 20260813 model-date tag matches canonical V4 Pro 0813; OpenRouter catalog audit distinguishes this release."),
}


def resolve_source_model(raw_name: str, model_lookup: dict[str, str]) -> tuple[str, str, str | None, str]:
    """Resolve only exact names, exact aliases, or enumerated source-specific aliases."""
    explicit = EXPLICIT_SOURCE_ALIASES.get(norm(raw_name))
    if explicit:
        model_id, effort, evidence = explicit
        return raw_name, effort, model_id, evidence
    # A full exact canonical model name takes precedence over a hyphen suffix:
    # e.g. Qwen3.8-Max is a model name, while Model (Max) is an effort label.
    direct = model_lookup.get(norm(raw_name))
    if direct:
        return raw_name, "unknown", direct, "Exact canonical model name or recorded alias."
    base, effort = parse_label(raw_name)
    model_id = model_lookup.get(norm(base))
    evidence = "Exact canonical model name/alias after removing explicit trailing effort label."
    return base, effort, model_id, evidence


def build(dataset: dict, files: dict[str, Path], file_manifest: list[dict]) -> tuple[dict, dict]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("PyArrow required: uv run --with pyarrow python pipeline/arena_import.py") from exc
    model_lookup, config_lookup = indexes(dataset)
    fragment = {key: [] for key in ("sources", "configurations", "benchmarks", "series", "observations", "external_mappings")}
    created_configs: dict[tuple[str, str], dict] = {}
    coverage = {"source": "Arena leaderboard-dataset", "revision": REVISION,
        "repository_url": REPO_URL, "retrieved_at": RETRIEVED_AT, "license": "CC BY 4.0",
        "partitions": [], "denominators": {"source_records": 0, "scored_records": 0},
        "counts": {}, "unresolved_aliases": [], "unresolved_configurations": [], "decisions": [],
        "identity_policy": "Only exact canonical names/aliases after removing an explicit trailing effort label are mapped; unresolved labels remain queued.",
        "snapshot_reuse_policy": "Existing snapshot-specific benchmark IDs are reused only when partition, overall category, and exact expected leaderboard publication date all match.",
        "metric_policy": {"rating": "Arena Bradley–Terry rating; higher is better.",
            "agent_ips": "Retain signed IPS estimate and bounds on source scale; higher is favorable net improvement, including raw behaviors whose untransformed rate is lower-is-better. Agent IPS benchmarks remain distinct from manually captured percentage signals.",
            "agent_methodology_url": "https://arena.ai/blog/agent-arena-methodology/",
            "agent_interval": "Source card defines score_ci_lower/upper as 95% confidence bounds.",
            "rating_interval": "Retain rating_lower/upper as source bounds; confidence level is unstated and left null."},
        "duplicate_policy": "Exact existing records with matching value, bounds, and count are deduplicated; same-date rating records with any mismatch are preserved in an HF-pinned separate series. Agent IPS observations are not conflated with percentage-style signal cards."}
    coverage["explicit_source_aliases"] = [
        {"normalized_source_label": label, "model_id": model_id, "effort": effort, "identity_basis": basis}
        for label, (model_id, effort, basis) in sorted(EXPLICIT_SOURCE_ALIASES.items())]
    coverage["reviewed_unmatched_examples"] = [
        {"source_label": "deepseek-r1-0528", "reason": "The captured OpenRouter catalog audit identifies this as the May 28 update, distinct from the canonical DeepSeek R1 model; not merged."},
        {"source_label": "GLM-5.2 / GLM-5.1 / GLM-5V-Turbo", "reason": "These labels are distinct source versions/families; the existing catalog has GLM-5.3 and GLM-5.3-Flash, so version similarity is insufficient."},
        {"source_label": "Qwen3.8-Max-0902", "reason": "The captured source label carries a dated model refresh tag; retained as unresolved because the catalog has only the undated release and no exact same-version entry."},
    ]
    existing_benchmarks = {b["id"]: b for b in dataset["benchmarks"]}
    existing_obs = dataset["observations"]

    for partition, parquet_path in sorted(files.items()):
        table = pq.read_table(parquet_path)
        rows = table.to_pylist()
        if not rows:
            continue
        columns = set(rows[0])
        rating_kind = "rating" in columns
        score_field = "rating" if rating_kind else "score"
        lower_field = "rating_lower" if rating_kind else "score_ci_lower"
        upper_field = "rating_upper" if rating_kind else "score_ci_upper"
        count_field = "vote_count" if rating_kind else "observation_count"
        source_id = f"arena_hf_{partition}_20261018"
        source_entry = next(entry for entry in file_manifest if entry["path"].split("/", 1)[0] == partition)
        fragment["sources"].append({"id": source_id, "url": f"{REPO_URL}/blob/{REVISION}/{source_entry['path']}",
            "title": f"Arena {partition.replace('_', ' ').title()} latest leaderboard partition", "publisher": "Arena (lmarena-ai)",
            "original_evaluator": "Arena", "retrieved_at": RETRIEVED_AT,
            "version": f"latest split at {REVISION}; row-level leaderboard dates retained",
            "content_sha256": source_entry["sha256"], "license": "CC BY 4.0", "attribution": "Arena / lmarena-ai; CC BY 4.0",
            "method": "Deterministic import of the official Hugging Face latest Parquet partition pinned to an immutable commit.",
            "locator": f"{partition}/latest-00000-of-00001.parquet; fields {', '.join(rows[0].keys())}"})
        coverage["partitions"].append({"partition": partition, "path": source_entry["path"], "sha256": source_entry["sha256"],
            "source_records": len(rows), "scored_records": sum(r.get(score_field) is not None for r in rows),
            "publish_dates": sorted({r.get("leaderboard_publish_date") for r in rows if r.get("leaderboard_publish_date")}),
            "categories": sorted({r.get("category") for r in rows if r.get("category")})})
        coverage["denominators"]["source_records"] += len(rows)
        coverage["denominators"]["scored_records"] += sum(r.get(score_field) is not None for r in rows)
        for row in rows:
            raw_name = row["model_name"]
            model_label, effort, model_id, identity_evidence = resolve_source_model(raw_name, model_lookup)
            record = {"partition": partition, "model_name": raw_name, "category": row.get("category"),
                      "leaderboard_publish_date": row.get("leaderboard_publish_date"), "source_metric_field": score_field,
                      "source_value": row.get(score_field), "source_lower_bound": row.get(lower_field),
                      "source_upper_bound": row.get(upper_field), "source_count": row.get(count_field),
                      "session_count": row.get("session_count"), "rank": row.get("rank")}
            value = row.get(score_field)
            if value is None:
                coverage["decisions"].append({**record, "status": "no_score", "reason": "source score is null"})
                continue
            if model_id is None:
                coverage["decisions"].append({**record, "status": "unresolved_alias"})
                coverage["unresolved_aliases"].append({"source_model": raw_name, "normalized_base": norm(model_label),
                    "partition": partition, "category": row.get("category"),
                    "leaderboard_publish_date": row.get("leaderboard_publish_date"), "rows": 1})
                continue
            config_id = config_lookup.get((model_id, effort))
            if not config_id and effort == "unknown":
                unknown = [c for c in dataset["configurations"] if c["model_id"] == model_id and (c.get("reasoning_label") or "unknown").casefold() == "unknown"]
                if len(unknown) == 1:
                    config_id = unknown[0]["id"]
            if config_id is None:
                key = (model_id, effort)
                if key not in created_configs:
                    cid = f"arena_hf_{model_id}_{effort if effort != 'unknown' else 'unknown'}"
                    mode = "unknown" if effort == "unknown" else "default" if effort == "default" else "disabled" if effort == "none" else "enabled"
                    created_configs[key] = {"id": cid, "model_id": model_id,
                        "reasoning_label": None if effort == "unknown" else effort, "mode": mode}
                config_id = created_configs[key]["id"]
            date = row.get("leaderboard_publish_date")
            if not date:
                coverage["decisions"].append({**record, "status": "excluded_missing_publish_date", "configuration_id": config_id})
                continue
            benchmark_id = category_name(partition, row.get("category") or "overall", date)
            agent_ips = partition.startswith("agent")
            stored_value = float(value)
            # Reuse existing reviewed Arena definitions when the metric and snapshot are the same.
            benchmark = existing_benchmarks.get(benchmark_id)
            if benchmark is None:
                name = BASE_CONFIG.get(partition, f"Arena {partition.replace('_', ' ').title()}")
                category = "agent" if partition.startswith("agent") else partition.replace("_", " ")
                unit = "Arena rating points" if rating_kind else "IPS score"
                metric_name = "Arena rating (Bradley–Terry)" if rating_kind else "IPS estimate" if agent_ips else "IPS score"
                lower = None
                upper = None
                # Preserve raw score scales and do not infer a bounded scale from a column name.
                if rating_kind:
                    lower = None
                benchmark = {"id": benchmark_id, "family_id": f"arena_hf_{partition}_{norm(row.get('category') or 'overall').replace(' ', '_')}",
                    "name": f"{name} · {row.get('category') or 'Overall'}", "version": f"Leaderboard published {date}; pinned source revision {REVISION[:7]}",
                    "category": category, "modality": "text, tools" if partition.startswith("agent") or partition == "webdev" else "text",
                    "metric_name": metric_name, "unit": unit,
                    # Agent dataset columns are signed IPS treatment effects, not raw
                    # rates: positive improvement is favorable even for lower-is-better
                    # underlying behaviors such as tool hallucinations.
                    "direction": "higher",
                    "owner": "Arena", "documentation_url": "https://arena.ai/leaderboard"}
                if lower is not None: benchmark["lower_bound"] = lower
                if upper is not None: benchmark["upper_bound"] = upper
                if benchmark_id not in {x["id"] for x in fragment["benchmarks"]}:
                    fragment["benchmarks"].append(benchmark)
            else:
                pass
            # This series identifies the immutable HF snapshot independently from the live page capture.
            series_id = benchmark_id + f"_hf_{partition}"
            if series_id not in {x["id"] for x in fragment["series"]}:
                fragment["series"].append({"id": series_id, "benchmark_id": benchmark_id, "evaluator": "Arena",
                    "protocol": f"Official Arena leaderboard-dataset latest partition at {REVISION}; source metric and interval retained.",
                    "protocol_version": f"{partition}, published {date}, HF revision {REVISION[:7]}",
                    "comparability_status": "comparable",
                    "comparability": "Comparable only within this Arena subset, category, metric, and pinned source snapshot."})
            # Existing manually captured page rows cover these same dated leaderboard runs.
            # Agent Arena's HF IPS estimand is a distinct metric from the site's
            # percentage-style signal cards, so it never aliases their benchmark.
            prior = None if agent_ips else next((o for o in existing_obs if o["configuration_id"] == config_id and o["benchmark_id"] == benchmark_id
                          and str(o.get("reported_at") or "").startswith(date)), None)
            preserved_prior = False
            prior_decision = None
            if prior:
                same_value = float(prior["value"]) == stored_value
                existing_interval = prior.get("uncertainty") or {}
                existing_half = existing_interval.get("half_width")
                existing_lower = existing_interval.get("lower_bound")
                existing_upper = existing_interval.get("upper_bound")
                if existing_lower is None and existing_upper is None and existing_half is not None:
                    existing_lower = float(prior["value"]) - float(existing_half)
                    existing_upper = float(prior["value"]) + float(existing_half)
                source_lower = row.get(lower_field)
                source_upper = row.get(upper_field)
                interval_match = existing_lower == source_lower and existing_upper == source_upper
                count_key = "sessions" if partition.startswith("agent") else "votes"
                existing_count = (prior.get("setup") or {}).get(count_key)
                source_count = row.get("session_count") if count_key == "sessions" else row.get("vote_count")
                count_match = existing_count == source_count
                exact_duplicate = same_value and interval_match and count_match
                prior_decision = {"status": "duplicate_identical" if exact_duplicate else "preserved_alternate_source_snapshot", "existing_observation_id": prior["id"],
                    "same_value": same_value, "source_value": value,
                    "source_unit": benchmark["unit"],
                    "existing_value": prior["value"], "existing_unit": prior["unit"],
                    "interval_match": interval_match, "count_match": count_match,
                    "note": None if exact_duplicate else "Same configuration, Arena subset, category, and date, but source values, intervals, counts, or source snapshot differ; retained a separate source-pinned observation and series."}
                if exact_duplicate:
                    coverage["decisions"].append({**record, **prior_decision})
                    continue
                preserved_prior = True
            obs_id = f"o_{benchmark_id}_{config_id}_{source_id}"
            lo, hi = row.get(lower_field), row.get(upper_field)
            stored_lo, stored_hi = lo, hi
            uncertainty = None if lo is None and hi is None else {"kind": "published confidence interval",
                "confidence_level": 95 if not rating_kind else None, "lower_bound": stored_lo, "upper_bound": stored_hi,
                "note": "Exact source bounds retained; rating confidence level is not stated in the source card." if rating_kind else "The Arena dataset card defines these as 95% confidence bounds."}
            setup = {"upstream_model_id": raw_name, "reasoning_effort": effort, "category": row.get("category"),
                     "rank": row.get("rank"), "organization": row.get("organization"), "license": row.get("license"),
                     "source_metric_field": score_field, "source_value": value,
                     "source_lower_bound": lo, "source_upper_bound": hi,
                     "score_interpretation": "signed IPS estimate retained on the source scale" if agent_ips else None}
            if row.get("variance") is not None: setup["source_variance"] = row["variance"]
            if row.get(count_field) is not None: setup["source_count_name"] = "vote_count" if rating_kind else "observation_count"; setup["source_count"] = row[count_field]
            if row.get("session_count") is not None: setup["session_count"] = row["session_count"]
            fragment["observations"].append({"id": obs_id, "configuration_id": config_id, "benchmark_id": benchmark_id,
                "series_id": series_id, "value": stored_value, "unit": benchmark["unit"], "source_id": source_id,
                "locator": f"{partition} latest row {raw_name!r}, category={row.get('category')!r}, published {date}; {score_field}={value}",
                "evaluator": "Arena", "reporting_relationship": "evaluator_measurement", "reported_at": date + "T00:00:00Z",
                "uncertainty": uncertainty, "setup": setup, "review_state": "candidate"})
            mapping_id = f"arena_{partition}_{re.sub(r'[^a-z0-9]+', '_', raw_name.lower()).strip('_')}"
            if mapping_id not in {x["id"] for x in fragment["external_mappings"]}:
                fragment["external_mappings"].append({"id": mapping_id, "source_id": source_id, "external_id": raw_name,
                    "internal_model_id": model_id, "status": "reviewed", "evidence": f"{identity_evidence} Exact effort={effort}."})
            if preserved_prior:
                prior_decision["observation_id"] = obs_id
            coverage["decisions"].append({**record, **(prior_decision or {}),
                "status": "preserved_alternate_source_snapshot" if preserved_prior else "candidate_import",
                "observation_id": obs_id})
    all_decisions = coverage["decisions"]
    status_counts: dict[str, dict[str, int]] = {}
    for decision in all_decisions:
        part = decision["partition"]
        bucket = status_counts.setdefault(part, {})
        bucket[decision["status"]] = bucket.get(decision["status"], 0) + 1
    alias_queue: dict[tuple[str, str], dict] = {}
    for item in coverage["unresolved_aliases"]:
        key = (item["partition"], item["source_model"])
        aggregate = alias_queue.setdefault(key, {"partition": item["partition"], "source_model": item["source_model"],
            "normalized_base": item["normalized_base"], "scored_records": 0, "categories": [], "publish_dates": []})
        aggregate["scored_records"] += 1
        if item.get("category") not in aggregate["categories"]: aggregate["categories"].append(item.get("category"))
        if item.get("leaderboard_publish_date") not in aggregate["publish_dates"]: aggregate["publish_dates"].append(item.get("leaderboard_publish_date"))
    config_queue: dict[tuple[str, str, str, str], dict] = {}
    for item in coverage["unresolved_configurations"]:
        key = (item["partition"], item["source_model"], item["model_id"], item["effort"])
        aggregate = config_queue.setdefault(key, {**item, "scored_records": 0})
        aggregate["scored_records"] += 1
    coverage["unresolved_aliases"] = list(alias_queue.values())
    coverage["unresolved_configurations"] = list(config_queue.values())
    coverage["status_counts_by_partition"] = status_counts
    # Full source rows are pinned and reproducible; retain detailed exclusions and value mismatches.
    coverage["decisions"] = [d for d in all_decisions if d["status"] in {
        "duplicate_identical", "preserved_alternate_source_snapshot", "unresolved_configuration", "excluded_missing_publish_date", "no_score"}]
    counts = {status: sum(part.get(status, 0) for part in status_counts.values()) for status in
              {status for part in status_counts.values() for status in part}}
    fragment["configurations"] = list(created_configs.values())
    coverage["unresolved_configurations"] = []
    coverage["counts"] = {**counts, "candidate_observations": len(fragment["observations"]),
        "benchmarks": len(fragment["benchmarks"]), "series": len(fragment["series"]),
        "unresolved_alias_labels": len(coverage["unresolved_aliases"]),
        "unresolved_configuration_labels": len(coverage["unresolved_configurations"]),
        "source_specific_configurations": len(fragment["configurations"])}
    return fragment, coverage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/curated/dataset.json")
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/arena-parquet"))
    parser.add_argument("--download", action="store_true", help="fetch all latest files at the pinned revision")
    parser.add_argument("--out", type=Path, default=ROOT / "data/expansion/arena-hf.json")
    parser.add_argument("--coverage", type=Path, default=ROOT / "data/expansion/arena-hf-coverage.json")
    args = parser.parse_args()
    manifest, files = source_files(args.cache_dir, args.download)
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    fragment, coverage = build(dataset, files, manifest)
    args.out.write_text(json.dumps(fragment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.coverage.write_text(json.dumps(coverage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
