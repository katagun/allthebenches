# All the Benches weekend implementation plan

Build in small, reviewable units. A lead reviewer owns the contract and acceptance gates; implementation models receive bounded tickets with declared file ownership. Do not ask each implementation model to reinterpret the whole product. Implementation began on 17 October 2026 with three smaller-model agents covering the Python pipeline, frontend, and source-backed dataset; the coordinating agent owns integration and review.

## Chosen architecture

Use a static React + TypeScript + Vite frontend, TanStack Table, actual shadcn/ui components built on Radix primitives, and Tailwind CSS. Use Python 3.12+ with uv, Pydantic, HTTPX, and pytest for collection, validation, reconciliation, saturation analysis, and JSON generation. Introduce HTML/PDF parsers only for a source that needs them. Pin dependencies and lockfiles when implemented.

No runtime server or database. Curated source records live in version control; Python builds static catalog, result, evidence, and market snapshots. The frontend reads only those snapshots. Start with a semantic HTML table and pagination for the large discovered catalog; add virtualization only after a measured need. Do not adopt a grid library that defeats keyboard access.

The Pydantic models are the schema authority. Export JSON Schema and generate TypeScript types from that artifact in a reproducible build step. Do not maintain independent handwritten Python and TypeScript contracts. Generate synthetic test fixtures separately from production data.

Proposed implementation layout:

```text
docs/                         product, methodology, source map, tickets
data/curated/                 reviewed labs, models, configurations, results
data/mappings/                reviewed external IDs and alias histories
data/presets/                 frontier selections and source/series policies
data/staging/                 proposed imports, never published automatically
pipeline/benches/             schema, collectors, reconciliation, build, CLI
pipeline/tests/               semantic cases and collector fixtures
web/src/generated/           schema-derived types
web/src/data/                snapshot loading and selectors
web/src/components/          table, filters, model/score drawers
web/src/styles/              product tokens and responsive styling
web/public/data/             generated published snapshots
.github/workflows/           checks, refresh proposals, Pages deployment
```

## Pipeline behavior

Fetch or read cached source snapshots → parse to staging → reconcile identities and claims → review → validate curated records → select display observations → calculate derived metadata → export deterministic JSON → build frontend → publish approved artifact.

Launch with structured catalog imports and curated benchmark observations. Automate two or three high-value benchmark sources after the schema works; do not spend the weekend building a universal scraper. JSON/API first, source tables second, PDF extraction with manual verification when unavoidable. An LLM may propose extraction but cannot publish it without validation and review.

Metadata imports should preserve upstream IDs, hash/version, attribution, and source timestamps. Unknown mappings go to a review queue, not fuzzy auto-merges. Subsequent refreshes only create proposed changes. Preserve the last valid public snapshot on upstream failure and report feed health.

Proposed CLI contract: `uv run benches validate`, `uv run benches build --offline`, `uv run benches collect --source SOURCE`, and `uv run pytest`. Frontend contract: `pnpm install --frozen-lockfile`, `pnpm run typecheck`, `pnpm test`, and `pnpm run build`. These commands are requirements for the implementers; they do not exist yet.

## Work packages

| Ticket | Deliverable and owned area | Depends on | Acceptance |
| --- | --- | --- | --- |
| T01 Contract | Pydantic entities, schema export, generated TS types, small synthetic fixtures; `pipeline/benches/schema*`, generated types | Product/data documents | Every entity has stable IDs; type generation is repeatable; missing, zero, unknown reasoning, conflicting claims, and censored usage are representable. |
| T02 Offline build | CLI, validation, observation selection, saturation, static outputs; pipeline build modules | T01 | Offline build is reproducible for fixed source inputs; dangling references and invalid units fail; data hashes are stable apart from explicit build metadata. |
| T03 Catalog reconciliation | peacefulcoexistance and models.dev collectors, lab/model mapping, candidate queue; collector and mapping modules | T01 | Upstream aliases remain traceable; developer is not confused with provider; release dates are not overwritten by first-seen times; deleted upstream models stay in history. |
| T04 Market data | OpenRouter models/endpoint quotes and daily usage collector; market modules | T01, mappings interface from T03 | No inference calls; credentials only in environment/CI secret; price units verified; same-route budget matching; Other and censored volume preserved; fixtures cover failure/staleness. |
| T05 Benchmark curation | Source registry, 12–18 benchmark variants, 18–24 benchmarked releases and 120–200 reviewed observations; `data/curated`, `data/presets` | T01 and source map | Required families/categories covered or explicit gaps; every number has a locator and method; exact configs; safety included; no fabricated fill. Counts are targets, quality gates are mandatory. |
| T06 Core table | App shell, semantic table, row grouping, search, category/column controls, sorting; core frontend components | T01 fixtures | Default screen is quiet; rows represent exact configurations; frozen labels and numeric alignment; missing last in both sort directions; no composite score. |
| T07 Filters and state | Drawer, compound AND conditions, selection, URL serialization, opt-in localStorage persistence, CSV; frontend selectors/state | T06 and T02 contract | Conditions apply to the same row; estimates explicitly included; missing fails; price predicates use one route; URL round-trip and CSV preserve meaning; remembered views restore, explicit URLs take precedence, and forgetting removes persistence. |
| T08 Evidence | Score/model details, source alternatives, estimates, prices, usage, coverage explanations; drawer components | T06 | Every score opens evidence; direct source links work; source setup differences visible; focus/Escape behavior correct; no claim that reported implies independent. |
| T09 Integration | Real data wiring, light/dark/mobile polish, accessibility and focused end-to-end checks | T02–T08 | Build works offline from reviewed data; key workflows work at 375px and desktop; no secrets or synthetic production records; numeric semantics pass. |
| T10 Release | README contribution flow, source attributions, CI, Pages artifact/workflow, launch audit | T09 | Correct repository base; deep-link refresh works; initial snapshot and manifest included; reviewed source credits; deployment smoke test passes once hosting is enabled. |

The lead owns preset choice and final score review. Suggested parallelism after T01: one implementation model on T02/T03, one on T04/T05 with a human/reviewer checking extraction, and one on T06. T07/T08 follow the stable table interfaces; integrate only after contracts pass. Avoid simultaneous edits to shared schemas or lockfiles.

Each assignment should contain: the relevant documents, one ticket, owned paths, input/output contract, explicit exclusions, acceptance cases, and a requirement to report changed files, commands run, source limitations, and unresolved decisions. Models may propose contract changes but must not silently alter shared semantics.

## Weekend sequence and cuts

Saturday morning: freeze T01 and representative fixtures; build the offline JSON path and a table skeleton. Saturday afternoon: curate the launch evidence while metadata and market collectors are built. Saturday evening: integrate the first complete vertical slice—one real model/configuration, one score, one evidence drawer, one filter, and one published snapshot.

Sunday morning: fill the representative matrix, add filters with optional remembered views, metadata details, optional price/usage columns, and share/export. Sunday afternoon: audit sources, safety metrics, missingness, accessibility, base paths, and the launch roster; publish the reviewed build once the project owner initiates the implementation/release stage.

If time runs short, cut automatic benchmark scraping, extra historical rows, source-specific charts, CSV niceties, and usage trend windows before cutting provenance, score/version correctness, basic compound filters, safety coverage, or mobile usability. A failed optional usage credential setup must not block the benchmark release; label it unavailable. Keep a catalog of discovered models without pretending their benchmark matrix is populated.

## Focused verification

Pipeline tests cover the semantic cases in DATA_MODEL.md, identity collisions, schema drift, and reproducibility. Collector tests use captured or synthetic responses rather than flaky live network calls. UI tests cover filter/URL round-trip, sort direction/missingness, same-configuration thresholds, same-route costs, drawers, and export. Test behavior, not the incidental component tree.

Persistence acceptance cases: no saved-view write before opt-in; committed changes survive a fresh visit; cancelled drafts do not persist; a shared link overrides rather than merges saved conditions and leaves the saved view intact until explicitly saved; clearing filters updates an actively remembered view; forgetting deletes it and disables future saving; blocked storage/corrupt state cannot crash the app or produce a false saved status; deployment base paths have isolated keys; removed benchmark/model IDs do not silently broaden saved filters. Include URL back/forward behavior in the shared-link check.

Perform a manual source audit of every default-table displayed score before release. Audit a sample of remaining observations, all estimated-size claims, every safety metric direction, and any source conflict. Verify the source itself, not just a search excerpt.

Smoke-test at `/allthebenches/` and an arbitrary project prefix. Use query/hash state with no server route dependency. Confirm refresh, relative data URLs, downloaded CSV, keyboard interactions, light/dark contrast, horizontal table scrolling, loading/error/empty states, and readable model labels at 375px. Aim for initial compressed JS under 250KB and initial data under 500KB; evidence can load separately. Treat these as budgets to measure, not excuses to remove essential detail.

## Refresh and contribution policy

Once implemented, schedule Python collection daily in GitHub Actions, with manual dispatch available. Catalog, price, and usage updates create a reviewable data PR; benchmark extraction updates enter the same review flow. A human or designated lead merges approved data changes. Do not silently alter live results merely because upstream HTML changed. This is a proposed repository workflow, not a Codex reminder or an automation created in this session.

Contributions can be structured source issues, curated-data PRs, or small collector PRs. Require a source URL, exact model/configuration, benchmark/version, reported value and unit, locator, setup notes, and evaluation date if known. Check duplicates and evidence before inclusion.

MVP licensing: MIT for original project code. Preserve upstream dataset licenses and required attributions separately; the code license does not relicense third-party source data. Do not relicense upstream documents, logos, or benchmark datasets wholesale. Include a data-sources/credits page and source-specific license metadata.

## Launch acceptance checklist

- [ ] Required current model families verified against official release evidence immediately before launch.
- [ ] Every displayed score has an admissible observation and usable source locator.
- [ ] Text, reasoning, math, coding, agent tasks, and safety have real reviewed coverage.
- [ ] Historical and saturated benchmarks can be found without appearing by default.
- [ ] Reasoning configurations never mix invisibly; harness comparison remains deferred.
- [ ] Estimated sizes, unavailable prices, and censored usage remain explicitly uncertain.
- [ ] Catalog, benchmark coverage, and market-data freshness are separately reported.
- [ ] Compound filtering, sharing, export, keyboard access, and mobile layout work.
- [ ] Optional remembered views restore correctly; shared URLs override them; users can forget them; storage failures remain usable.
- [ ] Static bundle contains no credentials; Python collection runs only at build/update time.
- [ ] GitHub Pages base path, snapshot checksums, attribution, and deployment verified.

Do not report any unchecked item as complete merely because its code was generated.
