#!/usr/bin/env python3
"""Upsert OpenRouter endpoint prices and observed performance into curated JSON.

This is an explicit import step. It joins only by exact OpenRouter model and
provider endpoint identity already present in curated routes; it never creates
or guesses a route from a display name.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.schema import Dataset  # noqa: E402


PERCENTILES = ("p50", "p75", "p90", "p99")
TOKEN_PRICE_KEYS = {
    "prompt": "input_price", "completion": "output_price",
    "input_cache_read": "cache_read_price", "input_cache_write": "cache_write_price",
    "input_cache_write_1h": "cache_write_1h_price",
}
AUXILIARY_UNITS = {
    "image": "USD per input image", "image_output": "USD per output image",
    "request": "USD per request", "web_search": "USD per web search",
    "audio": "USD per audio input token", "audio_output": "USD per audio output token",
    "input_audio_cache": "USD per cached audio input token", "image_token": "USD per image token",
    "internal_reasoning": "USD per internal reasoning token",
}


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() and result >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def _route_id(model_id: str, endpoint: dict[str, Any]) -> str:
    provider = endpoint.get("provider_name")
    tag = endpoint.get("tag") or "default"
    tier = endpoint.get("service_tier") or "default"
    if not isinstance(provider, str) or not provider:
        return ""
    return f"openrouter:{model_id}:{provider}:{tag}:{tier}"


def _source_id(route: dict[str, Any], sources: dict[str, dict[str, Any]]) -> str | None:
    upstream_id = route.get("upstream_model_id")
    if not isinstance(upstream_id, str):
        return None
    expected_url = f"https://openrouter.ai/api/v1/models/{upstream_id}/endpoints"
    return next((source_id for source_id in route.get("source_ids", [])
                 if isinstance(source_id, str) and sources.get(source_id, {}).get("url") == expected_url), None)


def _price_record(route: dict[str, Any], endpoint: dict[str, Any], observed_at: str,
                  source_id: str, existing: dict[str, Any] | None) -> dict[str, Any] | None:
    pricing = endpoint.get("pricing")
    if not isinstance(pricing, dict):
        return None
    discount = _decimal(pricing.get("discount"))
    if "discount" in pricing and discount is None:
        return None
    if discount is not None and discount > 1:
        return None
    multiplier = Decimal(1) - discount if discount is not None else Decimal(1)
    fields = {name: str(parsed * Decimal(1_000_000)) for key, name in TOKEN_PRICE_KEYS.items()
              if (parsed := _decimal(pricing.get(key))) is not None}
    fields = {name: str(Decimal(value) * multiplier) for name, value in fields.items()}
    charges = []
    for key, unit in AUXILIARY_UNITS.items():
        amount = _decimal(pricing.get(key))
        if amount is not None:
            charges.append({"name": key, "amount": str(amount * multiplier), "unit": unit})
    if not fields and not charges:
        return None
    base = dict(existing or {})
    # A fresh source record can omit a previously published charge; clear it
    # instead of showing yesterday's value with today's observation time.
    for field in TOKEN_PRICE_KEYS.values():
        base[field] = fields.get(field)
    base.update(fields)
    restrictions = ["USD per-token rates, including 1-hour cache writes, are multiplied by 1,000,000. Other charges retain their documented USD billing unit."]
    if discount is not None:
        restrictions.append("Displayed prices include the endpoint discount applied to listed charges.")
    if pricing.get("overrides"):
        restrictions.append("Conditional pricing overrides are not modeled; values reflect default endpoint conditions.")
    base.update({
        "id": (existing or {}).get("id") or f"price_openrouter_{hashlib.sha256(route['id'].encode()).hexdigest()[:16]}",
        "route_id": route["id"], "quote_scope": "OpenRouter provider endpoint listed price",
        "currency": "USD", "price_unit": "USD per 1M tokens", "context_tier": "default",
        "observed_at": observed_at, "source_id": source_id,
        "discount_fraction": str(discount) if discount is not None else None,
        "available": endpoint.get("status") == 0,
        "additional_charges": charges,
        "restrictions": restrictions,
    })
    return base


def _performance_rows(route: dict[str, Any], endpoint: dict[str, Any], observed_at: str, source_id: str) -> list[dict[str, Any]]:
    rows = []
    metrics = (("latency", endpoint.get("latency_last_30m")),
               ("throughput", endpoint.get("throughput_last_30m")))
    for metric, percentiles in metrics:
        if isinstance(percentiles, dict):
            rows.extend(_percentile_rows(route, metric, percentiles, None, None, observed_at, source_id))
    workloads = endpoint.get("perf_last_30m_by_workload")
    if isinstance(workloads, dict):
        for workload, detail in sorted(workloads.items()):
            if not isinstance(detail, dict):
                continue
            count = detail.get("request_count")
            sample_count = count if isinstance(count, int) and count >= 0 else None
            for metric in ("latency", "throughput"):
                rows.extend(_percentile_rows(route, metric, detail.get(metric), workload, sample_count, observed_at, source_id))
    # Some source fields repeat the same workload-derived series. Preserve the
    # aggregate fields and workload series as distinct, source-reported data.
    return rows


def _percentile_rows(route: dict[str, Any], metric: str, raw: Any, workload: str | None,
                     sample_count: int | None, observed_at: str, source_id: str) -> list[dict[str, Any]]:
    if not isinstance(raw, dict):
        return []
    unit = "seconds" if metric == "latency" else "tokens_per_second"
    rows = []
    for percentile in PERCENTILES:
        value = _decimal(raw.get(percentile))
        if value is None:
            continue
        # Stable IDs allow an import to replace the current point in place.
        identity = "\0".join((route["id"], metric, workload or "all_workloads", percentile))
        source_value = value
        # Infer a millisecond scale from captured payloads and the site's generic
        # formatter; the endpoint field's unit is not explicitly documented.
        if metric == "latency":
            value /= Decimal(1_000)
        rows.append({"id": f"perf_{hashlib.sha256(identity.encode()).hexdigest()[:24]}", "route_id": route["id"], "metric": metric,
                     "percentile": percentile, "value": float(value), "unit": unit,
                     "workload": workload, "sample_window_seconds": 1800,
                     "sample_count": sample_count, "source_value": float(source_value),
                     "source_unit": "source_reported" if metric == "latency" else "tokens_per_second",
                     "normalization_basis": "inferred_ms_scale" if metric == "latency" else None,
                     "observed_at": observed_at,
                     "source_id": source_id})
    return rows


def import_route_metrics(dataset_path: Path, staging_path: Path) -> dict[str, int]:
    raw_dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    dataset = Dataset.model_validate(raw_dataset)
    dataset_json = raw_dataset
    dataset_json.setdefault("performance", [])
    dataset_json_sources = dataset_json["sources"]
    sources = {source["id"]: source for source in dataset_json_sources}
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    routes = {route.id: route.model_dump(mode="json") for route in dataset.routes}
    prices = {price.route_id: raw_price for price, raw_price in zip(dataset.prices, dataset_json.get("prices", []), strict=True)
              if price.route_id and price.quote_scope == "OpenRouter provider endpoint listed price"}
    performance = list(dataset_json["performance"])
    fresh_ids: set[str] = set()
    refreshed_route_ids: set[str] = set()
    imported_quotes = imported_perf = unmatched = 0
    for model_id, envelope in sorted(staging.get("endpoints", {}).items()):
        if not isinstance(envelope, dict) or envelope.get("status") != "ok":
            continue
        retrieved_at = envelope.get("retrieved_at")
        if not isinstance(retrieved_at, str):
            continue
        # Validate timestamp before adding any rows.
        datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        data = envelope.get("data", {}).get("data", {})
        endpoint_rows = data.get("endpoints", []) if isinstance(data, dict) else []
        for endpoint in endpoint_rows if isinstance(endpoint_rows, list) else []:
            if not isinstance(endpoint, dict):
                continue
            target_id = _route_id(model_id, endpoint)
            route = routes.get(target_id)
            if not route:
                unmatched += 1
                continue
            source_id = _source_id(route, sources)
            if not source_id:
                continue
            # Source mapping must agree with the exact upstream model, provider,
            # and tag already curated on the route.
            if route.get("upstream_model_id") != model_id or route.get("provider") != endpoint.get("provider_name"):
                unmatched += 1
                continue
            refreshed_route_ids.add(target_id)
            source_record = next((source for source in dataset_json_sources if source.get("id") == source_id), None)
            if source_record:
                source_record["retrieved_at"] = retrieved_at
                if isinstance(envelope.get("sha256"), str):
                    source_record["content_sha256"] = envelope["sha256"]
            quote = _price_record(route, endpoint, retrieved_at, source_id, prices.get(target_id))
            if quote:
                prices[target_id] = quote
                imported_quotes += 1
            for item in _performance_rows(route, endpoint, retrieved_at, source_id):
                from pipeline.schema import RoutePerformance
                RoutePerformance.model_validate(item)
                performance.append(item)
                fresh_ids.add(item["id"])
                imported_perf += 1
    # Replace only OpenRouter endpoint metrics for routes represented in this
    # input snapshot; preserve other sources and routes that were not refreshed.
    dataset_json["prices"] = list(dataset_json["prices"])
    price_map = {item["id"]: item for item in dataset_json["prices"]}
    for quote in prices.values():
        price_map[quote["id"]] = quote
    dataset_json["prices"] = sorted(price_map.values(), key=lambda item: item["id"])
    perf_map = {item["id"]: item for item in performance
                if not (item["route_id"] in refreshed_route_ids
                        and item["source_id"] == _source_id(routes[item["route_id"]], sources))}
    for item in performance:
        if item["id"] in fresh_ids:
            perf_map[item["id"]] = item
    dataset_json["performance"] = sorted(perf_map.values(), key=lambda item: item["id"])
    Dataset.model_validate(dataset_json)
    dataset_path.write_text(json.dumps(dataset_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"quotes": imported_quotes, "performance_rows": imported_perf, "unmatched_endpoints": unmatched}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/curated/dataset.json")
    parser.add_argument("--staging", type=Path, default=ROOT / "data/staging/openrouter-endpoints.json")
    args = parser.parse_args()
    print(json.dumps(import_route_metrics(args.dataset, args.staging), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
