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
argument-hint: "[--focus performance|resilience|contract|lifecycle|all]"
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

## Output Format

For each finding produce:

1. **Endpoint** — which API endpoint
2. **Performance data** — relevant metrics or observations
3. **Issue** — what's wrong or missing
4. **Fix** — concrete recommendation
