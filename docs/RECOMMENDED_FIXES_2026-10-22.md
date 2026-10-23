# Recommended fixes and acceptance criteria

Companion to the [deep review](DEEP_REVIEW_2026-10-22.md), based on commit `c04f170050d4ee81dd0d0f04e29257be33f26668`. This is the original implementation backlog; the dated status below identifies completed work. Preserve original source records and historical links throughout migration.

## Implementation status — 23 October 2026

- **F01 implemented:** column selections invalidate the row query even with empty search. Worker and fallback regressions cover changes and cached returns; browser tests cover the real worker, reload, and history.
- **F02 exact-setup policy implemented:** one `exactScore` resolver controls table values and sorting, mobile ranking and bars, heat scales, winner highlighting, score thresholds, and all-model primary coverage. Missing setups expose a labeled evidence link. Multiple/disputed reports remain available in evidence but are unranked. CSV preserves raw evidence and adds explicit comparison eligibility/value columns. A separate reported-results mode and deeper series-resolution/filter changes remain deferred.
- **F03 implemented:** available/listed routes, available USD-per-million quotes, exact decimal cap checks, a 48-hour expiry boundary, and explicit persisted historical opt-in. Worker queries carry an as-of clock; open pages refresh at quote boundaries and on focus/visibility changes. Invalid/future dates and incompatible units remain ineligible even with historical opt-in.

See [implementation and verification notes](REVIEW_FIXES_2026-10-23.md) for results and limitations. F04–F14 remain open except for the specific improvements listed above.

## Suggested delivery order

| Order | Work | Why now |
| --- | --- | --- |
| 1 | F01 query invalidation | Small, independently reproducible correctness fix |
| 2 | F02 visible provenance and cross-surface policy; F03 quote eligibility | Correct misleading comparisons and stale-price matches |
| 3 | F04–F07 publication lifecycle, series resolution, setup and evidence filtering | Establish reliable domain semantics before adding more imports |
| 4 | F08–F11 evidence retention, collection recovery, uncertainty, saved-state recovery | Protect publication and long-lived user sessions |
| 5 | F12–F14 mobile/readability/accessibility, code organization, runtime payload | Improve usability and maintenance on top of stable semantics |

Keep each change reviewable. Do not combine schema migration, a new ranking policy, and a visual redesign into a single large PR. Start with failing tests expressing the intended invariant, then update the implementation. Existing tests that encode alternate-setup ranking should change only as part of an explicit policy decision.

## F01 — Make row-query dependencies complete

**Review:** R01. **Size:** small. **Files:** `web/src/data/useViewRows.ts`, worker-client tests and hook tests.

Include the effective selected benchmark IDs in the row key even when search is empty. A simple safe implementation includes `visibleColumnIds` unconditionally; later optimization may use a normalized query object shared by the hook and worker. Include the preset fallback when the explicit list is empty. Avoid keeping separate handwritten definitions of what a query depends on.

Acceptance:

- With the committed snapshot, All models → only Terminal-Bench 4 changes GPT-6 Astra from `max` to `high` immediately, matching a fresh selector call.
- Selecting benchmarks, reloading, following the shared URL, and browser Back/Forward produce the same row configuration IDs.
- The assertion passes using both worker transport and main-thread fallback.
- Changing an unused checkbox selection while compare mode is off does not unnecessarily rerun row selection.

## F02 — Resolve a score once, then render it consistently

**Review:** R02, R06, R08; export/coverage architecture. **Size:** medium, split into policy and presentation PRs. **Files:** selectors, heatmaps, row queries, `App.tsx`, `PortraitComparison.tsx`, CSV, coverage.

Recommended matrix default: **exact configuration**. A missing result remains missing; alternate setups are visibly available as “Other setups” with a count. **User clarification on 23 October supersedes this recommendation for mobile bar view:** show each model's reported score for the active benchmark, with setup details behind the score tap. Resolve the actual reporting row instead of copying scores onto the matrix's primary configuration. [Implemented selection and verification policy](MOBILE_REPORTED_SCORES_2026-10-23.md). Do not aggregate multiple setups to make the matrix denser.

Introduce a shared result type, for example:

```ts
type ResolvedCell = {
  configurationId: string;
  benchmarkId: string;
  state: 'selected' | 'agreed' | 'disputed' | 'multiple_protocols'
    | 'missing' | 'excluded';
  selectedSeriesId: string | null;
  observationIds: string[];
  numericValue: number | null;
  rankValue: number | null;
  unit: string;
  selectionReason: string;
  missingReason: string | null;
  alternatives: Array<{
    configurationId: string;
    seriesId: string | null;
    observationIds: string[];
  }>;
};
```

This is an interface sketch, not a ready-made schema migration. Model lifecycle and report ranges may justify discriminated unions rather than nullable fields. Keep uncertainty separate from ranges across reports.

Acceptance:

- Claude Opus 5.5's selected max setup does not display 74.2% as its own DeepSWE score; the actual reporting setup is visible before opening evidence.
- Every value eligible for sorting, filtering, bars, heatmaps, or bold highlighting comes from the same resolver. Disputed/missing/excluded cells have no ranking value.
- Desktop and mobile agree on numeric eligibility for the same configuration. Mobile bar view may resolve a different reporting configuration per active benchmark, as explicitly requested by the user; the evidence target must match its displayed score.
- Saturation exclusions cannot produce a bar beside a dash. Alternative setups obey the same explicit evidence policy.
- Evidence opens the records represented by the selected value or opens an explicitly labeled alternative-setup chooser.
- CSV distinguishes exact selected records, excluded/missing records, and optional alternative reports. The default export describes the visible comparison policy; an all-evidence export is a separately named operation.
- Coverage and legend language describe the actual policy. Adding an unrelated model/page does not silently change which reports qualify.

## F03 — Make market eligibility explicit and deterministic

**Review:** R03. **Size:** medium. **Files:** schema/publication market normalization, selectors, market components, state schema.

Create one `eligibleQuotes(model, constraints, asOf)` operation. It should enforce route identity, route availability, quote availability, context tier, normalized currency/unit, freshness, and free-route restrictions together. Decide how quote history selects the current record for each route/tier; do not select by array order. Use exact decimal arithmetic or a documented integer normalization that preserves comparison precision.

Pass `asOf` explicitly to queries/tests. If current-time freshness affects worker results, include a clock policy/time bucket in the cache key and reevaluate while a tab stays open. Otherwise the freshness fix itself introduces another stale-cache bug.

Acceptance:

- A quote just within 48 hours passes; just outside fails by default. Missing/invalid/future timestamps receive explicit handling.
- Historical quotes remain inspectable with a stale label and timestamp; opt-in historical filtering is clearly named and serialized.
- A quote cannot pass because it is numerically cheap in EUR/token when the control says USD/million.
- An unavailable route cannot qualify through a still-true quote flag.
- Input/output constraints pass on the same route and context tier.
- Exact decimal boundary values behave consistently in Python and TypeScript.
- The UI shows the route/quote satisfying the filter, rather than all-model ranges that appear to violate it.
- Empty usage coverage is communicated as unavailable, never zero or global popularity.

## F04 — Implement correction and status lifecycle before using it in curation

**Review:** R04, R05. **Size:** medium. **Files:** `pipeline/schema.py`, `pipeline/build.py`, evidence views and static-page generator.

Validate correction edges: no self-reference, cycles, or unexplained cross-identity replacement. Define whether cross-series corrections are permitted and when a changed setup requires a new identity. Resolve the active record graph before selecting comparable reports. Do not delete old evidence.

Represent review state, current validity, and publication/ranking eligibility separately. A current dispute is inspectable but unranked; a retraction is historical with a reason; a superseded record points to its replacement. A current missing cell may coexist with historical observations.

Acceptance:

- The synthetic reviewed correction in the probe replaces the old active score without creating a false dispute.
- Self-links, cycles, and unrelated replacements fail publication validation.
- An explicitly disputed observation remains accessible in the matrix evidence, entity pages, and generated reference pages, without a numeric filter/rank value.
- Retractions remove ranking eligibility but retain an accessible history and explanation.
- Repeated publication produces byte-identical output for the same inputs.

## F05 — Preserve evaluation-series boundaries and add selection policies

**Review:** R06; data-model critique. **Size:** medium/large, incremental. **Files:** generated contract, preset schema, publisher, frontend resolver.

Add a versioned policy for each selected benchmark: exact variant, permitted series/protocols, source preference where justified, handling of unknown setup, and treatment of conflicts. Keep the distinction between a comparison policy and an immutable source/evaluation identity.

First remove the frontend's automatic “multiple series means disputed” merge. Then implement explicit selection; do not retroactively declare unrelated protocols compatible. Existing data can migrate to a conservative “multiple protocols / not selected” state.

Acceptance:

- The 36 current multi-series pairs retain their original series and provenance.
- Equal numbers from incompatible protocols do not establish agreement.
- Different numbers under distinct protocols are labeled multiple protocols, not automatically a factual dispute.
- Conflicting equally eligible reports within the same policy remain disputed, with all records visible.
- Catalog coverage, the table, mobile, detail pages, static pages, and CSV use the same classification.

## F06 — Add publication-grade semantic validation

**Review:** R07. **Size:** medium, split by record type. **Files:** `pipeline/schema.py`, import adapters, runtime snapshot generator.

Keep staging tolerant enough to preserve unknown source fields, but enforce a stricter reviewed/publication contract. Normalize core evaluation setup into structured fields with explicit `known`, `unknown`, `not_applicable`, and `not_reported` meanings where needed. Preserve arbitrary source extras outside that decision structure.

Validate nonempty evidence locators/evaluators for reviewed records; mapping route/model consistency and validity windows; finite ordered parameter ranges with known units; selected-claim conflicts; aware market timestamps; source/documentation HTTP(S) URLs; and correction graph invariants. Do not require fabricated dates, hashes, or licenses when upstream evidence does not provide them—represent their absence explicitly.

Compute setup completeness and policy eligibility once at publication. Replace the current four-of-nine heuristic and duplicated unknown-string interpretation.

Acceptance:

- Blank reviewed provenance and mismatched route/model mappings from the probe fail publication with actionable errors.
- Four known setup fields with five missing fields cannot pass a control labeled complete setup.
- Empty strings, unknown variants, and unavailable metadata do not become known merely because a key exists.
- Compact/full snapshots yield identical eligibility using explicit generated flags, without duplicating the full setup dictionary.
- Raw import values remain recoverable for audit.

## F07 — Apply evidence constraints to selected reports

**Review:** R08. **Size:** small/medium after F02/F05.

Apply independent/provider/setup constraints to observations eligible for the selected benchmark and policy. Derive row inclusion from remaining cells. Keep “has any comparable evidence” as an explicitly existential filter; introduce strict compatible-series comparison separately if needed.

Acceptance:

- Independently measured ARC results for `claude_opus55_xhigh` remain available even though another benchmark on that configuration is a self-report.
- Adding a self-report on an unselected benchmark cannot remove an otherwise eligible ARC row.
- Excluded reports do not influence thresholds, bars, winners, or exported selected values.
- Whole-configuration purity, if retained, has a distinct explicit label and tests.

## F08 — Keep evidence usable across deployments

**Review:** R09. **Size:** small/medium. **Files:** runtime publication, snapshot loader, lazy evidence UI, deployment artifacts.

Choose a retention policy for immutable evidence files across releases, or provide explicit refresh recovery for expired snapshots. Retention must exist in the deployed artifact, not just a developer's local build directory. Record the evidence filename/hash and schema version as part of the runtime manifest contract.

Acceptance:

- Open comparison A, publish B, and then open an evidence drawer in A: it either loads matching A evidence or offers a clear snapshot-refresh action.
- Retrying an expired evidence URL does not loop without a recovery path.
- Refresh preserves the user's intended model/benchmark/filter selection, with unresolved identities shown explicitly.
- B evidence is never displayed under A scores.
- Schema/envelope failures produce a recoverable error rather than an uncaught render failure.

## F09 — Preserve last-good feed data on invalid successful responses

**Review:** R10. **Size:** small/medium. **Files:** `pipeline/collectors.py`, collector tests and health reporting.

Validate source-specific response envelopes, content type/size where useful, and expected identity fields. Separate the last valid payload from collection attempts. An unexpected empty/collapsed feed needs a warning/review path rather than automatic replacement; legitimate emptiness requires an explicit source policy.

Acceptance:

- `200 {"data": []}` after a good nonempty snapshot records a failed/suspicious attempt and retains the last-good mapping data under the chosen policy.
- A valid JSON error object is not a healthy model catalog.
- Partial endpoint failures preserve unaffected records and original capture times.
- Health output identifies failure without falsely advancing source freshness.
- Mocked tests require no live upstream network.

## F10 — Show uncertainty and meaningful configuration identity

**Review:** R11, R12. **Size:** medium, separable UI changes.

Render published uncertainty in score evidence and entity details, distinguishing confidence intervals, standard errors, and other source measures. Show units and confidence level/sample size only when actually provided. Keep report-to-report ranges separate.

Use a shared configuration display label in picker, selected chips, headers, mobile cards, and evidence. Include enough source/protocol context to distinguish duplicate `max`, `high`, and `unknown` choices. Preserve the stable ID in details, and explain unresolved identity rather than guessing equivalence.

Acceptance:

- An observation with a published confidence interval exposes its endpoints/type/level consistently in both evidence surfaces.
- Min–max across reports is never labeled a confidence interval.
- The three Claude Opus 5.5 `max` choices are visibly distinguishable before selection and after comparison.
- Two unrelated unknown settings do not collapse into indistinguishable “Reasoning: unknown” cards.
- Single-model phone cards also show the chosen setting/status, not only repeated-model cards.

## F11 — Preserve unresolved shared state and make encoding failure recoverable

**Review:** R13; shared-state resilience. **Size:** small/medium.

Treat an unknown preset as an unresolved semantic reference, not invalid syntax. Keep restrictions and show no matching results until the user chooses a migration/replacement. Store a stable current/default preset designation in curated metadata instead of spreading date-specific IDs through components.

Deduplicate validated ID arrays. Keep the payload limit, but guard URL writes so an oversized view does not throw halfway through a UI update. The current all-model state was 21,231 UTF-8 bytes in the probe, within the 32,768-byte limit; this is growth hardening, not a claim that the current All models preset already fails.

Acceptance:

- A retired preset preserves search, thresholds, selected configurations, and benchmark IDs and displays a recoverable unresolved state.
- Known migrations are explicit and do not weaken restrictions silently.
- Duplicate columns cannot create duplicate React keys or repeated cells.
- If a view becomes too large to share, the current UI remains usable with a clear message and an appropriate export/reduction path.
- Decide whether the mobile bar/matrix choice is part of a shared view; if yes, restore it through the same versioned parser.

## F12 — Rework the narrow-phone card and keyboard paths

**Review:** U01–U06. **Size:** medium, split responsive layout from accessibility semantics.

At narrow widths, use two lines for identity/status and dedicate the next line to the bar/value. Remove the unconditional 120px score allocation. Keep values in their native units and use structured bounds for axes; support non-percent and signed scales. Pair model/benchmark selection in Options, and show active constraints on the main comparison surface.

Replace the partial ARIA listbox with an established accessible interaction or a regular button list. Give Close a 44×44 hit box. Add row-header semantics and sort/page announcements to the transposed matrix. Use separate safe-area insets for left and right.

Acceptance:

- At 320, 375, 390, and 430px, model names and exact setup/status can be read without relying on hover. Similar release names remain distinguishable.
- Bars have a useful shared width and visible scale context; long ranges do not crowd out model identity.
- Full interactions work with Tab, arrows where promised, Enter, Escape, and focus return to the opener.
- Options, filter facets, picker, and evidence work at 844×390 and with the software keyboard open on an actual phone.
- Searchable benchmark/route facets show selected chips and distinguish repeated route labels.
- Geometry tests retain zero page overflow; add focused semantic assertions rather than screenshots alone.
- Run Chromium/WebKit/Firefox smoke checks and a manual VoiceOver pass; record limitations rather than claiming conformance from lint.

## F13 — Extract domain/presentation modules and reduce startup work

**Review:** architecture/performance critique. **Size:** medium, measured rather than wholesale rewrite.

After F02, extract the comparison controller, filter draft, cell renderer, evidence UI, market presentation, and CSV serializer from `App.tsx`. Format JSX normally and consolidate responsive CSS by surface. Keep the existing React/static deployment and bounded worker queue.

Publish a compact comparison read model that avoids full setup key bags and unnecessary market/evidence details. Serve catalog listings without requiring full evidence. Keep complete archival exports for reproducibility. Add worker readiness/query timeouts with fallback or a recoverable error.

Acceptance:

- Existing semantic and layout tests pass against the extracted modules.
- Compact and archival paths produce the same resolved comparison results.
- Model/benchmark directory first render does not fetch full observation evidence.
- Measure transfer, decoded size, parse time, worker readiness, long tasks, and representative interactions before/after on slower hardware or an explicitly documented throttle.
- A worker that never becomes ready cannot leave the UI permanently busy.
- Do not introduce a backend, database, or new state framework without a measured requirement.

## F14 — Close documentation, export, and publication hardening gaps

**Review:** operations, security, and documentation sections. **Size:** several small follow-ups.

- Update architecture diagrams and text for `comparison.json`, lazy evidence, current 1100px behavior, bar defaults in both orientations, and all-configuration entity links.
- Generate snapshot-dependent claims such as parameter coverage from data; remove the false “no selected size claims” copy.
- Check both expected generated outputs and stale unexpected generated pages. Preserve deliberate archives through an allowlist/retention policy.
- Neutralize spreadsheet formula prefixes in CSV text fields; test separators, quotes, line breaks, and formula-leading source strings without opening them in a spreadsheet.
- Validate source URLs consistently across Python publication and client rendering. Preserve valid original links and attribution.
- Consolidate duplicated CI/deploy checks through a reusable workflow; retain proposal-only safeguards and hash-bound promotion.
- Separate dependency vulnerability-audit results from deterministic correctness gates in reporting. No dependency vulnerability conclusions were made in this review.

## Verification recipes

Run the existing suites after implementation changes relevant to them:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pipeline.cli validate
.venv/bin/python -m scripts.check-generated
.venv/bin/ruff check pipeline tests scripts
pnpm --dir web run lint
pnpm --dir web test
pnpm --dir web run build
.venv/bin/python scripts/check-bundle.py
pnpm --dir web test:layout
```

The report's Python diagnostics are read-only with respect to application data:

```sh
.venv/bin/python docs/review-assets/2026-10-22/pipeline_probes.py
```

The saved frontend diagnostic source expects to run from `web/src/`. Copy it to an unused temporary test filename there, run Vitest on that filename, and remove the temporary copy afterward. Its assertions confirm the reviewed defects exist; it is not a regression suite asserting fixed behavior. Convert the diagnostic cases into normal intended-behavior tests when implementing F01–F03.

For domain changes, prioritize the acceptance criteria above over increasing test count. The goal is consistent published meaning across every surface, with visible provenance and a phone UI that remains legible.
