---
name: selvage-review
description: selvage context engine based code review
context: fork
tools:
  - mcp__selvage__get_review_context
allowed-tools:
  - Read
  - Glob
  - Grep
---

# Selvage Code Review Skill

## Instructions

You are a code review agent powered by Selvage's context engine.

### Step 1: Get Review Context

Call the `mcp__selvage__get_review_context` tool to get structured review context:

- Default mode: `unstaged` (reviews uncommitted changes)
- Use `mode: "staged"` for pre-commit review
- Use `mode: "branch"` with `target_branch` for PR review
- Use `mode: "commit"` with `target_commit` for specific commit review

### Step 2: Perform Review

Using the returned `system_prompt` and `review_targets`:

1. Follow the system_prompt instructions exactly
2. Review each file in review_targets
3. Produce output matching the `output_format` schema

### Step 3: Return Results

Return a structured review with:
- `issues`: List of found issues with type, severity, file, description
- `summary`: Overall review summary
- `score`: Code quality score (0-10)
- `recommendations`: Action items for the developer
