"""Canonical Pydantic data contract. Generated JSON Schema is published in schemas/."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Source(StrictModel):
    id: str
    url: str
    title: str
    publisher: str
    original_evaluator: str | None = None
    retrieved_at: datetime | None = None
    published_at: datetime | None = None
    version: str | None = None
    content_sha256: str | None = None
    license: str | None = None
    attribution: str | None = None
    method: str | None = None
    locator: str | None = None
    excerpt: str | None = None


class Lab(StrictModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    hq_country_codes: list[str] = Field(default_factory=list)
    verified_at: date | None = None
    source_ids: list[str] = Field(default_factory=list)


class ModelRelease(StrictModel):
    id: str
    lab_ids: list[str]
    family_id: str
    name: str
    version: str | None = None
    aliases: list[str] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=list)
    release_date: date | None = None
    release_date_precision: Literal["day", "month", "year", "unknown"] = "unknown"
    first_seen_at: datetime | None = None
    access_state: Literal["available", "preview", "waitlist", "unavailable", "unknown"] = "unknown"
    weights_state: Literal["available", "announced", "closed", "unknown"] = "unknown"
    upstream_ids: dict[str, str] = Field(default_factory=dict)
    source_ids: list[str] = Field(default_factory=list)
    @model_validator(mode="after")
    def date_precision_consistent(self):
        if self.release_date is None and self.release_date_precision != "unknown":
            raise ValueError("release_date_precision requires release_date")
        return self


class Configuration(StrictModel):
    id: str
    model_id: str
    reasoning_label: str | None = None
    reasoning_budget_tokens: int | None = Field(default=None, ge=0)
    mode: Literal["default", "enabled", "disabled", "unknown", "not_applicable"] = "unknown"
    precision: str | None = None


class BenchmarkVariant(StrictModel):
    id: str
    family_id: str
    name: str
    version: str
    subset: str | None = None
    split: str | None = None
    task: str | None = None
    category: str
    modality: str
    metric_name: str
    unit: str
    lower_bound: float | None = None
    upper_bound: float | None = None
    direction: Literal["higher", "lower"]
    scorer_version: str | None = None
    owner: str | None = None
    documentation_url: str | None = None
    @model_validator(mode="after")
    def bounds_order(self):
        if self.lower_bound is not None and self.upper_bound is not None and self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound exceeds upper_bound")
        return self


class EvaluationSeries(StrictModel):
    id: str
    benchmark_id: str
    protocol: str | None = None
    protocol_version: str | None = None
    evaluator: str | None = None
    comparability: str | None = None
    comparability_status: Literal["comparable", "heterogeneous", "unknown"] = "unknown"
    tools: str | None = None
    sampling: str | None = None
    judge: str | None = None
    budget: str | None = None
    setup_fingerprint: str | None = None


class Observation(StrictModel):
    id: str
    configuration_id: str
    benchmark_id: str
    series_id: str | None = None
    value: float = Field(allow_inf_nan=False)
    unit: str
    source_id: str
    locator: str
    evaluator: str
    reporting_relationship: Literal["self_report", "evaluator_measurement", "third_party_reproduction", "quoted_result"]
    reported_at: datetime | None = None
    evaluated_at: datetime | None = None
    setup: dict[str, Any] = Field(default_factory=dict)
    uncertainty: dict[str, Any] | None = None
    review_state: Literal["reviewed", "candidate", "disputed", "superseded", "retracted"] = "candidate"
    supersedes: list[str] = Field(default_factory=list)


class ServingRoute(StrictModel):
    id: str
    model_id: str
    provider: str
    upstream_model_id: str | None = None
    routing_variant: str | None = None
    availability: str = "unknown"
    capabilities: list[str] = Field(default_factory=list)
    context_tokens: int | None = Field(default=None, ge=0)
    quantization: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class RoutePriceCharge(StrictModel):
    """A separately billed item whose unit differs from per-token pricing."""
    name: str
    amount: Decimal = Field(ge=0)
    unit: str


class RoutePerformance(StrictModel):
    """One percentile from a source-reported serving performance window."""
    id: str
    route_id: str
    metric: Literal["latency", "throughput"]
    percentile: Literal["p50", "p75", "p90", "p99"]
    value: float = Field(ge=0, allow_inf_nan=False)
    unit: Literal["source_reported", "seconds", "tokens_per_second"]
    workload: str | None = None
    sample_window_seconds: int = Field(gt=0)
    sample_count: int | None = Field(default=None, ge=0)
    source_value: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    source_unit: Literal["source_reported", "milliseconds", "tokens_per_second"] | None = None
    normalization_basis: Literal["official_client", "inferred_ms_scale"] | None = None
    observed_at: datetime
    source_id: str

    @field_validator("observed_at")
    @classmethod
    def observed_at_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")
        return value

    @model_validator(mode="after")
    def unit_matches_metric(self):
        allowed = {"seconds", "source_reported"} if self.metric == "latency" else {"tokens_per_second"}
        if self.unit not in allowed:
            raise ValueError(f"{self.metric} requires one of {sorted(allowed)!r}")
        return self


class PriceObservation(StrictModel):
    id: str
    route_id: str | None = None
    quote_scope: str = "catalog"
    currency: str
    input_price: Decimal | None = None
    output_price: Decimal | None = None
    cache_read_price: Decimal | None = None
    cache_write_price: Decimal | None = None
    cache_write_1h_price: Decimal | None = None
    discount_fraction: Decimal | None = Field(default=None, ge=0, le=1)
    additional_charges: list[RoutePriceCharge] = Field(default_factory=list)
    price_unit: str
    context_tier: str | None = None
    observed_at: datetime
    source_id: str
    available: bool = True
    restrictions: list[str] = Field(default_factory=list)
    @field_validator("input_price", "output_price", "cache_read_price", "cache_write_price", "cache_write_1h_price")
    @classmethod
    def nonnegative(cls, v):
        if v is not None and v < 0:
            raise ValueError("price must be nonnegative")
        return v


class UsageObservation(StrictModel):
    id: str
    platform: str
    platform_variant_id: str | None = None
    upstream_route_id: str | None = None
    is_other_bucket: bool = False
    period_start: date
    period_end: date
    grain: str
    metric: str
    total: int | None = Field(default=None, ge=0)
    rank: int | None = Field(default=None, ge=1)
    coverage: Literal["complete", "lower_bound", "censored", "sampled", "unknown"] = "unknown"
    sampled: bool = False
    source_as_of: datetime | None = None
    source_id: str
    @model_validator(mode="after")
    def period_order(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end precedes period_start")
        return self


class Preset(StrictModel):
    id: str
    version: str
    name: str
    model_configuration_ids: list[str] = Field(default_factory=list)
    benchmark_ids: list[str] = Field(default_factory=list)
    reason: str | None = None
    reviewed_at: date | None = None
    saturation_policy_version: str | None = None


class CoverageGap(StrictModel):
    id: str
    scope: str
    reason: str
    source_ids: list[str] = Field(default_factory=list)


class MetadataClaim(StrictModel):
    id: str
    entity_type: Literal["lab", "model", "configuration", "route"]
    entity_id: str
    field: str
    value: Any
    unit: str | None = None
    basis: Literal["disclosed", "measured", "third_party_estimate", "internal_inference", "speculation"]
    confidence_rationale: str
    source_ids: list[str] = Field(default_factory=list)
    method: str | None = None
    claimed_at: datetime | None = None
    selected: bool = False


class ExternalMapping(StrictModel):
    id: str
    source_id: str
    external_id: str
    internal_model_id: str | None = None
    route_id: str | None = None
    status: Literal["reviewed", "candidate", "rejected", "unresolved"]
    evidence: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class MissingCell(StrictModel):
    id: str
    configuration_id: str
    benchmark_id: str
    reason: Literal["not_reported", "not_evaluated", "not_applicable", "unavailable_source", "excluded_protocol", "disputed", "missing_configuration"]
    explanation: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class Dataset(StrictModel):
    schema_version: str = "1.0.0"
    data_version: str = "0.1.0"
    generated_at: datetime | None = None
    sources: list[Source] = Field(default_factory=list)
    labs: list[Lab] = Field(default_factory=list)
    models: list[ModelRelease] = Field(default_factory=list)
    configurations: list[Configuration] = Field(default_factory=list)
    benchmarks: list[BenchmarkVariant] = Field(default_factory=list)
    series: list[EvaluationSeries] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    routes: list[ServingRoute] = Field(default_factory=list)
    prices: list[PriceObservation] = Field(default_factory=list)
    performance: list[RoutePerformance] = Field(default_factory=list)
    usage: list[UsageObservation] = Field(default_factory=list)
    presets: list[Preset] = Field(default_factory=list)
    coverage_gaps: list[CoverageGap] = Field(default_factory=list)
    metadata_claims: list[MetadataClaim] = Field(default_factory=list)
    external_mappings: list[ExternalMapping] = Field(default_factory=list)
    missing_cells: list[MissingCell] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_and_uniqueness(self):
        collections = {name: getattr(self, name) for name in ("sources", "labs", "models", "configurations", "benchmarks", "series", "observations", "routes", "prices", "performance", "usage", "presets", "coverage_gaps", "metadata_claims", "external_mappings", "missing_cells")}
        indexes: dict[str, dict[str, Any]] = {}
        for name, items in collections.items():
            ids = [item.id for item in items]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate IDs in {name}")
            indexes[name] = {item.id: item for item in items}
        def require(ref: str | None, group: str, owner: str):
            if ref is not None and ref not in indexes[group]:
                raise ValueError(f"{owner} references missing {group} ID {ref!r}")
        for lab in self.labs:
            for ref in lab.source_ids: require(ref, "sources", lab.id)
        for model in self.models:
            for ref in model.lab_ids: require(ref, "labs", model.id)
            for ref in model.source_ids: require(ref, "sources", model.id)
        for config in self.configurations: require(config.model_id, "models", config.id)
        for series in self.series: require(series.benchmark_id, "benchmarks", series.id)
        for obs in self.observations:
            require(obs.configuration_id, "configurations", obs.id)
            require(obs.benchmark_id, "benchmarks", obs.id)
            require(obs.series_id, "series", obs.id)
            require(obs.source_id, "sources", obs.id)
            if obs.series_id and indexes["series"][obs.series_id].benchmark_id != obs.benchmark_id:
                raise ValueError(f"{obs.id} series benchmark mismatch")
            benchmark = indexes["benchmarks"][obs.benchmark_id]
            if obs.unit != benchmark.unit:
                raise ValueError(f"{obs.id} unit {obs.unit!r} differs from benchmark unit {benchmark.unit!r}")
            if benchmark.lower_bound is not None and obs.value < benchmark.lower_bound or benchmark.upper_bound is not None and obs.value > benchmark.upper_bound:
                raise ValueError(f"{obs.id} value outside benchmark bounds")
            for ref in obs.supersedes: require(ref, "observations", obs.id)
        for route in self.routes:
            require(route.model_id, "models", route.id)
            for ref in route.source_ids: require(ref, "sources", route.id)
        for price in self.prices:
            require(price.route_id, "routes", price.id); require(price.source_id, "sources", price.id)
        for item in self.performance:
            require(item.route_id, "routes", item.id); require(item.source_id, "sources", item.id)
        for usage in self.usage: require(usage.source_id, "sources", usage.id)
        for preset in self.presets:
            for ref in preset.model_configuration_ids: require(ref, "configurations", preset.id)
            for ref in preset.benchmark_ids: require(ref, "benchmarks", preset.id)
        for gap in self.coverage_gaps:
            for ref in gap.source_ids: require(ref, "sources", gap.id)
        for claim in self.metadata_claims:
            require(claim.entity_id, {"lab":"labs", "model":"models", "configuration":"configurations", "route":"routes"}[claim.entity_type], claim.id)
            for ref in claim.source_ids: require(ref, "sources", claim.id)
        for mapping in self.external_mappings:
            require(mapping.source_id, "sources", mapping.id)
            require(mapping.internal_model_id, "models", mapping.id)
            require(mapping.route_id, "routes", mapping.id)
        for cell in self.missing_cells:
            require(cell.configuration_id, "configurations", cell.id)
            require(cell.benchmark_id, "benchmarks", cell.id)
            for ref in cell.source_ids: require(ref, "sources", cell.id)
            if any(o.configuration_id == cell.configuration_id and o.benchmark_id == cell.benchmark_id for o in self.observations):
                raise ValueError(f"{cell.id} is marked missing but has an observation")
        return self
