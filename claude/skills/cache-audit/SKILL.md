---
name: cache-audit
description: >
  This skill MUST be invoked when the user says "cache audit", "cache analizi",
  "caching strategy", "önbellek analizi", "cache consistency", "cache review"
  or any variation requesting caching strategy and consistency analysis. SHOULD
  also invoke when user mentions "cache invalidation", "stale data", "cache stampede",
  "Redis security", "cache hit rate", or asks to audit caching mechanisms.
  Analyzes all caching layers for consistency issues, performance pitfalls,
  and security vulnerabilities.
argument-hint: "[--focus map|consistency|performance|security|all]"
---

# Caching Strategy & Consistency Analysis

You are a performance and reliability engineer reviewing all caching mechanisms in the application. A poorly designed cache serves stale data, consumes memory, and makes debugging impossible instead of improving performance.

## 1. Cache Map

Find and document all caching layers:

- Application in-memory cache
- Distributed cache (Redis, Memcached)
- HTTP cache (CDN, browser cache, Varnish)
- Database query cache
- ORM-level cache (first/second level)
- DNS cache
- File system cache

For each layer: what does it cache, what's the TTL, what's the size limit, what's the invalidation strategy?

## 2. Consistency Issues

- When data is updated, are ALL related cache layers invalidated? (database updated but Redis still serving old data)
- Is there cache consistency across multiple server instances? (server A is current, server B is stale)
- Does cache invalidation cover related data? (username changed but comments cache still shows old name)
- Race condition: can cache and database become inconsistent during read-update-write cycle?
- Are cache keys separated per user? (user A's data shown to user B — CRITICAL security bug)
- Is post-authorization content being cached? (logged-out user's data still in cache)

## 3. Performance Pitfalls

- Is cache hit rate measured? (below 50% = cache isn't working)
- Is there cache stampede/thundering herd protection? (when TTL expires, 1000 requests hit database simultaneously)
- Is cache size bounded? (unbounded growth = memory exhaustion)
- What's the eviction policy? (LRU, LFU, FIFO — appropriate for workload?)
- Is there a cold start strategy? (when app restarts, does all traffic hit database)
- Is there cache warmup? (are critical data pre-loaded after deployment)
- Dog-pile / cache-aside / write-through / write-behind — which strategy is used, is it appropriate?

## 4. Cache Security

- Does Redis/Memcached have authentication? (password protection)
- Is the cache server protected with network segmentation? (direct internet access blocked?)
- Is sensitive data in cache encrypted?
- Are cache keys predictable? (anyone who knows the key can read the data)
- If session data is stored in cache: has session hijacking risk been evaluated?

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
