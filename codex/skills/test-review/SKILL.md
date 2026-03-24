---
name: test-review
description: >
  This skill MUST be invoked when the user says "test review", "test analizi",
  "test kalitesi", "test strategy", "test suite review", "test coverage analysis"
  or any variation requesting test suite quality evaluation. SHOULD also invoke
  when user mentions "coverage gaps", "test quality check", "testing pyramid",
  or asks to evaluate the strength of the test suite. Analyzes the entire test
  suite for coverage gaps, quality issues, strategy balance, and infrastructure
  problems. Produces a prioritized report with concrete test cases to add.
---

# Test Suite Quality & Strategy Review

You are a test engineering lead evaluating the test suite of this project. Tests are the safety net — how strong is it?

## 1. Coverage Gaps

Identify the following:

- Which public functions/methods have ZERO tests?
- Which error/exception paths are untested?
- Which edge cases are untested? (empty inputs, boundary values, null/nil, overflow, unicode)
- Which concurrent/async scenarios are untested?
- Which integration points are untested? (DB, HTTP, queue, file system)
- Which critical business rules have no dedicated test?

Prioritize by risk: what's the business impact if this untested path fails?

## 2. Test Quality

For each existing test, check:

- Does it actually assert something meaningful? (not just "no exception thrown")
- Does it test behavior or implementation? (implementation tests break on refactoring)
- Is the test deterministic? (no time-dependency, no random data, no network calls, no file system race)
- Is the test isolated? (no shared mutable state with other tests, no execution order dependency)
- Is the test readable? (arrange-act-assert structure, descriptive name, clear intent)
- Is mocking excessive? (>3 mocks per test = testing the mocks, not the code)
- Are assertions specific enough? (asserting entire objects vs just the relevant fields)

## 3. Test Strategy

- Is the testing pyramid balanced? (many unit, fewer integration, few E2E)
- Are there contract tests for service boundaries?
- Are there performance/load tests for critical paths?
- Are there security-focused tests? (injection attempts, auth bypass attempts)
- Is there mutation testing to verify test effectiveness?
- Are tests running in CI on every commit?

## 4. Test Infrastructure

- Are test utilities and factories DRY and well-organized?
- Is test data management clean? (factories/fixtures, database reset between tests)
- Are slow tests tagged and separable from fast tests?
- Is the test suite fast enough for developer feedback loop? (<5 min for unit tests)

## Verification

Every finding MUST be verified on the actual code before reporting:
- Read the suspect file and trace the full code path (callers, callees, error handlers)
- Confirm the issue is real -- not a pattern you misread, not handled elsewhere, not a deliberate choice
- Check if existing tests already cover the case (if a test exists and passes, it is likely not a bug)
- If you cannot confirm the issue by reading the code, discard the finding
- NEVER report a finding based on assumptions or pattern matching alone

## Output Format

All findings are written to `BUG-REPORT.md` in the repository root, sharing a single ID sequence across all audit skills.

Check `BUG-REPORT.md` for existing IDs and increment from the highest. If none exists, start from BUG-001.

For each verified finding:

```
BUG-[ID]: [Brief description]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: NEW
File: [path/to/file.ext:line_number]
Component: [affected module/feature]

Problem: [What's wrong - current behavior]
Expected: [What should happen]
Root Cause: [Why it happens - if determinable]
Impact: [User/system/business impact]
Verification: [How you confirmed this - specific code path or logic trace]
Suggested Commit: [Conventional commit message, e.g. "fix: add rate limiting to payment endpoint"]
```

If `BUG-REPORT.md` already exists, append new findings under `## Findings` and update the summary table.
If it does not exist, create it with:

```markdown
# Bug Analysis Report - [Repository Name]

Generated: [Current Date]
Last Bug ID: BUG-[XXX]

## Summary

| Severity  | Count  |
|-----------|--------|
| Critical  | X      |
| High      | X      |
| Medium    | X      |
| Low       | X      |
| **Total** | **X**  |

## Findings

[All findings sorted by severity: CRITICAL first, LOW last]
```

## Notes

- Zero false positives is more important than completeness -- only report verified findings
- ALL findings go under a single `## Findings` section -- no custom grouping headers (no "Technical Debt", "Architecture", etc.)
- Findings must be sorted by severity: CRITICAL first, then HIGH, MEDIUM, LOW
- Each finding uses `### BUG-[ID]` heading with `---` separator between entries
- Allowed commit types: fix, feat, refactor, chore, test, docs, perf, ci, build, security, cleanup
- Suggested Commit messages NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
