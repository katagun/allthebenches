> Integration status: merged into the local canonical dataset on 17 October 2026. Canonical category normalization and preset choices may differ from this extraction fragment.

# Historical expansion audit

This fragment adds historical primary-report results for **14 releases and 174 numeric observations**, represented as **91 report-and-protocol-specific benchmark variants**. It does not alter the canonical dataset. IDs are prefixed `hist_` to avoid accidental joins with broader benchmark names whose exact task/version/protocol has not been verified. The fragment intentionally has no new lab rows: model `lab_ids` reference the existing canonical IDs `anthropic`, `google_deepmind`, `meta`, and `mistral`.

## Included releases

- Anthropic: Claude 3 Opus, Sonnet, Haiku (2024-03-04); Claude 3.5 Sonnet June checkpoint (2024-06-21).
- Google DeepMind: Gemini 1.0 Ultra and Pro (2023-12-06); Gemini 1.5 Pro and Flash May 2024 report checkpoints (2024-05-14).
- Meta: Llama 3.1 8B, 70B, and 405B Instruct (2024-07-23).
- Mistral AI: Mistral 7B (2023-09-27); Mixtral 8x7B base and Instruct (2024-01-08).

Every score is tied to a source ID, exact table/page locator, report evaluator, reporting relationship, and a setup note. Values are transcribed as printed; percentages are preserved at the report's precision. A same-source table series is marked comparable only among rows in that exact report table/setting. The `hist_` variants deliberately prevent the frontend from silently equating different shot counts, prompting, model modes, or report-specific evaluation pipelines.

## Sources, hashes, and extraction locators

Checksums below are SHA-256 of the complete source PDF bytes downloaded to the temporary audit cache during extraction. The PDFs are not duplicated in the project. Source URLs and hashes are also recorded in each `sources` object.

| Source | Primary URL | PDF checksum | Data locator |
|---|---|---|---|
| Claude 3 Model Card | [Anthropic PDF](https://assets.anthropic.com/m/61e7d27f8c8f5919/original/Claude-3-Model-Card.pdf) | `88ae851f53c3034d436816164ce49a876b333fa9b550fb7ef29838182b59ba7d` | Table 1, p.6: Claude 3 MMLU, MATH, GSM8K, HumanEval, GPQA Diamond, MGSM, DROP, BBH, ARC-Challenge, HellaSwag. The score subset is 3 models × 13 cells. |
| Claude 3.5 Sonnet June addendum (combined card PDF) | [Anthropic PDF](https://assets.anthropic.com/m/61e7d27f8c8f5919/original/Claude-3-Model-Card.pdf) | `88ae851f53c3034d436816164ce49a876b333fa9b550fb7ef29838182b59ba7d` | Addendum Table 1, p.44: 11 Claude 3.5 Sonnet June checkpoint cells. The card text marks this as the June 20 addendum; the release date is June 21. |
| Claude 3.5 Sonnet launch page | [Anthropic announcement](https://www.anthropic.com/research/claude-3-5-sonnet) | HTML page; no PDF checksum | Page heading date Jun 21, 2024 and launch text; supports model release date. |
| Gemini 1.0 report | [Google DeepMind PDF](https://storage.googleapis.com/deepmind-media/gemini/gemini_1_report.pdf) | `e2ed7c48914289faf666fcbb1de0fcde5d4ec9ae30fe8f28ae8c1f672b9e7765` | Table 2, p.8: 10 rows for Ultra and Pro, including MMLU, GSM8K, MATH, BBH, HumanEval, DROP, HellaSwag, Natural2Code, and WMT23. The CoT MMLU row retains Ultra CoT@32 / Pro CoT@8. |
| Gemini 1.5 report, arXiv v5 | [Google DeepMind / arXiv](https://arxiv.org/abs/2403.05530) | `abcd3b8e4b54721ff2d2323204f7b2ad9212b0ff6c8ed77725657526a5418b13` | Table 11, p.30: 16 rows for Gemini 1.5 Pro and Flash (31 reported cells; the pretrained MATH majority@64 row is Pro-only). This December 2024 report version reports May 2024 model checkpoints. The pretrained MATH majority@64 cell is reported only for Pro and is assigned a separate pretrained configuration; Flash remains absent. Other 1.5 cells use the report’s instruction-tuned checkpoint configuration. |
| Llama 3 Herd of Models, arXiv v3 | [Meta AI / arXiv](https://arxiv.org/abs/2407.21783) | `481f1599468f95a07d05e97fafe55bbe786dc1624c6f881bcb4c7d14c933d083` | Table 2, p.3: 16 rows × 3 sizes. The paper states the table results are for Llama 3.1 despite abbreviated column headings; caption identifies fine-tuned models. The included releases are Instruct variants. |
| Mistral 7B, arXiv v1 | [Mistral AI / arXiv](https://arxiv.org/abs/2310.06825) | `dfbac4e7035344b305c947481f2e7e8a02f7a24a563917eb6e47f6591d14c5ae` | Table 2, p.4: 12 Mistral 7B rows. §3 specifies MMLU 5-shot; commonsense rows 0-shot; Natural Questions/TriviaQA 5-shot; HumanEval 0-shot; MBPP 3-shot hand-verified; MATH 4-shot maj@4; GSM8K 8-shot maj@8. |
| Mixtral of Experts, arXiv v1 | [Mistral AI / arXiv](https://arxiv.org/abs/2401.04088) | `f8bbf0e9d979b7a8ce7be65119266545a229a85b57e077d8bd048e458bb642da` | Table 2, p.4: 12 Mixtral base rows. §3 protocols are listed with the observations. Table 3, p.5: MT-Bench 8.30 for Mixtral Instruct on 0–10 scale. |

## Coverage and limitations

The fragment covers general knowledge (MMLU/MMLU-Pro), math (MATH, GSM8K, MGSM and source-specific math sets), reasoning/science (GPQA, BBH, ARC, DROP and related report rows), coding (HumanEval, MBPP), instruction following (IFEval), agent/tool use (BFCL, Nexus), long context (ZeroSCROLLS/QuALITY, InfiniteBench, needle retrieval), translation (WMT23), and chat judging (MT-Bench). It deliberately does **not** add unsupported historical safety scores. That absence is documented as a coverage gap and does not suppress safety rows already present in the canonical dataset.

The studies are self-reported and use different harnesses, prompts, checkpoints, sampling, and in some cases post-training/API endpoints. Identical benchmark names across report variants therefore do not establish comparability. Claude 3 model card GPQA and majority rows use multiple rollouts (10 randomizations noted in the card); Gemini self-consistency results use the method named in the row. Gemini 1.0 HumanEval and WMT23 cells explicitly marked PT use separate post-trained Gemini API configurations. Natural2Code is not marked PT in the table, so it remains on the report’s named release configuration without an API variant inferred. Gemini 1.5 May model measurements occur in the December v5 paper. Llama's table is instruction-tuned. Mistral 7B and Mixtral base results are not Instruct results; only the separately reported Mixtral MT-Bench cell uses the Instruct release.

No scores have been derived from other scores, copied from secondary comparison sites, or extrapolated across model sizes. No report cell absent from the source is represented by zero. Exact harness versions are not always published in the tables; observations retain each table's protocol and mark that limitation in `setup`. A raw source snapshot is available in the local temporary extraction cache for review, but is intentionally not a distributable artifact.
