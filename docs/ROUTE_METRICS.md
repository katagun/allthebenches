# Route prices and measured performance

OpenRouter endpoint observations remain separate from model benchmark scores. A serving route identifies an already reviewed provider endpoint; imported rows join only when its exact upstream model ID, provider name, tag, and service tier reproduce the existing route ID. The importer does not create or match routes from model names.

`RoutePerformance` stores one reported percentile per route, metric, optional workload, source window, and capture time. The endpoint response fields `latency_last_30m`, `throughput_last_30m`, and `perf_last_30m_by_workload` provide p50, p75, p90, and p99. The API reference shows those response fields and a rolling 30-minute suffix, but does not specify the latency unit or whether it is time to first token, total response time, or another measure. The importer therefore preserves the numeric latency value unchanged and labels its unit `source_reported`. It also preserves aggregate endpoint percentiles and workload-specific values separately. Where provided, workload `request_count` is retained as the sample count.

OpenRouter describes throughput as tokens per second in its product performance documentation, so those measurements are labeled `tokens_per_second`. The UI shows the captured time and snapshot age, describes the reported 30-minute sampling window, and marks values stale once the capture is older than that window. It does not treat the stored snapshot as live data.

The documented token price fields (`prompt`, `completion`, `input_cache_read`, and `input_cache_write`) are USD per token. The importer multiplies those values by 1,000,000 for the existing `USD per 1M tokens` fields. One-hour cache-write and other charge keys, including search pricing, are retained separately with their original value and marked with `source_reported_unit` because the endpoint API reference does not document their unit. The UI does not infer a per-request, per-search, per-image, or cache-write unit.

The official source references are [OpenRouter's endpoint API](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model) and [OpenRouter's performance descriptions](https://openrouter.ai/openai/o3/api). The endpoint reference currently demonstrates the percentile structures but does not document the raw latency unit or measurement semantics.

To import the current staged endpoint snapshot into curated data, run:

```sh
python scripts/import-route-metrics.py --dataset data/curated/dataset.json --staging data/staging/openrouter-endpoints.json
```

The operation is idempotent for the same staging snapshot: current metric rows replace the previous OpenRouter endpoint rows for exactly matched routes, and price records are upserted by their existing route-scoped IDs. The importer updates matching source retrieval timestamps and hashes from the staged snapshot. Review the resulting source and dataset diff before publication.

The reviewed public response snapshot for this import is `data/expansion/openrouter-endpoints-2026-10-18.json`; pass it with `--staging` to reproduce the import offline. Unmatched endpoints are counted and require identity review before publication.
