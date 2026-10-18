# All the Benches product specification

Decision baseline: 17 October 2026. Build a trustworthy, fast benchmark table that starts simple and can answer sophisticated comparison questions. The audience includes researchers, developers, enthusiasts, and buyers. Complexity should appear when requested.

## Weekend release

Ship a static GitHub Pages application and a Python data pipeline. Aim for 10–12 current models in the opening view, 18–24 benchmarked model releases overall, 12–18 benchmark variants, and roughly 120–200 reviewed observations. These are planning targets, not incentives to invent coverage. A much larger discovered model catalog can coexist with this smaller benchmark dataset.

Required launch categories: text and instruction following, reasoning, mathematics, coding, agent tasks, and safety. Older and saturated benchmarks remain available. Agent harness comparison is deferred; evaluation setup is still required provenance for agent-task scores.

The launch roster must cover the requested OpenAI, Anthropic, Google, Meta Wonder and Spark, Mistral, and Grok families when public results exist. Include at least two additional competitive model families from other labs if evidence supports them, including Chinese labs. Discovery and popularity help find candidates; neither proves frontier capability.

Minimum release gate: every required family is represented by a verified release and at least one admissible result, or is named in the public coverage gaps with a specific reason. All six categories have actual reviewed results somewhere in the dataset, including safety. The default table needs at least four populated benchmark columns across at least six models; no default model may be entirely empty. A category may have incomplete current-model coverage. Show that gap instead of filling it with a different evaluation.

## Default experience

Use models as rows and benchmark variants as columns. Each visible row identifies one exact model release and one reasoning configuration. Group alternate reasoning settings beneath their model and expand them on demand. Do not assemble a row from the best score at each setting.

The opening view contains:

- A restrained wordmark, one short description, and dataset review date.
- Two view choices: Frontier and All models. These select curated defaults, not unexplained rankings.
- A model search field, category choices, a Columns control, and a subtle Filters button.
- The full curated Frontier benchmark set, with a viewport-sized page of benchmark columns (up to 24). Include every row of the Gemini 4 Argon comparison table, plus retained safety/document coverage; show names, versions, units, and metric direction.
- A frozen model column and sticky table headers. Horizontal scrolling stays within the table.
- A small results count and a clear distinction between comparable evaluations and reported results with differing setups.

Default ordering is lab name, then model name. Sorting a score column is explicit and uses its metric direction. Missing values remain last in either direction. Do not add rank numbers, medals, a universal intelligence score, or a full-table heatmap. Highlighting a column maximum is allowed only inside a reviewed comparable evaluation series; it does not assert statistical significance.

The Frontier preset is a versioned editorial selection, reviewed for each release. It chooses explicit model/configuration IDs and benchmark variants with useful headroom and coverage. A 180-day age suggestion helps curation but does not automatically eject a still-relevant model. Availability, access restrictions, and preview status remain visible in model details.

All models defaults to benchmarked releases, with an explicit “Include models without scores” control for the discovered catalog. Search can offer a matching unbenchmarked model with a “No benchmark results yet” label. Availability through an API is not a prerequisite for historical inclusion.

## Progressive disclosure

Level one is the table. Level two is search, category selection, sorting, and selecting models. Level three is a right-side filter drawer. Level four is score or model evidence detail.

Clicking a score opens its value, unit, exact benchmark/subset, model/configuration, source link and locator, evaluator, reporting relationship, evaluation conditions, dates, and alternative observations. Missing cells open a short reason. A model name opens release metadata, disclosed and estimated sizes, available routes and prices, OpenRouter usage, and source attribution.

On desktop, the evidence drawer is about 400 pixels wide. On mobile it becomes a full-width sheet. Escape closes it, focus returns to the trigger, and keyboard navigation remains usable. Filter edits apply on Apply; Cancel discards the draft. The active filter summary remains visible after closing the drawer.

Use the same table for comparing selected model configurations without a five-model selection cap. Share the selection, filters, columns, and sort through versioned URL state. Export the current result selection as CSV with configuration, units, sources, and missing-value reasons. Exports must not silently flatten provenance.

The full applied view is shareable in one `v` URL query parameter containing a versioned JSON envelope encoded with URLSearchParams. The state includes all applied filters, search, preset/category, visible columns, sorting, and comparison selection. A Share action copies the complete URL; pasting it in a new browser must reproduce the same view against the available dataset. Use browser history for committed view changes and restore on back/forward; avoid one history entry per search keystroke. Do not place localStorage opt-in, credentials, or data payloads in the URL. View URLs work beneath the GitHub Pages repository base path without server-side routing.

## Remembering a view

Include an unchecked “Remember this view on this device” control at the bottom of the filter drawer. Use localStorage for the weekend release. Enabling it saves the current applied view; later committed changes update that saved view automatically. When the control is changed alongside draft filters, Apply commits both; Cancel changes neither. No account or cookies are needed for this feature.

Remember the applied filters, model search, preset/category, visible columns, sort, and selected comparison models. Restore them on a later visit in the same browser profile and site origin. Do not save unapplied drawer edits, open evidence panels, or benchmark data. The control's supporting text should say “Saved in this browser.” No cross-device sync is implied.

Startup precedence is an explicit shared URL, then a valid saved view, then the Frontier defaults. Treat shared URL state as a complete view; never add hidden saved conditions to it. Opening a shared link is temporary and does not replace the saved view. In that context, provide “Save this view on this device” to explicitly replace the saved view and resume automatic saving. Malformed URL state falls back to defaults with a short notice, rather than unexpectedly loading personal filters.

“Clear filters” clears the current filters and updates the saved view when automatic remembering is active. “Forget saved view” removes the stored view and disables remembering, while leaving the current screen usable for this visit. Unchecking the remember control has the same deletion behavior when applied. Merely visiting, opening a shared URL, or editing a cancelled draft must not enable persistence.

If storage is unavailable or a write fails, keep the current view working and show a small “Could not save this view in this browser” status. Do not claim it was saved. Validate saved state on restore. If a referenced benchmark or model is unavailable after a dataset update, retain the affected condition as unresolved with an explanation; do not silently remove a restrictive filter and broaden the results. Unknown state versions or corrupt records fall back to defaults with a notice and an option to forget the saved view.

## Filters

The drawer groups controls into Models, Benchmarks, Evidence, and Cost and usage. Support multiple conditions joined by AND; selections within a facet use OR. An arbitrary nested boolean language is outside the weekend scope.

Model controls: labs, headquarters countries, release year/date range, access status, available weights, modalities, architecture, reasoning setting, total/active parameters, and whether estimates are included. Country refers to the model developer's headquarters, not its hosting provider or parent company's country. A joint development record can have multiple headquarters values with a clear explanation.

Benchmark controls: category, selected versions, saturation state, and repeatable score conditions such as “RiemannBench ≥ 70 AND Terminal-Bench 4.0 ≥ 55.” A score condition binds to a specific column and comparison policy. Every condition must be satisfied by the same configuration row; success at high reasoning in one test and low reasoning in another cannot produce a passing synthetic model. Unknown or missing scores fail numeric predicates.

Evidence controls: comparable evaluations only, provider-reported allowed, independent evaluations only, and include results with incomplete setup. The default reported-results view allows reviewed incomplete setups but labels them, suppresses winner highlighting, and never treats unknown setup as equivalent. Strict mode excludes them.

Cost and usage controls: maximum input/output token price, selected provider/route, include free routes, OpenRouter usage availability, and popularity sorting. Price and usage columns are hidden initially. OpenRouter's latest complete daily public top-50 token volume is the first popularity measure. Label the UTC day. A missing top-50 entry is “Outside published top 50 / unavailable,” not zero usage. Weekly and monthly views require suitable source aggregates or explicitly labeled incomplete totals.

Filter examples:

- Models released this year, RiemannBench ≥ 70, with an available route at input ≤ $5/M and output ≤ $20/M.
- Available weights, active parameters ≤ 60B, estimates included, with a reviewed coding score.
- French-headquartered developers, historical benchmarks visible, all reasoning settings.
- Current benchmarked models sorted by OpenRouter token volume on the latest complete published UTC day.

## Estimated sizes

Attempt to find a documented estimate when a count is undisclosed. Accept sourced analysis and explicitly identified speculation, distinguishing both from official disclosure. Store a range when supported. Internal inference must have a written method and evidence. Never use benchmark performance or price alone to invent a parameter count.

Show “Estimated 100–300B,” source, date, basis, and confidence rationale. If no defensible estimate exists, retain “Unknown.” Do not force false precision to satisfy a completeness target. Total and active parameters are separate dimensions; parameters are not a promise about memory requirements.

Including estimates is an explicit checkbox in size filters, initially enabled when opening those controls, and appears in the applied filter summary. For a maximum-size constraint the entire estimated interval must fit; for a minimum, its lower bound must pass. An estimate spanning the cutoff is excluded with a reason. Point estimates are visibly estimated. Interval-overlap matching can come later.

## Saturation and safety

For eligible bounded capability metrics, start with a per-benchmark ceiling threshold of 95% of the defined scale, reached by three distinct model releases from at least two labs in one compatible evaluation series. This is a configurable product rule, not a scientific declaration that the task is solved. Variants of one release count once. Record the evidence and dataset snapshot used. Insufficient coverage yields Unknown; one exceptional model does not hide a benchmark.

Determine saturation during the data build across the reviewed reference set, not from the viewer's active filters. Thresholds can override the default with a reason. Unbounded metrics, Elo, and safety metrics are not automatically classified by this rule.

Safety has its own category and metric-specific direction. Keep attack success, harmful compliance, over-refusal, and helpfulness distinct. A high refusal rate is not a general safety score. Do not combine safety with capability into an overall rank. A saturated capability filter must not remove all safety information.

## Visual direction

Use actual shadcn/ui components with Tailwind CSS and semantic theme tokens. The filter sheet, evidence dialog, buttons, form controls, tabs, and table presentation should share that component foundation; preserve accessible keyboard and focus behavior.

Use a quiet reference-table aesthetic: warm near-white in light mode, charcoal in dark mode, one muted teal accent, native/system sans-serif, tabular numerals, subtle horizontal dividers, and little decorative chrome. No flags as country substitutes, giant hero, charts above the table, or logo wall.

Production tokens: body 14px; secondary labels 12px; row height about 52px; comfortable mode 60px; model column roughly 240px; score columns 110–140px; small corner radii. Minimum interactive targets increase on touch screens. Use color with text, not instead of text. Show native units; never silently turn different metrics into a common percentage.

The conversation design sketch is a study of filtering, evidence disclosure, and optional cost/usage columns. It is not the production UI or a complete, validated benchmark dataset.

## Explicit later work

Defer harness browsing/ranking, arbitrary boolean query trees, chart dashboards, benchmark execution, crowdsourced voting, accounts, saved server-side workspaces, subscriptions, a backend API, and universal score normalization. Defer transpose and full timeline charts until the primary table works well. The data contract supports additional modalities without requiring their launch curation.
