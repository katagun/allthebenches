# Dependency maintenance

Use Node.js 24.15+ and pnpm 12.14.0. Both package manifests pin the package manager so commands from the repository root and `web/` select the same version. Recent Corepack is required for pnpm's native launcher. The application lockfile is `web/pnpm-lock.yaml`; npm lockfiles are not used.

Install with `pnpm --dir web install --frozen-lockfile`. Run `sh scripts/check-precommit.sh` for type checks, workflow/performance tests, Python validation, and live audits. Enable that hook with `sh scripts/install-hooks.sh` after Git initialization. CI installs the frozen lockfile and runs the same audits. Audit service/network errors fail the check rather than being treated as clean results.

JavaScript: `pnpm --dir web audit --audit-level low` covers the entire resolved tree, including development and transitive packages. `pnpm --dir web outdated` checks direct dependencies against the registry.

Python: `uv run python scripts/audit-python-dependencies.py` audits every third-party name/version in `uv.lock`, including platform-conditional entries, using pinned pip-audit 2.10.1 and OSV. It does not infer safety from the packages installed on only one platform.

## Review on 2026-10-17

The initial JavaScript audit reported five advisories. Upgrading the test toolchain removed the Vitest and worker-pool advisories. The remaining unpatched `braces` advisory (GHSA-vfj7-8cjw-p6xm) came through the unused shadcn generator CLI; that development dependency was removed. The checked-in shadcn components, Radix dependencies, styling, and `components.json` remain in use. Do not add the generator back without rechecking its dependency tree.

The Python audit found PYSEC-2026-1845 in pytest 8.4.2; pytest was upgraded to 9.1.1. The resulting JavaScript dependency graph and all 17 third-party Python lock entries had no known advisories at the time of this review. No direct JavaScript package was reported outdated. Audits reflect current database knowledge and do not guarantee the absence of undiscovered vulnerabilities.

TypeScript is pinned to 6.0.3 for compatibility with typescript-eslint 8.71.2. The newer TypeScript 7 compiler API is not supported by that parser yet; upgrading it currently breaks type-aware linting. Upgrade these together after verifying `pnpm --dir web lint`, typechecking, tests, and the production build. ESLint and Ruff are development-only quality tools and are included in the vulnerability audits.
