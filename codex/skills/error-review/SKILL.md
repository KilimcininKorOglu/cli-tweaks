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
