# UI / UX review — 17 October 2026

Reviewed the live matrix, directories, detail pages, model picker and benchmark picker, then validated fixes locally on desktop and phone layouts.

| Finding | Fix |
| --- | --- |
| Directory searches disappeared after visiting a detail page and using browser Back, and on reload. | Search, lab/category, sort and pagination are stored in fragment parameters. Models and benchmarks retain independent state. |
| Detail pages always said “Back to comparison matrix,” even when reached from a directory. | Contextual return links preserve the originating directory and its filters. Matrix-origin links still return to the matrix. |
| Matrix search used a delayed URL update; navigating immediately could carry stale search state. | URL state is updated immediately; expensive result work remains in the worker. |
| Router treated all fragment changes as navigation and did not subscribe to all history signals. | Route rendering/scroll reset follows the path; catalog state follows hash, history and local state events separately. |
| “Columns” chose benchmark rows in the default orientation. | Renamed to “Choose benchmarks.” |
| “Clear” in the benchmark picker restored default columns through the empty-selection fallback. | Removed the misleading action. Explicit preset reset remains; the final selected benchmark/metric cannot be unchecked, with an explanation. |
| Category labels mixed display names and raw IDs; some benchmark headers repeated version numbers. | Consistent category labels and nonduplicated version display. |
| Catalog pagination could leave the reader near the bottom of a new page. | Page changes reset scroll to the top. |

Regression coverage includes mobile/desktop directory-to-detail round trips, independent directory searches, reload, browser Back/Forward, immediate matrix-search navigation, and the final benchmark selection guard. Existing overflow, sticky headers, toolbar and rendering-budget checks remain in place.

This is a focused usability/navigation review, not a claim of a complete accessibility audit. Keyboard focus semantics, screen-reader flows, and broader user testing should continue to be evaluated as the product grows.
