"""Build review proposals from live staging without mutating curated data."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any

from .build import canonical_json


_MODEL_FIELDS = ("id", "name", "family", "description", "release_date", "last_updated", "knowledge",
                 "limit", "modalities", "open_weights", "reasoning", "attachment", "structured_output",
                 "temperature", "tool_call", "links")
_ATLAS_FIELDS = ("id", "source_id", "name", "developer", "description", "distribution_modes", "model_type",
                 "licenses", "license_evidence", "license_review_status", "license_note", "metadata_verified_at",
                 "verified_at", "source_metadata")
_SOURCE_METADATA_FIELDS = ("description", "family", "knowledge_cutoff", "last_updated", "limits", "modalities",
                           "release_date", "reported_license", "reported_open_weights", "weights", "capabilities")


def _catalogs(staging: Path):
    def read(name):
        p = staging / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    atlas = read("peacefulcoexistance")
    models_dev = read("models.dev")
    openrouter = read("openrouter")
    endpoints = read("openrouter-endpoints")
    def feed(envelope, suffix):
        if not envelope: return None
        return next((f for f in envelope.get("feeds", []) if f.get("url", "").endswith(suffix)), None)
    return {
        "atlas_models": feed(atlas, "/models.json"), "atlas_models_dev": feed(atlas, "/models-dev.json"),
        "atlas_labs": feed(atlas, "/labs.json"), "models_dev": feed(models_dev, "models.json?type=all"),
        "openrouter": feed(openrouter, "/api/v1/models"), "openrouter_rankings": feed(openrouter, "rankings-daily"), "endpoints": endpoints,
    }


def _per_million(raw: Any) -> str | None:
    if raw is None: return None
    try:
        return format(Decimal(str(raw)) * Decimal(1_000_000), "f")
    except (InvalidOperation, ValueError):
        return None


def _quote(price: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(price, dict): return None
    fields = {"prompt":"input", "completion":"output", "input_cache_read":"cache_read", "input_cache_write":"cache_write"}
    values = {label:price.get(key) for key,label in fields.items() if price.get(key) is not None}
    auxiliary = []
    auxiliary_keys = ("image", "image_output", "request", "web_search", "audio", "audio_output",
                      "input_audio_cache", "image_token", "input_cache_write_1h")
    for key in auxiliary_keys:
        if price.get(key) is not None:
            auxiliary.append({"name":key, "raw":str(price[key]), "unit":"source_reported_unit"})
    if not values and not auxiliary: return None
    return {"source_unit":"USD per token", "raw":values,
            "usd_per_million_tokens":{label:_per_million(value) for label,value in values.items()},
            "auxiliary_charges":auxiliary,
            "conversion":"raw USD/token × 1,000,000; auxiliary charge units are unspecified by the endpoint API and remain source-reported",
            "overrides":price.get("overrides", [])}


def _endpoint_performance(endpoint: dict[str, Any]) -> dict[str, Any] | None:
    fields = ("latency_last_30m", "throughput_last_30m", "perf_last_30m_by_workload")
    metrics = {key:endpoint[key] for key in fields if endpoint.get(key) is not None}
    if not metrics:
        return None
    return {"sample_window_seconds":1800, "reported_fields":metrics,
            "units":{"latency_last_30m":"unit not specified in the endpoint API; source values retained",
                     "throughput_last_30m":"tokens per second"},
            "interpretation":"OpenRouter provider endpoint metrics use the rolling 30-minute window. Endpoint API docs do not state the latency unit or measurement semantics; values are preserved as reported. Throughput is tokens/second per OpenRouter's documentation. Workload request_count is the reported sample count when present."}


def candidate_openrouter_ids(dataset_path: Path, staging: Path) -> list[str]:
    """Return IDs found by exact curated-name Atlas candidates and exact catalog membership."""
    curated = json.loads(dataset_path.read_text(encoding="utf-8"))
    feeds = _catalogs(staging)
    rows = []
    for key in ("atlas_models", "atlas_models_dev"):
        feed = feeds[key]
        if feed:
            rows.extend(feed.get("data", {}).get("models", []))
    known = {r.get("id") for r in (feeds["openrouter"] or {}).get("data", {}).get("data", []) if isinstance(r, dict)}
    names = {m.get("name") for m in curated.get("models", [])}
    return sorted({r.get("source_id") for r in rows
                   if r.get("source_id") and r.get("source_id") in known
                   and ((r.get("name") or (r.get("source_metadata") or {}).get("name")) in names)})


def create_reconciliation_proposal(dataset_path: Path, staging: Path) -> dict[str, Any]:
    curated = json.loads(dataset_path.read_text(encoding="utf-8"))
    feeds = _catalogs(staging)
    atlas_records = {}
    for key in ("atlas_models", "atlas_models_dev"):
        f = feeds[key]
        if not f: continue
        rows = f.get("data", {}).get("models", [])
        for row in rows if isinstance(rows, list) else []:
            source_id = row.get("source_id")
            if source_id:
                atlas_records.setdefault(source_id, []).append((key, row, f))
    md_catalog = (feeds["models_dev"] or {}).get("data", {})
    or_catalog = (feeds["openrouter"] or {}).get("data", {}).get("data", [])
    or_by_id = {row.get("id"): row for row in or_catalog if isinstance(row, dict) and row.get("id")}
    endpoint_data = (feeds["endpoints"] or {}).get("endpoints", {})
    rankings_feed = feeds["openrouter_rankings"]
    rankings = (rankings_feed or {}).get("data", {})
    ranking_rows = rankings.get("data", []) if isinstance(rankings, dict) else []
    ranking_meta = rankings.get("meta", {}) if isinstance(rankings, dict) else {}
    day_keys = sorted({r.get("date") for r in ranking_rows if r.get("date")})
    route_map: dict[str,list[str]] = {}
    usage_map: dict[str,list[dict[str,Any]]] = {}
    for row in ranking_rows:
        variant = row.get("model_permaslug")
        if variant and variant.lower() != "other":
            usage_map.setdefault(variant, []).append({"date":row.get("date"),"total_tokens":row.get("total_tokens"),"model_permaslug":variant})
    models = []
    for model in curated.get("models", []):
        display_name = model.get("name", "")
        name_candidates = []
        for source_name in ("atlas_models", "atlas_models_dev"):
            f = feeds[source_name]
            if not f: continue
            rows = f.get("data", {}).get("models", [])
            for row in rows if isinstance(rows, list) else []:
                source_display = row.get("name") or (row.get("source_metadata") or {}).get("name")
                if source_display == display_name:
                    name_candidates.append((source_name, row, f))
        unique = {}
        for src, row, feed_info in name_candidates:
            key = row.get("source_id") or row.get("id")
            unique.setdefault(key, (src,row,feed_info))
        candidate = list(unique.values())
        entry: dict[str, Any] = {"curated_model_id":model["id"], "curated_name":display_name,
                                 "status":"needs_human_review", "match_basis":"exact display-name equality only; no curated upstream ID existed"}
        if len(candidate) == 1:
            atlas_source, atlas_row, atlas_feed = candidate[0]
            source_id = atlas_row.get("source_id")
            entry["atlas"] = {"feed":atlas_source, "record_id":atlas_row.get("id"), "source_id":source_id,
                              "metadata":{k:atlas_row[k] for k in _ATLAS_FIELDS if k in atlas_row and k != "source_metadata"},
                              "source_metadata":{k:v for k,v in (atlas_row.get("source_metadata") or {}).items() if k in _SOURCE_METADATA_FIELDS},
                              "feed_provenance":{"url":atlas_feed.get("url"), "retrieved_at":atlas_feed.get("retrieved_at"), "sha256":atlas_feed.get("sha256")}}
            md = md_catalog.get(source_id) if source_id and isinstance(md_catalog, dict) else None
            if isinstance(md, dict) and md.get("id") == source_id:
                entry["models_dev"] = {"external_id":source_id, "metadata":{k:md[k] for k in _MODEL_FIELDS if k in md},
                                        "match_basis":"exact Atlas source_id == models.dev map key and record id",
                                        "feed_provenance":{"url":feeds["models_dev"].get("url"), "retrieved_at":feeds["models_dev"].get("retrieved_at"), "sha256":feeds["models_dev"].get("sha256")}}
            elif source_id:
                entry["models_dev"] = {"status":"not_found_by_exact_ID", "external_id":source_id}
            else:
                # The exact-name candidate is preserved for manual crosswalk review;
                # it is not joined because Atlas supplied no source_id bridge.
                md_names = [(key,row) for key,row in md_catalog.items()
                            if isinstance(row,dict) and row.get("name") == display_name]
                entry["models_dev_name_candidates"] = [
                    {"external_id":key, "metadata":{k:row[k] for k in _MODEL_FIELDS if k in row},
                     "match_basis":"exact display-name candidate only; no shared source ID; do not auto-join"}
                    for key,row in md_names]
            if source_id and source_id in or_by_id:
                catalog = or_by_id[source_id]
                detail = endpoint_data.get(source_id)
                endpoint_list = (detail or {}).get("data", {}).get("data", {}).get("endpoints", [])
                entry["openrouter"] = {"external_id":source_id, "match_basis":"exact Atlas source_id == OpenRouter catalog model ID",
                                       "catalog":{"name":catalog.get("name"), "created":catalog.get("created"),
                                                  "context_length":catalog.get("context_length"), "architecture":catalog.get("architecture"),
                                                  "top_provider":catalog.get("top_provider"), "pricing":_quote(catalog.get("pricing")),
                                                  "details_url":catalog.get("links", {}).get("details")},
                                       "catalog_quote_scope":"OpenRouter catalog quote; not an endpoint guarantee",
                                       "endpoints":[{"candidate_route_id":f"openrouter:{source_id}:{ep.get('provider_name','unknown')}:{ep.get('tag') or 'default'}:{ep.get('service_tier') or 'default'}",
                                                     "provider_name":ep.get("provider_name"), "model_id":ep.get("model_id"),
                                                     "tag":ep.get("tag"), "service_tier":ep.get("service_tier"),
                                                     "context_length":ep.get("context_length"), "max_prompt_tokens":ep.get("max_prompt_tokens"),
                                                     "max_completion_tokens":ep.get("max_completion_tokens"), "quantization":ep.get("quantization"),
                                                     "supported_parameters":ep.get("supported_parameters"), "pricing":_quote(ep.get("pricing")),
                                                     "performance":_endpoint_performance(ep)}
                                                    for ep in endpoint_list],
                                       "endpoint_feed_status":(detail or {}).get("status"),
                                       "endpoint_feed_provenance":{"url":(detail or {}).get("url"),
                                           "retrieved_at":(detail or {}).get("retrieved_at"),"sha256":(detail or {}).get("sha256")},
                                       "feed_provenance":{"url":feeds["openrouter"].get("url"), "retrieved_at":feeds["openrouter"].get("retrieved_at"), "sha256":feeds["openrouter"].get("sha256")}}
                route_map[source_id] = [ep["candidate_route_id"] for ep in entry["openrouter"]["endpoints"]]
            else:
                entry["openrouter"] = {"status":"no exact catalog ID"}
            if source_id:
                usage_rows = usage_map.get(source_id, [])
                observed_dates = sorted({r["date"] for r in usage_rows})
                entry["openrouter_usage"] = {"exact_variant_id":source_id,
                    "status":"complete_window" if day_keys and observed_dates == day_keys else "censored_lower_bound" if observed_dates else "absent_censored_unknown",
                    "source_as_of":ranking_meta.get("as_of"), "window_start":ranking_meta.get("start_date"),
                    "window_end":ranking_meta.get("end_date"), "grain":"daily",
                    "metric":"public prompt plus completion tokens", "observations":usage_rows,
                    "missing_dates":[d for d in day_keys if d not in set(observed_dates)],
                    "interpretation":"Observed rows preserve exact variant totals. An absent row is censored/unknown, never zero; do not sum an incomplete window as exact."}
            else:
                entry["openrouter_usage"] = {"status":"unmapped_unknown", "interpretation":"No exact Atlas source_id is available to join a platform variant."}
        elif candidate:
            entry["candidate_records"] = [{"feed":src,"record_id":row.get("id"),"source_id":row.get("source_id")} for src,row,_ in candidate]
            entry["status"] = "ambiguous_exact_name"
        else:
            entry["status"] = "unmatched"
        models.append(entry)
    lab_proposals = []
    lab_feed = feeds["atlas_labs"]
    if lab_feed:
        source_labs = lab_feed.get("data", {}).get("labs", [])
        for lab in curated.get("labs", []):
            aliases = [lab.get("name"), *(lab.get("aliases") or [])]
            aliases.extend(part.strip() for part in str(lab.get("name", "")).split("/") if part.strip())
            matches = [r for r in source_labs if r.get("name") in aliases or any(a in (r.get("catalog_names") or []) for a in aliases)]
            lab_proposals.append({"curated_lab_id":lab["id"], "curated_name":lab.get("name"),
                                  "status":"needs_human_review" if len(matches)==1 else "ambiguous" if matches else "unmatched",
                                  "match_basis":"exact name or exact curated alias in Atlas catalog_names; proposal only",
                                  "records":[{"id":r.get("id"),"name":r.get("name"),"catalog_names":r.get("catalog_names"),
                                              "headquarters":r.get("headquarters"),"verified_at":r.get("verified_at"),
                                              "evidence":r.get("evidence"),"organization_note":r.get("organization_note")} for r in matches]})
    other_bucket = [r for r in ranking_rows if str(r.get("model_permaslug","")).lower()=="other"]
    return {"proposal_version":"1", "source_status":"staged live GET responses; review before importing",
            "sources":{key:{"url":feed.get("url"),"retrieved_at":feed.get("retrieved_at"),"sha256":feed.get("sha256"),"status":feed.get("status")}
                       for key,feed in feeds.items() if isinstance(feed,dict) and feed.get("url")},
            "models":models,"labs":lab_proposals,
            "openrouter_usage":{"as_of":ranking_meta.get("as_of"),"window_start":ranking_meta.get("start_date"),
                                 "window_end":ranking_meta.get("end_date"),"days":len(day_keys),"rows":len(ranking_rows),
                                 "rows_per_day":{d:sum(1 for r in ranking_rows if r.get("date")==d) for d in day_keys},
                                 "other_bucket_rows":other_bucket,
                                 "scope":"OpenRouter daily top-50 variants plus aggregate Other bucket. Absent variants are censored, not zero.",
                                 "aggregate_policy":"No multi-day sums are calculated."},
            "notes":["No records were written to data/curated/dataset.json.",
                     "No benchmark observations were imported from Atlas/model.dev metadata.",
                     "OpenRouter quotes preserve raw USD-per-token strings and show a derived per-million value; endpoint prices are separate by provider route.",
                     "Name equality nominates review candidates only. Shared source IDs are required before metadata can be joined."]}


def write_reconciliation_proposal(dataset_path: Path, staging: Path, output: Path) -> dict[str, Any]:
    proposal = create_reconciliation_proposal(dataset_path, staging)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json(proposal))
    return proposal
