# All the Benches source map

Latest coverage research: [Benchleader comparison and source audit, 18 October 2026](research/BENCHLEADER_AUDIT.md), including a complete inventory of its 219 benchmark pages and 43 credited publishers, plus primary-source Mistral Large 4 candidates. This is an ingestion queue, not an assertion that these sources are already collected.

Research checkpoint: 17 October 2026. These are source leads and verified documentation capabilities, not a completed extraction of benchmark observations. Recheck releases and source contracts immediately before launch. The authoritative launch roster is a reviewed preset, not this research list.

## Reuse existing catalogs

| Source | Role in this project | Entry points and constraints |
| --- | --- | --- |
| peacefulcoexistance | Lab identity, headquarters, aliases, evidence, reviewed release access/licensing, discovery channels | Its [published-data documentation](https://peacefulcoexistance.com/) links stable JSON feeds, including [labs.json](https://peacefulcoexistance.com/labs.json), [models.json](https://peacefulcoexistance.com/models.json), [models-dev.json](https://peacefulcoexistance.com/models-dev.json), [taxonomy.json](https://peacefulcoexistance.com/taxonomy.json), and [license-evidence.json](https://peacefulcoexistance.com/license-evidence.json). Use documented feeds, not internal `/app/` payloads. |
| models.dev | Broad canonical model and provider discovery, specifications, feature flags, price fallback | Its [usage documentation](https://models.dev/) lists `/models.json?type=all`, `/api.json?type=all`, and `/catalog.json?type=all` for canonical, provider, and combined views. The [repository](https://github.com/anomalyco/models.dev) supports commit-pinned ingestion. Import one canonical view and the required provider view; do not count the same record three times. |
| OpenRouter | Serving routes, catalog quotes, availability, public platform usage | [Model API documentation](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties) describes `/api/v1/models`, upstream IDs, pricing, pagination, and detail links. Follow returned endpoint-detail URLs. Recheck auth requirements and the live response shape in the collector task. |
| Official releases and model/system cards | Release identity, exact configurations, disclosed size, provider-reported results | Resolve links through official model pages. Preserve published methodology and footnotes. |
| Benchmark maintainers and independent evaluators | Benchmark definitions and measurements under documented protocols | Prefer structured downloadable results and versioned repositories; curated extraction is acceptable for the weekend. |

peacefulcoexistance's published lab records expose headquarters country codes, catalog aliases, and evidence URLs. Its documentation separates access/deployability assessments from benchmark quality, parameter count, and transient price. Reuse the metadata extensively; do not import its editorial scores as capability results. Its catalog documentation labels Atlas-authored data CC BY 4.0 and models.dev imports MIT-attributed. Preserve source-specific attribution and provenance. [Documentation](https://peacefulcoexistance.com/), [lab feed](https://peacefulcoexistance.com/labs.json).

The model feed could not be read reliably through the research browser during this session. The implementation task must validate its actual schema; do not invent a contract from the file name. The lab feed was inspected. No upstream dataset was copied into this project during planning.

Use peacefulcoexistance's lab channels to discover official release pages, its reviewed models to enrich model identity and access, and its licensing evidence to explain weights availability. Keep upstream record IDs so corrections can be traced and improvements can later be contributed upstream. No upstream contribution has been sent.

## OpenRouter prices and popularity

Use `/api/v1/models` for discovery and catalog quotes, and documented per-model endpoint details for route-specific quotes. Catalog metadata may supply a `created` time, which is a catalog timestamp rather than evidence of a public release date. Store raw price strings and units before normalization. [Model API](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties).

The [daily rankings API](https://openrouter.ai/docs/api/api-reference/datasets/get-rankings-daily) documents `/api/v1/datasets/rankings-daily`, an API-key requirement, daily top-50 variant token totals, an Other bucket, and source-window metadata. Cache collection in CI; keep the key out of the static application. Use the source's required citation, including its as-of value. A collector can be built and tested against fixtures before credentials are configured.

The [rankings methodology](https://openrouter.ai/rankings) distinguishes token-based model rankings from request-based author shares, excludes private traffic, keeps variants separate, and licenses rankings reuse with attribution. Our implementation therefore labels the metric “OpenRouter public token volume,” preserves window and variant scope, and never calls it global adoption. Detailed aggregation rules are in [the data contract](DATA_MODEL.md).

Popularity can support sorting, an optional column, and discovery prioritization. Prices support input/output budget filters. Neither changes benchmark results, a model's evidence status, or the definition of the Frontier preset. A scatterplot of score versus scenario cost and task-specific usage are later features.

If credentials are unavailable at launch, ship model discovery and reviewed prices from accessible sources, and mark usage unavailable. Do not request a key in chat or fabricate activity. The implementation owner can configure an `OPENROUTER_API_KEY` repository secret when setting up that collector. No account usage, private prompts, or inference calls are required for this project.

## Current launch candidates

| Family | Candidate at this checkpoint | Evidence and admission work |
| --- | --- | --- |
| OpenAI | GPT-6 Astra and GPT-6.1 Sol | [Astra release](https://openai.com/index/gpt-6-astra/) and [6.1 Sol release](https://openai.com/index/introducing-gpt-6-1-sol/). Extract exact reasoning levels and distinguish model results from production agent configurations. |
| Anthropic | Claude Opus 5.5; Fable 5.1 as an additional frontier comparison | [Opus 5.5 release](https://www.anthropic.com/claude-opus-5-5). Inspect fallback-model and harness qualifications before admitting a model-only result. |
| Google | Gemini 4 Argon | [Model card](https://deepmind.google/models/model-cards/gemini-4-argon/) and [evaluation methodology](https://deepmind.google/models/evals-methodology/gemini-4-argon). Preserve benchmark versions and task subsets. |
| Meta | Muse Wonder; Wonder Full if its setup fits; Muse Spark 1.3 and Muse Spark Open | [Wonder report](https://research.meta.ai/blog/muse-wonder), [Spark 1.3](https://research.meta.ai/blog/introducing-muse-spark-1-3), [Spark Open](https://research.meta.ai/blog/muse-spark-open). Treat each release separately; do not copy scores between Spark variants. |
| Mistral | Mistral Large 4 preview | [Release](https://mistral.ai/news/mistral-large-4/). The announcement distinguishes preview API access from a planned later weights release. Record availability as of the launch snapshot. |
| Grok | Grok 4.7 | [Release](https://x.ai/news/grok-4-7), discovered through the [official news index](https://x.ai/news). Do not freeze the roster to the older 4.5 search result. |
| Additional labs | At least two competitive, evidence-backed releases from the discovered catalog | Audit current DeepSeek, Qwen, GLM, Kimi, and other candidates using official sources and comparable evaluations. OpenRouter usage helps find candidates but is not evidence of benchmark leadership. Exact releases remain a launch-curation task. |

Choose 10–12 for the default preset after reviewing score coverage and configuration purity; the rest remain in All models. Do not crowd out an entire requested lab to make one lab's many variants fit. Include historical anchors from the original GPT-4 era and subsequent years, with explicit release IDs and original benchmark versions. Possible anchors include GPT-4, early Claude/Gemini releases, Llama and Mixtral releases, and later GPT-4o/reasoning generations; selected Claude/Gemini/Llama/Mixtral anchors are now extracted; see the expansion audits for exact scope.

## Benchmark discovery and launch selection

| Category | Candidate sources and benchmarks | Admission rule |
| --- | --- | --- |
| Text and reasoning | Instruction-following evaluations, HLE variants, GPQA Diamond, and contemporary tasks identified from cards; [HELM capabilities](https://crfm.stanford.edu/2025/03/20/helm-capabilities.html) | Pin dataset, grader, tool setting, and public result source. Distinguish composites from individual tests. |
| Math and science | RiemannBench, FrontierMath variants, and LABBench 2 in the [Gemini model documentation](https://deepmind.google/models/gemini/) | Find benchmark-owner definitions and comparable records before selecting default columns. High-scoring variants may belong in history. |
| Coding | DeepSWE v1.1 and other contemporary coding results in current provider reports | Preserve task/subset identity, provider harness, and repeated-run aggregation. |
| Agent tasks | [Terminal-Bench 4.0](https://www.tbench.ai/news/terminal-bench-4-0), AutomationBench, OSWorld variants | Record evaluation setup even though harness browsing is deferred. Terminal-Bench's version announcement describes resource and task changes; old versions cannot be merged. |
| Safety | [HELM safety](https://crfm.stanford.edu/helm/safety/latest/), [AIR-Bench](https://crfm.stanford.edu/helm/air-bench/), documented current prompt-injection evaluations | Include at least two distinct safety metrics if evidence permits. Pin leaderboard versions. Do not equate refusal with overall safety or cyber capability with safeguards. |
| History | MMLU, GSM8K, HumanEval, older math/coding suites | Admit original metric and evaluation variants from primary records; retain even after saturation. No assumed saturation merely from age. |

This is a selection queue. Final benchmark IDs, units, source priority, threshold settings, and row/column coverage are deliverables of the data-curation ticket. Do not launch on a collection of unverified benchmark names.

## Architecture references

The chosen frontend is React, TypeScript, Vite, and TanStack Table with shadcn/ui, Radix primitives, and Tailwind CSS. The Python pipeline uses Pydantic, HTTPX, and a small number of parsers as needed. These are implementation decisions for familiarity and delivery speed, not claims of benchmark superiority.

[Vite's GitHub Pages instructions](https://vite.dev/guide/static-deploy.html#github-pages) require the correct repository base path and describe Actions deployment. [Pydantic's JSON Schema documentation](https://docs.pydantic.dev/latest/concepts/json_schema/) supports generating the shared schema from Python models. Pin actual dependency versions and generated-schema tooling during bootstrap.

## 18 October evaluator import update

The Epoch → Vals → Artificial Analysis → Arena → LiveBench snapshot imports are now integrated. See [reviewed source imports and remaining exclusions](research/SOURCE_IMPORTS_2026-10-18.md) for current counts and the authoritative coverage boundary. Earlier seed coverage counts below/above describe the initial collection, not the expanded snapshot.
