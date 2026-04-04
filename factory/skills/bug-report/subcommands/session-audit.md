# Session Management & State Persistence Deep Analysis

This subcommand replaces the old standalone `/session-audit` skill.

## Command

```bash
/bug-report session-audit [--focus lifecycle|storage|cookies|csrf|all]
```

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
- If JWT is used: run `/bug-report jwt` for deep code-level scanning (algorithm confusion, signature bypass, weak secrets, missing claim validation). Basic check: is sensitive data in the JWT payload? (JWT is not encrypted, only signed)
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



## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
