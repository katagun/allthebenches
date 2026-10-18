# ARC Prize verified coverage additions

Reviewed on 2026-10-18 against the official ARC Prize result pages. Each SHA-256 in `arc-prize-scores.json` and `coverage-model-additions.json` hashes the exact HTML response bytes retrieved with Python `urllib.request` from the recorded URL. The score tables were separately re-parsed from those pages' HTML and checked against the captured rows. Retrieval timestamps are UTC.

| Catalog model | Official result page | Verified values captured |
|---|---|---|
| GPT-5.6 Sol (`gpt56_sol`) | https://arcprize.org/results/openai-gpt-5-6 | ARC-AGI-1, 2 and 3; Max, XHigh, High, Medium, Low |
| Grok 4.6 (`grok46`) | https://arcprize.org/results/xai-grok-4-6 | ARC-AGI-1, 2 and 3; XHigh, High, Medium, Low |

The GPT-5.6 source is a family results page. The HTML verified table labels the first group `Sol`; its rows are the scores recorded for catalog model `gpt56_sol`. Terra and Luna scores were excluded from this Sol snapshot. Both this page and the Grok 4.6 page show a single unlabeled ARC-AGI-3 column, so those values remain in the importer's unspecified-harness series. Dashes are missing values.

`coverage-model-additions.json` is ready to merge for four more verified releases: DeepSeek V4.1 Flash, Dots3-Note Preview, GLM-5.3-Flash and Qwen3.8-27B. It contains proposed model records, the one additional lab record (Dots Studio), source records and exact table snapshots. Release dates and model/provider names are from each official page header. Access state and weight state remain unknown; modalities record text plus image input for ARC evaluation.

After these model and lab records are integrated in the curated dataset, merge the four `snapshots` into `arc-prize-scores.json`, run `uv run python scripts/import-arc-prize.py`, then `uv run benches build --offline`. The importer has not been run because it writes the curated dataset and presets.

ARC Prize's [official testing policy](https://arcprize.org/policy) explains verified semi-private evaluations and the separate ARC-AGI-3 harness conditions.
