# Reviewed source imports — 18 October 2026

The researched source leads are now production imports, applied in this order:

| Source | Added observations | Snapshot boundary |
| --- | ---: | --- |
| Epoch | 925 | Official ZIP, primary score per top-level benchmark CSV |
| Vals | 533 | 45 public benchmark pages; exact names and profile-verified aliases |
| Artificial Analysis | 1,082 | Captured public model payload; 30 verified metric contracts |
| Arena | 2,564 | All 24 latest partitions at immutable HF revision `0ebb411abf001fa30ad48fc7e49c5cd5891d5f8a` |
| LiveBench | 586 | v1 2026-06-25 and v2 key 2026-09-02, displayed 2026-10-14 |
| **Total added** | **5,690** | Existing canonical releases only |

The catalog now contains **6,538 observations, 593 benchmark variants and 342 configurations across 45 model releases**. Mistral Large 4 has **171 observations across 166 variants**, up from 17 observations. Observations are source reports, not necessarily independent experiments; related tasks, categories and snapshots remain separate variants. These counts are not a claim of one directly comparable matrix.

Use the five evaluator views under **More views**, the complete **All models** view, or individual model pages. Scores retain evidence links, exact source labels, capture hashes, configuration uncertainty and evaluator-specific protocols. The existing frontier selection is kept curated rather than flooded with every category/snapshot.

## Coverage limits and review decisions

- Epoch: 925 primary-score rows admitted; 6,175 external model rows lack an approved catalog identity; eight ForecastBench rows have an unresolved transformed-score contract; one row conflicts between model-suffix and explicit reasoning settings. Secondary score fields remain in evidence, not separate invented aggregates.
- Vals: all 3,177 leaderboard rows accounted for: 533 admitted, 28 unresolved, 2,616 excluded. Exact linked profiles resolve punctuation/display aliases; version-ambiguous families remain excluded. Profile default effort does **not** prove row-specific effort, so these configurations are explicitly unknown with profile settings retained in evidence.
- AA: 67 exact matched source model/configuration rows across 29 catalog releases. Eleven estimated composite index values are omitted. Fractions, signed index points and Elo use distinct contracts. SciCode's published dataset-under-review caveat is preserved.
- Arena: all 30,387 scored records accounted for: 2,564 admitted and 27,823 without verified catalog identity. Most unmatched names concern models outside the catalog or distinct releases. Thirteen same-date overlaps with different values/intervals/counts are preserved as alternative source snapshots. Signed agent IPS effects are distinct from the earlier site signal cards.
- LiveBench: all 1,976 numeric cells accounted for: 586 admitted and 1,390 without verified catalog identity. v1 tasks and v2 suites remain separate. No unweighted category averages are invented.

This is coverage of specified source snapshots for verified existing releases. It is **not globally complete coverage**, and a missing result is never interpreted as zero. Similar names, guessed reasoning effort and unpublished evaluations do not qualify as verified results.

## Audits and reproduction

- [Epoch audit](EPOCH_IMPORT_AUDIT_2026-10-18.md)
- [Vals audit](VALS_IMPORT_AUDIT_2026-10-18.md)
- [AA audit](../../data/expansion/aa-2026-10-18-audit.md)
- [Arena row accounting](../../data/expansion/arena-hf-coverage.json)
- [LiveBench cell accounting](../../data/expansion/livebench-coverage.json)
- [Reviewed fragment hashes and ordered integration manifest](../../data/expansion/reviewed-source-imports-2026-10-18.json)

```sh
uv run python scripts/import-reviewed-snapshots.py data/expansion/reviewed-source-imports-2026-10-18.json
uv run benches build --offline
```

Integration verifies approved fragment hashes, rejects conflicting IDs, explicitly promotes candidates after review, validates the complete joined schema, and refreshes source presets. Reapplying the same manifest is idempotent. Changing a fragment requires a new review/hash approval. Collection adapters remain separate from promotion; running a scraper alone cannot silently publish new scores.
