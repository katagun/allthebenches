# Mobile reported-score correction evidence

- `live-before-390.jpg`: the deployed PR #50 site at 390 × 844. Mistral Large 4 on Vals Index shows a setup count instead of its available 48.66% score.
- `live-desktop-before.jpg`: the deployed PR #50 desktop at 1440 × 900, preserving the matrix's selected-configuration behavior. No browser console errors were observed during inspection.
- `corrected-320.png`, `corrected-390.png`, `corrected-844.png`: unedited Playwright captures of the corrected production build. The regression checks model scores, descending ranking, matching bars, winner highlighting, compact rows, and absence of setup-count placeholders.

The JPGs are direct in-app browser captures from `https://allthebenches.com/`. The PNGs are local build test artifacts. Post-deployment verification runs the same regression scenarios against the live URL; see the linked PR/task completion record and [behavior documentation](../../../MOBILE_REPORTED_SCORES_2026-10-23.md).
