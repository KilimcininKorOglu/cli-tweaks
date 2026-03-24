---
name: session-audit
description: >
  This skill MUST be invoked when the user says "session audit", "oturum güvenliği",
  "session management", "oturum yönetimi", "CSRF audit", "cookie security"
  or any variation requesting session management and state persistence analysis.
  SHOULD also invoke when user mentions "session fixation", "JWT security",
  "CORS audit", "cookie flags", "SameSite", or asks to audit authentication
  state handling. Reviews session lifecycle, storage, cookies, client-side state,
  and CSRF/CORS protection for security vulnerabilities.
---

# Session Management & State Persistence Deep Analysis

You are a security and architecture specialist reviewing session management and application state persistence mechanisms. Session management flaws directly lead to account takeover, data leakage, and privilege escalation.

## 1. Session Lifecycle

- How is the session ID generated? Is there sufficient entropy? (at least 128 bits of randomness, cryptographic PRNG)
- Is the session ID regenerated after authentication? (session fixation protection)
- Is there session expiration? Are absolute timeout and idle timeout managed separately?
- When the user logs out, is the session completely destroyed server-side? (just deleting the cookie is insufficient)
- On password change/reset, are all active sessions terminated?
- Is there a concurrent session limit? (how many devices can the same account be logged into)
- Is "remember me" functionality secure? (separate token, hashed in database, single-use rotation)

## 2. Session Storage

- Where is session data stored? (server memory, file system, database, Redis, JWT)
- Server-side storage: Is it scalable? Can it be shared across multiple server instances?
- If JWT is used:
  * Is there an algorithm "none" or "HS256 with public key" vulnerability?
  * Is token size reasonable? (putting too much data in JWT wastes bandwidth on every request)
  * Is there a token revocation mechanism? (JWT cannot be revoked by default — needs blocklist/short lifetime)
  * Is sensitive data in the JWT payload? (JWT is not encrypted, only signed — anyone can read it)
- Is session data encrypted? (mandatory especially for cookie-based sessions)

## 3. Cookies and Client-Side State

- Does the session cookie have the `HttpOnly` flag? (prevents JavaScript access — XSS protection)
- Is the `Secure` flag set? (sent only over HTTPS)
- Is the `SameSite` attribute set? (`Lax` or `Strict` — CSRF protection)
- Is cookie `Domain` and `Path` scope correct? (too broad = subdomain attack)
- Is there sensitive data in client-side `localStorage`/`sessionStorage`? (accessible via XSS)
- Is client-side state (React state, Vuex, Redux) used for security decisions? (client-side is never trustworthy)

## 4. CSRF and Cross-Origin Protection

- Is there a CSRF token for every state-changing operation?
- Is the CSRF token tied to the session? (cannot be stolen across users)
- Is the CSRF token single-use or session-based? (document the trade-off)
- What is the CSRF strategy for SPA (single page applications)? (custom header, double submit cookie)
- Is CORS configuration correct? (`Access-Control-Allow-Origin: *` is dangerous)
- Is `Access-Control-Allow-Credentials: true` used with wildcard origin? (CRITICAL vulnerability)

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
