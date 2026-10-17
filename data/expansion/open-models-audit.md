> Integration status: merged into the local canonical dataset on 17 October 2026. Canonical category normalization and preset choices may differ from this extraction fragment.

# Open-model expansion audit

This is an **extraction Dataset fragment**, not a replacement for `data/curated/dataset.json`. It adds eight source-identified model releases and 116 reviewed observations drawn from primary technical reports. All results are self-reported by the model authors. No benchmark result was estimated or synthesized.

## Scope and counts

| Report family | Model releases included | Observations | Benchmark variants |
| --- | --- | ---: | ---: |
| Qwen3 base report | Qwen3-30B-A3B-Base, Qwen3-14B-Base, Qwen3-8B-Base | 45 | 15 |
| Qwen2.5 report | Qwen2.5-72B-Instruct | 13 | 13 |
| DeepSeek-V3 report | DeepSeek-V3-Base | 31 | 31 |
| DeepSeek-R1 report | DeepSeek-R1, DeepSeek-R1-Distill-Qwen-7B, DeepSeek-R1-Distill-Qwen-32B | 27 | 17 |
| **Total** | **8** | **116** | **76** |

Each benchmark variant is kept distinct by report/version, subset, and protocol where applicable. For example, Qwen3's base MMLU is `qwen3_base_mmlu`, Qwen2.5's reported MMLU-Pro is `qwen25_instruct_mmlu_pro`, and the DeepSeek reports retain their own variants. The fragment does not assert cross-report equivalence merely because display names match. The Qwen3 series marks the within-report base-model comparison as comparable; other series do not claim comparability beyond their source's stated setup.

## Primary sources and exact locators

- [Qwen3 Technical Report, arXiv:2505.09388v1](https://arxiv.org/abs/2505.09388v1): Tables 3–6, pages 5–7; benchmark definitions and shot settings, pages 3–4. Qwen3 protocol details and scores are transcribed from these tables. Model-card identity checks: [Qwen3-30B-A3B-Base](https://huggingface.co/Qwen/Qwen3-30B-A3B-Base), [Qwen3-14B-Base](https://huggingface.co/Qwen/Qwen3-14B-Base), and [Qwen3-8B-Base](https://huggingface.co/Qwen/Qwen3-8B-Base).
- [Qwen2.5 Technical Report, arXiv:2412.15115v2](https://arxiv.org/abs/2412.15115v2): Table 6, pages 9–10; evaluation methodology §5.2. It supplies the 72B-Instruct observations. Identity check: [Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct).
- [DeepSeek-V3 Technical Report, arXiv:2412.19437v2](https://arxiv.org/abs/2412.19437v2): Table 3, pages 23–24; benchmark and protocol descriptions §4.4.1. Identity check: [DeepSeek-V3-Base](https://huggingface.co/deepseek-ai/DeepSeek-V3-Base).
- [DeepSeek-R1 Technical Report, arXiv:2501.12948v2](https://arxiv.org/abs/2501.12948v2): Table 8, pages 40–41; Table 15, page 60; evaluation settings §D.1. Table 8 supplies R1 results and Table 15 supplies the two Distill-Qwen rows. Identity checks: [DeepSeek-R1](https://huggingface.co/deepseek-ai/DeepSeek-R1), [DeepSeek-R1-Distill-Qwen-7B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B), and [DeepSeek-R1-Distill-Qwen-32B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B).

The source records in the JSON fragment carry retrieval dates, report versions, publisher/evaluator attribution, and table/section locators. Observation `locator` values identify the source table, model column, and benchmark row. Exact harness commits and all decoding details are not available for every report table; observation setup notes retain that limitation rather than fill it by inference.

## Identity and exclusion decisions

The Qwen3 report evaluates five base checkpoints in its tables. This fragment includes only the three for which exact public base-model repository pages were verified. It excludes Qwen3-235B-A22B-Base and Qwen3-32B-Base: searches located the report rows but did not establish a matching public base checkpoint repository. The separately published `Qwen/Qwen3-235B-A22B` and `Qwen/Qwen3-32B` IDs are not substituted because their cards describe pretraining and post-training and do not establish that they are the exact base-only evaluation checkpoints. This exclusion avoids conflating a model's benchmark row with a different artifact.

The DeepSeek distill variants retain their published Distill-Qwen identities; they are not aliases for the underlying Qwen base checkpoints. Qwen2.5-72B-Instruct remains a post-trained release and is not merged with a base model record.

## Known limitations

- All 116 scores are vendor self-reports; this fragment does not add independent replications.
- Tables often abbreviate harness details. The observation's `setup` preserves reported protocol and explicitly notes where complete details are absent.
- Similar benchmark names across reports are separate variants in this fragment. They require a protocol-level review before canonical cross-source merge or comparison.
- DeepSeek-R1 report v2 is the cited table source; report version and table locator are recorded so a later audit can detect revisions.
- There are no serving-route prices or usage observations in this expansion. This work is benchmark evidence only.
- The integration passed canonical schema and relationship validation; the fragment remains as an extraction audit artifact.
