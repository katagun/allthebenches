# Benchmark coverage audit

**Reviewed 17 October 2026 against the live primary pages and the merged local snapshot.** The snapshot has 37 releases, 67 configurations, 309 benchmark variants, and 663 observations. The 75 BullshitBench and 12 TRACES observations previously held in expansion files are integrated, as are 18 more Agent Arena observations for three exact frontier configurations. None of those are outstanding gaps. Coverage means a result was found for an exact release and source-defined benchmark variant. An empty cell means no mapped observation was found, unless the source explicitly marks that cell as unreported.

## Frontier matrix

The machine-readable file [frontier_coverage.csv](frontier_coverage.csv) contains 190 cells: 10 releases from the Frontier preset by the 19 rows in Google's Gemini 4 Argon comparison table. **84 cells have an observation in at least one configuration** (the row records how many configurations and observations); the remaining 106 are unobserved in this particular matrix. This is an all-configuration coverage count, not a common-protocol score grid. It retains separate report/evaluator results and does not imply that values within a row are directly comparable.

The all-source catalog contains multiple variants per release and evaluator; these counts are useful for breadth only, not protocol matching:

| Release | Distinct benchmark variants with a curated observation | Observed in the 19 selected rows |
| --- | ---: | ---: |
| GPT-6 Astra | 37 | 19/19 |
| Claude Opus 5.5 | 34 | 18/19 |
| Claude Fable 5.1 | 32 | 17/19 |
| Gemini 4 Argon | 22 | 19/19 |
| Muse Wonder Full | 17 | 3/19 |
| Grok 4.7 | 10 | 2/19 |
| Mistral Large 4 | 14 | 2/19 |
| GPT-6.1 Sol | 69 | 0/19 |
| Muse Spark 1.3 | 19 | 1/19 |
| Muse Wonder | 25 | 3/19 |

GPT-6.1's zero in this specific matrix does not mean it lacks data: its system-card, GDP.pdf, sudo L7, and Parallel results use separate source and benchmark variants. The CSV distinguishes the three Google table dashes for Claude from ordinary unobserved cells; the other empty intersections should remain unknown until an applicable source is checked.

The matrix is deliberately tied to Google's nineteen named rows. GDP.pdf and the two safety columns in the Frontier preset are additional comparisons outside this 19-row count.

## Concrete public results still outside the snapshot

### Arena Agent

The live [Agent Arena Overall table](https://arena.ai/leaderboard/agent) reported 52 models and 2,534,501 sessions on 16 October. The local snapshot now contains six Agent Arena metrics for **seven of those 52 exact configurations**. During this audit I confirmed the live rows for Muse Wonder Max, Muse Spark 1.3 Max, and Grok 4.7 xHigh, and those three sets of six observations are now integrated alongside the four exact configurations from the earlier snapshot. For traceability, their captured values are:

| Exact configuration | Net Improvement | Confirmed Success | Praise vs Complaint | Steerability | Bash Reliability | Tool Hallucination |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Muse Wonder (Max) | 4.94% | 9.51% | 4.41% | 5.16% | 5.73% | 0.26% |
| Muse Spark 1.3 (Max) | 3.82% | 5.51% | 4.32% | 5.49% | 2.60% | 0.58% |
| Grok 4.7 (xHigh) | 3.21% | 6.84% | 2.95% | 0.52% | 9.15% | 0.59% |

The integrated observations retain the displayed intervals and session counts. Arena's accessible page shows ± intervals but does not state their confidence level there, so no confidence level is assigned. Tool Hallucination is lower-is-better; the other five signals are higher-is-better. These six columns are separate outcomes, and Net Improvement is not a general quality score.

The page also exposes Code, Chat, and Work Agent Arena categories. These are additional public views to capture as their own variants. More Arena categories and modalities are documented in [Arena's leaderboard dataset card](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset); do not merge ratings across categories or capture dates.

### Mistral Large 4 Preview

The official [Mistral Large 4 release](https://mistral.ai/news/mistral-large-4/) has several numeric results that are already in the 11 curated observations: CyberGym-E2E 82%, Cybench 93%, DeepSWE v1.1 61.7%, SWE-Atlas-QnA 59.4%, Terminal-Bench 4 28.3%, Coding Agent Index 49.8%, Surge blind coding preference 3.74/5, AA AutomationBench 59.9%, AA-Briefcase 1,393 Elo, B3 resistance 93.3%, and KORA 1.691/2. Keep **AA AutomationBench (657 workflows)** distinct from Zapier AutomationBench: the publisher, workflow set, and evaluation are different.

One exact numerical result on that same official page is not represented in the curated records: **Dense 200 visual grounding, Mistral Large 4 42% vs GPT-6 Astra 41%**. This is available-but-unimported, with the setup still needing detail from the linked widget. Add it as its own benchmark variant if the widget/source clarifies its metric and protocol. By contrast, the page's finance/legal superiority claims, SciCode-Verified claim, and STEM claims are described without a score in the page text; their embedded images/widgets or linked evaluator reports need inspection before calling them missing numeric data. Mistral says further benchmarks and methodology will follow, so a few omissions are simply not published yet at this checkpoint.

### GPT-6.1 Sol

The [OpenAI launch page](https://openai.com/index/introducing-gpt-6-1-sol/) gives relative claims for DeepSWE v1.1, Zapier AutomationBench, OSWorld 2.0, and Terminal-Bench Science, but no absolute GPT-6.1 scores for those comparisons in its text. The [DeepSWE v1.1 owner page](https://deepswe.datacurve.ai/) showed a 22 September update and 21 displayed configurations without GPT-6.1; the [OSWorld 2.0 owner page](https://osworld-v2.xlang.ai/) exposed a dynamic leaderboard but no GPT-6.1 row in its accessible text. Zapier's current page exposes only its top ten of 126 models before a “See 116 more” control, so absence from the retrieved text does not establish absence from the full leaderboard. The Terminal-Bench Science page did not expose a text leaderboard. These remain **unverified absolute results**, not “not reported” or confirmed unavailable.

Exact GPT-6.1 numbers are available and already captured on separate variants. The official [system-card addendum](https://deploymentsafety.openai.com/gpt-6-1-sol/math-side-tasking-monitor-evasion) reports HealthBench Professional 64.2, HealthBench 58.5, HealthBench Hard 36.2, and HealthBench Consensus 96.0, all length-adjusted. OpenAI's launch page reports 7.7% factual-error rate at low effort. The evaluator pages give GPT-6.1 35% on Surge GDP.pdf and 28.9% on sudo L7. None should be repurposed as the missing absolute result for the four launch comparisons above.

### Integrated expansions and remaining unmatched records

BullshitBench's **75** observations (25 leaderboard rows × three published fields across V1 and V2) and TRACES' **12** observations for three exact model identities are now included in the 663-observation snapshot. TRACES' results JSON still publishes 30 model rows; 27 remain unmapped pending exact release identity checks. That is a source-backed follow-up queue, not 27 proven current-release scores. Use the [TRACES results JSON](https://intellicat.ai/traces/data/site.json) and [paper](https://arxiv.org/html/2608.11415v1) to resolve names and preserve the ten-run protocol.

## Source-level “not reported” versus unknown

The dataset records three explicit `not_reported` cells from Google's table: Agent's Last Exam and OSWorld 2.0 for Claude Fable 5.1, plus OSWorld 2.0 for Claude Opus 5.5. Google's table uses em dashes for these cells. The 19×10 CSV labels these publisher-explicit cells separately. The other empty cells are merely unmapped/unobserved in this matrix. A live result may exist under another effort, configuration, or benchmark variant; a source may omit the score; or the exact identity may be unresolved. Keep those cases unknown until checked.

For the 27 TRACES panel rows, record identity as unresolved until the release is verified. For OpenRouter usage, zero rows in the captured top-50-per-day feed means censored/unknown, not zero usage. For Arena, the 52-row headline roster and the seven matched configurations do not imply a complete match of the other 45 rows.

## Next collection actions

1. Inspect the Mistral Dense 200 widget and linked benchmark details; add the 42% row if the metric and setup can be identified.
2. Resolve absolute GPT-6.1 values from the full Zapier “See 116 more” list and dynamic benchmark-owner data where available; retain the launch page's deltas as claims only.
3. Review the remaining 27 TRACES model identities, then capture useful Arena Code/Chat/Work slices with exact release/config matching.
