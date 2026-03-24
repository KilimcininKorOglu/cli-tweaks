---
name: bug-report
description: >
  This skill MUST be invoked when the user says "bug report", "bug raporu",
  "hata raporu", "bug analizi", "find bugs", "hataları bul" or any variation
  requesting systematic bug analysis. SHOULD also invoke when user mentions
  "security audit", "code review for bugs", "güvenlik taraması", or asks to
  scan the codebase for issues. Analyzes the entire repository to identify
  and document all bugs systematically. Creates a BUG-REPORT.md with
  severity-ranked findings, root cause analysis, and recommendations.
---

# Bug Analysis & Report

Analyze the entire repository to identify and document all bugs systematically.

## Usage

```bash
$bug-report                    # Full analysis, all severities
$bug-report --severity high    # Filter by severity
```

## Process

### Step 1: Repository Assessment

Map the project structure:
- Identify technology stack and dependencies
- Find main entry points and critical paths
- Check for existing tests and linting configurations
- Look for existing `BUG-REPORT.md` to continue ID sequence
- Scan for `TODO`, `FIXME`, `HACK`, `XXX`, `BUG` comments

### Scanning Scope

Always skip non-source directories and generated files:
- `node_modules/`, `vendor/`, `dist/`, `build/`, `.next/`, `__pycache__/`, `.venv/`
- Lock files (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Gemfile.lock`, `poetry.lock`)
- Minified files (`*.min.js`, `*.min.css`), source maps, compiled output
- Third-party code, vendored dependencies, and auto-generated files
- Focus exclusively on project-authored source code

### Step 2: Bug Discovery

For large repositories (50+ source files), scan in parallel:
- Use Grep and Glob tools across different areas simultaneously
- Split by category (security, logic, code quality) or by directory (frontend, backend, shared)
- Merge findings and deduplicate before generating the report

Scan for these categories:

| Severity | Examples                                                                  |
|----------|---------------------------------------------------------------------------|
| CRITICAL | SQL injection, XSS, CSRF, auth bypass, data corruption, crashes, leaks   |
| HIGH     | Logic errors, race conditions, missing validation, wrong API contracts    |
| MEDIUM   | Swallowed exceptions, edge cases, integration problems                    |
| LOW      | Deprecated APIs, dead code, N+1 queries, technical debt                   |

### Step 3: Verify Each Finding

Every potential bug MUST be verified on the actual code before reporting:
- Read the suspect file and trace the full code path (callers, callees, error handlers)
- Confirm the bug is real -- not a pattern you misread, not handled elsewhere, not a deliberate choice
- Check if existing tests already cover the case (if a test exists and passes, it is likely not a bug)
- If you cannot reproduce or confirm the logic flaw by reading the code, discard the finding
- NEVER report a bug based on assumptions or pattern matching alone

Only verified findings proceed to documentation.

### Step 4: Document Each Bug

```
BUG-[ID]: [Brief description]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: NEW | CONFIRMED | IN_PROGRESS | FIXED | WONT_FIX
File: [path/to/file.ext:line_number]
Component: [affected module/feature]

Problem: [What's wrong - current behavior]
Expected: [What should happen]
Root Cause: [Why it happens - if determinable]
Impact: [User/system/business impact]
Verification: [How you confirmed this bug - specific code path or logic trace]
Suggested Commit: [Conventional commit message for the fix, e.g. "fix: prevent XSS in user input sanitizer"]
```

### Step 5: ID Management

Bug IDs must never reset. Always increment from the highest existing ID.
Check `BUG-REPORT.md`, `bugs.md`, `bug.md` for existing IDs.
If no existing bugs, start from BUG-001.

### Step 6: Generate Report

Save to `BUG-REPORT.md` in repository root:

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

- Zero false positives is more important than completeness -- only report verified bugs
- ALL findings go under a single `## Findings` section -- no custom grouping headers (no "Technical Debt", "Architecture", etc.)
- Findings must be sorted by severity: CRITICAL first, then HIGH, MEDIUM, LOW
- Each finding uses `### BUG-[ID]` heading with `---` separator between entries
- If `bugs.md` or `bug.md` exists, merge into new report and delete old file
- Allowed commit types: fix, feat, refactor, chore, test, docs, perf, ci, build, security, cleanup
- Suggested Commit messages NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
