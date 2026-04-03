# Queue & Async Job Management Resilience Analysis

This subcommand replaces the old standalone `/queue-audit` skill.

## Command

```bash
/bug-report queue-audit [--focus reliability|workers|scheduling|monitoring|all]
```

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

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
