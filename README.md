# All the Benches

A static benchmark explorer covering frontier models and historical results. Compare exact model configurations, inspect evaluation evidence, and share a filtered view through its URL.

Built with React, TypeScript, Vite, TanStack Table, shadcn/ui, and Tailwind CSS. Python validates curated evidence and generates static JSON and crawlable HTML reference pages. No runtime backend or API key is required to browse.

## Run locally

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 24.15+, and pnpm 12.14.0 (pinned in `packageManager`). Use an up-to-date Corepack (`corepack enable pnpm`) or install that pnpm version.

```sh
uv sync --frozen
uv run benches validate
uv run benches build --offline
cd web
pnpm install --frozen-lockfile
pnpm run install:browsers
pnpm run dev
```

Install the commit hook from the repository root with `sh scripts/install-hooks.sh`. Use `pnpm check` to run the full checks, including live dependency audits (network required).

## Check and build

```sh
uv run pytest
uv run benches build --offline
cd web
pnpm run typecheck
pnpm test
pnpm run build
```

The publishable site is `web/dist/`. The Pages workflow targets **allthebenches.com** at base path `/`. See [Deployment](docs/DEPLOYMENT.md) for repository settings, DNS records, HTTPS and release verification.

## Data

The committed curated dataset powers reproducible offline builds. Each score retains its source and evaluation setup; missing or conflicting evidence is not replaced with an invented score. Launch coverage is intentionally incomplete: see the [data audit](docs/DATA_AUDIT.md) and in-app evidence.

`uv run benches build --offline` regenerates all snapshots together, preserving the feed metadata in the existing `manifest.json` and embedding that same manifest in `comparison.json`. It ignores local staging files, so rebuilding in a clean checkout produces the same output. To deliberately refresh feed health from local collection results, run `uv run benches build` without `--offline`. Stage the complete generated output together; do not restore or edit either manifest independently. Run `uv run python -m scripts.check-generated` before committing to verify the snapshots are in sync.

```sh
uv run benches collect --source all
```

Collectors stage peacefulcoexistance, models.dev, and OpenRouter feeds for review. Set `OPENROUTER_API_KEY` only in your local environment or GitHub Actions secret for feeds requiring authentication. Never place it in frontend environment variables. The daily metadata workflow uploads a staging artifact for human review; it does not silently publish new results.

## Project documentation

See [Architecture](docs/ARCHITECTURE.md) for system, data-flow and interaction diagrams, and [coverage gaps](docs/COVERAGE_GAPS.md) for known data limits. The [MVP log](docs/MVP_STATUS.md) is a historical development record.

- [Deployment and custom domain](docs/DEPLOYMENT.md)
- [Security policy](SECURITY.md)
- [Community conduct](CODE_OF_CONDUCT.md)
- [Product and interface specification](docs/PRODUCT.md)
- [Data contract and comparison rules](docs/DATA_MODEL.md)
- [Source map](docs/SOURCES.md)
- [Automated collection and review](docs/COLLECTION_AUTOMATION.md)
- [Implementation tickets](docs/IMPLEMENTATION_PLAN.md)
- [Contribution and evidence rules](CONTRIBUTING.md)

Code is MIT licensed. Source data and reports retain their upstream licenses and attribution requirements.

For local commit guardrails, run `sh scripts/install-hooks.sh` after Git is initialized. The hook runs frontend performance/workflow tests, type checking, Python tests, and data validation. Run the same checks now with `sh scripts/check-precommit.sh`; see [Contributing](CONTRIBUTING.md).

### Data maintenance and reference pages

- [Static detail pages](docs/STATIC_PAGES.md): scores and sources available without JavaScript.
- [Freshness policy](docs/FRESHNESS.md): scheduled checks for changing market data, without expiring historical evaluations.
- [Route metrics](docs/ROUTE_METRICS.md): provider pricing and measured performance provenance.
