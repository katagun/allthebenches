# Mistral Large 4 public-preview evidence audit

Reviewed 2026-10-17. This fragment adds nine values stated in the text of Mistral’s official launch page and two model-card parameter claims. It does not extract chart-only values or claim a complete benchmark matrix.

## Identity and availability

Mistral’s [October 6, 2026 launch announcement](https://mistral.ai/news/mistral-large-4/) says the public preview API is available and weights are planned for the end of October (sections “Frontier performance” and “What comes next”). The [official model card](https://docs.mistral.ai/models/mistral-large-4-0) identifies “Public Preview Open v26.10”, the model slug `mistral-large-4`, and a 1.05T-total / 52B-active parameter MoE. The launch page rounds total size to “1 trillion”; the fragment uses the model card’s more precise 1.05T and converts it to 1,050B. “Open” in the preview card does not mean weights had already been released: the launch announcement explicitly distinguishes the public API preview from the end-of-month weights release.

The evaluation observations use the existing `mistral_large4_unknown` configuration so they appear with the existing Mistral Large 4 model row. This denotes the preview model, not a known inference setting. Mistral does not disclose benchmark-specific reasoning effort, decoding parameters, or exact backend checkpoint hash in the cited text; these remain unknown.

## Text-reported evaluations added

All nine values below are transcribed from the named statements in the launch page’s “Capabilities deep-dive” sections. They remain source-reported results, not independently reproduced measurements.

| Value | Source locator | Evidence treatment |
| --- | --- | --- |
| DeepSWE v1.1: 61.7% | “Agentic coding”, paragraph beginning “ML4 excels…” | Version is stated; exact split, harness, sampling, and run settings are not. |
| SWE-Atlas-QnA: 59.4% | Same paragraph | Benchmark name and value are stated; version and protocol details are not. |
| Terminal-Bench 4: 28.3% | Same paragraph | Version is stated; exact harness/settings are not. |
| Coding Agent Index: 49.8% | Same paragraph | Reported as a combined index score; its formula and constituent weighting are not in the cited text. |
| CyberGym-E2E: 82% | “Cybersecurity”, paragraph beginning “ML4 is one…” | The page frames this as one test in the Artificial Analysis Cyber Index: reproduce a real vulnerability in open-source software and patch it. It is not the overall index score. Evaluator is recorded as Artificial Analysis, as reported by Mistral. |
| Cybench: 93% | Same cybersecurity section, next paragraph | The page describes a set of 40 exercises. The reported percentage is preserved as-is; no integer challenge count is inferred. |
| AA-AutomationBench: 59.9% | “Agentic Workflows”, first paragraph | Mistral describes 657 business workflows across apps including Gmail, Sheets, Slack, and Salesforce; the benchmark version is unspecified. This is a separate `mistral_automationbench_aa_657` variant, not the catalog’s existing Google/Zapier AutomationBench lineage. |
| AA-Briefcase: 1,393 Elo | Same section, next sentence | The launch page characterizes this as a long-horizon knowledge-work evaluation. |
| Surge AI blind coding-quality evaluation: 3.74 / 5 | “Agentic coding”, paragraph beginning “We also ran…” | Mistral reports a blind human evaluation by professional annotators, ranked second of five. This is a human rating, not a conventional benchmark percentage. |

The source does not include the full harness, date of each run, sampling/aggregation details, or configuration details for these results. Series are therefore marked `comparability_status: unknown`. No cross-model comparability is asserted for the newly named variants. Where the benchmark already exists in the catalog (DeepSWE v1.1 and Terminal-Bench 4.0), the source-specific series is kept distinct. AA-AutomationBench is represented as a new version-unspecified variant because its 657-workflow identity is not established as the existing Google/Zapier AutomationBench lineage.

## Scope and remaining gaps

Only explicit numeric values in page text were included. Mistral’s launch page contains multiple embedded charts and image-based material; this task intentionally did not extract chart values. The source also states qualitative claims about SciCode-Verified and other capabilities without a text numeric score in the cited passages, so no numeric rows were added for those claims. Existing Mistral B3 and KORA observations were not duplicated. The existing full-matrix coverage gap remains: these nine partial results do not make Mistral Large 4 broadly comparable across the catalog.

## Primary sources

- [Introducing Mistral Large 4 — Mistral AI, October 6, 2026](https://mistral.ai/news/mistral-large-4/), especially lines/sections 36–42, 69–74, 89–104, and 179–183 in the rendered article.
- [Mistral Large 4 model card — Mistral Docs](https://docs.mistral.ai/models/mistral-large-4-0), release badge and description identify Public Preview Open v26.10, the model ID, and parameter counts.
