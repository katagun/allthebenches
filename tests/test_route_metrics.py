import json
import runpy
from pathlib import Path

import pytest
from pydantic import ValidationError

from pipeline.reconcile import _quote as RECONCILE_QUOTE
from pipeline.schema import Dataset


ROOT = Path(__file__).parents[1]
IMPORTER = runpy.run_path(str(ROOT / "scripts/import-route-metrics.py"))["import_route_metrics"]
PRICE_RECORD = runpy.run_path(str(ROOT / "scripts/import-route-metrics.py"))["_price_record"]


def fixture():
    route_id = "openrouter:lab/model:Provider:provider:default"
    return {
        "sources": [{"id": "or-endpoints", "url": "https://openrouter.ai/api/v1/models/lab/model/endpoints", "title": "OpenRouter endpoints", "publisher": "OpenRouter"}],
        "models": [{"id": "model", "lab_ids": [], "family_id": "family", "name": "A model"}],
        "routes": [{"id": route_id, "model_id": "model", "provider": "Provider", "upstream_model_id": "lab/model", "routing_variant": "provider", "source_ids": ["or-endpoints"]}],
        "prices": [
            {"id": "existing", "route_id": route_id, "quote_scope": "OpenRouter provider endpoint listed price", "currency": "USD", "input_price": "1", "output_price": "2", "price_unit": "USD per 1M tokens", "observed_at": "2026-01-01T00:00:00Z", "source_id": "or-endpoints"},
            {"id": "catalog", "route_id": route_id, "quote_scope": "catalog", "currency": "USD", "input_price": "9", "price_unit": "USD per 1M tokens", "observed_at": "2026-01-01T00:00:00Z", "source_id": "or-endpoints"},
        ],
        "performance": [{"id": "old", "route_id": route_id, "metric": "latency", "percentile": "p50", "value": 1, "unit": "source_reported", "sample_window_seconds": 1800, "observed_at": "2026-01-01T00:00:00Z", "source_id": "or-endpoints"}],
    }


def test_route_metrics_schema_requires_nonnegative_values_and_matching_units():
    base = {"id": "p", "route_id": "r", "metric": "latency", "percentile": "p50", "value": 25,
            "unit": "seconds", "sample_window_seconds": 1800, "observed_at": "2026-01-01T00:00:00Z", "source_id": "s"}
    with pytest.raises(ValidationError):
        Dataset.model_validate({"performance": [{**base, "value": -1}]})
    with pytest.raises(ValidationError):
        Dataset.model_validate({"performance": [{**base, "unit": "tokens_per_second"}]})
    with pytest.raises(ValidationError):
        Dataset.model_validate({"performance": [{**base, "observed_at": "2026-01-01T00:00:00"}]})


def test_import_uses_only_exact_curated_routes_and_is_idempotent(tmp_path):
    data_path = tmp_path / "dataset.json"
    staging_path = tmp_path / "endpoints.json"
    data_path.write_text(json.dumps(fixture()))
    endpoint = {
        "provider_name": "Provider", "tag": "provider", "service_tier": None, "status": 0,
        "latency_last_30m": {"p50": 654.5, "p90": 800}, "throughput_last_30m": {"p50": 70},
        "perf_last_30m_by_workload": {"text_generation": {"latency": {"p50": 600}, "throughput": {"p50": 60}, "request_count": 42}},
        "pricing": {"prompt": "0.000003", "completion": "0.000009", "input_cache_write_1h": "0.000005", "web_search": "0.01", "request": "0.02", "discount": "0.2", "overrides": [{"min_prompt_tokens": 1000, "prompt": "0.000002"}]},
    }
    staging = {"endpoints": {"lab/model": {"status": "ok", "retrieved_at": "2026-10-17T12:00:00Z", "sha256": "a" * 64, "data": {"data": {"endpoints": [endpoint, {**endpoint, "provider_name": "Unreviewed Provider"}]}}}}}
    staging_path.write_text(json.dumps(staging))

    first = IMPORTER(data_path, staging_path)
    imported = json.loads(data_path.read_text())
    second = IMPORTER(data_path, staging_path)
    again = json.loads(data_path.read_text())
    assert first["unmatched_endpoints"] == 1
    assert first["quotes"] == second["quotes"] == 1
    assert imported == again
    source = imported["sources"][0]
    assert source["retrieved_at"] == "2026-10-17T12:00:00Z" and source["content_sha256"] == "a" * 64
    assert len(imported["routes"]) == 1
    quote = next(item for item in imported["prices"] if item["id"] == "existing")
    assert next(item for item in imported["prices"] if item["id"] == "catalog")["input_price"] == "9"
    assert quote["input_price"] == "2.4000000"
    assert quote["cache_write_1h_price"] == "4.0000000"
    assert quote["discount_fraction"] == "0.2"
    assert any("default endpoint conditions" in restriction for restriction in quote["restrictions"])
    assert {item["name"]: (item["amount"], item["unit"]) for item in quote["additional_charges"]} == {
        "web_search": ("0.008", "USD per web search"),
        "request": ("0.016", "USD per request"),
    }
    assert any(row["metric"] == "latency" and row["unit"] == "seconds" and row["value"] == 0.6545 for row in imported["performance"])
    latency = next(row for row in imported["performance"] if row["metric"] == "latency" and row["percentile"] == "p50" and row["workload"] is None)
    assert latency["source_value"] == 654.5 and latency["source_unit"] == "source_reported"
    assert latency["normalization_basis"] == "inferred_ms_scale"
    assert any(row["workload"] == "text_generation" and row["sample_count"] == 42 for row in imported["performance"])
    assert not any(row["id"] == "old" for row in imported["performance"])


def test_price_charge_units_and_discount_bounds():
    charge = {"name": "request", "amount": "0.01", "unit": "USD per request"}
    Dataset.model_validate({"sources": [{"id": "s", "url": "https://example.com", "title": "s", "publisher": "s"}], "prices": [{"id": "p", "currency": "USD", "price_unit": "USD per 1M tokens",
                                         "observed_at": "2026-01-01T00:00:00Z", "source_id": "s",
                                         "additional_charges": [charge], "discount_fraction": "0.25"}]})
    with pytest.raises(ValidationError):
        Dataset.model_validate({"sources": [{"id": "s", "url": "https://example.com", "title": "s", "publisher": "s"}], "prices": [{"id": "p", "currency": "USD", "price_unit": "USD per 1M tokens",
                                             "observed_at": "2026-01-01T00:00:00Z", "source_id": "s",
                                             "discount_fraction": "1.1"}]})


def test_missing_status_is_not_reported_available_and_bad_reconcile_prices_are_skipped():
    route = {"id": "r", "source_ids": [], "upstream_model_id": "m"}
    quote = PRICE_RECORD(route, {"pricing": {"prompt": "0.000001"}}, "2026-01-01T00:00:00Z", "s", None)
    assert quote is not None and quote["available"] is False
    assert RECONCILE_QUOTE({"prompt": "NaN", "web_search": "-1", "discount": "Infinity"}) is None
