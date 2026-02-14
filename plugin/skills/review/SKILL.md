---
name: review
description: Selvage AST-based smart context code review. Use when reviewing code changes, checking diffs, or analyzing code quality.
context: fork
agent: selvage-reviewer
allowed-tools:
  - Read
  - Glob
  - Grep
argument-hint: "(e.g., 'staged', 'branch main', 'commit abc1234')"
---

# Selvage Code Review Skill

## Argument Parsing

Parse `$ARGUMENTS` to determine the review mode:

| Input | mode | target_branch | target_commit |
|-------|------|---------------|---------------|
| (empty) | `unstaged` | - | - |
| `staged` | `staged` | - | - |
| `branch main` | `branch` | `main` | - |
| `branch develop` | `branch` | `develop` | - |
| `commit abc1234` | `commit` | - | `abc1234` |

If `$ARGUMENTS` does not match any pattern above, default to `unstaged` mode.

## Workflow

### Step 1: Get Review Context

Call `mcp__selvage__get_review_context` with the parsed parameters.

Inspect the response and branch on the result:

**Case A - Inline context** (no `context_id` in response):
- The `review_targets` field contains all file contexts inline.
- Proceed directly to Step 2 with the full context.

**Case B - Split context** (`context_id` is present in response):
- The context was too large to return inline.
- The response includes `context_id` and `file_list` (list of file paths).
- For each file in `file_list`, call `mcp__selvage__get_file_review_context` with the `context_id` and `file_path`.
- Call these in parallel where possible to minimize latency.
- Collect all returned `review_target` results, then proceed to Step 2.

### Step 2: Perform Review

Using the `system_prompt` from Step 1 as your review guidelines:

1. **Follow the system_prompt instructions exactly** - it contains the review criteria and context interpretation rules.
2. **Review each file** in the collected review targets:
   - Analyze hunks (changed code sections) for bugs, security issues, performance problems, and design concerns.
   - Pay attention to `context_type` in each target:
     - `SMART_CONTEXT`: AST-analyzed related code blocks - use these to understand the broader code structure around changes.
     - `FALLBACK_CONTEXT`: Text-based pattern matches - still useful but less precise than AST analysis.
     - `FULL_CONTEXT`: Complete file content - typically for new or heavily rewritten files.
3. **Verification Principle**: When you identify a potential issue but are not certain, verify it before reporting:
   - Use `Read` to examine the actual source file for additional context.
   - Use `Grep` to search for related patterns, usages, or definitions across the codebase.
   - Use `Glob` to find related files if needed.
   - Only report issues you are confident about after verification.

### Step 3: Report Results

Present the review as **free-form text** (not JSON). Structure your response as:

1. **Summary**: Brief overview of the changes and overall quality assessment (2-3 sentences).
2. **Issues Found**: List each issue with:
   - Severity indicator: `[error]`, `[warning]`, or `[info]`
   - Category: bug, security, performance, style, or design
   - File and location reference
   - Clear description of the problem
   - Concrete suggestion for how to fix it
   - Code snippet if helpful
3. **Score**: Overall code quality score from 0-10.
4. **Recommendations**: Actionable next steps for the developer.

If no issues are found, state that the changes look good and provide a brief positive summary.
