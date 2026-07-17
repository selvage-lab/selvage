#!/usr/bin/env bash
# Configure git to use the .githooks/ directory for hooks in this repo.
# Run once after cloning: ./scripts/setup-git-hooks.sh
#
# This enables the post-checkout hook that copies .claude/settings.json and
# settings.local.json into new git worktrees (including orca-managed worktrees).

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

git config core.hooksPath .githooks

echo "Configured core.hooksPath = .githooks"
echo "Hooks in .githooks/ will now run on git events."
