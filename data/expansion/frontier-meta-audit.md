# Meta frontier expansion audit

## Scope and verification

This fragment adds 42 reviewed, source-reported observations: 15 rows for each of Muse Wonder and Muse Wonder Full, plus 12 metrics for Muse Spark 1.3. It adds one separate Muse Wonder Full `xhigh` configuration because the model-card table explicitly labels its SWE-Marathon value `xhigh`; the other Wonder and Full rows are explicitly `max`. It does not add Muse Spark 1.1/1.2, Spark Open, or competitor values.

The identities were checked on Meta's [Muse Wonder developer page](https://dev.meta.ai/models/muse-wonder), the [Muse Spark 1.3 developer page](https://dev.meta.ai/models/muse-spark), the [Muse Wonder model card PDF](https://research.meta.ai/static/muse-wonder-model-card), and the linked [Muse Spark 1.3 Evaluation Methodology PDF](https://research.meta.ai/static/muse-spark-1-3-multimodal-evaluation-methodology). The official Wonder model card names both releases and the October 12, 2026 release date (p. 1). The Spark page identifies the model as Muse Spark 1.3, labels its benchmark column max, and publishes the API ID `muse-spark-1.3`; its official methodology says results are generated through Meta Model API with max reasoning for Spark 1.3.

I downloaded the Wonder card from the official URL and verified SHA-256 `63e19276146bc146f1a14a2534360b9712641918f617ca432ef1443991f4edce`, matching the canonical `meta_wonder_card` source. Its benchmark table is rasterized on printed PDF p. 3; I visually checked the rendered page at 180 dpi. The browser PDF text view reports 13 pages and omits that image table, while the downloaded official file is 8 pages. These are different pagination/extraction representations of the same source URL, not different score tables. For locators and methodology I use the downloaded PDF's printed pages: overall methodology pp. 4–5 and benchmark details pp. 5–6. The page-image used for visual review is `/tmp/muse-wonder-page-03.png` (temporary, not part of the dataset).

The official Spark methodology PDF was downloaded and its SHA-256 is `315a5d1de2932bf772caf1945aa2c7460a1e040c5df3d8b6bbfb53eddea864fe`. It says (pp. 1–4) that Spark 1.3 results use max reasoning; gives benchmark versions, task counts, primary metrics, and harness/source notes. The page table is the score source; the methodology is recorded separately in each Spark observation's setup.

## Included Wonder and Wonder Full values

Values are listed as `Muse Wonder Full / Muse Wonder`; both use max reasoning except the explicitly marked Full SWE-Marathon result.

| Benchmark row | Full / Wonder | Source meaning and handling |
| --- | ---: | --- |
| Personal Superintelligence Index | 59.1 / 54.3 | Meta internal seven-evaluation composite; retained as points, without an invented percent scale. |
| Harvey LAB-AA | 13.1 / 10.0 | Artificial Analysis result; version 1.1, perfect task-criteria and hallucination-check pass share. |
| Vals Finance Agent V2 | 59.1 / 56.6 | Vals AI private-test-set accuracy, as named by Meta. |
| HealthBench Pro | 62.3 / 60.5 | Meta common internal framework; 525 questions, no tools, GPT-5.4 judge; weighted rubric score. |
| AutomationBench-AA | 45.4 / 39.1 | Artificial Analysis strict pass@1. Kept distinct from Zapier's AutomationBench task set. |
| GDP.pdf | 33.2 / 30.8 | Surge-reported values; use shared `gdp_pdf_surge` variant from curation. |
| JobBench | 75.3 / 70.5 | 65 professional tasks; mean rubric reward. |
| OSWorld V2.1 partial reward | 78.4 / 72.6 | Primary mean per-task partial reward over 108 workflows. |
| OSWorld V2.1 binary completion | 39.4 / 34.3 | Separate secondary metric for the same version and tasks. |
| MemoryBench | 85.5 / 85.6 | Meta internal weighted rubric score. |
| Terminal-Bench 4.0-AA | 57.1 / 52.0 | Artificial Analysis accuracy; reuses canonical Terminal-Bench 4.0 variant with a separate Meta-report series. |
| DeepSWE 1.1 | 79.0 / 78.8 | DataCurve third-party results; v1.1 pass@1. Reuses canonical DeepSWE v1.1 variant and uses a separate series. |
| SWE-Marathon | 57.5 (Full xhigh) / 53.1 (Wonder max) | Abundant AI pass@1 values. Full's xhigh label is preserved as a distinct configuration. The report notes the other vendors use their own agent products, so this comparison is marked heterogeneous. |
| ProgramBench | 59.0 / 50.0 | Mini-swe-agent; rollouts passing at least 95% of hidden tests. |
| Artificial Analysis Index | 56 / 52 | Artificial Analysis Index v4.3, retained as index points. |

## Included Muse Spark 1.3 values

The values below come only from the official developer-page `Muse Spark 1.3 (max)` column. No values are copied from Spark 1.2, Spark Open, or a different model. Units and variants distinguish ratings, retrieval bands, and the partial/binary OSWorld metrics.

| Benchmark row | Value | Exact method detail retained |
| --- | ---: | --- |
| GDPVal-AA v2 | 1754 | Elo rating; Artificial Analysis leaderboard result. This is not GDP.pdf. |
| JobBench | 64.9 | Official 65-task set and file-aware rubric grader. |
| OSWorld 2.0 partial | 66.9 | Primary mean partial score; validated benchmark release 08.08. |
| OSWorld 2.0 binary | 32.0 | Separate strict completion rate on that evaluation. |
| DeepSearchQA | 90.3 | F1 over 900 questions; same search backend and browser harness across compared models. |
| Agentic IF Index (Internal) | 57.8 | Meta internal composite; no external task-count claim. |
| AutomationBench v3 | 49.6 | Zapier public v3 task set, 600 workflows, pass@1; distinct from AutomationBench-AA. |
| MRCR v2, 256K–512K | 98.5 | 100 examples, 8-needle variant, o200k_base token rebinning, mean sequence-matcher ratio. |
| MRCR v2, 512K–1M | 98.1 | Same protocol, separate token band and benchmark variant. |
| DeepSWE v1.1 | 75.4 | Spark max with mini-swe agent; the method says other model scores come from DataCurve, so the series is marked heterogeneous. |
| SWE-Atlas Codebase QnA | 59.4 | Public split, 124 tasks, mini-swe-agent, Scale AI leaderboard protocol. |
| Terminal-Bench 2.1 | 88.8 | 89 tasks; models use native coding harnesses, so cross-model series is marked heterogeneous. |

## Exclusions and limitations

- No Spark 1.3 GDP.pdf value is added. It is absent from the inspected official Spark score table and methodology. The 27.6 value discussed elsewhere was not located in the official sources inspected for this fragment, so it is deliberately omitted pending an exact source locator.
- No ExploitGym `92` result is added. The Wonder card says this is 92 captured flags, of which only 21 used the intended vulnerability; the published ranking counts the 21 intended exploits, not the 92 raw flags (card p. 7). Those are different counts and should not be presented as one comparable benchmark score.
- The Wonder card's HTML developer page table and raster PDF table agree on the extracted values. The table itself has no printed unit suffixes; the fragment uses percent only where the methodology defines a proportion/rate or the shared benchmark schema already does. Internal/composite index and rubric values use neutral `points`/`score points` labels without asserting an unverified percent scale.
- `reported_at` is the public report date (October 12 for Wonder; September 2 for Spark), not an inferred evaluation date. Exact evaluation timestamps and confidence intervals are not published in these sources.
- Some source rows are provider reports quoting third-party results, not independent Meta runs. Observation relationships and evaluators preserve that distinction. The Spark methodology explicitly combines Meta evaluations, official leaderboard entries, and provider-reported scores; series marked heterogeneous or unknown should not be treated as controlled head-to-head evidence.
- The Spark methodology PDF is 4 pages in the downloaded source. The report's API page does not expose a checksum; the retrieved HTML source is identified by URL and row locator.
