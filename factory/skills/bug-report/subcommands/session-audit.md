# Session Management, JWT & State Persistence Security

This subcommand replaces the old standalone `/session-audit` skill.

## Command

```bash
/bug-report session-audit [--focus lifecycle|storage|cookies|csrf|jwt|all]
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
- If JWT is used:
  * Is there an algorithm "none" or "HS256 with public key" vulnerability?
  * Is there a token revocation mechanism? (JWT cannot be revoked by default — needs blocklist/short lifetime)
  * Is token size reasonable? (too much data in JWT wastes bandwidth on every request)
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



## 5. JWT Deep Scan

If the application uses JWTs, run an automated two-phase code-level scan for JWT vulnerabilities.

### What JWT Vulnerabilities Are

- **alg:none** — token header declares `"alg": "none"`, server skips signature verification
- **RS256→HS256 confusion** — server configured for RS256 accepts HS256 tokens signed with the public key
- **Signature verification disabled** — `jwt.decode()` instead of `jwt.verify()`, or `verify_signature: False`
- **Weak/hardcoded HMAC secret** — short, guessable, or hardcoded secret brute-forceable with `hashcat`/`jwt_tool`
- **Embedded JWK injection** — server trusts `jwk` header in the token to verify the same token
- **JKU/X5U header injection** — key URL in token header fetched without allowlist validation
- **kid header injection** — `kid` interpolated into SQL query (SQLi) or file path (path traversal)
- **Missing claim validation** — `exp`, `iss`, `aud`, `nbf` not checked

### Phase 1: Map the JWT Lifecycle

Launch a subagent with the following instructions:

> **Goal**: Map every JWT issuance and verification site, the library used, the signing algorithm and key configuration, and which claims are used for authorization. Return findings in your response.
>
> **What to search for**:
>
> **JWT library imports**: Python: `import jwt`, `from jose import`; Node.js: `require('jsonwebtoken')`, `jose`; Java: `io.jsonwebtoken`, `com.auth0.jwt`; Go: `golang-jwt/jwt`; Ruby: `require 'jwt'`; PHP: `firebase/php-jwt`; C#: `System.IdentityModel.Tokens.Jwt`
>
> **Issuance sites**: `jwt.encode(...)`, `jwt.sign(...)`, `Jwts.builder().signWith(...)`, `JWT.create().sign(...)` — note algorithm and secret/key source
>
> **Verification sites**: `jwt.decode(...)`, `jwt.verify(...)`, `Jwts.parserBuilder()...parseClaimsJws(...)` — note options, algorithm restriction, claims validated
>
> **Signing secret/key**: where defined (env var, config, hardcoded), apparent strength
>
> **kid/jwk/jku usage**: any header injection vectors
>
> **Output format** — return findings in your response:
>
> ```markdown
> # JWT Recon: [Project Name]
> JWT is [used / not used]. Library: [name]. Algorithm(s): [alg].
>
> ## Issuance Sites
> ### 1. [name] — File: path:lines — Algorithm: X — Secret: env/hardcoded/config
>
> ## Verification Sites
> ### 1. [name] — File: path:lines — Call: jwt.verify/decode — alg restricted: yes/no — sig verified: yes/no — claims: exp/iss/aud/none
>
> ## Secret Configuration
> Source: env/hardcoded — Strength: strong/weak/unknown
> ```

If no JWT usage is found, skip Phase 2 and write nothing to BUG-REPORT.md for this section.

### Phase 2: Analyze Verification Sites for Vulnerabilities

Launch a second subagent **after Phase 1 completes**, providing Phase 1 findings as context. Instructions:

> **For each verification site, check**:
>
> 1. **Algorithm restriction** — is allowed algorithm explicitly specified? Can `alg: none` bypass verification? Can RS256→HS256 confusion be used?
> 2. **Signature verification** — is `jwt.decode()` (no-verify) used instead of `jwt.verify()`? Is `verify_signature: False` set?
> 3. **HMAC secret strength** — hardcoded? Short/dictionary word? Brute-forceable?
> 4. **Embedded JWK/JKU/X5U injection** — does verification code trust key material from the token header?
> 5. **kid injection** — is `kid` interpolated into SQL or file path unsanitized?
> 6. **Claim validation** — is `exp` checked? `iss`? `aud`? Are `role`/`permissions` claims trusted without server-side verification?
> 7. **Token revocation** — no blacklist or short-lived token+refresh pattern for long-lived tokens?
>
> **Output format** — write confirmed findings to `BUG-REPORT.md` using the shared report format from `../SKILL.md`.
>
> **Severity mapping**:
> - alg:none / algorithm confusion / signature disabled → CRITICAL
> - Weak/hardcoded secret / JWK injection → HIGH
> - Missing claim validation (exp/iss/aud) → HIGH
> - No revocation for long-lived tokens → MEDIUM
>
> Do **NOT** write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

### JWT Important Reminders

- `jwt.decode()` in Node.js jsonwebtoken is decode-only — never verifies. Only `jwt.verify()` validates signatures.
- PyJWT < 2.0 accepted `alg: none` by default. Check library version.
- RS256→HS256 confusion requires: RS256 server + accessible public key + no algorithm restriction.
- Always check `kid` header lookup implementation for injection vectors.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
