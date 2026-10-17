# Wide-table performance

The comparison table renders at most 10 benchmark columns and 50 model/configuration rows at a time. Selected columns are created in TanStack Table only for the current page; the full selected benchmark set remains intact for URL state, sorting, evidence, and CSV export. Row selection, filtering, and sort run in a module worker when available. It receives one snapshot per loaded dataset, keeps one active query and one replaceable latest query, and ignores stale responses. A task-scheduled main-thread fallback is used when workers are unavailable or fail; it yields before computation but cannot isolate computation from the UI thread. While a query is running, the table reports that state and does not show old rows under the new view. Column-only changes and ordinary selections do not re-run the row query. TanStack sorting state is memoized and its internal page reset is disabled because pagination is managed by the app.

## Local scaling check

Run the deterministic DOM guardrail and synthetic row-scale test with:

```sh
cd web
pnpm run test:performance
```

The performance test opens the actual 282-column All models preset and checks that no more than 10 benchmark headers plus the sticky model column, and no more than 11 cells per displayed row, reach the DOM. It verifies that the full column count remains exposed through table ARIA metadata, column navigation reaches page two, and a sort on page two is retained in the URL. A second test adds 70 synthetic model/configuration entries to push the rendered row set beyond 50, checks the row bound, and verifies selection persists while navigating between row pages. A StrictMode test switches from Frontier to All models and uses React Profiler `actualDuration` plus commit count as a guardrail against runaway rerendering.

## Measured result

Measurements below use the same 282-column, 51-configuration All models snapshot in Vitest’s jsdom environment. The render wall-time includes Testing Library and table population. The preset-switch React duration is summed from React Profiler `actualDuration` values and excludes Testing Library query, click, wait, browser layout, and paint time. These are regression indicators, not Firefox or real-browser timings.

| Metric | Before paging | After paging |
| --- | ---: | ---: |
| Rendered table cells (headers + body) | 10,754 | 418 |
| App DOM nodes | 24,584 | 1,341 |
| Render-to-populated-table time | 18,397 ms | about 800 ms |
| Frontier → All models React commits after click | 100+ commits / 4.68 s | 6 commits / about 616 ms actualDuration |

The DOM node count dropped by about 94.5%. The test wall-time improvement includes reduced accessibility-query overhead and is not an estimate of browser rendering speed. The runaway preset-switch rerender loop is covered by a bounded StrictMode commit guardrail. The focused test logs fresh measurements when run. Firefox timing is not inferred from jsdom; use the manual check below for browser layout and interaction.

## Firefox manual check

1. Open the app and select **All models**. Confirm the first page reports the 1–10 benchmark range, the model column stays visible during horizontal scroll, and row/column pagination is available only when needed.
2. Advance to a later benchmark page, sort by one of its columns, and reload or use Back/Forward. Confirm the sorted column’s page is shown and its sort direction remains visible.
3. Select a model on a later row page, navigate away and back, and confirm selection remains. Apply a search/filter and confirm row pagination resets or clamps to the filtered set.
4. Export CSV and confirm it includes every selected visible benchmark and all filtered rows, including records beyond the currently rendered pages.
5. Use keyboard navigation and a screen reader to verify the pager names, range announcements, `aria-rowcount`, `aria-colcount`, and indexed visible cells remain understandable.

## Responsive release check

At 320, 390, 768, and 1024 CSS pixels, verify the compact Options disclosure,
scrollable category strip, model/benchmark pagination, and both table orientations.
The document must not overflow horizontally; the table may scroll internally.
Phone tables render bounded groups of three data columns so users can swipe between
models without mounting the complete matrix. Verify sticky headers during vertical
scroll and sticky row labels during horizontal scroll. Open a numeric score and
check source links and the Close control in its evidence sheet. At desktop widths
(above 1100px), verify the existing toolbar and layout are unchanged.

Browser viewport tests must record the actual `innerWidth`, since browser zoom can
make requested device dimensions differ from CSS pixel dimensions. Component tests
and column-budget tests run in pre-commit; these visual and scrolling checks require
a real browser and are not claimed as automated layout coverage.
