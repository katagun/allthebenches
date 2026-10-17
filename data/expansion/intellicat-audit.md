# TRACES / Intellicat expansion audit

This additive fragment records four TRACES aggregate metrics for three exact model identities already present in the canonical dataset. It does not modify the canonical dataset or claim that the current panel is fully represented.

## Sources and retrieval

- Results viewer: [TRACES technical results](https://intellicat.ai/traces/technical.html), whose JavaScript loads [`data/site.json`](https://intellicat.ai/traces/data/site.json). The JSON snapshot was retrieved 2026-10-17T15:34:41Z; SHA-256 `cca4a44de42a401ca91c86b994fe82ad4c8765892a36c959b0fbc6c263a15b20`. The snapshot declares `meta.benchmark = full-panel-10x`, ten run IDs, and 30 model rows.
- Methodology: [TRACES arXiv v1](https://arxiv.org/html/2608.11415v1), submitted 2026-08-11. §2.2 defines IFR-a, IFR-i, and disclaimer tax; §2.5 defines EDI; Appendix B describes the OpenRouter chat-completions setup and token caps; Appendix E says the displayed confidence intervals are bootstrap percentile intervals over ten full-panel runs. The interval confidence level is not stated in the inspected text, so it is explicitly left unknown in the data.
- Publisher overview: [Introducing TRACES](https://intellicat.ai/introducing-traces/), dated 2026-10-08, describes 30 models, 42 probes, ten repetitions, single-turn prompts without a system prompt, deterministic scoring, and manual response inspection. It explains why Fable was excluded after empty responses on 33 of 42 probes.

The site JSON is the numeric-results source; the arXiv paper and publisher overview support metric meaning and protocol. `reported_at` and `evaluated_at` remain null because the live results JSON does not identify their dates. I did not re-score or reaggregate the response corpus.

## Metric interpretation

- **IFR-a** is the agentic influence failure rate: only refusing the unsafe request counts as a pass. Higher values mean more failures; lower is better.
- **IFR-i** is the interactive influence failure rate: a refusal or engagement with a substantive recognition of the unreliable premise counts as a pass. Higher values mean more failures; lower is better.
- **Disclaimer tax** is IFR-a minus IFR-i, the difference attributed to users noticing substantive warnings. Lower is better.
- **EDI mean** is the mean withheld-detail reproduction score among engaged responses. It is reported separately from the pass/fail rates, ranges from 0 to 1, and lower means less reproduction of source-specific or field-specific details.

The `ifr_a_ci` and `ifr_i_ci` snapshot fields are retained as bootstrap percentile intervals. Their confidence level is unknown from the inspected source text. No interval is provided by the viewer for disclaimer tax or EDI mean.

## Included identities and results

All mappings use exact OpenRouter identifiers in the result JSON and the canonical models’ exact upstream identity or checkpoint name. They are identity mappings only; they do not imply a particular provider-side backend or stable serving route. Configurations are separate TRACES-specific records because the benchmark does not disclose a reasoning effort setting; existing `max`/default configurations are not reused.

| OpenRouter ID | Canonical model | IFR-a | IFR-i | Disclaimer tax | EDI mean |
| --- | --- | ---: | ---: | ---: | ---: |
| `openai/gpt-5.6-sol` | `gpt56_sol` | 0.914286 | 0.542857 | 0.371429 | 0.253486 |
| `deepseek/deepseek-r1-distill-qwen-32b` | `deepseek_r1_distill_qwen_32b` | 1.000000 | 0.988095 | 0.011905 | 0.158423 |
| `meta-llama/llama-3.1-8b-instruct` | `llama31_8b_instruct` | 0.988095 | 0.969048 | 0.019048 | 0.151053 |

The current viewer lists GPT-5.6 Sol, whereas Appendix B of the August arXiv v1 panel does not. For that reason, its exact model-level token cap is recorded as unknown; the 4096-token default is not copied onto that model. The two other included IDs are listed in Appendix B at the 4096-token cap. Per-route provider endpoint details and the reasoning setting are not disclosed in the current site JSON and are not inferred.

## Coverage and exclusions

The fragment has 3 exact model mappings, 3 isolated configurations, 4 benchmark variants, 4 series, and 12 reviewed observations. The other 27 site model rows were not imported because they do not have a sufficiently verified exact identity match to a canonical release in this bounded fragment. They should remain unmerged until reviewed against upstream release identities. No model records, benchmark scores, aliases, or release dates were invented. Fable is absent from the live 30-row viewer and the publisher says its empty-response behavior caused its exclusion; no Fable values are added.

The current viewer’s score table is a public evaluator result, not a claim that different providers’ underlying route implementations were identical. The shared protocol supports same-series comparison at the benchmark level, while provider endpoint routing remains an unreported limitation.
