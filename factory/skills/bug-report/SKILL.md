---
name: bug-report
description: >
  This skill MUST be invoked when the user asks for systematic bug analysis, or any focused audit such as "api audit", "cache audit", "disaster recovery", "error review", "feature flags audit", "integration security", "observability audit", "payment security", "queue audit", "release discipline", "serialization audit", "session audit", "tech debt", "tenant isolation", "test review", "upload security", "ai code audit", or "dead code". Use `/bug-report` for general scans and `/bug-report <subcommand>` for domain-specific audits. All modes write verified findings to BUG-REPORT.md using the shared report contract.
argument-hint: "[--severity critical|high|medium|low|all | <subcommand> [subcommand-options]]"
---

# Bug Analysis & Audit Router

Analyze the repository either broadly (`/bug-report`) or through a focused audit subcommand (`/bug-report <subcommand>`).

## Usage

```bash
/bug-report                              # Full repository bug analysis
/bug-report --severity high              # General scan filtered by severity
/bug-report api-audit                    # Focused API audit
/bug-report error-review                 # Focused error handling audit
/bug-report dead-code                    # Focused dead-code audit
```

## Subcommands

| Subcommand | Command | Description |
|------------|---------|-------------|
| `api-audit` | `/bug-report api-audit` | API performance, resilience, contract, and lifecycle audit |
| `cache-audit` | `/bug-report cache-audit` | Caching strategy, consistency, and Redis/security audit |
| `disaster-recovery` | `/bug-report disaster-recovery` | Disaster recovery and business continuity readiness audit |
| `error-review` | `/bug-report error-review` | Error message quality, disclosure, and fallback-state audit |
| `feature-flags-audit` | `/bug-report feature-flags-audit` | Feature flag hygiene, rollout safety, and experimentation audit |
| `integration-security` | `/bug-report integration-security` | Third-party integration, webhook, and OAuth security audit |
| `observability-audit` | `/bug-report observability-audit` | Logging, metrics, tracing, and debugging-readiness audit |
| `payment-security` | `/bug-report payment-security` | Payment flow and financial transaction security audit |
| `queue-audit` | `/bug-report queue-audit` | Queue, worker, retry, and DLQ resilience audit |
| `release-discipline` | `/bug-report release-discipline` | Version control, review process, and release-discipline audit |
| `serialization-audit` | `/bug-report serialization-audit` | Serialization, parsing, and data transformation security audit |
| `session-audit` | `/bug-report session-audit` | Session lifecycle, cookies, CSRF, and state-management audit |
| `tech-debt` | `/bug-report tech-debt` | Technical debt mapping and prioritization audit |
| `tenant-isolation` | `/bug-report tenant-isolation` | Multi-tenant isolation and cross-tenant leakage audit |
| `test-review` | `/bug-report test-review` | Test suite quality, coverage gaps, and strategy audit |
| `upload-security` | `/bug-report upload-security` | File upload and media processing security audit |
| `ai-code-audit` | `/bug-report ai-code-audit` | AI-generated code detection, security, and quality audit |
| `dead-code` | `/bug-report dead-code` | Dead code, unused declarations, and cleanup audit |

## Operating Modes

### General Mode
Use `/bug-report` when the user wants a broad repository scan for bugs, logic flaws, correctness issues, and high-confidence findings.

### Focused Audit Mode
Use `/bug-report <subcommand>` when the user asks for a specific audit domain. The domain-specific checklist lives in the matching file under `subcommands/`.

- For `/bug-report api-audit`: see [subcommands/api-audit.md](subcommands/api-audit.md)
- For `/bug-report cache-audit`: see [subcommands/cache-audit.md](subcommands/cache-audit.md)
- For `/bug-report disaster-recovery`: see [subcommands/disaster-recovery.md](subcommands/disaster-recovery.md)
- For `/bug-report error-review`: see [subcommands/error-review.md](subcommands/error-review.md)
- For `/bug-report feature-flags-audit`: see [subcommands/feature-flags-audit.md](subcommands/feature-flags-audit.md)
- For `/bug-report integration-security`: see [subcommands/integration-security.md](subcommands/integration-security.md)
- For `/bug-report observability-audit`: see [subcommands/observability-audit.md](subcommands/observability-audit.md)
- For `/bug-report payment-security`: see [subcommands/payment-security.md](subcommands/payment-security.md)
- For `/bug-report queue-audit`: see [subcommands/queue-audit.md](subcommands/queue-audit.md)
- For `/bug-report release-discipline`: see [subcommands/release-discipline.md](subcommands/release-discipline.md)
- For `/bug-report serialization-audit`: see [subcommands/serialization-audit.md](subcommands/serialization-audit.md)
- For `/bug-report session-audit`: see [subcommands/session-audit.md](subcommands/session-audit.md)
- For `/bug-report tech-debt`: see [subcommands/tech-debt.md](subcommands/tech-debt.md)
- For `/bug-report tenant-isolation`: see [subcommands/tenant-isolation.md](subcommands/tenant-isolation.md)
- For `/bug-report test-review`: see [subcommands/test-review.md](subcommands/test-review.md)
- For `/bug-report upload-security`: see [subcommands/upload-security.md](subcommands/upload-security.md)
- For `/bug-report ai-code-audit`: see [subcommands/ai-code-audit.md](subcommands/ai-code-audit.md)
- For `/bug-report dead-code`: see [subcommands/dead-code.md](subcommands/dead-code.md)

## Shared Workflow

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

### Step 2: Discovery

For large repositories (50+ source files), scan in parallel:
- Spawn up to 3 sub-agents to scan different areas simultaneously
- Split by category (security, logic, code quality) or by directory (frontend, backend, shared)
- Merge findings and deduplicate before generating the report

For general `/bug-report`, scan broad bug categories:

| Severity | Examples |
|----------|----------|
| CRITICAL | SQL injection, XSS, CSRF, auth bypass, data corruption, crashes, leaks |
| HIGH | Logic errors, race conditions, missing validation, wrong API contracts |
| MEDIUM | Swallowed exceptions, edge cases, integration problems |
| LOW | Deprecated APIs, dead code, N+1 queries, technical debt |

For `/bug-report <subcommand>`, follow the domain-specific checklist in the matching subcommand file.

### Step 3: Verify Each Finding

Every potential finding MUST be verified on the actual code before reporting:
- Read the suspect file and trace the full code path (callers, callees, error handlers)
- Confirm the issue is real -- not a pattern you misread, not handled elsewhere, not a deliberate choice
- Check if existing tests already cover the case (if a test exists and passes, it is likely not a bug)
- If you cannot reproduce or confirm the logic flaw by reading the code, discard the finding
- NEVER report a finding based on assumptions or pattern matching alone

Only verified findings proceed to documentation.

### Step 4: Document Each Finding

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
Verification: [How you confirmed this finding - specific code path or logic trace]
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

- Zero false positives is more important than completeness -- only report verified findings
- ALL findings go under a single `## Findings` section -- no custom grouping headers (no "Technical Debt", "Architecture", etc.)
- Findings must be sorted by severity: CRITICAL first, then HIGH, MEDIUM, LOW
- Each finding uses `### BUG-[ID]` heading with `---` separator between entries
- If `bugs.md` or `bug.md` exists, merge into new report and delete old file
- Allowed commit types: fix, feat, refactor, chore, test, docs, perf, ci, build, security, cleanup
- Suggested Commit messages NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
