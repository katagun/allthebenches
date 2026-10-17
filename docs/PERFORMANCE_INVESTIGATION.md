# Frontend performance investigation

Date: 2026-10-17. Scope: preset-switch CPU/render behavior on the current curated snapshot, without changing frontend implementation.

## Snapshot and baseline

The checked-in snapshot has 37 model releases, 51 configurations, 282 benchmark variants, 492 reviewed result cells, and 295 evaluation-series records. The all-model preset requests 282 benchmark IDs and 51 configurations. The table paginates to 50 rows and renders at most 10 benchmark columns at once; the ordinary all-model view had 37 visible rows and 407 body cells (including the model column).

`pnpm run test:performance -- --reporter=verbose` passed the wide-table tests. Across three runs, the first test's `renderMs` ranged 787–2,122 ms; its measured interval includes Testing Library `findByRole`/`waitFor`, so it is not a React commit duration. Overall test duration ranged 3.1–7.8 seconds. The synthetic 70-row addition test took 1.9–4.1 seconds. These results varied under parallel development/test load and are useful as a rough harness baseline, not a browser performance guarantee.

## Isolated selector and DOM-query costs

A temporary Vitest harness called `rowsForView` 30 times with the real all-model preset and measured each synchronous call with `performance.now()`: median 0.133 ms, p95 0.187 ms, maximum 3.779 ms. This isolates selector CPU from React rendering, accessibility-tree queries, worker startup, and the browser paint pipeline.

On the loaded jsdom DOM (1,341 nodes), one `getByRole('button', { name: 'All models' })` took 138 ms, `getByRole` for the searchbox took 4.5 ms, and a first-row `getAllByRole('button')` took 5.3 ms. A CSS `querySelector('button')` took 0.57 ms. This shows that accessibility-role queries can add visible test overhead, especially broad name searches, but they do not explain the multi-second preset-switch behavior observed before the fix.

## Preset-switch loop and profiler interpretation

Before the frontend fix, a React `<Profiler>` around `App` recorded an unbounded stream of commits after clicking **All models**. The click/`act` interval reached 4.68 seconds and the test hit its 5-second deadline; the captured output already contained more than 100 commit records. A representative pre-switch React commit sequence had nine commits and 168.6 ms cumulative `actualDuration`, with a largest commit of 78.6 ms. The first pre-fix switch commit alone reported 295.4 ms `actualDuration`.

`actualDuration` is React's measured render work for a commit; it does not include the full browser event-to-paint time, accessibility query cost, or all layout/paint work. The click/`act` interval measures the test's wall time for dispatch and React flushing, not a browser-paint benchmark. The pre-fix profile was intentionally interrupted by the test deadline, so its cumulative commit count and total render time are lower bounds, not a completed end-to-end duration.

The observed update loop aligned with a fresh empty TanStack sorting array being passed on every render and automatic page-index resets repeatedly scheduling state updates. The frontend has since memoized the sort state, disabled TanStack's unused page-index auto-reset, and moved row selection/sorting work behind the worker-backed query path.

After those changes, two bounded StrictMode profiles clicked **All models** from the default Frontier view and waited for the table to report `aria-busy="false"`, plus a 120–150 ms settle window. The temporary profile showed 10 rows before the click and 37 after; React reported 6 commits and 615.6 ms cumulative `actualDuration`. Its click-through-stable interval was 1,212 ms. The updated committed test subsequently reported 6 commits and 945 ms cumulative `actualDuration` for the same wide-preset switch. These are development/jsdom measurements and varied with test load.

The click-through-stable interval includes the role query, `userEvent`, worker response, `waitFor`, and settle delay; it is not React CPU or browser paint. React `actualDuration` sums measured render work across commits and excludes non-React worker time, layout, and paint. Both bounded profiles completed without a repeated commit loop. The second test also switched back to Frontier and verified that commit counts stopped increasing after settlement.

The committed `App.performance.test.tsx` guard now starts with the Frontier preset, switches to **All models**, switches back, and verifies that commits settle. The earlier version clicked Frontier while already on Frontier and did not exercise the wide-preset transition; the frontend corrected that guard during this investigation. The temporary independent profile was removed after measurement.

The parent also reported a native Firefox double-`requestAnimationFrame` next-paint observation of 96 ms. At that point the worker-backed table was still showing zero result cells; later the accessibility tree showed the final ten visible rows. This measures placeholder first paint only, not completed query/render latency, and is not compared with the jsdom measurement. The run ended before a MutationObserver-based completion duration was collected.

The earlier Firefox timeout was `Script terminated by timeout` in TanStack's `createTable` → `makeVisibleColumnsMethod` → `table.getHeaderGroups` stack, pointing to `ColumnVisibility.ts:235` (`filter(d => d.getIsVisible())`). This call filters the column list while producing visible header groups. The observed stack is consistent with repeated table header-group work during the pre-fix update loop; it does not by itself establish that column filtering was the primary cause.

## Next measurement

Keep the StrictMode preset-switch regression assertion on **All models** and wait for stable rows. For future profiles, time the role query, click dispatch, worker completion, and React Profiler intervals independently. Validate completed behavior in a real Firefox session because jsdom does not model browser layout, paint, or Firefox's main-thread scheduling.
