# BullshitBench source and extraction audit

Reviewed 17 October 2026. This is an additive fragment; it introduces no model or lab records. It reuses ten already-curated exact releases and adds thirteen reasoning configurations absent from the canonical file. The fragment contains 25 leaderboard rows represented by 75 observations: three published metrics per row. Six benchmark variants keep V1 and V2 separate and distinguish average grade, all-attempt clear-pushback rate, and all-attempt accepted-nonsense rate.

## Primary sources and pinned releases

- [V1 leaderboard CSV](https://raw.githubusercontent.com/petergpt/bullshit-benchmark/main/data/latest/leaderboard.csv), snapshot generated `2026-09-10T20:14:35Z`; manifest SHA-256 `2605907319773e0e5858a24bd8c63ec46501ce282082eff3d134283811d2af6f`.
- [V2 leaderboard CSV](https://raw.githubusercontent.com/petergpt/bullshit-benchmark/main/data/v2/latest/leaderboard.csv), snapshot generated `2026-10-13T17:37:22Z`; manifest SHA-256 `98b485e08764d1c97144bc4f7b28ced1a96d50850947c775870dfda0e5d749b5`.
- [V1 manifest](https://raw.githubusercontent.com/petergpt/bullshit-benchmark/main/data/latest/manifest.json) and [V2 manifest](https://raw.githubusercontent.com/petergpt/bullshit-benchmark/main/data/v2/latest/manifest.json) identify the release dates, question assets and checksums. The hash fields on CSV source records are copied from those manifests.
- [README](https://github.com/petergpt/bullshit-benchmark/blob/main/README.md), particularly “Scoring,” V1/V2 table and V2 scope, describes the task, 3-judge panel and suite dimensions. [Technical guide](https://github.com/petergpt/bullshit-benchmark/blob/main/docs/TECHNICAL.md#grade-panel-policy) specifies a full three-judge panel, mean aggregation and retry policy. [Viewer implementation](https://raw.githubusercontent.com/petergpt/bullshit-benchmark/main/viewer/next/app.mjs) lines 82–83 and 214–220 documents dashboard score and bar denominators.

BullshitBench asks whether a model notices a false or nonsensical premise, challenges it, and avoids treating it as true. V1 has 55 questions. V2 has 100 questions and covers 13 nonsense techniques across software, finance, legal, medical and physics. The README names the judge panel as Claude Sonnet 4.6, GPT-5.2 and Gemini 3.1 Pro Preview. The evaluator’s three judges grade the same response; the published consensus is their mean. The results are third-party evaluator measurements collected through OpenRouter, not the model providers’ self-reported benchmark scores.

## Metric and denominator handling

The fragment keeps three distinct values without recalculation:

- `avg_score` is stored as `grade points (0–2)`. It is the evaluator’s published mean grade. Its scale is 0 for accepting nonsense, 1 for partial challenge and 2 for clear pushback. The score is not a percent.
- `green_rate` is stored as a fraction with the benchmark’s CSV full-attempt denominator. The source CSV retains this all-attempt rate; this differs from the dashboard’s primary clear-pushback score, which divides clear answers by attempts minus candidate refusals. Errors remain in the rate denominator.
- `red_rate` is stored as a fraction with the same CSV full-attempt denominator. It measures accepting the premise, so lower is better.

The viewer’s README states the headline clear score formula and says canonical leaderboard CSVs retain all-attempt rates. The implementation independently confirms the dashboard uses non-refusal attempts for its score/ranking and controls only the bars with the refusal toggle. No refusal rate was made a score: refusing is not universally better, and the benchmark treats provider-declared candidate refusals as unscored. The Muse Wonder rows each contain one empty output classified as an unscored refusal by explicit evaluator instruction, not a provider-declared refusal; those are retained in the row’s setup metadata.

Each observation locator identifies the CSV line by row number (`rank + 1`, with the header on line 1), rank, exact published model slug and reasoning tier. The setup object retains question count, attempts, answered count, refusals, errors and the published 2/1/0 consensus counts. The numeric observations are copied exactly from the CSV fields `avg_score`, `green_rate` and `red_rate`. The leaderboard has no confidence intervals; none are inferred.

## Included rows

Each row below is an exact `model` slug and reasoning setting in the pinned leaderboard. The observation locator in JSON gives the precise line/rank and the three CSV columns copied.

| Suite | Rank | Exact model slug | Reasoning | Average grade | Clear rate, all attempts | Accepted rate, all attempts |
|---|---:|---|---|---:|---:|---:|
| V1 | 36 | `openai/gpt-6-astra` | max | 1.3152 | 0.4727 | 0.1636 |
| V1 | 66 | `openai/gpt-6-astra` | low | 1.0848 | 0.2909 | 0.2000 |
| V1 | 50 | `anthropic/claude-opus-5.5` | max | 1.1975 | 0.4364 | 0.2545 |
| V1 | 79 | `openai/gpt-5.6-sol` | max | 0.9152 | 0.2727 | 0.3455 |
| V1 | 80 | `openai/gpt-5.6-sol` | low | 0.9152 | 0.2545 | 0.3273 |
| V2 | 8 | `anthropic/claude-fable-5.1` | low | 1.8165 | 0.77 | 0.02 |
| V2 | 21 | `anthropic/claude-fable-5.1` | max | 1.655 | 0.64 | 0.06 |
| V2 | 12 | `mistralai/mistral-large-4-0` | none | 1.7333 | 0.8 | 0.07 |
| V2 | 32 | `mistralai/mistral-large-4-0` | high | 1.5983 | 0.68 | 0.09 |
| V2 | 13 | `anthropic/claude-opus-5` | xhigh | 1.721 | 0.70 | 0.04 |
| V2 | 16 | `anthropic/claude-opus-5` | low | 1.7106 | 0.73 | 0.08 |
| V2 | 25 | `anthropic/claude-opus-5.5` | low | 1.6374 | 0.63 | 0.04 |
| V2 | 27 | `anthropic/claude-opus-5.5` | max | 1.6296 | 0.62 | 0.02 |
| V2 | 31 | `openai/gpt-6-astra` | max | 1.6067 | 0.69 | 0.04 |
| V2 | 38 | `openai/gpt-6-astra` | low | 1.5433 | 0.64 | 0.04 |
| V2 | 35 | `openai/gpt-6.1-sol` | max | 1.5683 | 0.59 | 0.01 |
| V2 | 39 | `openai/gpt-6.1-sol` | low | 1.53 | 0.65 | 0.07 |
| V2 | 44 | `google/gemini-4-argon` | low | 1.5 | 0.66 | 0.13 |
| V2 | 46 | `google/gemini-4-argon` | high | 1.4867 | 0.65 | 0.15 |
| V2 | 48 | `x-ai/grok-4.6` | minimal | 1.48 | 0.66 | 0.16 |
| V2 | 71 | `x-ai/grok-4.6` | max | 1.3533 | 0.56 | 0.17 |
| V2 | 73 | `meta/muse-wonder` | minimal | 1.3367 | 0.57 | 0.20 |
| V2 | 74 | `meta/muse-wonder` | max | 1.3333 | 0.52 | 0.18 |
| V2 | 78 | `openai/gpt-5.6-sol` | low | 1.3 | 0.48 | 0.14 |
| V2 | 79 | `openai/gpt-5.6-sol` | max | 1.2933 | 0.47 | 0.13 |

## Identity and limitations

The exact publisher model slug is preserved in each observation’s setup and separately recorded in `external_mappings` as a reviewed model-identity join to an existing canonical release. These joins do not imply a fixed serving endpoint, a provider-direct route, or immutable model weights. The leaderboard uses provider/model permaslugs; its public CSV does not pin a provider endpoint, model snapshot digest, temperature, or other decoding settings. Therefore the suite is comparable within each one published version/run for the evaluator’s intended table, but its setup is incomplete for strict replication. V1 and V2 are deliberately separate benchmark families and must not be ranked together.

The evaluator publishes aggregate rows only in these two source files. A larger catalog of models/configurations is not imported merely because the browser dashboard exposes them; rows are included only where the source slug and reasoning tier can be unambiguously joined to an already curated release. In particular, Muse Spark 1.2 is not relabeled as canonical Muse Spark 1.3; older Claude 3.5 Sonnet’s undated provider alias is not joined to the dated June 2024 canonical release; and no unavailable or unreported row is assigned a zero. Results represent false-premise challenge behavior, not general harmfulness, calibration, or safety. This is therefore a reliability category measure and is not treated as a standalone safety score.
