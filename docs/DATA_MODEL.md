# All the Benches data contract and methodology

This is the contract to implement, not a generated schema. Python owns validation and publication. A result is an observation, not an editable number in a wide spreadsheet. The UI pivots validated long-form observations into a matrix.

## Entities and ownership

| Entity | Required meaning and fields |
| --- | --- |
| Lab | Stable ID, name, aliases, developer headquarters ISO country code(s), effective/verified date, source references. Keep developer, parent, and inference provider separate. |
| Model release | Stable ID, lab IDs, family ID, exact public name, version/snapshot, aliases, modalities, release date with precision, first-seen date, access state, weights availability, upstream IDs, metadata claim references. |
| Configuration | Model release ID, provider-native reasoning label, reasoning token budget if known, mode, precision/quantization if known. Unknown, default, disabled, and not applicable are different values. |
| Benchmark variant | Family ID, exact version, subset/split, task, category, modality, metric name, unit, bounds, direction, scorer/version, benchmark owner and documentation. One column must not mix different variants. |
| Evaluation series | Benchmark variant ID, protocol/version, evaluator, comparability rules, tools, sampling/pass-k, judge and version, budgets and infrastructure limits, eligible setup fingerprints. Unknowns do not establish compatibility. |
| Observation | Stable ID, configuration ID, benchmark variant ID, evaluation series ID or explicit unknown, numeric value and native unit, source ID and locator, evaluator, evidence relationship, reported/evaluated dates, setup, uncertainty if published, review state, supersession links. |
| Source | URL, title, publisher, original evaluator if different, publication/retrieval dates, version or commit, content hash when captured, license/attribution, extraction method, exact table/page/row locator, short evidence excerpt where appropriate. |
| Metadata claim | Entity and field, value/range, unit, basis (disclosed / measured / third-party estimate / internal inference / speculation), confidence rationale, source IDs, method, dates, selected status. Conflicting claims remain available. |
| Serving route | Model release mapping, provider, upstream model/endpoint IDs, routing variant, availability, supported capabilities, context tier, quantization if documented, evidence. Not a new model merely because another host serves it. |
| Price observation | Route ID or explicit catalog quote scope, currency, input/output/cache prices and units, context tiers, request/tool charges if present, observation time, source, availability/free restrictions. Preserve raw decimal values. |
| Usage observation | Platform, upstream route/variant ID, period start/end, grain, metric, numeric total or ordinal rank, coverage/censoring, sampled status, source as-of timestamp, source ID. Usage is not a benchmark result. |
| Preset | Version, name, selected configurations, columns and their source/series policies, editorial reason, reviewed date, saturation policy version. |

## Identity and discovery

Take the union of models.dev, OpenRouter, peacefulcoexistance, official release pages, and benchmark records. Discovery creates candidates; it does not automatically publish reviewed identities or scores. Preserve historical records after providers remove them.

Keep a reviewed external-ID mapping table with source, external ID, internal model ID, optional route ID, mapping status, evidence, and valid-from/to dates. Never join on display name alone. Retain dated snapshots; a mutable `latest` alias is a route alias with resolution history. A free/fast route, hosted quantization, or provider is not automatically a new canonical release. A materially changed checkpoint is.

Reconcile source discrepancies field by field. Official release evidence decides model identity and launch dates. peacefulcoexistance supplies curated lab/headquarters and release/licensing claims, retaining its attribution and linked evidence. models.dev supplies discovery, specifications, and provider mappings. OpenRouter supplies its routes, quotes, and its own usage. No single source wins for every field.

OpenRouter's catalog creation time is not the model's release date. Import both separately. Distinguish weights announced for future release from weights actually available, and open weights from an open-source license determination.

## Observations and display selection

Never estimate, interpolate, or copy benchmark scores across model releases, reasoning settings, datasets, or harnesses. Only metadata may have estimates. Zero is a valid result when the source reports zero.

Required setup fields include tools/web/code access, harness name/version if reported, reasoning setting, pass-k or repeated-run aggregation, task count/subset, prompt protocol, grader, fallback models, and resource budget. Values may be explicitly unknown in a reported-results view. A result with a fallback model is a system/configuration result with a conspicuous qualification, not a clean result for the primary model. Exclude heterogeneous fallback systems from the default model-only preset.

For each column, first select the benchmark variant and comparison policy. Prefer a benchmark-maintainer or independent standardized evaluation series when it covers the relevant models. In reported-results mode, a declared source order may fall back to providers, with visible setup differences. Comparability checks happen before source priority. Do not choose a numerically higher result to resolve a conflict.

Within a compatible series, prefer an explicit corrected/superseding observation, then a current reviewed record according to the declared source policy. If equally preferred conflicting observations remain, mark the cell disputed and expose both; exclude it from strict filtering/ranking until reviewed. Reposts link to the original observation and do not count as independent corroboration.

Store reporting relationships separately: provider self-report, evaluator's own measurement, third-party reproduction, or quoted competitor result. A provider comparison table quoting another report is not an independent measurement of that competitor.

Source, model, or benchmark deletion never deletes history. Retractions and corrections change status with reason and supersession. Preserve source precision; display rounded values without sorting rounded strings. Do not invent confidence intervals or statistically significant winners.

## Missingness

A missing display value has a reason: not reported, not evaluated, not applicable, unavailable source, excluded protocol, disputed, or missing configuration. A reported failed task may still legitimately score zero. Numeric thresholds fail for all absent values; zero participates numerically.

All-model discovery records may have no observations. Keep catalog count, benchmarked-model count, observation count, and cell coverage distinct. A populated percentage should use the displayed row/column matrix as its denominator, not the full discovered catalog.

## Prices

Normalize published prices to USD per million tokens when the upstream unit is documented. Keep source units and decimal strings so rounding cannot change a filter decision. Never interpret absent, unsupported, or non-price sentinel values as free. A real zero quote is free subject to its route restrictions.

Compare input and output constraints against the same currently available route and context tier. Do not combine one provider's cheapest input price with another's cheapest output price. Prefer endpoint quotes; catalog quotes lacking route details must be labeled as such and excluded from route-specific guarantees.

Default displayed prices are uncached text input/output quotes. Cache, batch, long-context, tools, images, and regional charges remain separate details. “From” pricing must say which eligible routes were considered. Retrieval date and source date appear in the drawer; quotes aged 48 hours or more receive a stale label and fail “current price” filters unless the viewer includes stale quotes.

Token price is not benchmark execution cost. Do not label price divided by benchmark score as efficiency. A later scenario calculator may combine an explicit input/output mix on one route; it must explain that reasoning tokens and actual workloads vary.

## Popularity

Use OpenRouter's own documented data, not a count of catalog entries or benchmark scores. The first metric is public prompt-plus-completion token volume by variant on the latest complete published UTC day. Preserve the platform's scope, source timestamp, metric, and required attribution.

The daily dataset publishes a top 50 and an aggregate Other bucket. Therefore an omitted model has censored/unknown volume, not zero. Keep Other for dataset totals but never map it to a model. Do not attribute the same usage to each reasoning configuration. Display usage at model/route scope, with a label that it covers all included reasoning settings.

A sum across seven daily snapshots is exact only for a variant observed on every included day (or days known to precede availability). Otherwise it is a lower bound. Do not rank such sums as exact weekly totals. Prefer a source-supplied aggregate with documented coverage, or keep daily volume for the MVP. A source-provided weekly ordering can be shown as an ordinal ranking without inventing volumes.

Keep free and paid variants separately at launch. Collapsing them requires reviewed alias mapping, mutually exclusive traffic, complete coverage, and a published aggregation rule. Never double-count aliases or distribute a missing model's share of Other. A model absent from OpenRouter can still be included in the frontier view.

Usage does not represent global market share, unique users, spend, preference, or intelligence. Tokenization and output length affect volume. Sampled task/language breakdowns must remain labeled estimates and are deferred beyond the weekend.

## Publication and freshness

Maintain reviewed source records plus deterministic generated artifacts. Proposed outputs:

- `manifest.json`: schema/data version, snapshot ID, generated time, last reviewed benchmark update, per-feed source as-of dates and health, checksums, coverage totals.
- `catalog.json`: small model, lab, configuration, benchmark, and preset metadata.
- `results.json`: selected display records plus observation references.
- `details.json`: full evidence and alternative observations, lazy-loaded.
- `market.json`: current route quotes and usage summaries, with coverage metadata.

Use relative paths under the GitHub Pages project base. Date display can localize to the viewer; OpenRouter bucket boundaries stay labeled UTC. Refreshing HTML must not advance the dataset's source freshness date. Keep the last valid snapshot when a feed fails, mark it stale, and make the failure visible in CI and feed health. Never overwrite a good source with an empty failed response.

## Client view state

The frontend owns a versioned, validated view-state contract shared by URL serialization and optional localStorage persistence. This is user preference state, separate from the published data schema. Reuse the same parser and semantic validation for both inputs. Persist only the allowlisted filters, search, preset/category, columns, sort, and comparison selection, using stable IDs rather than display labels.

Use a storage key namespaced by application and normalized deployment base path, such as `allthebenches:/allthebenches/:saved-view`, because other GitHub Pages projects can share the same origin. The stored envelope contains `format_version`, `saved_at`, and `view`; the presence of a successfully saved envelope records the opt-in. Do not store credentials, source payloads, or scraped data there. Saved filters apply to the currently loaded dataset, not a frozen copy of old scores.

Load, parse, migration, validation, and writes must handle errors without breaking the table. Migrate only known state versions. Preserve unresolved restrictive conditions after data changes; they must not produce passing matches until resolved or explicitly removed. Browser back/forward navigation follows URL state without overwriting saved preferences. Shared-link sessions do not write the remembered view until the visitor explicitly saves that view. Implement the opt-in, clearing, and forgetting behavior defined in PRODUCT.md.

## Validation examples that must pass

1. A reported zero survives import, display, filtering, and CSV export.
2. A missing score fails `>= 0`, while actual zero passes it.
3. High and medium configurations cannot combine to satisfy two thresholds.
4. A 90% pass@10 score cannot replace a 70% pass@1 observation.
5. A benchmark's changed subset/scorer is a different variant or series.
6. A quoted competitor score retains its original evaluator and source chain.
7. A 100–300B estimate fails a maximum 200B size filter; a 100–150B estimate passes when estimates are enabled.
8. Three settings of one model do not establish saturation; three releases from two labs can, within one eligible series.
9. An attack-success metric sorts ascending; an unbounded metric never gets the generic ceiling rule.
10. Upstream removal preserves the historical model and its benchmark observations.
11. An absent OpenRouter top-50 row stays unknown, and a six-day sum stays a lower bound for a seven-day window.
12. Two routes cannot be combined to satisfy input and output price constraints.
13. A provider-created timestamp cannot overwrite the model release date.
14. Foreign-key, unit, range, duplicate, provenance, and source-status errors block publication.

Use synthetic fixtures for tests and label them; never ship them as real scores.

## Comparison implementation update — 23 October 2026

The client uses exact configuration scores for numeric display, sorting, mobile bars, and winner coloring. A single report must be finite, in the benchmark unit, non-disputed, and admitted by the saturation filter. Multiple reports are conservatively unranked even if their values agree; adjudicating compatible-series agreement remains future work. Matrix cells keep their selected configuration; “Other setups (n)” opens evidence without attributing those scores to it. Mobile bar view selects a reporting configuration for the chosen benchmark and uses that actual row for both its score and evidence target. It never shows setup counts in place of available model scores. Explicit Compare configurations and filters remain binding; [selection policy](MOBILE_REPORTED_SCORES_2026-10-23.md).

Current price filtering admits USD-per-million-token quotes observed less than 48 hours before the explicit query clock, with `available: true` on an available/listed route. Future/invalid dates, missing routes, unavailable routes, and unsupported currency/units fail closed. The saved `includeStalePrices` flag defaults to false for both new and older version-1 views. Historical mode includes older quotes and labels them; it does not convert currencies or override availability. Input and output limits are compared as decimals against the same quote. No source records or generated dataset schemas were changed.

CSV remains an evidence export: `value` contains the reported observation, including disputed reports; `comparison_value` is blank and `comparison_eligible` is false whenever that evidence cannot supply the displayed numeric comparison. Alternate setups are never substituted into the selected configuration's export rows.
