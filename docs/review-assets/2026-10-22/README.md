# Review evidence

Supporting artifacts for [the deep review](../../DEEP_REVIEW_2026-10-22.md) and [recommended fixes](../../RECOMMENDED_FIXES_2026-10-22.md). Captured from commit `c04f170050d4ee81dd0d0f04e29257be33f26668`, using a local production build. Screenshots show existing behavior, not implemented fixes.

| Screenshot | CSS viewport / surface |
| --- | --- |
| [desktop-1440.jpg](desktop-1440.jpg) | 1440×900 desktop matrix |
| [phone-320.jpg](phone-320.jpg) | 320×740 phone bars |
| [phone-390.jpg](phone-390.jpg) | 390×844 phone bars |
| [phone-alternate-evidence.jpg](phone-alternate-evidence.jpg) | 390×844 evidence behind the 74.2% alternate-setup preview |
| [phone-options.jpg](phone-options.jpg) | 390×844 Options |
| [phone-filters.jpg](phone-filters.jpg) | 390×844 filters |
| [phone-model-detail.jpg](phone-model-detail.jpg) | 390×844 model detail |
| [landscape-844.jpg](landscape-844.jpg) | 844×390 phone bars |
| [landscape-matrix.jpg](landscape-matrix.jpg) | 844×390 optional matrix |

Image pixel dimensions differ from CSS viewport dimensions because of browser rendering scale. Viewport measurements were verified in the DOM. Screenshots are JPEGs returned by the browser, without postprocessing.

`pipeline_probes.py` reads the committed dataset, runs semantic checks on synthetic in-memory copies, and mocks collection into a temporary directory. It never modifies curated data. `pipeline-probes.json` records its output at a fixed review time.

`frontend-probes.test.tsx.txt` is an archived temporary diagnostic test designed to be copied into an unused filename in `web/src/` and run with Vitest. Its imports assume that location. `frontend-probes.txt` records its execution. These probes confirm current defects; they should be rewritten to assert intended behavior when fixes are implemented. The temporary test was removed from `web/src/` after review.

No external services were mutated, upstream data recollected, or production behavior changed during this review.
