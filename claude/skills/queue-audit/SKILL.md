---
name: queue-audit
description: >
  This skill MUST be invoked when the user says "queue audit", "kuyruk analizi",
  "async job review", "job management", "worker analizi", "DLQ audit"
  or any variation requesting queue and async job management resilience analysis.
  SHOULD also invoke when user mentions "dead letter queue", "idempotency",
  "retry mechanism", "worker scaling", "job scheduling", or asks to audit
  background job processing. Reviews job reliability, worker management,
  scheduling, and queue observability for resilience gaps.
argument-hint: "[--focus reliability|workers|scheduling|monitoring|all]"
---

# Queue & Async Job Management Resilience Analysis

You are a distributed systems engineer reviewing queue systems and async job management. Queues are the application's "invisible backbone" — when they fail silently, it can go unnoticed for days.

## 1. Job Reliability

- Is the queue durable? (are messages written to disk, or memory-based — are messages lost if the application crashes)
- Is every job idempotent? (if the same message is processed twice, are there side effects — double email, double payment)
- Is there a retry mechanism for failed jobs? With exponential backoff?
- Is there a maximum retry count defined? What happens when exceeded?
- Is there a Dead Letter Queue (DLQ)? Are messages in DLQ monitored?
- Is job ordering guaranteed? (if order matters, is FIFO queue being used)
- Is the state of partially processed jobs managed? (3/5 steps completed, then error — is there rollback)

## 2. Worker Management

- Do workers shut down gracefully? (when SIGTERM signal arrives, do they finish current job or cut immediately)
- Can worker count be scaled? (auto-scaling based on queue depth)
- Is each worker monitored for memory leaks? (memory accumulation in long-running workers)
- Are workers automatically restarted when they crash? (supervisor, systemd, Kubernetes)
- What happens when connection between worker and queue drops? (automatic reconnection)
- Is there protection against the same job being picked up by multiple workers? (visibility timeout, consumer group)

## 3. Scheduling and Prioritization

- Are there scheduled jobs (cron)? Is double execution prevented across multiple instances? (leader election or distributed lock)
- Are delayed jobs supported? Is scheduling precision sufficient?
- Is there job prioritization? (are critical jobs processed before ordinary jobs)
- Are long-running jobs bounded by timeout? (infinite running job blocks others)
- Are batch jobs broken into smaller chunks? (1M records in single job = memory exhaustion, timeout)

## 4. Monitoring and Observability

- Is queue depth monitored? (continuous growth = consumer can't keep up)
- Is job completion time monitored? (early detection of slowing jobs)
- Is failure rate monitored? (increasing error rate = fundamental problem)
- Does DLQ fill rate generate alerts?
- Is job status shown to the user? (progress of background processing)
- Are jobs traceable? (correlating logs, metrics, and status via job ID)

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
