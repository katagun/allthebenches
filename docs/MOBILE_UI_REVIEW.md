# Mobile UI review — 20 October 2026

Reviewed the phone bar view (portrait and landscape), the matrix view, the
Options drawer, the model picker, filters, evidence sheets, and the catalog and
entity pages at 320–1024px widths. No page-level horizontal overflow was found
anywhere; all measurements of `document.scrollWidth - innerWidth` were zero.

| # | Finding | Status |
| --- | --- | --- |
| 1 | Bar-view cards show another configuration's score for rows with no result on the shown benchmark (e.g. `74.2%`), yet sort those rows as missing: they land below `—` rows and draw no bar. Sorting reads as broken, bars look missing, and scoreless rows look prominent. The selector module itself says alternate setups must never drive sorting or highlighting. | Fixed — cards show the same number the matrix shows (single score, multi-report range, or other-setup preview) via a shared `previewScore` interval driving display; cards rank by the low end so leading numbers stay ordered, and bars draw the shown span (zero-based for singles, floating segment with a visibility floor for ranges). Only truly scoreless rows sit last as dashes. Provenance stays in the score button's accessible label and evidence sheet (as in the matrix) so cards keep the compact one-line budget; the default benchmark still counts exact-configuration scores. Matrix/table sorting stays primary-only. |
| 2 | Compare mode can render two cards with the identical model name and no reasoning or setup label, so same-model configurations are indistinguishable. Desktop shows a Reasoning badge per row. An unused `.mobile-model-setup` rule suggests a setup line was planned but never rendered. | Fixed — cards sharing one model now show a `Reasoning:` line (reviving that style); single-model cards stay at 45px. |
| 3 | In the Options drawer, `Choose models` wraps onto a lone full-width row after Share and Export CSV instead of pairing with `Choose benchmarks`. | Open |
| 4 | The mobile shell uses `env(safe-area-inset-left)` for both horizontal sides; the right side should use `inset-right`. Only visible on notched phones in landscape. | Open |
| 5 | At 844x390 in matrix mode the table card is 270px tall (about three benchmark rows) and sticky header model names wrap to three lines. Usable but tight. | Open |

Deliberately not filed: model-name ellipsis at 320px (full name remains in the link title, matching the CSS intent), and directory links living only in the Options drawer on mobile (tradeoff, not breakage).

Verification for each fix should re-run the focused component test plus the
`mobile-layout` and `mobile-simplicity` Playwright specs.
