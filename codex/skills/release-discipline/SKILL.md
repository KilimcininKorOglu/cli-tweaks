---
name: release-discipline
description: >
  This skill MUST be invoked when the user says "release discipline", "versiyon yönetimi",
  "branching strategy", "code review audit", "release process", "change management"
  or any variation requesting version control and release discipline evaluation.
  SHOULD also invoke when user mentions "commit quality", "PR review process",
  "changelog", "semantic versioning", "branch protection", or asks to audit
  git workflow and release practices. Evaluates branching strategy, commit quality,
  code review process, and release discipline.
---

# Version Control, Change Management & Release Discipline

You are an engineering manager evaluating version control practices, branching strategy, and release discipline. Good version management is the foundation for a team to balance stability with speed.

## 1. Branching Strategy

- Is there a defined branching strategy? (GitFlow, trunk-based, GitHub Flow)
- Are there long-lived branches? (>1 week = merge hell risk) How many?
- Is direct push to main branch blocked? (branch protection rules)
- What's the merge strategy? (merge commit, squash, rebase — consistent?)
- Is branch cleanup performed? (are merged branches deleted)
- Is conflict resolution process defined?

## 2. Commit Quality

- Are commit messages descriptive? (do they say what was done AND why)
- Is there a consistent commit message format? (Conventional Commits, Jira reference)
- Are commits atomic? (each commit a single logical change, or 10 different changes in one commit)
- Are there large PRs/MRs? (>500 lines changed = impossible to review — should be kept small)
- Are there sensitive data commits? (secrets deleted but still accessible in git history)
- Is .gitignore properly configured? (unnecessary files: node_modules, .env, build outputs)

## 3. Code Review Process

- Is every change reviewed by at least one person before merging?
- Is there a review checklist? (security, performance, test coverage, documentation)
- What's the review wait time? (<24 hours target — longer = bottleneck)
- What's review quality like? (just "LGTM" or genuinely constructive feedback)
- Do critical changes (security, database, infrastructure) require additional review?
- Do automated checks run before review? (lint, test, security scan)

## 4. Release Process

- What's the versioning scheme? (Semantic Versioning — MAJOR.MINOR.PATCH consistent?)
- Is the CHANGELOG auto-generated? Derived from commit messages?
- Are release notes user-friendly? (technical detail vs user impact)
- What's the release frequency? (daily, weekly, sprint-based — consistent?)
- Is the hotfix process defined? (how are emergency fixes done, do they break main flow)
- Is the release rollback procedure defined and tested?
- Is there a release approval process? (who approves, did QA pass, was staging tested)

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
