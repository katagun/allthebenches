# OpenRouter endpoint review

`data/expansion/openrouter-endpoints-2026-10-18.json` is the historical endpoint snapshot used to review the 50 previously unmatched records. The route importer reads its exact model IDs, provider names, tags and service tiers, and writes route and source records only. It does not add endpoint prices or performance measurements.

Run the historical import and produce the row-by-row decision audit with:

```sh
python3 scripts/review-openrouter-endpoints.py
```

The importer validates every route and source record, checks unique IDs and source references, and rejects ambiguous identities, duplicate endpoints, incorrect source URLs, and raw-response hash or JSON mismatches. Its audit is `data/expansion/openrouter-endpoints-review-audit.md`.

The three new model identity joins are deliberately explicit in the script. DeepSeek R1 is matched by the exact OpenRouter ID and reviewed against the exact catalog name and created timestamp; the full model catalog also distinguishes it from `deepseek/deepseek-r1-0528`, whose name and description identify the later update. DeepSeek V4 Pro 0813 and Kimi K3 use exact OpenRouter IDs and exact base names matched to existing curated model records. The identity source bytes and retrieval details are saved in `data/expansion/openrouter-model-catalog-2026-10-18.json` and its provenance file.

`data/expansion/openrouter-endpoints-current-2026-10-18.json` stores a newer set of raw endpoint responses as Base64 alongside parsed JSON, URL, UTC retrieval time and SHA-256. The importer verifies each decoded response hash before refreshing existing route fields and source records:

```sh
python3 scripts/review-openrouter-endpoints.py \
  --snapshot data/expansion/openrouter-endpoints-current-2026-10-18.json \
  --audit data/expansion/openrouter-endpoints-current-audit.md \
  --refresh-existing
```

This keeps the original 50-row audit while recording a separate current refresh audit. Provider status `0` maps to `listed`; other status values map to `unknown`. An absent status is not treated as available.

After route review, `import-route-metrics.py` imports the historical snapshot followed by the current snapshot. The result contains 86 route quotes. The newer responses for these 50 routes have null latency and throughput fields; those routes therefore have no current performance observation, rather than reusing an older measurement with a newer source timestamp. The other reviewed routes retain their dated observations and display their snapshot age.

## October 24 refresh

See [feed health and price reconciliation](FEED_HEALTH_PRICE_REFRESH_2026-10-24.md). Capture reviewed IDs with:

```sh
uv run python scripts/refresh-reviewed-prices.py \
  --previous data/expansion/openrouter-endpoints-current-2026-10-18.json \
  --output data/expansion/openrouter-endpoints-current-2026-10-24.json
```

A partial exit is a review signal. Inspect statuses before importing; rejected records retain their original timestamp and are skipped by importers. Use the route reviewer with `--refresh-existing` and the dated snapshot/audit paths, then `import-route-metrics.py --staging <snapshot>`. Missing routes in accepted model responses become unknown availability; failed models retain historical evidence. Rebuild with `uv run benches build` after copying reviewed endpoint evidence into staging for health publication.
