# Benchleader comparison and benchmark source audit

Reviewed 18 October 2026 against local main `640c020` and live public sources. This is a research and ingestion plan, not a completed data import. No candidate scores in this directory are served by the application.

## Finding

Our coverage gap is real. The curated dataset contains 45 releases, 111 configurations, 318 benchmark variants, and 848 observations. For Mistral Large 4 it contains **17 observations across 14 benchmark variants and three configurations**. Eleven observations come from the Mistral announcement; six are BullshitBench metrics for two settings. Only **three** of those variants occur in the current 31-column Frontier preset (DeepSWE, Terminal-Bench, and B3). Both missing collection and preset visibility contribute to the sparse appearance.

Benchleader's [home page](https://www.benchleader.com/) reports 439 ranked models and 761 ranked configurations. Its [benchmark directory](https://www.benchleader.com/benchmarks) links 219 benchmark pages. This audit fetched all 219 and resolved their credited publisher and source URL: **43 publisher labels, zero failed pages, zero missing publisher links**. Publisher labels are not necessarily distinct organizations or data feeds. Our 318 variants are not evidence of broader coverage: historical, report-specific and metric-specific variants inflate a different denominator.

The [Mistral page](https://www.benchleader.com/models/mistral-large-4) contains **67 benchmark rows**, including submetrics and composites, versus our 14 variants. These are not 67 independent tests or 53 proven missing compatible cells.

## Why our pipeline missed this

`pipeline/collectors.py` has automated discovery for peacefulcoexistance, models.dev and OpenRouter, plus route endpoints. Benchmark scores were largely curated from a finite selection of reports and leaderboards. There are no equivalent recurring ingestion adapters for Epoch, Vals, AA or LiveBench. Merely adding another source URL to `docs/SOURCES.md` never made it a collector.

The scheduled freshness workflow checks prices, usage and route performance. It records benchmark-source ages as historical information; it does not compare a dynamic leaderboard's current rows with our imported rows. Thus a valid build and a freshness report can coexist with substantial missing benchmark data. Historical measurements should remain valid; we need separate **last successful source refresh** and **upstream coverage** checks.

## What to adopt and where to differentiate

This is an information architecture and data-functionality comparison, not a new cross-device visual test.

| Area | Gap / lesson | Improvement for All the Benches |
| --- | --- | --- |
| Breadth | Their evaluator-led collection reaches many more releases and results. | Build source adapters before another cosmetic redesign. Ingest all eligible rows for our known releases, then review unmatched releases. |
| Model pages | Category grouping, visible setting choices and sources make a model's evidence easier to explore. | Add category sections and coverage counts to existing model pages; link directly to “all results for this model” and “shared benchmarks” in the matrix. |
| Benchmark pages | Test explanations and limitations give context to the number. | Add concise task, scoring, version and interpretation descriptions with primary citations; retain exact protocols in evidence panels. |
| Discovery | Task-oriented browsing and cost/speed comparisons help people choose. | Add optional coding/research/agent collections and configurable token workloads. Keep the matrix as the main workspace and avoid a marketing hero. |
| Freshness | Source health and result history make maintenance visible. | Display last checked, last changed, stale/failed state and import coverage per source. Publish a result-change log, including corrections. |
| Comparisons | Summary rankings are convenient but hide selection and normalization choices. | Prioritize shared-protocol comparisons, coverage denominators and uncertainty. Offer optional summaries only with explicit eligibility and weighting. |
| Provenance | Our schema already represents reports, configurations, setup and uncertainty separately. | Make these distinctions legible, including independent vs provider-reported evidence and conflicting results. Do not silently choose the highest score across harnesses. |
| Open data | Their public summary does not contain the raw score matrix. | Publish documented, versioned raw observations, aliases and source manifests under applicable source terms, plus reproducible adapters. This is a stronger differentiator than another opaque index. |

Our mobile cards, giant matrix, persistent/shareable state, static detail pages and evidence panels already exist. They need better coverage and discovery, not replacement with features we already have.

Benchleader describes a best-run/default-setting policy and a normalized composite in its [methodology](https://www.benchleader.com/methodology). We should retain exact releases, harnesses and settings and avoid treating cross-benchmark disagreement as experimental confidence. Its JSON is a top-100 summary, not a full score export. Its derived index/category fields are labeled CC BY-NC 4.0; upstream measurements retain source-specific terms. Use it for discovery, then collect upstream.

## Mistral: where the 67 rows come from

| Credited source on model page | Rows | Next action |
| --- | ---: | --- |
| Artificial Analysis | 19 | Use its documented API where available; audit additional public page fields and benchmark versions. |
| Vals AI | 16 | Collect benchmark pages and model configuration details; the primary model page already has 17 results. |
| Epoch AI Benchmarking Hub | 10 | Import official CSV archive; distinguish internal runs from mirrored external results. |
| Arena | 10 | Import the dated leaderboard dataset across categories, with intervals and sample counts. |
| LiveBench | 8 | Resolve suite/version and category definitions before importing. Current 2.0 is a different suite. |
| SciCode, Cognition, Harvey, Scale SEAL | 1 each | Follow direct benchmark sources; deduplicate observations mirrored through Epoch/AA. |

Every row's source link is in [mistral-large4-source-leads.csv](mistral-large4-source-leads.csv). The rows are discovery leads, not approved scores.

### Primary evidence checked

- **Epoch:** the [official data page](https://epoch.ai/benchmarks/use-this-data) links [benchmark_data.zip](https://epoch.ai/data/benchmark_data.zip). Mistral appears in 26 records across 17 CSV files. This includes metadata and processed duplicates; it is not 26 new observations. Eight direct benchmark CSVs include GPQA 0.8806818, OTIS 0.9833333, FrontierMath v2 tiers 1–3 0.5859649, tier 4 0.2682927, SimpleQA 0.2, Chess 0.33, Mystery Game 0.17 and Furniture Assembly 0.2083333. They identify `mistral-large-4-0_high` and run IDs. Preserve raw fraction units, standard errors, dates and original run identity. External CSVs additionally expose FrontierCode's Chisel harness/Mean@5 and original source links. Epoch explicitly distinguishes its own CC BY data from externally licensed material.
- **Vals:** its [Mistral model page](https://www.vals.ai/models/mistralai_mistral-large-4) exposes 17 results and a `high` reasoning setting. Examples include Finance Agent v2 **54.68%**, Harvey legal agent **15.83%**, Vibe Code v1.1 **78.40%**, and Terminal-Bench 4.0 **27.78%**. SWE-bench Multimodal **33.13%** is another lead beyond Benchleader's listed 67. The [Finance Agent leaderboard](https://www.vals.ai/benchmarks/fabv2) independently within that publisher confirms 54.68%. Capture benchmark-level settings and intervals before admission.
- **Artificial Analysis:** the public [model page](https://artificialanalysis.ai/models/mistral-large-4) embeds structured `currentModel` data. We extracted fields directly, rather than copying Benchleader: Terminal-Bench 0.2676768, SciCode 0.5416667, HLE 0.3503244, MMMU-Pro 0.7641618, AA-LCR 0.8133333, AutomationBench 0.5990136, signed Omniscience -5.3 and Briefcase 1391.97 Elo, among others. These fields have different units. The [documented API](https://artificialanalysis.ai/api-reference) requires a key and attribution; keep the key server-side in collection. Public page serialization works for research but is not a stable API contract.
- **LiveBench:** inspected its public frontend to locate [2.0 CSV](https://livebench.ai/table_2026_09_02.csv) and [historical v1 CSV](https://livebench.ai/v1/table_2026_06_25.csv). The frontend labels the 2.0 release key `2026-09-02` as `2026-10-14`; preserve both. Current Mistral values are design/layout 65.6, research 28.1, browser 8.0, coding 60.0, long-horizon 11.8, data analysis 76.5 and reasoning 83.9. The v1 file contains task-level values for `mistral-large-4-high`. Do not map these to Benchleader's eight category scores without reproducing the correct release and aggregation. Its [repository](https://github.com/LiveBench/LiveBench) also documents answer/judgment downloads.

Raw primary extracts, locators, source URLs and SHA-256 capture hashes are in [mistral-large4-primary-candidates.json](mistral-large4-primary-candidates.json). A capture hash supports identity of the downloaded bytes, not independent reproduction of the evaluation.

### Exceptions caught during verification

1. Benchleader renders AA Cyber Index as **4,951.1%**. This is a unit-validation flag; we have not established the correct underlying value in this audit. Do not import it as a percentage.
2. Terminal-Bench has **28.3%** in our Mistral announcement, **27.78%** at Vals and approximately **26.77%** at AA. These must remain separate series until protocol and dates are reconciled, not overwrite each other or take the maximum.
3. Benchleader describes “cost per run” as one full Intelligence Index run, but the AA payload has approximately **$1.134 in `intelligenceIndexCostPerTask`**, versus **$1,607.12 in `intelligenceIndexCost.total`**. Verify definitions before presenting cost; do not call a per-task aggregate a full evaluation run.
4. Benchleader labels the model open weights, while AA's captured payload says `isOpenWeights: false`; Vals also calls it open. Our release evidence records API preview and announced later weights. Recheck the official release/weights repository, rather than overwriting identity metadata from leaderboard labels.
5. AA's raw non-hallucination counterpart would require an explicit transformation of hallucination rate. Derived metrics must carry their formula and denominator; never present them as an unmodified raw field.

## Source coverage roadmap

The full [219-row mapping](benchleader-benchmark-sources.csv) records benchmark, publisher, source URL, page hash and check date. The [source registry](benchmark-source-registry.json) groups all 43 publisher labels and records the 23 source entries exposed in the public JSON. Benchleader advertises 24 feeds: its JSON list alone is therefore not a complete feed specification. Nor does this inventory establish that the internet has no additional benchmarks.

| Priority | Source family | Acquisition contract / review |
| --- | --- | --- |
| P0 | Epoch (44 directory entries) | Official CSV ZIP and Python client; separate internal from external results, preserve original publisher, deduplicate processed ECI data. |
| P0 | Vals (45) | Public benchmark/model tables; inspect page payload or supported export, pin versions and settings, preserve reported uncertainty. No stable API contract verified yet. |
| P0 | Artificial Analysis (34) | Documented keyed API with explicit units; determine which supplementary metrics need another supported source. Preserve prompt-length-specific latency. |
| P0 | Arena (13) | [Hugging Face leaderboard dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset), pinned revision/date; keep categories and Agent Arena metrics distinct. |
| P0 | LiveBench (8) | Public dated tables plus category/breakdown metadata; separate v1 and v2. |
| P1 | Scale SEAL (23), Scale/CAIS (2), HELM (6), MathArena (4) | Audit versioned leaderboard artifacts, split/task definitions and original-source terms; avoid duplicating hub mirrors. |
| P1 | SWE-bench, Terminal-Bench, BFCL, tau-bench, Aider, ARC | Capture complete known-model rows and configurations, not a few manually selected frontier rows; extend existing ARC coverage rather than double-importing. |
| P2 | Remaining specialist publishers | Use registry URLs; confirm stable artifacts, metric direction, identities, dates and reuse terms individually. |
| Keep | BullshitBench, TRACES, official model/system cards, safety sources | Sources outside this competitor inventory remain useful. Clearly separate provider reports from independent evaluations. |

### Implement as reviewable tickets

1. **Source registry + health:** add adapter/version, upstream release, last successful fetch, last semantic change, licence/attribution, row counts, retained-stale status and review owner. Avoid refreshing an observation's evaluation date merely because a page was fetched again.
2. **Epoch adapter first:** deterministic fixtures for eight direct Mistral runs plus mirrored records; include all resolvable existing models. Queue unknown IDs. Exclude metadata/processed duplicates; preserve uncertainty and protocol versions.
3. **Vals + AA + LiveBench + Arena adapters:** stage raw records and candidate mappings. Require exact release/configuration identity; unknown effort remains unknown. Do not merge harness runs into the same cell without visible multiple-report handling.
4. **Coverage reconciliation:** report upstream eligible records, mapped, imported, duplicate, rejected, unresolved and inaccessible counts. Define completeness against a dated source snapshot, not the Cartesian product of every model and benchmark.
5. **Guardrails:** offline pre-commit fixtures for unit transforms, range/direction, null-vs-zero, aliases, mirrored duplicates, corrected scores, stale source fallback and disappeared rows. Run network refresh/coverage checks in scheduled CI; alert on dropped row counts and unhandled new benchmark IDs. Never depend on live network state for deterministic score tests.
6. **Coverage UI:** show “3 in this view · 14 total recorded variants” for the present Mistral data, offer “show all recorded results”, and distinguish “not collected” from a source's explicit “not evaluated”. Add category grouping and source freshness to model pages.

Acceptance criterion: for each chosen source snapshot and existing canonical release, every eligible result is either imported with exact provenance or has a machine-readable exclusion reason. Only then claim complete coverage of that source. A complete global model-by-benchmark matrix is not available: many evaluations were never performed or published.
