# Vals existing-model import audit (2026-10-18)

This is a candidate-only expansion sourced from frozen public Vals AI benchmark leaderboard pages. It does not change the curated dataset. The extraction is deterministic from `data/expansion/vals-all-source-snapshot-2026-10-18.json`; `pipeline/vals_import.py` turns that evidence into the schema-shaped `data/expansion/vals-2026-10-18.json` fragment.

## Scope and coverage

The snapshot covers all 45 Vals benchmark URLs in the source registry, each captured with HTTP 200 and a SHA-256 digest. Its table inventory contains 3,177 displayed model rows. Exact display-name matching selected 372 rows; an additional 161 rows across 39 pages were verified through the exact linked Vals model profile and its title, for 533 imported score rows across 41 pages and 20 canonical releases. Verified labels are GLM 5.3/Flash, Qwen 3.8 Max/27B, Wonder Full, Muse Spark 1.3 Max, and DeepSeek R1. The Muse Spark 1.3 Max profile identifies the 1.3 release and separately labels its profile as Max; the canonical release is reused while the application of the profile setting to each leaderboard row remains unknown. DeepSeek R1’s linked profile is titled simply DeepSeek R1 and has no 0528 suffix, matching the existing January release rather than the separately versioned May release. `Claude Fable 5` and `DeepSeek V4` remain excluded because their exact source profiles do not verify the canonical 5.1 / 0813 versions. Four pages have no imported candidate; the other four pages initially lacking an exact-name match contain verified profile-linked alias rows.

Every inventoried row is counted exactly once as a candidate (533), unresolved (28), or excluded (2,616). `coverage.unresolved` and `coverage.excluded` retain per-page grouped model labels and counts. Unresolved means the display label is a close spelling, shortened label, or apparent variant of a canonical release; it is deliberately not mapped. Excluded means no conservative canonical-name correspondence was found. Labels such as `Wonder`, `Muse Spark`, `GPT-6 Sol`, and versioned Claude variants remain unmapped. Each alias promotion retains the row’s exact display label and linked model path, the fetched profile URL/hash/title, and the mapping rationale in the snapshot.

All 21 linked model profiles were captured independently. Their displayed effort settings, when present, are retained as profile metadata in observation setup with the explicit note that their application to the leaderboard row is not established. Imported `Configuration` entities use `mode: unknown` and no reasoning label, with deterministic IDs scoped by canonical release and source profile; this does not overstate profile metadata as a proven row setting. Benchmark category and modality are assigned only when the captured benchmark title or page description supports the classification; otherwise they remain unknown. For each imported benchmark page, candidate scores are non-increasing as displayed rank advances, supporting `direction: higher`; exact metric headers are retained. No uncertainty interval is displayed, so the import does not invent one. No evaluation timestamp is supplied by the pages. Capture metadata records the known date only; exact retrieval time was not retained.

Only benchmark names and table values needed to identify a result are included; no leaderboard prose or benchmark task content is copied. Vals AI is attributed as publisher and evaluator. No reuse license was established, so the source records leave `license` null. A benchmark version is recorded only when explicitly printed in the page title (for example, Terminal-Bench 2.1 and 4.0); otherwise it is `unversioned-as-reported`. Existing curated variants are reused only on exact benchmark-name match and compatible unit.

## Reproduction and checks

The frozen raw HTML files used for the capture are held outside the repository under `/tmp/vals-pages-2026-10-18/`, `/tmp/vals-model-pages-2026-10-18/`, and `/tmp/vals-alias-profiles-2026-10-18/`; their public URLs, hashes, parsed inventory, exact candidate cells, and model-profile evidence are retained in the snapshot. The adapter needs only the retained JSON:

```sh
python3 pipeline/vals_import.py \
  --snapshot data/expansion/vals-all-source-snapshot-2026-10-18.json \
  --dataset data/curated/dataset.json \
  --output data/expansion/vals-2026-10-18.json
```

Validation:

```sh
./.venv/bin/python -m pytest tests/test_vals_import.py -q
```

The test merges by entity ID with curated records taking precedence, so importing a reviewed/promoted candidate ID remains idempotent. The 533 rows are candidates for review, not approved benchmark claims.
