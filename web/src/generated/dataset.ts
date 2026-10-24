// Generated from pipeline/schema.py. Do not edit by hand.

export type BenchmarkVariant = { id: string; family_id: string; name: string; version: string; subset?: string | null; split?: string | null; task?: string | null; category: string; modality: string; metric_name: string; unit: string; lower_bound?: number | null; upper_bound?: number | null; direction: "higher" | "lower"; scorer_version?: string | null; owner?: string | null; documentation_url?: string | null };

export type Configuration = { id: string; model_id: string; reasoning_label?: string | null; reasoning_budget_tokens?: number | null; mode?: "default" | "enabled" | "disabled" | "unknown" | "not_applicable"; precision?: string | null };

export type CoverageGap = { id: string; scope: string; reason: string; source_ids?: Array<string> };

export type EvaluationSeries = { id: string; benchmark_id: string; protocol?: string | null; protocol_version?: string | null; evaluator?: string | null; comparability?: string | null; comparability_status?: "comparable" | "heterogeneous" | "unknown"; tools?: string | null; sampling?: string | null; judge?: string | null; budget?: string | null; setup_fingerprint?: string | null };

export type ExternalMapping = { id: string; source_id: string; external_id: string; internal_model_id?: string | null; route_id?: string | null; status: "reviewed" | "candidate" | "rejected" | "unresolved"; evidence?: string | null; valid_from?: string | null; valid_to?: string | null };

export type Lab = { id: string; name: string; aliases?: Array<string>; hq_country_codes?: Array<string>; verified_at?: string | null; source_ids?: Array<string> };

export type MetadataClaim = { id: string; entity_type: "lab" | "model" | "configuration" | "route"; entity_id: string; field: string; value: unknown; unit?: string | null; basis: "disclosed" | "measured" | "third_party_estimate" | "internal_inference" | "speculation"; confidence_rationale: string; source_ids?: Array<string>; method?: string | null; claimed_at?: string | null; selected?: boolean };

export type MissingCell = { id: string; configuration_id: string; benchmark_id: string; reason: "not_reported" | "not_evaluated" | "not_applicable" | "unavailable_source" | "excluded_protocol" | "disputed" | "missing_configuration"; explanation?: string | null; source_ids?: Array<string> };

export type ModelRelease = { id: string; lab_ids: Array<string>; family_id: string; name: string; version?: string | null; aliases?: Array<string>; modalities?: Array<string>; release_date?: string | null; release_date_precision?: "day" | "month" | "year" | "unknown"; first_seen_at?: string | null; access_state?: "available" | "preview" | "waitlist" | "unavailable" | "unknown"; weights_state?: "available" | "announced" | "closed" | "unknown"; upstream_ids?: Record<string, string>; source_ids?: Array<string> };

export type Observation = { id: string; configuration_id: string; benchmark_id: string; series_id?: string | null; value: number; unit: string; source_id: string; locator: string; evaluator: string; reporting_relationship: "self_report" | "evaluator_measurement" | "third_party_reproduction" | "quoted_result"; reported_at?: string | null; evaluated_at?: string | null; setup?: Record<string, unknown>; uncertainty?: Record<string, unknown> | null; review_state?: "reviewed" | "candidate" | "disputed" | "superseded" | "retracted"; supersedes?: Array<string> };

export type Preset = { id: string; version: string; name: string; model_configuration_ids?: Array<string>; benchmark_ids?: Array<string>; reason?: string | null; reviewed_at?: string | null; saturation_policy_version?: string | null };

export type PriceObservation = { id: string; route_id?: string | null; quote_scope?: string; currency: string; input_price?: number | string | null; output_price?: number | string | null; cache_read_price?: number | string | null; cache_write_price?: number | string | null; cache_write_1h_price?: number | string | null; discount_fraction?: number | string | null; additional_charges?: Array<RoutePriceCharge>; price_unit: string; context_tier?: string | null; observed_at: string; source_id: string; available?: boolean; restrictions?: Array<string> };

export type RoutePerformance = { id: string; route_id: string; metric: "latency" | "throughput"; percentile: "p50" | "p75" | "p90" | "p99"; value: number; unit: "source_reported" | "seconds" | "tokens_per_second"; workload?: string | null; sample_window_seconds: number; sample_count?: number | null; source_value?: number | null; source_unit?: "source_reported" | "milliseconds" | "tokens_per_second" | null; normalization_basis?: "official_client" | "inferred_ms_scale" | null; observed_at: string; source_id: string };

export type RoutePriceCharge = { name: string; amount: number | string; unit: string };

export type ServingRoute = { id: string; model_id: string; provider: string; upstream_model_id?: string | null; routing_variant?: string | null; availability?: string; capabilities?: Array<string>; context_tokens?: number | null; quantization?: string | null; source_ids?: Array<string> };

export type Source = { id: string; url: string; title: string; publisher: string; original_evaluator?: string | null; retrieved_at?: string | null; published_at?: string | null; version?: string | null; content_sha256?: string | null; license?: string | null; attribution?: string | null; method?: string | null; locator?: string | null; excerpt?: string | null };

export type UsageObservation = { id: string; platform: string; platform_variant_id?: string | null; upstream_route_id?: string | null; is_other_bucket?: boolean; period_start: string; period_end: string; grain: string; metric: string; total?: number | null; rank?: number | null; coverage?: "complete" | "lower_bound" | "censored" | "sampled" | "unknown"; sampled?: boolean; source_as_of?: string | null; source_id: string };

export type Dataset = { schema_version?: string; data_version?: string; generated_at?: string | null; sources?: Array<Source>; labs?: Array<Lab>; models?: Array<ModelRelease>; configurations?: Array<Configuration>; benchmarks?: Array<BenchmarkVariant>; series?: Array<EvaluationSeries>; observations?: Array<Observation>; routes?: Array<ServingRoute>; prices?: Array<PriceObservation>; performance?: Array<RoutePerformance>; usage?: Array<UsageObservation>; presets?: Array<Preset>; coverage_gaps?: Array<CoverageGap>; metadata_claims?: Array<MetadataClaim>; external_mappings?: Array<ExternalMapping>; missing_cells?: Array<MissingCell> };

export type DisplayCell = { configuration_id: string; benchmark_id: string; series_id: string | null; state: 'selected' | 'agreed' | 'disputed'; value: number | null; unit: string | null; observation_ids: string[] };

export type SaturationAssessment = { benchmark_id: string; series_id: string | null; policy_version: string; state: 'ineligible' | 'unknown' | 'saturated' | 'not_saturated'; eligible: boolean; ineligible_reasons: string[]; threshold: number | null; threshold_formula: string; distinct_model_count: number; distinct_lab_count: number; models_at_threshold: string[]; high_lab_ids: string[]; high_lab_count: number; required_models: number; required_labs: number; evidence: Array<{ model_id: string; lab_ids: string[]; configuration_ids: string[]; observation_ids: string[]; conservative_value: number }> };

export type CatalogSnapshot = { schema_version: string; data_version: string; generated_at: string | null; labs: Lab[]; models: ModelRelease[]; configurations: Configuration[]; benchmarks: BenchmarkVariant[]; presets: Preset[]; coverage_gaps: CoverageGap[]; metadata_claims: MetadataClaim[]; missing_cells: MissingCell[]; saturation: SaturationAssessment[] };

export type ResultsSnapshot = { schema_version: string; observations: Observation[]; cells: DisplayCell[] };

export type DetailsSnapshot = { schema_version: string; sources: Source[]; series: EvaluationSeries[]; observations: Observation[]; external_mappings: ExternalMapping[]; metadata_claims: MetadataClaim[] };

export type MarketSnapshot = { schema_version: string; routes: ServingRoute[]; prices: PriceObservation[]; performance: RoutePerformance[]; usage: UsageObservation[] };

export type ManifestSnapshot = { schema_version: string; data_version: string; snapshot_id: string; generated_at: string | null; files: Record<string, { sha256: string; bytes: number }>; coverage: { models: number; benchmarked_models: number; observations: number; display_cells: number; benchmarks: number }; feeds: Array<{ source_id: string; status: string; as_of?: string | null; attempted_at?: string | null; url?: string | null; record_count?: number | null; error?: unknown }>; };
