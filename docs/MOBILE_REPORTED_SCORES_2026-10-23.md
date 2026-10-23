# Mobile reported scores — 23 October 2026

## Product correction

PR #50 deployed successfully as `14299084a5ff9658a06bded0a39369507a81d856`, but its mobile behavior did not meet the intended product requirement. “Other setups (1)/(2)” occupied score positions even when a reviewed model result existed for the selected benchmark. Reducing the label font size fixed geometry, not that behavior. The earlier regression tests mistakenly required these labels on mobile.

The user clarified the requirement: **show each model's reported score for the selected mobile benchmark; keep the reporting configuration and sources behind the score tap.**

The live before-fix check reproduced this with Mistral Large 4 on Vals Index: the card displayed “Other setups (1)” while its evidence contained 48.66%. The live desktop configuration-reselection test and desktop/mobile historical-price tests passed. [Original deployment](https://github.com/katagun/allthebenches/actions/runs/39997189606).

## Behavior

- Mobile bar view selects a reporting configuration for the active benchmark after applying the existing model, configuration, evidence, and price filters.
- If the normal primary configuration has an eligible numeric score, retain it. Otherwise use the first eligible reporting configuration in stable catalog order. Selection never maximizes the score. If only ambiguous evidence exists, retain an evidence-bearing configuration and leave it unranked; otherwise show a dash.
- The numeric score, bar length, rank, heat/winner calculation, and evidence target all use that same actual configuration. No score is copied onto a different configuration ID, and no range or average is invented.
- Explore shows one card per model. Explicit Compare selections remain exact configurations; configuration filters cannot be bypassed to fill a score.
- Mobile score positions contain numbers, a dash, or an ambiguity label. They do not contain setup counts. The evidence drawer retains configuration details and source links.
- Changing benchmarks, reloading, and browser history resolve the appropriate reporting row again. The desktop matrix and mobile matrix preserve exact-configuration semantics.
- Initial scores wait for row selection to finish so the default benchmark cannot briefly display another benchmark's results. Loading also suppresses the empty-results message.

The mobile selector reuses `rowsForView` with a benchmark-specific selection argument. Its component memoizes the active benchmark's result rows. The desktop worker query/cache is unchanged. `exactScore` still decides numeric eligibility in both views.

## Verification

- The stronger live regression failed on the deployed old mobile behavior and passed the existing desktop and price scenarios (4/5 scenarios before the correction).
- Selector tests cover benchmark changes, valid zero, stable selection rather than the largest score, preserving an eligible preset configuration, configuration filters, explicit Compare selections, and disputed evidence.
- Component coverage checks that the displayed score, rank, bar, winner range, and evidence click all use the reporting row.
- Focused local checks passed: 44 selector/component tests and 14 production-build browser scenarios covering the corrected behavior and existing mobile geometry.
- The first full browser run caught a transient default-benchmark render (71/72 passed). A component regression now verifies that no result cards appear until row selection has resolved the default benchmark; the existing browser assertion is unchanged.
- Browser regressions cover 320px, 390px, and 844px mobile layouts, both one- and two-setup cases, score ordering, bar values, winner highlighting, compact geometry, no horizontal overflow, direct evidence, reload, and Back.
- `LAYOUT_BASE_URL=https://allthebenches.com/ pnpm --dir web test:layout e2e/review-regressions.spec.ts` runs the same behavioral scenarios against production without starting a local server. Browser interactions change only test-session view state.

Final local, CI, and production results are recorded in the associated PR and this task's completion report. Screenshots are stored in [mobile-reported-scores](review-assets/2026-10-23/mobile-reported-scores/).

## Remaining limitations

Stable configuration preference is not a scientific adjudication of evaluation protocols or source quality. Multiple/disputed reports on one configuration remain unranked. Separate comparison/evidence CSV export modes, observation-scoped evidence filtering, configuration-label improvements, and the other open findings in the original review remain outstanding. CSV continues to export the underlying matrix configuration selection; this change does not introduce a mobile leaderboard export mode. Physical-device Safari and screen-reader checks remain unverified.
