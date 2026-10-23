# Priority review fixes — 23 October 2026

Follow-up to the [22 October review](DEEP_REVIEW_2026-10-22.md) and [recommended fixes](RECOMMENDED_FIXES_2026-10-22.md). These changes address stale configuration selection, alternate-setup score attribution/ranking, and stale price filtering. Source records, canonical schemas, and generated datasets are unchanged.

## What changed

### Configuration selection and cached queries

Visible benchmark IDs now always participate in the row-query key. Changing benchmarks with an empty search recalculates the most-covered configuration immediately. Returning to an earlier selection can use the matching cached result. Unused model checkbox selections still do not trigger row selection until compare mode consumes them.

The worker and fallback receive the same explicit `asOf` timestamp. Both the query key and worker-client cache account for it, so freshness changes cannot reuse rows calculated at an earlier time. The page refreshes the clock at quote observation/expiry boundaries and when focus or visibility changes after suspension.

### Exact-setup scores on desktop and mobile

**Mobile correction:** the initial setup-count behavior described below was rejected by the user after deployment. Mobile bar view now selects the actual reporting configuration for its active benchmark and displays its score directly. See [the correction and verification record](MOBILE_REPORTED_SCORES_2026-10-23.md). The original description remains here as implementation history; matrix semantics are unchanged.

`exactScore` supplies a number only for a single finite report on the selected configuration and benchmark, with the correct unit and selected saturation state. It is used for desktop score values/accessors/sorting, mobile ranking/bars, heat scales, winner highlighting, numeric threshold filters, and primary-configuration coverage.

- A missing cell shows **Other setups (n)** when sibling configurations have evidence; it does not display their numbers or use them for ranking, color, or bars.
- Multiple-report and disputed cells remain available as labeled evidence buttons and sort after numeric scores. Multiple reports are conservatively unranked even if values agree.
- Zero remains a valid score. Higher/lower direction, tied winners, and a shared mobile bar scale remain supported.
- The evidence drawer still exposes each report and source, and the alternative-setup chooser opens the actual reporting configuration.
- Mobile evidence labels use 12px text inside the existing 44px touch targets, keeping “Other setups (n)” and “Multiple reports” compact across system fonts while numeric scores remain 15px.
- CSV preserves raw observation `value` and adds `comparison_value` and `comparison_eligible`, making evidence values distinguishable from eligible comparison values. Alternate setups are not substituted into exported rows.

This removes the earlier mobile-only policy of ranking source ranges and alternate setups by their low endpoint. It does not introduce a reported-results mode or adjudicate incompatible evaluation series.

### Current and historical price eligibility

`prices.ts` centralizes quote eligibility. A current quote requires:

1. A known route whose availability is `available` or `listed`, and a quote with `available: true`.
2. USD currency and supported USD-per-million-token units.
3. A valid observation timestamp at or before the query time, aged **less than 48 hours**. At exactly 48 hours it becomes stale.
4. Any requested route and free-route constraints.
5. Both active price caps satisfied by the **same quote**, using decimal comparison rather than binary floating-point rounding.

**Include stale price quotes (historical)** is explicit serialized view state. Older version-1 links and saved views default it to false. Historical inclusion admits older observations but does not override invalid/future dates, unavailable routes, or incompatible units. The price table labels stale quotes; mobile displays a persistent historical-price notice even when Options is closed. Model evidence retains archived quotes with their dates and stale labels.

The committed snapshot's price observations are from 18 October, so current-price filters correctly yield no priced matches on 23 October unless historical inclusion is enabled. This is an expected correction, not missing source data.

## Regression coverage and verification

| Check | Result |
| --- | --- |
| Unit/component regressions (`pnpm --dir web test --maxWorkers=2`) | 111 passed across 18 files |
| Focused desktop/mobile regressions | 5 passed |
| Full desktop/mobile browser suite (`pnpm --dir web test:layout`) | 69 passed |
| Production build | Passed; existing main-chunk size advisory remains |
| TypeScript and ESLint | Passed, including the final test-harness edit |
| Bundle budgets | Passed after the font correction: 170,494 bytes gzip JS / 204,800 budget; 14,622 bytes gzip CSS / 16,384 budget (deployment base path) |
| Whitespace validation | `git diff --check` passed |

An earlier unrestricted unit run timed out under host load. Limiting concurrency and correcting the resize-observer test harness produced a complete passing run without changing production behavior, test assertions, or timeouts. The first browser run passed 67/69 checks; the new regression fixture and persistent mobile historical-price notice were corrected, all five focused regressions then passed, and the final complete browser run passed all 69 checks.

New regression coverage includes:

- Empty-search benchmark changes and a cached return, through both worker transport and fallback.
- Quotes expiring while the page stays open; historical opt-in restores eligible archived quotes on both execution paths.
- Exact freshness boundary, invalid/future dates, unavailable routes/quotes, wrong currency/unit, free routes, decimal thresholds, and backward-compatible saved-state parsing.
- Multiple-report and saturation-excluded scores cannot win, drive sorting, or satisfy numeric thresholds; valid zero scores remain eligible.
- Real browser worker reselection through benchmark controls, reload, Back, and Forward.
- Desktop and phone historical-price controls, persistence, alternative evidence links, neutral styling, and absence of alternate-setup bars.
- Existing layout checks across phone, tablet, landscape, desktop, picker, evidence, theme contrast, and lazy evidence loading. The resize test mock now targets the table observer explicitly; Radix checkbox observers previously overwrote its callback depending on mount timing. No assertion or timeout was relaxed.

The in-app browser tool rejected access to the open local preview under its URL policy. Interactive inspection through that tool was therefore unavailable. UI verification uses the repository's production-build Playwright suite; generated desktop and phone test screenshots were also inspected. This does not substitute for physical-device Safari or screen-reader testing. Saved mobile captures: [320px](review-assets/2026-10-23/exact-scores-320.png), [390px](review-assets/2026-10-23/exact-scores-390.png), with [capture notes](review-assets/2026-10-23/README.md).

### CI follow-up

The first PR CI run passed 63/69 browser checks but found six mobile geometry failures: Linux system-font metrics wrapped “Other setups (1)” onto two lines, increasing rows to 53px. Evidence labels now use a smaller font while preserving the touch target and numeric score size. The bar-geometry regression also forces a wider monospace fallback to exercise font variation on local machines; row-height, alignment, and overflow assertions remain unchanged. The stronger regression reproduced the 53px rows at both phone widths on the previous build, then all six affected cases passed after the correction. CI must pass on the updated commit before merging.

## Remaining work and limitations

- R04–R13 remain open: supersession/dispute publication, compatible evaluation-series resolution, semantic validation, observation-scoped evidence filters, retention of old lazy evidence snapshots, empty-feed protection, uncertainty presentation, unique configuration labels, and obsolete-preset recovery.
- F02's broader redesign remains partial: the CSV retains evidence-export semantics with explicit eligibility columns, rather than introducing separate comparison/evidence export modes. Coverage badges and “has evidence” filters remain evidence-oriented; they are not all counts of eligible numeric scores.
- Quote-history selection (latest quote per route/context tier), explicit context-tier filtering, currency conversion, and tier normalization remain separate work. The current snapshot contains route/context quotes; these fixes enforce age, availability, unit, and same-quote cap rules without inventing a history-selection policy.
- Existing narrow-phone truncation, picker keyboard/dismiss behavior, Options hierarchy, unique setup labels, and landscape safe-area issues remain in the review backlog. This change does not redesign the mobile layout.
- The production build still emits its existing advisory for the roughly 511 kB main JavaScript chunk. Bundle-budget validation determines whether the measured output meets repository limits.
- These validation results were recorded before publication; the associated pull request and CI runs provide the publication record.
