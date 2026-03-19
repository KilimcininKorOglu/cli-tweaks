---
name: observability-audit
description: >
  This skill MUST be invoked when the user says "observability audit", "logging review",
  "log analizi", "monitoring audit", "izlenebilirlik", "debugging readiness"
  or any variation requesting logging, observability, and debugging readiness
  evaluation. SHOULD also invoke when user mentions "structured logging",
  "distributed tracing", "health check", "metrics", "SLI", "correlation ID",
  or asks to audit production observability. Reviews logging quality, metrics,
  health checks, distributed tracing, and debugging aids for production readiness.
argument-hint: "[--focus logging|metrics|health|tracing|debugging|all]"
---

# Logging, Observability & Debugging Readiness

You are an SRE reviewing this codebase's production readiness from an observability perspective. When production breaks at 3 AM, can you diagnose the issue from logs and metrics alone?

## 1. Logging Quality

- Is there structured logging? (JSON format with consistent fields, not free-text printf)
- Are log levels used correctly? (DEBUG for dev, INFO for business events, WARN for recoverable issues, ERROR for failures requiring attention)
- Is there a correlation/request ID propagated through the entire request lifecycle?
- Are critical business operations logged? (user actions, payment events, auth events)
- Are error logs actionable? (include context: what was attempted, what input caused it, what failed)
- Are there excessive DEBUG/TRACE logs that would flood production? Proper log level gating?
- Is sensitive data filtered from logs? (passwords, tokens, PII, credit card numbers)

## 2. Metrics & Monitoring

- Are the RED metrics covered? (Rate, Errors, Duration for each endpoint/service)
- Are business metrics instrumented? (signups, purchases, key feature usage)
- Are resource utilization metrics tracked? (connection pool, queue depth, cache hit rate, memory)
- Are there custom metrics for known failure modes?
- Are SLIs defined and measurable from the code?

## 3. Health & Readiness

- Is there a health check endpoint that verifies all dependencies? (DB, cache, queues, external services)
- Is there a separate readiness probe? (ready to serve traffic vs just alive)
- Is there graceful shutdown? (drain in-flight requests, close connections, flush buffers)
- Are startup dependencies checked and reported clearly on boot?

## 4. Distributed Tracing

- Is there trace context propagation across service boundaries?
- Are spans created for significant operations? (DB queries, HTTP calls, queue operations)
- Are trace IDs included in error responses for user-reportable debugging?

## 5. Debugging Aids

- Is there a way to enable verbose logging for a specific request/user without redeploying?
- Are there feature flags to disable problematic code paths?
- Is there a way to replay failed operations?
- Are database migrations reversible?

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
