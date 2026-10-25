# Price coverage and mobile prices — 2026-10-24

## Outcome

Reviewed all 39 releases lacking fresh available prices. Added verified pricing for 17 releases: 16 through 195 exact OpenRouter provider routes, plus a direct Alibaba Cloud Singapore International route for Qwen3.8-Max. Fresh available coverage is now **25 of 47 releases across 275 routes** (at capture time), up from 8 releases / 86 routes. There are 286 recorded quotes, including historical and unavailable routes. Prices expire after 48 hours.

## Mobile UI

Tap **Show prices** beside the benchmark selector. Each model row then shows input/output ranges in USD per 1M tokens. Tap that summary for provider routes, paired input/output quotes, observation times, cache/additional charges, restrictions and primary source links. **Hide prices** restores compact score rows. The setting uses the existing API-price column state, so it survives reloads and shared URLs, and selecting API price in the column picker works in the mobile bar view too.

Missing prices say “No eligible API price” and “Unknown, not free.” Explicit source-reported zero charges remain $0. Historical prices appear only with the existing opt-in and are labeled. Price summaries do not change benchmark scoring, ranking, or evidence selection. Ranges are over eligible routes and are not a promise that input/output extrema belong to the same route.

## Identity and evidence

The reviewed crosswalk pins curated names, exact upstream IDs, catalog names, canonical release slugs and weight IDs where supplied. The importer verifies catalog hashes, rejects changed or conflicting identities, and is idempotent. GPT-4o uses its May 13 checkpoint; DeepSeek V4.1 Flash uses its September 10 identity. Newer snapshots, base/instruct substitutions, retired redirects and sibling variants are not promoted. The endpoint reviewer now accepts a partial independently reviewed batch without demanding unrelated legacy crosswalk entries.

Catalog and endpoint raw evidence, hashes, the 39-release decision register, the direct-provider quote, and the DeepInfra audit catalog are saved under `data/expansion/` with `2026-10-24` names. The direct Alibaba quote is a manually reviewed source table, not a general HTML scraper: standard Singapore International rates only, excluding promotions, batch rates and explicit-cache pricing.

## Decisions for all 39 releases

| Release | Decision | Evidence / reason |
|---|---|---|
| Claude Opus 5.5 | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/anthropic/claude-opus-5.5/endpoints) |
| Claude Fable 5.1 | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/anthropic/claude-fable-5.1/endpoints) |
| Gemini 4 Argon | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/google/gemini-4-argon/endpoints) |
| Muse Wonder | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/meta/muse-wonder/endpoints) |
| Muse Wonder Full | subscription only | Meta lists Muse Wonder Full only in Muse Code subscriptions, with no per-token Model API price. Muse Wonder rates do not apply. [source 1](https://dev.meta.ai/models/muse-wonder) |
| Mistral Large 4 | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/mistralai/mistral-large-4-0/endpoints) |
| Grok 4.7 | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/x-ai/grok-4.7/endpoints) |
| Grok 4.6 | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/x-ai/grok-4.6/endpoints) |
| Qwen-AgentWorld-35B-A3B | unverified route | No exact current hosted price in the reviewed OpenRouter, DeepInfra, or Together sources. Do not substitute Qwen3.5-35B-A3B or treat downloadable weights as free API access. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| Qwen3-30B-A3B-Base | base variant mismatch | Curated record is the base/pretrained release. Hosted instruct, chat, reasoning or fine-tuned variants are distinct; no verified base-model API quote found in reviewed catalogs. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| Qwen3-14B-Base | base variant mismatch | Curated record is the base/pretrained release. Hosted instruct, chat, reasoning or fine-tuned variants are distinct; no verified base-model API quote found in reviewed catalogs. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| Qwen3-8B-Base | base variant mismatch | Curated record is the base/pretrained release. Hosted instruct, chat, reasoning or fine-tuned variants are distinct; no verified base-model API quote found in reviewed catalogs. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| Qwen2.5-72B-Instruct | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/qwen/qwen-2.5-72b-instruct/endpoints) |
| DeepSeek-V3-Base | base variant mismatch | Curated record is the base/pretrained release. Hosted instruct, chat, reasoning or fine-tuned variants are distinct; no verified base-model API quote found in reviewed catalogs. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| DeepSeek-R1 | retained historical | OpenRouter returned an empty collection in the preceding refresh. DeepInfra marks original R1 deprecated and replaced by R1-0528. Preserve the old quote; do not transfer replacement prices. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list) |
| DeepSeek-R1-Distill-Qwen-7B | unverified route | No exact current hosted quote in reviewed catalogs; 1.5B, 14B, 32B and Llama distill variants are not substitutes. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| DeepSeek-R1-Distill-Qwen-32B | deprecated route | DeepInfra catalog retains a price but marks this endpoint deprecated with a different replacement. Not promoted as an available route; absent from current OpenRouter catalog. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list) |
| Claude 3 Opus | retired release | Anthropic retirement documentation and current catalog do not establish a current route for this exact historical release. Retain benchmark evidence without borrowing newer-model prices. [source 1](https://platform.claude.com/docs/en/about-claude/model-deprecations); [source 2](https://openrouter.ai/api/v1/models) |
| Claude 3 Sonnet | retired release | Anthropic retirement documentation and current catalog do not establish a current route for this exact historical release. Retain benchmark evidence without borrowing newer-model prices. [source 1](https://platform.claude.com/docs/en/about-claude/model-deprecations); [source 2](https://openrouter.ai/api/v1/models) |
| Claude 3 Haiku | retired release | Anthropic retirement documentation and current catalog do not establish a current route for this exact historical release. Retain benchmark evidence without borrowing newer-model prices. [source 1](https://platform.claude.com/docs/en/about-claude/model-deprecations); [source 2](https://openrouter.ai/api/v1/models) |
| Claude 3.5 Sonnet (June 2024) | retired release | Anthropic retirement documentation and current catalog do not establish a current route for this exact historical release. Retain benchmark evidence without borrowing newer-model prices. [source 1](https://platform.claude.com/docs/en/about-claude/model-deprecations); [source 2](https://openrouter.ai/api/v1/models) |
| Gemini 1.0 Ultra | unverified route | Historical release; no exact current per-token route in reviewed catalogs. Do not use current Gemini or subscription prices. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://ai.google.dev/gemini-api/docs/changelog) |
| Gemini 1.0 Pro | unverified route | Historical release; no exact current route or price verified. Do not substitute later Gemini releases. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://ai.google.dev/gemini-api/docs/changelog) |
| Gemini 1.5 Pro (May 2024 report checkpoint) | retired release | Google release notes say Gemini 1.5 models shut down September 29, 2025; the curated record is specifically the May 2024 report checkpoint. [source 1](https://ai.google.dev/gemini-api/docs/changelog); [source 2](https://openrouter.ai/api/v1/models) |
| Gemini 1.5 Flash (May 2024 report checkpoint) | retired release | Google release notes say Gemini 1.5 models shut down September 29, 2025; the curated record is specifically the May 2024 report checkpoint. [source 1](https://ai.google.dev/gemini-api/docs/changelog); [source 2](https://openrouter.ai/api/v1/models) |
| Llama 3.1 8B Instruct | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/meta-llama/llama-3.1-8b-instruct/endpoints) |
| Llama 3.1 70B Instruct | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/meta-llama/llama-3.1-70b-instruct/endpoints) |
| Llama 3.1 405B Instruct | deprecated route | Exact DeepInfra endpoint is deprecated and replaced by Hermes 3, a distinct fine-tune. No exact current OpenRouter route. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list) |
| Mistral 7B | base variant mismatch | Curated record is the base/pretrained release. Hosted instruct, chat, reasoning or fine-tuned variants are distinct; no verified base-model API quote found in reviewed catalogs. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| Mixtral 8x7B | base variant mismatch | Curated record is the base/pretrained release. Hosted instruct, chat, reasoning or fine-tuned variants are distinct; no verified base-model API quote found in reviewed catalogs. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| Mixtral 8x7B Instruct | deprecated route | DeepInfra marks the exact instruct endpoint deprecated. Together lists training/dedicated-related prices rather than a current serverless per-token quote in the reviewed table. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://api.deepinfra.com/models/list); [source 3](https://www.together.ai/pricing) |
| GLM-5.3 | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/z-ai/glm-5.3/endpoints) |
| Qwen3.8-Max | filled | Official qwen3.8-max model-specific Singapore International price; kept distinct from the OpenRouter September 2 snapshot and Prime. [source 1](https://www.alibabacloud.com/help/en/model-studio/qwen3-8-max) |
| DeepSeek V4.1 Flash | filled | The canonical slug identifies the September 10 release matching curated release_date; exclude the separate October 17 snapshot. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash/endpoints) |
| Dots3-Note Preview | filled | Exact Dots3-Note Preview release name and canonical slug; :free is the serving tier, not a different model. Zero prices require an available endpoint with explicit zero charges. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/dots-studio/dots-3-note-preview:free/endpoints) |
| GLM-5.3-Flash | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flash/endpoints) |
| Qwen3.8-27B | filled | Exact release name and upstream ID reviewed against the curated release; publisher namespace agrees. Base, instruct, parameter size, preview, and Flash variants remain distinct. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/qwen/qwen3.8-27b/endpoints) |
| GPT-4o | filled | The curated release date is 2024-05-13. Use the explicit May 13 endpoint, not the floating GPT-4o alias or August/November checkpoints. [source 1](https://openrouter.ai/api/v1/models); [source 2](https://openrouter.ai/api/v1/models/openai/gpt-4o-2024-05-13/endpoints) |
| Grok 3 | retired redirect | xAI documents retirement and automatic redirection to Grok 4.3. A resolving Grok 3 slug no longer establishes Grok 3 serving or pricing. [source 1](https://docs.x.ai/developers/migration/may-15-retirement); [source 2](https://openrouter.ai/api/v1/models) |

## Remaining limitations

22 releases remain without fresh available prices. “No verified route” is bounded to the sources reviewed here, not a claim of global unavailability. Provider catalogs may retain obsolete prices; deprecated/replaced records are not automatically eligible. Downloadable weights and monthly subscriptions are not per-token API prices. Benchmark access_state metadata is independent and was not globally rewritten by this pricing audit.

Daily collection still requires review/publication; this is not automatic price curation. The health panel reports recorded collection status separately from quote freshness. Performance observations remain lazy-loaded with evidence. The existing mobile CSV/matrix-selection mismatch remains outside this change.

## Validation

Regression coverage includes changed/duplicate/missing crosswalk identities with no partial mutation, independent endpoint batches, region/unit preservation, free versus unknown prices, historical labels, mobile price toggling and persistence, source-linked details, and score-evidence behavior. The release gate runs the complete Python/frontend/browser suites, generated snapshot checks, lint/types, startup budgets and dependency audits.

## Reproduce the reviewed import

```sh
uv run python scripts/import-reviewed-price-mappings.py \
  --catalog data/expansion/openrouter-price-coverage-catalog-2026-10-24.json \
  --provenance data/expansion/openrouter-price-coverage-catalog-2026-10-24-provenance.json \
  --decisions data/expansion/price-coverage-reviewed-mappings-2026-10-24.json
uv run python scripts/review-openrouter-endpoints.py \
  --snapshot data/expansion/openrouter-price-coverage-endpoints-2026-10-24.json \
  --audit data/expansion/openrouter-price-coverage-endpoints-2026-10-24-audit.md \
  --refresh-existing
uv run python scripts/import-route-metrics.py \
  --staging data/expansion/openrouter-price-coverage-endpoints-2026-10-24.json
```

The direct Alibaba quote is separately preserved as reviewed source/route/price records in `alibaba-qwen38-max-reviewed-price-2026-10-24.json`; updating it requires reviewing the region-specific primary table again. Rebuilding or rerunning imports never advances observation times to the current clock.

## Automatic refresh follow-up

[Automatic price refresh](AUTOMATIC_PRICE_REFRESH_2026-10-24.md) supersedes the manual-update limitation above: all curated OpenRouter route IDs and the exact Alibaba Singapore quote now refresh during daily Pages publications and every deployment. Failures retain original observation dates; the 48-hour rule is unchanged.
