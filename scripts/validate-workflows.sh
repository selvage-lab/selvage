#!/usr/bin/env bash
# Validate all GitHub Actions workflows with actionlint.
# Run before pushing any workflow change: ./scripts/validate-workflows.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if ! command -v actionlint >/dev/null 2>&1; then
  echo "ERROR: actionlint not installed. Run: brew install actionlint" >&2
  exit 1
fi

echo "Validating GitHub Actions workflows..."
# shellcheck disable=SC2046
if actionlint $(find .github/workflows -name '*.yml' -o -name '*.yaml' 2>/dev/null); then
  echo "OK: all workflows valid"
else
  echo "FAIL: workflow validation failed (see errors above)" >&2
  exit 1
fi
