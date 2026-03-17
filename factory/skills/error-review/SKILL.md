---
name: error-review
description: >
  This skill MUST be invoked when the user says "error review", "hata mesajları",
  "error message audit", "information disclosure", "bilgi sızıntısı", "error UX"
  or any variation requesting error message and user feedback review. SHOULD also
  invoke when user mentions "stack trace leak", "error codes", "hata kodları",
  "error pages", "fallback states", or asks to audit error handling quality.
  Reviews all error messages for information disclosure risks, UX quality,
  error code consistency, and failure page completeness.
argument-hint: "[--focus disclosure|ux|codes|fallback|all]"
---

# Error Message & User Feedback System Review

You are a security and UX specialist reviewing the application's error messages, user feedback mechanisms, and information disclosure risks. Error messages are a double-edged sword: too little information frustrates users, too much gives attackers a roadmap.

## 1. Information Disclosure

Review every error response:

- Do HTTP error responses leak stack traces?
- Do error messages reveal database table/column names, SQL queries?
- Are file paths, server names, IP addresses disclosed?
- Are framework/library version numbers disclosed? (helps attackers search for CVEs)
- Do authentication errors give away too much? ("user not found" vs "wrong password" — reveals which exists)
- Do authorization errors disclose resource existence? (403 vs 404 — 403 tells resource exists)
- Do rate limit responses reveal remaining attempts or reset time? (facilitates brute force calculation)
- Can debug mode be enabled in production? (`?debug=true`, special header, cookie)
- Do API responses leak internal service names, microservice topology?

## 2. Error Message Quality

From user perspective:

- Do error messages help users understand the problem? (human language, not technical jargon)
- Do error messages tell users what to do next? (not just "an error occurred")
- Do form validation errors show which field is wrong and why?
- Are validation errors shown collectively? (showing one at a time frustrates users)
- Are error messages localized? (hardcoded English messages are a problem in international applications)
- Is there user-friendly feedback for network errors? ("check your connection" vs technical error code)
- Is there progress indication and cancel option for long-running operations?

## 3. Error Code System

- Is there a consistent error code system? (machine-readable: `AUTH_001`, `VALIDATION_002`)
- Are error codes documented? (developer portal, API documentation)
- Can client applications behave differently based on error codes?
- Is the error response schema consistent? (does every endpoint use the same error format)
- Do error responses include a request ID? (for support team to find the issue)

## 4. Failure Pages and Fallback States

- Are there custom 404, 500, 503 pages? (default framework error page leaks information)
- Is there a maintenance mode page? With correct HTTP status code (503) and `Retry-After` header?
- Are JavaScript errors caught and reported? (window.onerror, React Error Boundary)
- Is there graceful feedback when third-party services fail? (what does the user see when payment service is down)
- When rate limit is exceeded, is there a meaningful message and wait time shown to the user?

## Output Format

For each finding produce:

1. **File:line** — exact location in codebase
2. **Current error output** — what is currently shown
3. **Risk/UX impact** — security risk or user experience problem
4. **Corrected version** — the improved error message or handling
