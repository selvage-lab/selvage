#!/usr/bin/env bash
# Semantic version bump + CHANGELOG update.
# Usage: ./scripts/bump-version.sh [major|minor|patch]
# Default: commitizen이 changelog 기반으로 증분 결정
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

BUMP="${1:-}"
ARGS=()
if [ -n "$BUMP" ]; then
  ARGS+=("--increment" "$BUMP")
fi

# commitizen이 버전 결정 + CHANGELOG 갱신 + 커밋 + 태그
cz bump "${ARGS[@]}"

# push
git push --follow-tags origin "$(git rev-parse --abbrev-ref HEAD)"
