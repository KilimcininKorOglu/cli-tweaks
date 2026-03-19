---
name: tech-debt
description: >
  This skill MUST be invoked when the user says "tech debt", "teknik borç",
  "technical debt audit", "borç haritası", "debt mapping", "code quality audit"
  or any variation requesting technical debt mapping and prioritization. SHOULD
  also invoke when user mentions "TODO audit", "FIXME", "dead code", "dependency
  debt", "test debt", "architectural debt", or asks to systematically catalog
  and prioritize technical debt. Maps explicit, hidden, dependency, test, and
  architectural debt with interest rate scoring and a payoff plan.
---

# Technical Debt Mapping & Prioritization

You are a senior software engineer systematically mapping, measuring, and prioritizing all technical debt in the codebase. Technical debt is like credit card debt — if you don't pay it, interest accumulates and eventually crashes the system.

## 1. Explicit Debt

Find issues already marked in code:

- Collect ALL TODO, FIXME, HACK, XXX, WORKAROUND, TEMPORARY, KLUDGE comments
- For each, determine the date (via git blame), author, and why it's still unresolved
- How many are older than 6 months? 1 year? 2 years?
- Which of these carry security or data integrity risk?
- Identify code written as a temporary solution that became permanent

## 2. Hidden Debt

Find problems that nobody marked but exist:

- Excessive complexity: functions with cyclomatic complexity >15, files >500 lines, functions with >5 parameters
- Duplicated code: code blocks with >80% similarity (copy-paste debt)
- Outdated patterns: old design approaches not used in the rest of the project
- Dead code: functions called from nowhere, unreachable endpoints, unused dependencies
- Missing abstraction: same logic manually repeated in 3+ places
- Wrong layer: business logic in controllers, database queries in views
- Undocumented behavior: critical code sections with no answer to "why does this work this way"

## 3. Dependency Debt

- How many dependencies are outdated? (minor, major, critical security updates)
- Are there deprecated API or function calls?
- Is there code stuck on an old version of the language/framework?
- Are there library changes that need migration but have been deferred?

## 4. Test Debt

- Which critical modules have test coverage below 80%?
- Are there broken (disabled/skipped) tests?
- Which flows require manual testing but have no automation?
- Is the test infrastructure itself technical debt? (slow, fragile, hard to maintain)

## 5. Architectural Debt

- Are there structures that were appropriate in the initial design but no longer fit scale/requirements?
- Are there modules that should be separated from the monolith but remain coupled?
- Are there database schema structures that no longer meet business requirements?
- Are there architectural shortcuts made during emergencies that were never fixed?

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

If `BUG-REPORT.md` already exists, append new findings and update the summary table.
If it does not exist, create it with:

```markdown
# Bug Analysis Report - [Repository Name]
Generated: [Current Date]
Last Bug ID: BUG-[XXX]

## Summary
| Severity     | Count |
|--------------|-------|
| Critical     | X     |
| High         | X     |
| Medium       | X     |
| Low          | X     |
| **Total**    | **X** |

## Findings
[All findings grouped by severity]

## Recommendations
[Suggested fixes and preventive measures]
```

## Notes

- Zero false positives is more important than completeness -- only report verified findings
- Suggested Commit messages follow conventional commits and NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
