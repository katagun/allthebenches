#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo 'No Git repository yet. After git init, run sh scripts/install-hooks.sh.' >&2
  exit 1
fi
existing=$(git config --local --get core.hooksPath || true)
if [ -n "$existing" ] && [ "$existing" != '.githooks' ]; then
  echo "Existing hooksPath ($existing) preserved; add scripts/check-precommit.sh to your hook." >&2
  exit 1
fi
git config --local core.hooksPath .githooks
echo 'Pre-commit checks enabled.'
