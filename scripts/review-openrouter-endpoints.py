#!/usr/bin/env python3
"""Review and import exact OpenRouter endpoint identities from a dated snapshot.

This importer adds serving routes and source records only. It never imports
endpoint pricing or performance observations.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.schema import ServingRoute, Source  # noqa: E402


# These are the only newly joined identities. The API's exact model ID and
# base model name are checked against the corresponding curated name/alias.
VERIFIED_CROSSWALK = {
    "deepseek/deepseek-r1": {
        "model_id": "deepseek_r1",
        "api_name": "DeepSeek: R1",
        "curated_name": "DeepSeek-R1",
        "evidence": "Exact OpenRouter ID deepseek/deepseek-r1 maps to curated DeepSeek-R1 via its recorded alias DeepSeek R1. The catalog lists it as 'DeepSeek: R1' (created 1737381095); the distinct deepseek/deepseek-r1-0528 record is named 'DeepSeek: R1 0528' and describes itself as the May 28 update to original R1.",
    },
    "deepseek/deepseek-v4-pro-0813": {
        "model_id": "deepseek_v4_pro_0813",
        "api_name": "DeepSeek: DeepSeek V4 Pro 0813",
        "curated_name": "DeepSeek V4 Pro 0813",
        "evidence": "Exact OpenRouter ID and base name map to the curated model with the identical release name 'DeepSeek V4 Pro 0813'.",
    },
    "moonshotai/kimi-k3": {
        "model_id": "kimi_k3",
        "api_name": "MoonshotAI: Kimi K3",
        "curated_name": "Kimi K3",
        "evidence": "Exact OpenRouter ID and base name map to the curated model with the identical release name 'Kimi K3'.",
    },
}

CAPABILITY_KEYS = (
    "reasoning", "include_reasoning", "max_tokens", "stop", "tool_choice",
    "tools", "response_format", "verbosity", "reasoning_effort",
)


def source_id(model_id: str) -> str:
    return "openrouter_endpoints_" + re.sub(r"[^a-z0-9]+", "_", model_id.lower()).strip("_")


def route_id(model_id: str, endpoint: dict[str, Any]) -> str:
    provider = endpoint.get("provider_name")
    if not isinstance(provider, str) or not provider:
        raise ValueError(f"Missing provider_name for {model_id}")
    tag = endpoint.get("tag") or "default"
    tier = endpoint.get("service_tier") or "default"
    return f"openrouter:{model_id}:{provider}:{tag}:{tier}"


def validate_endpoint_snapshot(snapshot: dict[str, Any], verify_raw_bodies: bool = False) -> None:
    """Check provenance and response consistency before trusting endpoint data."""
    for upstream, envelope in snapshot.get("endpoints", {}).items():
        if envelope.get("status") != "ok":
            continue
        expected_url = f"https://openrouter.ai/api/v1/models/{upstream}/endpoints"
        if envelope.get("url") != expected_url:
            raise ValueError(f"Unexpected endpoint URL for {upstream}: {envelope.get('url')!r}")
        encoded = envelope.get("body_base64")
        if encoded is None:
            if verify_raw_bodies:
                raise ValueError(f"Missing raw endpoint response body for {upstream}")
            continue
        try:
            raw = base64.b64decode(encoded, validate=True)
            parsed = json.loads(raw)
        except ValueError as exc:
            raise ValueError(f"Invalid raw endpoint response body for {upstream}") from exc
        if hashlib.sha256(raw).hexdigest() != envelope.get("sha256"):
            raise ValueError(f"Raw endpoint response hash mismatch for {upstream}")
        if parsed != envelope.get("data"):
            raise ValueError(f"Raw endpoint response body differs from parsed envelope data for {upstream}")


def _map_models(dataset: dict[str, Any], snapshot: dict[str, Any], catalog_rows: dict[str, dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    models = {m["id"]: m for m in dataset["models"]}
    mapped: dict[str, str] = {}
    evidence: dict[str, str] = {}
    # Reuse established, exact OpenRouter IDs already attached to curated routes.
    for route in dataset["routes"]:
        upstream = route.get("upstream_model_id")
        if upstream:
            previous = mapped.setdefault(upstream, route["model_id"])
            if previous != route["model_id"]:
                raise ValueError(f"Ambiguous existing route mapping for {upstream}")
            evidence[upstream] = "Exact upstream_model_id already used by curated routes."
    # Existing external model mappings are also an exact ID bridge.
    for row in dataset.get("external_mappings", []):
        if row.get("status") != "reviewed" or row.get("route_id") is not None:
            continue
        extid, mid = row.get("external_id"), row.get("internal_model_id")
        if isinstance(extid, str) and isinstance(mid, str) and mid in models:
            previous = mapped.setdefault(extid, mid)
            if previous != mid:
                raise ValueError(f"Ambiguous reviewed external mapping for {extid}")
            evidence[extid] = f"Reviewed exact external mapping {row['id']} ({row['source_id']})."

    for upstream, record in VERIFIED_CROSSWALK.items():
        mid = record["model_id"]
        if mid not in models:
            raise ValueError(f"Curated model {mid} is missing")
        if models[mid].get("name") != record["curated_name"]:
            raise ValueError(f"Curated model name changed for reviewed mapping {upstream}")
        envelope = snapshot.get("endpoints", {}).get(upstream)
        api_model = (((envelope or {}).get("data") or {}).get("data") or {})
        api_name = api_model.get("name")
        api_id = api_model.get("id")
        if api_id != upstream or not isinstance(api_name, str):
            raise ValueError(f"OpenRouter model identity is incomplete for {upstream}")
        expected_name = record["api_name"]
        if api_name.casefold().strip() != expected_name.casefold().strip():
            raise ValueError(f"OpenRouter name {api_name!r} differs from reviewed exact name {expected_name!r}")
        catalog_record = catalog_rows.get(upstream)
        if not catalog_record or catalog_record.get("name") != api_name:
            raise ValueError(f"OpenRouter full catalog does not corroborate endpoint identity for {upstream}")
        if upstream == "deepseek/deepseek-r1":
            revision = catalog_rows.get("deepseek/deepseek-r1-0528", {})
            if (catalog_record.get("created") != 1737381095
                    or revision.get("name") != "DeepSeek: R1 0528"
                    or "update to the [original DeepSeek R1](/deepseek/deepseek-r1)" not in revision.get("description", "")):
                raise ValueError("DeepSeek R1 versus R1-0528 distinction was not corroborated")
        previous = mapped.setdefault(upstream, mid)
        if previous != mid:
            raise ValueError(f"Conflicting exact mapping for {upstream}")
        evidence[upstream] = record["evidence"]

    for upstream in snapshot.get("endpoints", {}):
        if upstream not in mapped:
            raise ValueError(f"No reviewed exact upstream model mapping for {upstream}")
    return mapped, evidence


def review(dataset: dict[str, Any], snapshot: dict[str, Any], catalog_rows: dict[str, dict[str, Any]],
           catalog_source_id: str, refresh_existing: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    validate_endpoint_snapshot(snapshot, verify_raw_bodies=refresh_existing)
    models, identity_evidence = _map_models(dataset, snapshot, catalog_rows)
    routes_by_id = {route["id"]: route for route in dataset["routes"]}
    sources_by_id = {source["id"]: source for source in dataset["sources"]}
    additions: list[dict[str, Any]] = []
    sources: dict[str, dict[str, Any]] = {}
    audit_rows: list[dict[str, Any]] = []
    seen_snapshot_routes: set[str] = set()

    for upstream, envelope in sorted(snapshot.get("endpoints", {}).items()):
        if envelope.get("status") != "ok":
            continue
        api_model = envelope.get("data", {}).get("data", {})
        if api_model.get("id") != upstream:
            raise ValueError(f"Response ID mismatch for {upstream}")
        mid = models[upstream]
        model = next(item for item in dataset["models"] if item["id"] == mid)
        sid = source_id(upstream)
        url = envelope.get("url")
        digest = envelope.get("sha256")
        retrieved_at = envelope.get("retrieved_at")
        if not all(isinstance(value, str) and value for value in (url, digest, retrieved_at)):
            raise ValueError(f"Missing source provenance for {upstream}")
        source = {
            "id": sid,
            "url": url,
            "title": f"OpenRouter provider endpoints for {model['name']}",
            "publisher": "OpenRouter",
            "published_at": None,
            "retrieved_at": retrieved_at,
            "content_sha256": digest,
            "method": "OpenRouter model endpoint API snapshot; response SHA-256 recorded in the staging envelope.",
            "locator": "Response `data.endpoints[]`; provider, endpoint model ID, tag, service tier and route metadata.",
            "original_evaluator": None,
            "version": None,
            "attribution": None,
            "license": None,
            "excerpt": None,
        }
        prior_source = sources_by_id.get(sid)
        if prior_source and prior_source.get("url") != url:
            raise ValueError(f"Existing endpoint source does not match snapshot for {upstream}")
        if not prior_source:
            sources[sid] = source
        elif refresh_existing:
            prior_source.update(source)

        for endpoint in api_model.get("endpoints", []):
            if endpoint.get("model_id") != upstream:
                raise ValueError(f"Endpoint model ID mismatch for {upstream}")
            rid = route_id(upstream, endpoint)
            if rid in seen_snapshot_routes:
                raise ValueError(f"Duplicate endpoint route identity in snapshot: {rid}")
            seen_snapshot_routes.add(rid)
            identity = {
                "upstream_model_id": upstream,
                "model_id": mid,
                "provider": endpoint["provider_name"],
                "tag": endpoint.get("tag") or "default",
                "tier": endpoint.get("service_tier") or "default",
                "source_id": sid,
                "source_sha256": digest,
                "source_retrieved_at": retrieved_at,
            }
            existing = routes_by_id.get(rid)
            if existing:
                if existing.get("model_id") != mid or existing.get("upstream_model_id") != upstream:
                    raise ValueError(f"Existing route identity conflict: {rid}")
                supported = endpoint.get("supported_parameters") or []
                if refresh_existing:
                    existing.update({
                        "availability": "listed" if endpoint.get("status") == 0 else "unknown",
                        "capabilities": [key for key in CAPABILITY_KEYS if key in supported],
                        "context_tokens": endpoint.get("context_length"),
                        "quantization": endpoint.get("quantization") or "unknown",
                    })
                    if upstream == "deepseek/deepseek-r1" and catalog_source_id not in existing["source_ids"]:
                        existing["source_ids"].append(catalog_source_id)
                audit_rows.append({**identity, "route_id": rid,
                                   "classification": "refreshed_exact_match" if refresh_existing else "already_curated",
                                   "identity_evidence": identity_evidence[upstream]})
                continue
            supported = endpoint.get("supported_parameters") or []
            route = {
                "id": rid,
                "model_id": mid,
                "provider": endpoint["provider_name"],
                "upstream_model_id": upstream,
                "routing_variant": endpoint.get("tag") or "default",
                "availability": "listed" if endpoint.get("status") == 0 else "unknown",
                "capabilities": [key for key in CAPABILITY_KEYS if key in supported],
                "context_tokens": endpoint.get("context_length"),
                "quantization": endpoint.get("quantization") or "unknown",
                "source_ids": [sid],
            }
            if upstream == "deepseek/deepseek-r1":
                route["source_ids"].append(catalog_source_id)
            additions.append(route)
            audit_rows.append({**identity, "route_id": rid, "classification": "added_exact_match",
                               "identity_evidence": identity_evidence[upstream]})
    return additions, list(sources.values()), audit_rows


def write_audit(path: Path, snapshot_path: Path, snapshot: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    added_rows = [row for row in rows if row["classification"] == "added_exact_match"]
    refreshed_rows = [row for row in rows if row["classification"] == "refreshed_exact_match"]
    already_rows = [row for row in rows if row["classification"] == "already_curated"]
    by_model = Counter(row["upstream_model_id"] for row in rows)
    if refreshed_rows:
        decision_summary = f"{len(refreshed_rows)} previously reviewed endpoints were rechecked and refreshed from current responses."
    else:
        decision_summary = f"{len(already_rows)} already matched curated routes and {len(added_rows)} unmatched records received reviewed routes."
    lines = [
        "# OpenRouter endpoint route review",
        "",
        f"Source snapshot: `{snapshot_path.resolve().relative_to(ROOT)}` (retrieved {snapshot['attempted_at']}).",
        "Each endpoint was compared by exact OpenRouter model ID, provider name, tag and service tier. Existing IDs, names and routes were reused; route IDs were not inferred from similar provider/model names.",
        "",
        f"Reviewed {len(rows)} endpoint records: {decision_summary} Added routes cite the endpoint API response hashes recorded in their source records.",
        "",
        "The three model identities without pre-existing route bridges were checked against exact OpenRouter response IDs and base names, then matched to existing curated names/aliases: DeepSeek R1, DeepSeek V4 Pro 0813, and Kimi K3. A separate exact catalog ID distinguishes original `deepseek/deepseek-r1` (created 1737381095) from `deepseek/deepseek-r1-0528` (`DeepSeek: R1 0528`, created 1748455170; explicitly described as an update to the original). The catalog response SHA-256 is recorded in the curated source `openrouter_model_catalog_2026_10_18`.",
        "No endpoint prices or performance metrics were imported by this review.",
        "",
        "## Endpoint decisions",
        "",
        "| Classification | OpenRouter model ID | Curated model | Provider | Tag | Service tier | Route ID | Source SHA-256 | Retrieved at (UTC) | Decision basis |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        cells = [row["classification"], row["upstream_model_id"], row["model_id"], row["provider"], row["tag"], row["tier"], row["route_id"], row["source_sha256"], row["source_retrieved_at"], row["identity_evidence"]]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in cells) + " |")
    lines += ["", "## Reviewed route counts", ""]
    for model_id, count in sorted(by_model.items()):
        lines.append(f"- `{model_id}`: {count}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_routes_and_sources(dataset: dict[str, Any]) -> None:
    route_ids = [route["id"] for route in dataset["routes"]]
    source_ids = [source["id"] for source in dataset["sources"]]
    if len(route_ids) != len(set(route_ids)) or len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate route or source IDs")
    sources = set(source_ids)
    for route in dataset["routes"]:
        ServingRoute.model_validate(route)
        missing = set(route.get("source_ids", [])) - sources
        if missing:
            raise ValueError(f"Route {route['id']} references missing sources: {sorted(missing)}")
    for source in dataset["sources"]:
        Source.model_validate(source)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/curated/dataset.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "data/expansion/openrouter-endpoints-2026-10-18.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/expansion/openrouter-model-catalog-2026-10-18.json")
    parser.add_argument("--catalog-provenance", type=Path, default=ROOT / "data/expansion/openrouter-model-catalog-provenance-2026-10-18.json")
    parser.add_argument("--audit", type=Path, default=ROOT / "data/expansion/openrouter-endpoints-review-audit.md")
    parser.add_argument("--check", action="store_true", help="validate and print counts without writing the dataset")
    parser.add_argument("--refresh-existing", action="store_true", help="refresh route metadata and source hashes from a current snapshot")
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    catalog_bytes = args.catalog.read_bytes()
    catalog_provenance = json.loads(args.catalog_provenance.read_text(encoding="utf-8"))
    catalog_hash = hashlib.sha256(catalog_bytes).hexdigest()
    if catalog_hash != catalog_provenance.get("content_sha256"):
        raise ValueError("OpenRouter catalog file does not match recorded raw-response SHA-256")
    catalog_payload = json.loads(catalog_bytes)
    catalog_rows = {row["id"]: row for row in catalog_payload.get("data", []) if isinstance(row, dict) and isinstance(row.get("id"), str)}
    catalog_source_id = "openrouter_model_catalog_2026_10_18"
    catalog_source = {
        "id": catalog_source_id,
        "url": catalog_provenance["url"],
        "title": "OpenRouter model catalog snapshot (2026-10-18)",
        "publisher": "OpenRouter",
        "published_at": None,
        "retrieved_at": catalog_provenance["retrieved_at"],
        "content_sha256": catalog_hash,
        "method": "Raw OpenRouter model catalog API response; SHA-256 checked against the saved response bytes.",
        "locator": "Exact IDs and names for deepseek/deepseek-r1 and deepseek/deepseek-r1-0528; original-versus-update description.",
        "original_evaluator": None,
        "version": None,
        "attribution": None,
        "license": None,
        "excerpt": None,
    }
    known_source_ids = {item["id"] for item in dataset["sources"]}
    source_ids_before = set(known_source_ids)
    if catalog_source_id not in known_source_ids:
        dataset["sources"].append(catalog_source)
    elif args.refresh_existing:
        next(item for item in dataset["sources"] if item["id"] == catalog_source_id).update(catalog_source)
    validate_endpoint_snapshot(snapshot, verify_raw_bodies=args.refresh_existing)
    additions, sources, rows = review(dataset, snapshot, catalog_rows, catalog_source_id, args.refresh_existing)
    unmatched_count = sum(row["classification"] == "added_exact_match" for row in rows)
    dataset["routes"].extend(additions)
    known_source_ids = {source["id"] for source in dataset["sources"]}
    dataset["sources"].extend(source for source in sources if source["id"] not in known_source_ids)
    validate_routes_and_sources(dataset)
    if not args.check and (args.refresh_existing or additions or not args.audit.exists()):
        write_audit(args.audit, args.snapshot, snapshot, rows)
    if not args.check:
        args.dataset.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "endpoint_records_reviewed": len(rows),
        "already_curated": len(rows) - unmatched_count,
        "exact_matches_refreshed": sum(row["classification"] == "refreshed_exact_match" for row in rows),
        "routes_added": len(additions),
        "sources_added": len({source["id"] for source in dataset["sources"]} - source_ids_before),
        "audit": str(args.audit),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
