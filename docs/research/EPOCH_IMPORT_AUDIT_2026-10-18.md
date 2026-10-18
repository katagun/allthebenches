# Epoch snapshot import — 18 October 2026

Source: https://epoch.ai/benchmarks/use-this-data and its official CSV ZIP.
Archive SHA-256: `6d4b51e3b2ba6421b62c510ebe9aba02597aa1b9c57443670b5810878fbf73a1`.

The adapter stages 925 primary-score observations for 34 existing model releases across 70 archive benchmark variants. See `data/expansion/epoch-2026-10-18.coverage.json` for every input row and decision. Snapshot coverage concerns top-level benchmark CSVs, not metadata or duplicate ECI processed tables. Additional score columns and settings are preserved verbatim in each observation's source row; they are not silently averaged or substituted for the primary measure.

- Staged: 925.
- Unresolved model identity/outside current catalog: 6175. Exact allowlist in `data/mappings/epoch_models.json`; no fuzzy family matches. Pro editions, base/instruct variants, quantized models, and differently dated releases are not merged by resemblance.
- Conflicting reasoning settings: 1 (the source model suffix says max while its explicit row setting says medium).
- Unreviewed metric contract: 8 ForecastBench rows. These remain excluded until the archive's transformed overall-score scale is reconciled with the original evaluator, rather than guessing a Brier-score direction.

## Metric and configuration review

Internal runs use `mean_score × 100`, not the optimistic `Best score (across scorers)`. Standard errors use the same conversion; a standard error is not called a confidence interval. Zero is a valid result and missing/nonfinite values are excluded. External primary scores remain on the original archive scale, explicitly labeled `source score`; neither the ECI `scale` parameter nor a guessed percent multiplier is applied. BTF-3 pooled scores are lower-is-better, verified at https://evals.futuresearch.ai/#btf3. Other admitted primary measures are higher-is-better.

Exact source model versions, run IDs, source row locators, evaluator links, harnesses, reasoning settings and archive hashes survive in the evidence. Explicit suffixes identify reasoning effort; absent effort remains unknown. Different archive variants use separate benchmark IDs; cross-run comparability is unknown. External rows are attributed as quoted results via Epoch, not Epoch-run measurements. No publication date is inferred from retrieval time.

The importer emits candidates. Integration requires an explicit reviewed promotion after inspecting the allowlist and metric contracts. Tests exercise identity exclusions, zero versus missing, mean versus best score, invalid uncertainty, lower-is-better raw units and schema joins.

## Reproduction

```sh
curl -L https://epoch.ai/data/benchmark_data.zip -o /tmp/epoch-benchmarks.zip
.venv/bin/python -m pipeline.epoch_import --archive /tmp/epoch-benchmarks.zip --retrieved-at 2026-10-18T14:20:00Z --output data/expansion/epoch-2026-10-18.json
```

The endpoint is mutable: verify the archive hash above to reproduce this exact snapshot. Epoch's own data is CC BY 4.0; external projects retain their original terms and attribution.
