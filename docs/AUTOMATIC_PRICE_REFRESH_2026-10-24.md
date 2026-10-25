# Automatic refresh of reviewed price routes

The previous scheduled metadata collector only staged review artifacts. Its endpoint selection also depended on discovery catalogs, omitting reviewed identities that did not match Atlas names. It did not keep published price observations fresh.

## Publication behavior

The Pages workflow now runs daily at 06:47 UTC, as well as on main pushes and manual dispatch. Every deployment refreshes prices after the deterministic source checks and before the final production build. This avoids publishing old committed quotes again on a later code deployment. GitHub may delay scheduled runs; a successful schedule is not a guarantee that an upstream is available.

`python -m pipeline.price_refresh --output web/public/data` collects all 25 exact OpenRouter model IDs present on curated routes, covering the 16 releases added in PR #53 as well as existing routes. The importer only updates existing exact model/provider/tag/service-tier identities; it cannot create routes or transfer prices to a sibling model. Unreviewed endpoints remain excluded. The separate discovery collector now includes curated route IDs even when discovery catalogs are absent.

The Qwen3.8-Max Alibaba route is refreshed from its official model page. The parser requires the original model ID, the Pricing section before Snapshot Versions, Singapore / International scope, USD per 1M tokens and the reviewed billing-table structure. It updates standard input, output and implicit-cache rates. Different regions, snapshot variants, currencies, units or changed layouts are rejected; batch and explicit-cache charges are not substituted for these fields.

## Failures and retained evidence

The workflow restores a dedicated last-good evidence cache. A cold cache is seeded from committed reviewed endpoint snapshots so empty/collapsed-feed protection applies on the first run too. Accepted payloads can be replayed on a new runner with their original observation dates. Cached older quotes cannot replace newer curated observations. New requests must pass identity and feed validation before their timestamps advance.

An upstream failure, empty/collapsed endpoint response or rejected Alibaba table retains the last accepted quote without changing its observation date. Other providers can still refresh and publish. The public Data health panel shows failures and last attempts, including Alibaba. The existing 48-hour expiry remains: a prolonged upstream outage can still reduce fresh coverage, correctly. Missing prices never become zero. Cache eviction falls back to committed evidence, which may already be stale.

The workflow uploads raw refresh evidence and `price-refresh-report.json` for 14 days. The last-good cache is separate from review-only discovery staging. Refreshed data is a deployment artifact rather than an automatic commit to main; committed generated files remain reproducible offline. To inspect the current publication use the deployed manifest, source observation dates and workflow artifacts, rather than expecting deployed hashes to equal the committed data snapshot after a refresh.

## Validation and operation

Regression tests cover all curated IDs without discovery catalogs; exact Alibaba identity/region/currency/units; price changes; last-good replay across clean runners; failed/empty responses without redating; no route or benchmark mutation; and daily deployment wiring. A mobile smoke test runs against the refreshed production build after the existing deterministic desktop/mobile suite. Bundle limits still apply to the final refreshed build.

Run locally against a copy of the dataset and output directory when testing live requests:

```sh
uv run python -m pipeline.price_refresh --dataset /tmp/dataset.json --staging /tmp/price-evidence --output /tmp/public-data
```

The output directory must initially contain the committed generated data so unrelated discovery-feed health metadata is preserved. Manual production refresh: dispatch **Deploy GitHub Pages** on `main`. Inspect `published-price-evidence` and the site's Data health panel if quotes are not advancing. New route identities and provider-specific parsers still require review; this change does not automatically fill the remaining 22 price gaps.

Deployment verification compares UTC timestamps after normalizing equivalent `Z` and `+00:00` suffixes. The first production refresh succeeded but exposed an overly strict string comparison in the smoke test; the follow-up fixes that assertion without changing quote dates or the refresh pipeline.

## Refresh-safe browser tests

Price regressions use `web/e2e/fixtures/prices.ts` to replace only price routes, quotes, source evidence and feed-health inputs in the browser. The app, real worker and benchmark catalog still run normally. Its fixed clock belongs to synthetic observations generated relative to that clock; it is never applied to changing published prices. Two controlled routes provide a paid quote and an explicit zero quote, while other models exercise unknown pricing. Feed fixtures cover successful collection and retained stale evidence with separate accepted/attempt timestamps.

The deterministic tests verify mobile show/hide and saved state, source links, zero versus unknown, stale-price opt-in across reload, feed counts/timestamps, and eligibility one millisecond before 48 hours, exactly at 48 hours, and for a future observation. They work against either the local preview or a deployed app because their changing inputs are isolated.

`web/e2e/price-refresh.spec.ts` is the separate **unmocked** publication suite. It freezes the actual run time, reads the served comparison snapshot, independently calculates eligible price coverage and checks the rendered UI. It tests mobile evidence at 320/390/844px, feed health at 1440/390px, market/comparison agreement and equivalent UTC timestamps. Counts, dates and failed-feed expectations come from that publication; it does not require a specific provider to remain failed or a fixed number of available routes. This suite runs after automatic refresh in the Pages workflow.

Run both layers together against production:

```sh
LAYOUT_BASE_URL=https://allthebenches.com/ pnpm --dir web exec playwright test \
  e2e/mobile-prices.spec.ts e2e/feed-health.spec.ts \
  e2e/review-regressions.spec.ts e2e/price-refresh.spec.ts
```

A deterministic fixture pass proves application behavior under controlled conditions. Only the unmocked tests exercise actual published quote availability and collection metadata. An upstream outage may legitimately render unknown prices; publication tests check that the UI agrees with the evidence rather than fabricating fresh coverage.
