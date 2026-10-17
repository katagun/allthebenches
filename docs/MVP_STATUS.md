# MVP development log — 17 October 2026

Historical notes below describe successive implementation passes; counts and checkout status are not current release guarantees. Use [Architecture](ARCHITECTURE.md), [Deployment](DEPLOYMENT.md), the checked-in manifest, and current CI results for publication.

The local MVP is implemented. Work was delegated to three GPT-6 Luna agents for the frontend, Python pipeline, and source curation; the coordinating agent reviewed the contracts, code, data, and build integration.

## Delivered

- React/TypeScript/Vite frontend with TanStack Table, shadcn/ui primitives, Radix, and Tailwind semantic theme tokens.
- Frontier and historical model views, exact reasoning configurations, source evidence sheets, configurable columns, compound score conditions, metadata filters, comparison selection, and CSV export.
- Versioned base64url `v` URL state with legacy JSON-link support; optional browser-local saved views. Shared URLs take precedence without silently replacing the saved view.
- Python/Pydantic validation, deterministic static snapshots, generated schema/types, live-tested discovery collectors, explicit ID reconciliation, and conservative saturation assessment.
- 37 model releases, 51 configurations, 282 benchmark variants, 492 reviewed observations, eight labs (seven with verified headquarters), and 36 provider-specific route prices.
- GitHub Actions validation, Pages deployment, and daily upstream staging for review.

## Verification and release limits

All 12 Python tests and 34 frontend workflow/selector/state/worker/performance tests pass, along with TypeScript checking and the production build. The production site was served at the `/allthebenches/` project base; JavaScript/CSS requests and all four data-file SHA-256 hashes passed an HTTP smoke check. The app rendered successfully in the in-app browser and its desktop styling was inspected. Browser input and viewport automation timed out, so manual mobile interaction, focus traversal, clipboard behavior, and browser download verification remain release checks; component tests cover filter apply/cancel, URL precedence/back navigation, unavailable storage, and load retry.

The source audit is in `DATA_AUDIT.md`. Benchmark coverage remains intentionally partial. All 37 cataloged releases now have reviewed numeric evidence. Coverage remains uneven and evaluation settings differ. Several historical same-report series now document comparable setups, but benchmark saturation still requires the configured cross-model and cross-lab evidence thresholds. OpenRouter rankings were collected, but current exact model IDs could not be reconciled to their ranking identifiers; no popularity values were invented. Agent harness comparison remains deferred, while evaluation setup is retained in source evidence.

Development remains local at `http://127.0.0.1:4173/`. The dev server is intentionally left running. No remote repository or live Pages deployment was established. The working folder was not a Git checkout, and the inferred `katagun/allthebenches` repository was not found by the available GitHub CLI session. Configure the intended repository and enable Pages via GitHub Actions to publish the tested artifact.

## Local expansion pass

Added 22 historical/open-weight releases and 314 observations, including 24 extra frontier results. New views cover historical releases, open-weight releases, Qwen3 base checkpoints, and DeepSeek reasoning. The Frontier default now follows the full curated preset, with viewport-sized benchmark pages (up to 24 columns). Published parameter counts for all eight new Qwen/DeepSeek releases enable size filtering; active counts are included only when disclosed.

Google-card peer results now retain their unspecified exact effort as “Highest reported,” and benchmark-specific evaluator/quoted-result relationships have been corrected. Explicit Gemini pretraining and post-training results have distinct configurations. The column picker restores the active preset, and market hints reflect the snapshot's actual data.

Extraction records are in `data/expansion/historical-audit.md` and `data/expansion/open-models-audit.md`. These fragments were integrated into the canonical dataset; canonical category normalization and preset selections are authoritative. Browser rendering and menu contents were observed; subsequent click/screenshot automation timed out, so automated component tests remain the interaction verification for this pass.

## Frontier gap review

Added 108 reviewed observations: GPT-6.1 Sol (56), Muse Spark 1.3 (13), Muse Wonder (15), Muse Wonder Full (15 additional), and Mistral Large 4 (9 additional). The default Frontier view now includes all five, using exact preferred effort configurations; alternative efforts remain expandable. A Frontier gap review preset exposes selected extra metrics. Native score precision is preserved in table cells and evidence panels, including rates such as 0.983.

The coordinating review independently checked OpenAI's HealthBench table, Surge GDP.pdf and sudo L7 entries, Parallel's exact model profile, Meta's developer table and rendered Wonder PDF table, Mistral's numeric release statements, and its model-card parameter counts. Different AutomationBench versions and task sets remain separate. See the three `data/expansion/frontier-*-audit.md` documents and `docs/FRONTIER_REVIEW.md` for remaining gaps.

## Performance follow-up

Preset switching exposed a TanStack update loop caused by unstable sorting state and page auto-resets. Sorting state is now stable, internal auto-reset is disabled, and a StrictMode regression checks that both preset transitions settle. Rows are selected and sorted in a module worker with indexed immutable snapshots, bounded request/result caching, and stale-response protection. Table construction and rendering are limited to the current column/row page. The pre-commit script passes locally; its installer awaits Git initialization because this workspace has no `.git` directory. See `PERFORMANCE_INVESTIGATION.md` for profiling evidence and measurement limits.
