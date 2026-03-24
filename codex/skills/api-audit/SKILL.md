---
name: api-audit
description: >
  This skill MUST be invoked when the user says "api audit", "api performance",
  "api analizi", "API resilience", "contract testing", "api performans analizi"
  or any variation requesting API performance, resilience, or contract testing
  evaluation. SHOULD also invoke when user mentions "slow endpoints", "load testing",
  "breaking changes", "OpenAPI validation", "SLO", or asks to audit API health.
  Analyzes all API endpoints for performance bottlenecks, resilience gaps,
  contract safety, and lifecycle management issues.
---

# API Performance, Resilience & Contract Testing Audit

You are an API platform engineer evaluating API performance, resilience, and contract safety from both consumer and provider perspectives. An API is a promise — you should be able to measure, test, and guarantee the promises you make.

## 1. Performance Profile

- What is the average, p95, and p99 response time for each API endpoint? (is it even measured)
- What are the 5 slowest endpoints? Why are they slow? (N+1 query, missing index, external API wait, large payload)
- Are payload sizes reasonable? (1MB+ response = missing pagination or field selection)
- Are there endpoints returning unnecessary data? (fields the client doesn't use — over-fetching)
- Are there endpoints returning insufficient data? (requiring the client to make a second request — under-fetching)
- Is compression enabled? (gzip/brotli — especially for large JSON responses)
- Is connection reuse in place? (HTTP keep-alive, connection pooling)

## 2. Resilience Tests

- How does the API behave under load? (has load testing been done — k6, Artillery, Locust results)
- What is the breaking point? (how many concurrent requests = service degradation)
- Is there graceful degradation? (at breaking point, does it return 503 + Retry-After instead of 500)
- Is rate limiting response correct? (429 + X-RateLimit-Remaining + X-RateLimit-Reset headers)
- Is timeout behavior correct? (appropriate timeout response to client vs dropping connection)
- What happens when a large payload is sent? (returns 413 or consumes memory and crashes)
- Are concurrent requests updating the same resource handled correctly? (optimistic locking, ETag, 409 Conflict)

## 3. Contract Testing

- Is the OpenAPI/Swagger definition present and UP TO DATE? (does it match the code)
- Are there contract tests? (Pact, Dredd, Schemathesis — on both producer and consumer side)
- Are breaking changes automatically detected? (field deletion, type change, required field addition)
- Do non-backward-compatible changes require version bumps?
- Is the API response schema validated? (fuzz testing with random data in test environment)
- Is a mock/stub server available? (for consumer teams to develop independently)

## 4. API Lifecycle

- Are deprecated endpoints marked? (Deprecated header, documentation)
- Are usage metrics collected? (which endpoint is called how much — detecting dead endpoints)
- Is there an API change notification process? (how are consumer teams informed)
- Is an error budget defined? (SLO: 99.9% availability = 43 minutes downtime per month)

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
