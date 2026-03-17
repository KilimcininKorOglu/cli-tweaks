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

## Output Format

For each finding produce:

1. **Cache layer** — which caching mechanism
2. **Key example** — sample cache key involved
3. **Issue** — what's wrong
4. **Impact** — performance, consistency, or security consequence
5. **Fix strategy** — concrete recommendation
