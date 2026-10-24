# Feed health and price reconciliation — 2026-10-24

## Changes

The comparison footer now has an expandable **Data health** panel on desktop and mobile. It distinguishes last collection attempt from last accepted payload, flags failed refreshes, and computes fresh available price coverage using the same eligibility rules and clock as the comparison view. Counts describe the whole catalog, independent of view filters. Collection success is explicitly a recorded snapshot result, not a live availability guarantee or automatic promotion of discovered records.

Collectors validate JSON content type, a 50 MB response size ceiling, source-specific collection wrappers and record identities. Empty/error-shaped responses and collections smaller than half the last accepted record count are rejected. Endpoint responses must match the requested model ID at both response and provider levels. Successful unaffected feeds advance independently; rejected feeds retain their original data, hash, and retrieval timestamp, with a separate attempt timestamp and failure status. First-time failures never report success. No requested endpoint IDs is an error at the collector boundary.

The build publishes compact metadata for the four known collector sources, excluding reconciliation proposals, raw payloads and upstream exception details. Offline builds preserve the recorded health snapshot. The daily staging workflow restores/saves cached last-good staging; any partial collection now fails its workflow step instead of silently passing. The cache is bounded, evictable storage, not a permanent archive. Collection and publication remain review-separated.

## Reviewed price refresh

Captured current responses using `scripts/refresh-reviewed-prices.py`, requesting only exact OpenRouter IDs already used on curated routes. The dated endpoint snapshot records raw response bytes (Base64), SHA-256, capture times, parsed content and attempt status. The route reviewer verifies byte/hash/JSON consistency before importing routes. Prices and performance use the existing exact route importer.

- 9 reviewed upstream IDs requested; 8 accepted and 1 retained after an empty response.
- 88 provider endpoint records reconciled; 84 existing identities and 4 additional provider routes on already mapped models.
- 88 quotes refreshed; **86 available routes across 8 of 47 releases** at publication. Two returned routes do not report available status.
- 90 total quotes remain: 88 current and 2 historical. DeepSeek R1 returned an empty endpoint collection; its October 18 quote was retained. One previously listed Kimi K3 route disappeared from an otherwise accepted response; its availability is now unknown and its old quote remains historical.
- Fresh price coverage: Claude Opus 5, DeepSeek V4 Pro 0813, GPT-4, GPT-5.6 Sol, GPT-6 Astra, GPT-6.1 Sol, Kimi K3, and Muse Spark 1.3.
- 1,300 performance rows were captured by the existing importer. Latency normalization remains explicitly inferred; it is not a newly verified source unit.

The coverage gap now reflects these counts. Missing prices remain unknown, not free. Fresh prices expire at 48 hours; failed attempts cannot renew their age. No model identities were inferred from similar names, and no usage rows were promoted.

Evidence: `data/expansion/openrouter-endpoints-current-2026-10-24.json` and the adjacent audit. The route audit is reproducible: rerunning it classifies newly added routes as existing matches. The four additions above describe the change from the pre-refresh dataset.

## Regression coverage

Mocked collector tests cover empty/error/collapsed feeds, missing identities, mismatched endpoint IDs, first-run failures, repeated retention, independent partial successes, and compact health publication without raw data. Route-review tests cover empty accepted envelopes and missing-route availability without changing failed-model records. UI tests cover attempt versus accepted timestamps, absent health metadata, and price expiry. Browser checks exercise the published panel at 1440px and 390px, including no horizontal overflow and retained R1 evidence. Existing selection, mobile reported-score and stale-price regressions remain in the suite.

Performance rows now travel with the content-addressed evidence payload loaded on demand. The comparison startup keeps prices and route metadata but omits unused performance rows, preserving the startup budget; model detail pages restore the complete performance records. Regression tests verify that lazy loading does not mutate the cached comparison data.

## Remaining issues

- 39 releases lack fresh available prices: one has retained historical pricing and 38 have no reconciled price. This task refreshes reviewed identities; wider mapping still needs evidence review.
- Empty endpoint lists can mean legitimate withdrawal or transient upstream failure. They require review; this policy deliberately does not automatically delete last-good evidence.
- A drop below half the accepted count requires review, even if legitimate. The 50 MB check occurs after download and is not a streaming memory limit.
- The health panel updates when a reviewed site snapshot is published. Daily collection artifacts/caches do not automatically update the live site or curate prices. Quotes can therefore expire between publications.
- GitHub may evict the staging cache. Without previous data, a failed response is reported as an error rather than fabricated retained coverage.
- Provider status and quoted prices are observations, not guarantees of route availability or final billed cost; conditional override limitations remain recorded on quotes.
- Mobile bar-view CSV exports still follow matrix selection semantics, as documented in the prior mobile fix report.
