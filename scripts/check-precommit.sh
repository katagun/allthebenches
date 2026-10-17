#!/bin/sh
# Read-only validation; live vulnerability checks require network access.
set -eu
cd "$(dirname "$0")/.."
uv lock --check
uv run python scripts/check-staged.py
pnpm --dir web install --lockfile-only --frozen-lockfile --ignore-scripts
pnpm --dir web run lint
pnpm --dir web run typecheck
pnpm --dir web test
uv run ruff check pipeline tests scripts
uv run pytest -q
uv run benches validate
uv run python -m scripts.check-generated
VITE_BASE_PATH=/allthebenches/ pnpm --dir web run build
uv run python scripts/check-bundle.py
LAYOUT_BASE_PATH=/allthebenches/ pnpm --dir web test:layout
pnpm --dir web audit --audit-level low
uv run python scripts/audit-python-dependencies.py
