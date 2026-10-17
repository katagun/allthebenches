# Contributing

Use Python 3.12+ with uv and Node.js 24. Run the validation and build commands in the README before proposing a change.

## Data changes

Edit `data/curated/dataset.json`; the Pydantic contract in `pipeline/schema.py` is authoritative. Keep stable IDs. Treat each benchmark version, subset, metric, and protocol separately. Scores belong to an exact model configuration, with a source URL, table/figure locator, evaluator, reporting relationship, and review state. Missing scores are never zero. Preserve conflicting reports rather than choosing the highest score. Do not infer benchmark scores.

A source repeating another evaluator's score is a quoted result, not an independent replication. Release dates are distinct from catalog listing timestamps. Parameter estimates need a source, basis, and rationale. Route prices need units and observation dates; OpenRouter usage describes that platform only. Censored rankings do not establish zero usage.

`uv run benches collect --source all` stages external feeds and unresolved mapping candidates under `data/staging/`. Review mappings and evidence before adding canonical records. Collection does not publish new scores automatically. The scheduled metadata workflow uploads a review artifact; it does not change the live site.

Update `docs/DATA_AUDIT.md` when adding or correcting coverage. Regenerate schema/types and static data with `uv run benches build --offline`. Generated files should not be edited manually.

## Interface changes

Use the existing shadcn/ui components and semantic Tailwind theme. Keep advanced controls behind the filter sheet. Preserve keyboard access, visible focus, the source evidence path, and usable horizontal table scrolling on small screens.

URL state is versioned and takes precedence over opt-in saved state. Never silently discard restrictive unknown filters or overwrite a saved view when opening a shared link. Test state migration and filtering changes, including missing values and numeric zero.

## Attribution

Project code is MIT licensed. Upstream material retains its own terms. Preserve source attribution and licenses; peacefulcoexistance-authored data is attributed under CC BY 4.0 and models.dev-derived data under MIT. Do not assume the code license relicenses third-party reports or benchmark assets.

## Pre-commit checks

Run `sh scripts/install-hooks.sh` once after cloning or initializing Git. It enables the versioned `.githooks/pre-commit` hook without replacing an existing custom hooks path. Nothing is published by installing hooks.

The hook runs TypeScript checks, all frontend tests (including the table rendering budget), Python tests, curated-data validation, and live JavaScript/Python vulnerability audits (network required; failures block the commit). Run it manually with `sh scripts/check-precommit.sh`. Install dependencies first (`pnpm --dir web install --frozen-lockfile` and `uv sync`). CI runs these checks as well, so bypassing a local hook does not bypass review checks. Checks inspect the working tree; stage the verified files before committing.

Shared links now use `v=b1.<base64url>` containing UTF-8 JSON. Old JSON links remain readable. Encoding is not compression or encryption. Decoding is size limited and passes through the same allowlisted state validation as saved views; saved browser state keeps its existing format.

Use pnpm for all JavaScript dependency changes; commit `web/pnpm-lock.yaml` and install with `pnpm --dir web install --frozen-lockfile`. The shadcn generator CLI is deliberately absent because its current dependency tree contains an unpatched advisory; the checked-in shadcn components and Radix runtime remain in use. Audits cover development/transitive packages as well as application dependencies. A clean audit means no known advisories in the queried databases at that time, not a guarantee against undiscovered vulnerabilities.

### Additional quality gates

The pre-commit hook and CI also run correctness-focused linting, generated-output drift checks, a production build, and compressed asset budgets. Run `pnpm --dir web lint` and `uv run ruff check pipeline tests scripts` for quick feedback. These catch forgotten `await`s, hook dependency mistakes, inaccessible JSX, undefined Python names, and other likely defects. Do not suppress a rule globally to make generated code pass; fix the cause or document a narrowly scoped exception.

`uv run python -m scripts.check-generated` rebuilds contracts and snapshots in a temporary directory and compares bytes. It never silently repairs the files it checks. After changing curated data or the schema, explicitly run `uv run benches build --offline` and stage the resulting snapshots/types. Feed-health metadata is retained from the checked-in manifest because it records collection-time state.

After a production build, `uv run python scripts/check-bundle.py` limits all JavaScript assets (including lazy chunks and workers) to 200 KiB gzip and CSS to 16 KiB gzip. These are regression budgets, not browser responsiveness measurements; the existing StrictMode rendering and selector tests remain necessary. Increase budgets only with a measured explanation in review.

Focused `.only` tests are forbidden, including locally, so an accidentally narrowed suite cannot pass a commit.

The hook checks lockfile consistency, staged whitespace/conflict markers, and rejects partially staged files so working-tree checks cannot approve different versions of those files. Checks do not auto-format, stage files, or update dependencies. Stage all relevant new files too; CI provides the clean-checkout verification. Live audits intentionally remain required. Browser interaction profiling, comprehensive screen-reader testing, and source verification still need human review; static checks cannot establish scientific accuracy.

## Pull requests and issues

Use a focused branch and explain the problem, resulting behavior, and checks actually run. Use the issue templates for bugs and data corrections. Include screenshots for layout changes and measurements for performance changes. Keep generated outputs in the same pull request as their input changes. Follow the [community conduct rules](CODE_OF_CONDUCT.md) and use the [security policy](SECURITY.md) for vulnerabilities. See [architecture](docs/ARCHITECTURE.md) before changing pipeline or worker boundaries.

### Browser layout regressions

After installing JS dependencies, run `pnpm --dir web install:browsers` once (and
again when Playwright updates). Pre-commit requires the matching Chromium binary;
it does not silently skip browser checks or download browsers during a commit.
CI installs Chromium and its Linux dependencies explicitly.

`pnpm --dir web build && pnpm --dir web test:layout` checks production output at
320, 375, 390, 430, 768, 1024 and 1422 CSS pixels. It checks both orientations,
document overflow, the default control/table height budgets, sticky headers and
labels after scrolling, mobile column counts, expanded Options, and filter-sheet
actions. Tests use an isolated preview server on port 4187; stop any unrelated
process using that port. For a subpath build, set `LAYOUT_BASE_PATH` to the same
base used for the build. Failure screenshots/traces are in `web/test-results/`
and uploaded by CI. Real-device touch and Safari testing remain manual checks.
