# Logging, Observability & Debugging Readiness

This subcommand replaces the old standalone `/observability-audit` skill.

## Command

```bash
/bug-report observability-audit [--focus logging|metrics|health|tracing|debugging|all]
```

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

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
