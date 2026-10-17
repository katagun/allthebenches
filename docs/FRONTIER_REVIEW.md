# Frontier evidence review — 17 October 2026

This local-only pass adds 108 reviewed observations. The canonical snapshot now contains 37 models, 51 configurations, 282 benchmark variants, and 492 observations. All 37 models have some numeric evidence; this does not imply complete coverage or controlled comparability.

| Release | Added observations | Current total |
| --- | ---: | ---: |
| GPT-6.1 Sol | 56 | 56 |
| Muse Spark 1.3 | 13 | 13 |
| Muse Wonder | 15 | 15 |
| Muse Wonder Full | 15 | 17 |
| Mistral Large 4 | 9 | 11 |

Research was delegated to three GPT-6 Luna agents. The coordinating review inspected the primary source text and Meta's rendered capability table, checked exact release/effort identities, corrected one AutomationBench attribution, and validated integration.

## Sources and review decisions

- [GPT-6.1 audit](../data/expansion/frontier-gpt61-audit.md): OpenAI system-card results retain native units, including 0–1 rates, length-adjusted scores, correlations and negative log-likelihood. Unknown effort remains unknown. Surge GDP.pdf and sudo L7 supply exact max-effort results; sudo L7 retains Codex in setup. Parallel search and no-search conditions remain distinct.
- [Meta audit](../data/expansion/frontier-meta-audit.md): Wonder and Full capability rows were checked against the rendered official PDF table. Full's SWE-Marathon result is explicitly xhigh and receives a separate configuration. Spark's official max-effort table contributes twelve metrics. OSWorld partial and binary scores remain distinct, as do different OSWorld releases and Terminal-Bench versions.
- [Mistral audit](../data/expansion/frontier-mistral-audit.md): nine explicit release-page numbers are included, with incomplete evaluation settings marked unknown. The model remains a public API preview with announced weights. The model card discloses 1.05T total and 52B active parameters; claims use 1,050B and 52B.
- The coordinator additionally verified [Surge's GDP.pdf leaderboard](https://surgehq.ai/benchmarks/gdp-pdf), exact `Muse Spark 1.3 (xHigh reasoning)` row, 27.6%. This is recorded in `frontier-review.json`, separate from Spark's official max-effort configuration. It resolves the extraction agent's narrower exclusion of that result from Meta's own sources.
- Meta's Vals Finance Agent V2 private-test-set accuracy rows are reconciled to the existing `vals_finance_agent_v2` variant. Their source-specific series and provenance remain separate from Google's reported rows.
- Mistral's 657-workflow AA-AutomationBench result is a distinct variant, rather than being added to the existing Google/Zapier lineage. Meta's Spark v3/600-workflow and Wonder AA variants also remain distinct.

The Meta PDF extractor and downloaded PDF reported different pagination. The downloaded PDF's SHA-256 matched the existing canonical source, and its actual rendered capability table was inspected. Locators retain the extraction's printed-page context; this is not a claim that the two rendering systems paginate identically.

## UI and verification

The eight-column Frontier default now uses GDP.pdf and Vals Finance Agent V2, and includes GPT-6.1, Spark 1.3 and base Wonder. A separate Frontier gap review preset exposes extra metrics. URL state still takes precedence, so an existing saved/shared Qwen view is not forcibly replaced.

A review also found that one-decimal formatting rounded rates such as 0.983 to 1. Score formatting now preserves numeric precision in cells and evidence. A regression test covers 0.983, 0.5282 and 1.691.

## Remaining gaps

GPT-6.1's exact DeepSWE, OSWorld, AutomationBench and Terminal-Bench Science launch-chart scores/settings remain uncurated; relative deltas were not converted into absolute results. Some safety results for Spark/base Wonder and Mistral's chart-only finance/legal/science results remain missing. The rows include provider reports, quoted evaluator results and direct evaluator measurements, with those relationships retained. No source-specific result is represented as an independent replication unless its provenance supports that claim.

Nothing was published. The local development server remains at `http://127.0.0.1:4173/`.
