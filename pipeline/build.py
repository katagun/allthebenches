"""Deterministic validation, schema export, and static snapshot publication."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .schema import Dataset


def canonical_json(value: Any) -> bytes:
    def encode(item: Any):
        if hasattr(item, "model_dump"):
            return item.model_dump(mode="json")
        if hasattr(item, "isoformat"):
            return item.isoformat()
        return str(item)
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": "), default=encode) + "\n").encode()


def load_dataset(path: Path) -> Dataset:
    return Dataset.model_validate_json(path.read_text(encoding="utf-8"))


def schema_document() -> dict[str, Any]:
    return Dataset.model_json_schema()


def _ts_type(schema: dict[str, Any] | bool) -> str:
    if isinstance(schema, bool): return "unknown"
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "const" in schema:
        return json.dumps(schema["const"])
    if "enum" in schema:
        return " | ".join(json.dumps(v) for v in schema["enum"])
    if "anyOf" in schema:
        return " | ".join(_ts_type(v) for v in schema["anyOf"])
    typ = schema.get("type")
    if typ == "array": return f"Array<{_ts_type(schema.get('items', {}))}>"
    if typ == "object":
        if schema.get("additionalProperties") not in (None, False):
            return f"Record<string, {_ts_type(schema['additionalProperties'])}>"
        props = schema.get("properties", {})
        req = set(schema.get("required", []))
        return "{ " + "; ".join(f"{k}{'' if k in req else '?'}: {_ts_type(v)}" for k, v in props.items()) + " }"
    return {"string":"string", "integer":"number", "number":"number", "boolean":"boolean", "null":"null"}.get(typ, "unknown")


def typescript_declarations() -> str:
    schema = schema_document()
    defs = schema.get("$defs", {})
    declarations = ["// Generated from pipeline/schema.py. Do not edit by hand."]
    for name, definition in defs.items():
        declarations.append(f"export type {name} = {_ts_type(definition)};")
    declarations.append(f"export type Dataset = {_ts_type(schema)};")
    declarations.extend([
        "export type DisplayCell = { configuration_id: string; benchmark_id: string; series_id: string | null; state: 'selected' | 'agreed' | 'disputed'; value: number | null; unit: string | null; observation_ids: string[] };",
        "export type SaturationAssessment = { benchmark_id: string; series_id: string | null; policy_version: string; state: 'ineligible' | 'unknown' | 'saturated' | 'not_saturated'; eligible: boolean; ineligible_reasons: string[]; threshold: number | null; threshold_formula: string; distinct_model_count: number; distinct_lab_count: number; models_at_threshold: string[]; high_lab_ids: string[]; high_lab_count: number; required_models: number; required_labs: number; evidence: Array<{ model_id: string; lab_ids: string[]; configuration_ids: string[]; observation_ids: string[]; conservative_value: number }> };",
        "export type CatalogSnapshot = { schema_version: string; data_version: string; generated_at: string | null; labs: Lab[]; models: ModelRelease[]; configurations: Configuration[]; benchmarks: BenchmarkVariant[]; presets: Preset[]; coverage_gaps: CoverageGap[]; metadata_claims: MetadataClaim[]; missing_cells: MissingCell[]; saturation: SaturationAssessment[] };",
        "export type ResultsSnapshot = { schema_version: string; observations: Observation[]; cells: DisplayCell[] };",
        "export type DetailsSnapshot = { schema_version: string; sources: Source[]; series: EvaluationSeries[]; observations: Observation[]; external_mappings: ExternalMapping[]; metadata_claims: MetadataClaim[] };",
        "export type MarketSnapshot = { schema_version: string; routes: ServingRoute[]; prices: PriceObservation[]; performance: RoutePerformance[]; usage: UsageObservation[] };",
        "export type ManifestSnapshot = { schema_version: string; data_version: string; snapshot_id: string; generated_at: string | null; files: Record<string, { sha256: string; bytes: number }>; coverage: { models: number; benchmarked_models: number; observations: number; display_cells: number; benchmarks: number }; feeds: Array<{ source_id: string; status: string; as_of?: string | null; error?: unknown }>; };",
    ])
    return "\n\n".join(declarations) + "\n"


def export_schema(repo: Path) -> None:
    (repo / "schemas").mkdir(parents=True, exist_ok=True)
    (repo / "schemas/dataset.schema.json").write_bytes(canonical_json(schema_document()))
    generated = repo / "web/src/generated/dataset.ts"
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text(typescript_declarations(), encoding="utf-8")


def select_observations(dataset: Dataset) -> list[dict[str, Any]]:
    """Produce reviewed per-configuration/variant/series display cells conservatively."""
    groups: dict[tuple[str, str, str | None], list[Any]] = {}
    for observation in dataset.observations:
        if observation.review_state == "reviewed":
            key = (observation.configuration_id, observation.benchmark_id, observation.series_id)
            groups.setdefault(key, []).append(observation)
    cells = []
    for (configuration_id, benchmark_id, series_id), observations in sorted(groups.items(), key=lambda pair: tuple(v or "" for v in pair[0])):
        values = {(o.value, o.unit) for o in observations}
        agreed = len(values) == 1
        first = observations[0]
        cells.append({
            "configuration_id": configuration_id,
            "benchmark_id": benchmark_id,
            "series_id": series_id,
            "state": "selected" if len(observations) == 1 else "agreed" if agreed else "disputed",
            "value": first.value if agreed else None,
            "unit": first.unit if agreed else None,
            "observation_ids": sorted(o.id for o in observations),
        })
    return cells


SATURATION_POLICY_VERSION = "capability-saturation-1.0"


def assess_saturation(dataset: Dataset) -> list[dict[str, Any]]:
    """Assess bounded higher-is-better capability variants conservatively."""
    configuration_by_id = {c.id:c for c in dataset.configurations}
    model_by_id = {m.id:m for m in dataset.models}
    series_by_id = {s.id:s for s in dataset.series}
    display_cells = select_observations(dataset)
    cells_by_key: dict[tuple[str,str|None],dict[str,dict[str,list[float]]]] = {}
    for cell in display_cells:
        if cell["value"] is None: continue
        config = configuration_by_id[cell["configuration_id"]]
        model = model_by_id[config.model_id]
        per_model = cells_by_key.setdefault((cell["benchmark_id"],cell["series_id"]),{})
        per_model.setdefault(model.id,{}).setdefault(cell["configuration_id"],[]).append(cell["value"])
    result = []
    for benchmark in dataset.benchmarks:
        eligible = (benchmark.category.lower() != "safety" and benchmark.direction == "higher"
                    and benchmark.lower_bound is not None and benchmark.upper_bound is not None
                    and benchmark.upper_bound > benchmark.lower_bound)
        reasons = []
        if benchmark.category.lower() == "safety": reasons.append("safety metrics are excluded")
        if benchmark.direction != "higher": reasons.append("metric direction is not higher-is-better")
        if benchmark.lower_bound is None or benchmark.upper_bound is None: reasons.append("metric is not bounded")
        if benchmark.lower_bound is not None and benchmark.upper_bound is not None and benchmark.upper_bound <= benchmark.lower_bound:
            reasons.append("metric bounds have no positive range")
        threshold = (benchmark.lower_bound + .95 * (benchmark.upper_bound - benchmark.lower_bound)) if eligible else None
        matching_series = sorted({series for b_id,series in cells_by_key if b_id == benchmark.id}, key=lambda x:x or "")
        if not matching_series: matching_series=[None]
        for series_id in matching_series:
            per_model = cells_by_key.get((benchmark.id,series_id),{})
            model_scores: dict[str,float] = {}
            for model_id, config_scores in per_model.items():
                scores=[v for values in config_scores.values() for v in values]
                if scores:
                    # Requiring every reviewed configuration to clear the bar prevents cherry-picking.
                    model_scores[model_id] = min(scores)
            labs = {lab for model_id in model_scores for lab in model_by_id[model_id].lab_ids}
            high_models = sorted(model_id for model_id,value in model_scores.items() if threshold is not None and value >= threshold)
            high_labs = sorted({lab for model_id in high_models for lab in model_by_id[model_id].lab_ids})
            evidence = []
            for model_id,config_scores in sorted(per_model.items()):
                model_config_ids = sorted(config_scores)
                model_cells = [cell for cell in display_cells
                               if cell["benchmark_id"]==benchmark.id and cell["series_id"]==series_id
                               and configuration_by_id[cell["configuration_id"]].model_id==model_id and cell["value"] is not None]
                if model_cells:
                    evidence.append({"model_id":model_id,"lab_ids":model_by_id[model_id].lab_ids,
                        "configuration_ids":model_config_ids,
                        "observation_ids":sorted({oid for cell in model_cells for oid in cell["observation_ids"]}),
                        "conservative_value":model_scores[model_id]})
            sufficient = len(model_scores) >= 3 and len(labs) >= 2
            comparable = series_id is not None and series_by_id.get(series_id) is not None and series_by_id[series_id].comparability_status == "comparable"
            state = "ineligible" if not eligible else "unknown" if not comparable or not sufficient else "saturated" if len(high_models) >= 3 and len(high_labs) >= 2 else "not_saturated"
            result.append({"benchmark_id":benchmark.id,"series_id":series_id,"policy_version":SATURATION_POLICY_VERSION,
                "state":state,"eligible":eligible,"ineligible_reasons":reasons,
                "threshold":threshold,"threshold_formula":"lower_bound + 0.95 × (upper_bound - lower_bound)",
                "distinct_model_count":len(model_scores),"distinct_lab_count":len(labs),
                "models_at_threshold":high_models,"high_lab_ids":high_labs,"high_lab_count":len(high_labs),
                "required_models":3,"required_labs":2,"evidence":evidence})
    return result


def build(dataset: Dataset, output: Path, feeds: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    catalog = {"schema_version": dataset.schema_version, "data_version": dataset.data_version,
               "generated_at": dataset.generated_at, "labs": dataset.labs, "models": dataset.models,
               "configurations": dataset.configurations, "benchmarks": dataset.benchmarks,
               "presets": dataset.presets, "coverage_gaps": dataset.coverage_gaps,
               "metadata_claims": dataset.metadata_claims, "missing_cells": dataset.missing_cells,
               "saturation": assess_saturation(dataset)}
    results = {"schema_version": dataset.schema_version, "observations": [o for o in dataset.observations if o.review_state == "reviewed"],
               "cells": select_observations(dataset)}
    details = {"schema_version": dataset.schema_version, "sources": dataset.sources,
               "series": dataset.series, "observations": dataset.observations,
               "external_mappings": dataset.external_mappings, "metadata_claims": dataset.metadata_claims}
    market = {"schema_version": dataset.schema_version, "routes": dataset.routes,
              "prices": dataset.prices, "performance": dataset.performance, "usage": dataset.usage}
    payloads = {"catalog.json": catalog, "results.json": results, "details.json": details, "market.json": market}
    encoded = {name: canonical_json(payload) for name, payload in payloads.items()}
    files = {}
    for name, data in encoded.items():
        (output / name).write_bytes(data)
        files[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    snapshot_digest = hashlib.sha256("".join(files[n]["sha256"] for n in sorted(files)).encode()).hexdigest()
    model_ids = {o.configuration_id for o in dataset.observations}
    config_to_model = {c.id: c.model_id for c in dataset.configurations}
    benchmarked_models = {config_to_model[i] for i in model_ids if i in config_to_model}
    manifest = {"schema_version": dataset.schema_version, "data_version": dataset.data_version,
                "snapshot_id": snapshot_digest[:16], "generated_at": dataset.generated_at,
                "files": files,
                "coverage": {"models": len(dataset.models), "benchmarked_models": len(benchmarked_models),
                             "observations": len(dataset.observations), "display_cells": len(select_observations(dataset)),
                             "benchmarks": len(dataset.benchmarks)},
                "feeds": feeds or []}
    (output / "manifest.json").write_bytes(canonical_json(manifest))
    from .static_pages import build_static_pages
    build_static_pages(dataset, output.parent)
    return manifest
