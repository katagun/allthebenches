# Competitive review: LLM Stats and All the Benches

Reviewed 17 October 2026 against the live sites. Counts below are observations at review time, not permanent product claims.

## Where LLM Stats leads

- **Discovery:** its [home page](https://llm-stats.com/) exposes task-oriented entry points, a clear leaderboard, model search, and prominent pricing/context information. Its table lists 408 models; our snapshot contains 37 reviewed releases. These are different inclusion policies, but our release coverage is materially narrower.
- **Catalog navigation:** dedicated [models](https://llm-stats.com/ai-models) and [benchmarks](https://llm-stats.com/benchmarks) pages make exploration more approachable than starting with a large matrix. The benchmark page reports 744 benchmarks, while we have 309 variants. Definitions differ; do not present this as an apples-to-apples count comparison.
- **Decision support:** [comparison](https://llm-stats.com/models/compare), cost, speed, and capability views make it easier to shortlist models for a workload. We currently have limited route/price data and no measured latency feed.
- **Discoverability:** its public pages provide substantial server-readable content. Our client-rendered hash routes work on GitHub Pages but are weaker for search indexing and link previews.

## Differentiation to make tangible

Be the inspectable, reproducible evaluation matrix: exact model releases and reasoning configurations, explicit benchmark versions/splits/metrics, direct source locators, competing reports, historical results, and honest coverage gaps. LLM Stats also discusses provenance and methodological limitations; we should not claim evidence is unique to us. Our distinction is the depth and accessibility of the configuration/variant matrix and the open snapshot/pipeline.

Avoid a universal score until a defensible, documented methodology exists. The competitor's [rating methodology](https://llm-stats.com/methodology/llm-stats-score) is a separate product choice, not a reason to average incompatible scores. Preserve the giant matrix, no marketing hero, and mobile density options.

## Implemented in this pass

- Searchable, paginated model directory with lab filters, release-date/name/coverage ordering, logos, and exact-configuration matrix links.
- Benchmark variant directory with category filters, version/family/metric search, metric direction, release coverage, and direct matrix links.
- Coverage and evidence page with reporting relationships, curation limitations, known gaps, snapshot downloads, and correction/contribution links.
- Consistent directory navigation on detail pages; distinct benchmark directory and matrix column picker.
- Reporting relationship visible on individual score cards rather than only inside expanded setup details.
- Coverage derived from published cells, deduplicated by release/variant, excluding disputed or missing scores. Raw observation totals retain conflicting evidence.
- Mobile and desktop regression checks for directory navigation, empty states, logos, downloads, and matrix return paths.

## Remaining work, in priority order

1. **Broader verified coverage:** prioritize missing current releases/families and high-value benchmarks. Use competitor catalogs as discovery leads, then verify each exact release/configuration against primary sources. Do not copy aggregate rankings or attach scores to guessed configurations.
2. **Freshness and coverage audit automation:** maintain per-source refresh policies, flag stale records, and distinguish unavailable public results from uncollected results. Snapshot generation time alone is not result freshness.
3. **Cost comparison:** expand dated provider-route quotes, preserve input/output/cache units and routing differences, then add explicit workload-based cost comparison. Do not call a model cheapest from incomplete quotes.
4. **Static discoverability:** generate crawlable model/benchmark documents, a sitemap, canonical metadata, and social cards during the Python/build pipeline. Keep matrix state in fragments to avoid HTTP URL limits.
5. **Latency and throughput:** add only with a reproducible measurement protocol or a clearly attributed measurement source. No speed estimates inferred from model size.
6. **Protocol-aware comparison summaries:** show overlap and differences within genuinely comparable evaluation series; avoid declaring overall winners from sparse, mismatched evidence.

These are substantive data and architecture projects, not gaps that can be closed by changing presentation or inventing measurements. Existing performance, dependency, provenance, and responsive-layout checks remain release gates.
