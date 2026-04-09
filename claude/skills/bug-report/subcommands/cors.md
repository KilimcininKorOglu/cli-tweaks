---
name: cors
description: >-
  Detect CORS misconfiguration vulnerabilities using a two-phase approach:
  first find CORS configuration sites (middleware, response headers, framework
  options), then verify whether misconfigurations allow unauthorized cross-origin
  access. Use when asked to find CORS issues or cross-origin policy bugs.
---

# CORS Misconfiguration Detection

You are performing a focused security assessment to find CORS misconfiguration vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **discovery** (find all CORS configuration points) then **verify** (confirm whether configurations allow unauthorized cross-origin access or credential leakage).

---

## What is CORS Misconfiguration

Cross-Origin Resource Sharing (CORS) controls which external origins can access API responses in the browser. Misconfigured CORS policies can allow attacker-controlled websites to read sensitive data, perform authenticated actions, or bypass same-origin protections. The core pattern: *a CORS policy trusts an origin the application should not trust, especially when credentials are included.*

### What CORS Misconfiguration IS

- Reflecting the `Origin` header directly into `Access-Control-Allow-Origin` without validation
- Allowing wildcard `*` origin combined with `Access-Control-Allow-Credentials: true`
- Trusting `null` origin (exploitable via sandboxed iframes, `data:` URIs)
- Weak regex that matches attacker-controlled subdomains: `/\.example\.com$/` matches `evil-example.com`
- Overly permissive `Access-Control-Allow-Methods` or `Access-Control-Allow-Headers` on sensitive endpoints
- Dynamic origin check with substring matching instead of exact match: `origin.includes('example.com')`

### What CORS Misconfiguration is NOT

Do not flag these as CORS vulnerabilities:

- **Wildcard on public APIs**: `Access-Control-Allow-Origin: *` without credentials on intentionally public, non-sensitive endpoints
- **CORS on static assets/CDN**: Wildcard on images, fonts, CSS — standard practice
- **Development-only configuration**: `localhost` origins in clearly dev-scoped config files
- **API gateway CORS**: CORS configured at gateway level where application-level config is absent by design
- **Preflight-only headers**: `Access-Control-Allow-Methods` in preflight responses for safe methods (GET, POST with standard content types)

### Patterns That Prevent CORS Misuse

When you see these patterns, the code is likely **not vulnerable**:

**1. Strict origin allowlist**
```javascript
const ALLOWED_ORIGINS = ['https://app.example.com', 'https://admin.example.com'];
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('CORS not allowed'));
    }
  },
  credentials: true
}));
```

**2. Anchored regex with protocol check**
```javascript
origin: /^https:\/\/([a-z0-9-]+\.)?example\.com$/
```

**3. Framework-level strict config**
```python
# Django — explicit allowlist
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com",
]
CORS_ALLOW_CREDENTIALS = True
```

---

## Vulnerable vs. Secure Examples

### Node.js / Express — Reflected Origin

```javascript
// VULNERABLE: Reflects any origin with credentials
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin);
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  next();
});

// SECURE: Allowlist check
const ALLOWED = new Set(['https://app.example.com']);
app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (ALLOWED.has(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
  }
  next();
});
```

### Node.js / Express — cors middleware

```javascript
// VULNERABLE: Wildcard + credentials intent
app.use(cors({ origin: '*', credentials: true }));

// VULNERABLE: Boolean true reflects any origin
app.use(cors({ origin: true, credentials: true }));

// SECURE: Explicit list
app.use(cors({
  origin: ['https://app.example.com'],
  credentials: true
}));
```

### Python — Django (django-cors-headers)

```python
# VULNERABLE: Allow all origins with credentials
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# SECURE: Explicit allowlist
CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
CORS_ALLOW_CREDENTIALS = True
```

### Python — Flask (flask-cors)

```python
# VULNERABLE: Wildcard with supports_credentials
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# SECURE: Specific origins
CORS(app, resources={r"/api/*": {"origins": "https://app.example.com"}}, supports_credentials=True)
```

### Java — Spring

```java
// VULNERABLE: allowedOrigins("*") or allowedOriginPatterns("*") with allowCredentials
@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/api/**")
        .allowedOriginPatterns("*")
        .allowCredentials(true);
}

// SECURE: Explicit origins
@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/api/**")
        .allowedOrigins("https://app.example.com")
        .allowCredentials(true);
}
```

### Go — Manual CORS Headers

```go
// VULNERABLE: Reflects Origin header
func corsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", r.Header.Get("Origin"))
        w.Header().Set("Access-Control-Allow-Credentials", "true")
        next.ServeHTTP(w, r)
    })
}

// SECURE: Allowlist check
var allowedOrigins = map[string]bool{"https://app.example.com": true}
func corsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        origin := r.Header.Get("Origin")
        if allowedOrigins[origin] {
            w.Header().Set("Access-Control-Allow-Origin", origin)
            w.Header().Set("Access-Control-Allow-Credentials", "true")
        }
        next.ServeHTTP(w, r)
    })
}
```

### Regex Bypass

```javascript
// VULNERABLE: Unanchored regex — matches evil-example.com
origin: /\.example\.com$/

// VULNERABLE: Missing protocol — matches http://sub.example.com
origin: /^([a-z]+\.)?example\.com$/

// SECURE: Anchored with protocol
origin: /^https:\/\/([a-z0-9-]+\.)?example\.com$/
```

### Null Origin

```javascript
// VULNERABLE: Allows null origin (exploitable via sandboxed iframe)
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || origin === 'null') {
      callback(null, true);
    }
  },
  credentials: true
}));
```

---

## Execution

### Phase 1: Find CORS Configuration Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where CORS is configured — middleware setup, response header setting, framework CORS options, or manual `Access-Control-*` header manipulation. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the web framework, middleware stack, and API layer.
>
> **What to search for — CORS configuration patterns**:
>
> 1. **CORS middleware / library setup**:
>    - `cors(`, `CORS(`, `corsOptions`, `cors_allowed_origins`
>    - Framework CORS config: `CORS_ALLOW_ALL_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `addCorsMappings`, `@CrossOrigin`
>    - `flask-cors`, `django-cors-headers`, `rack-cors`, `rs/cors`
>
> 2. **Manual Access-Control header setting**:
>    - `Access-Control-Allow-Origin` — any response header set to a dynamic value
>    - `Access-Control-Allow-Credentials` — presence indicates credentials mode
>    - `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`
>
> 3. **Origin validation logic**:
>    - `req.headers.origin`, `request.headers.get('Origin')`, `r.Header.Get("Origin")`
>    - Regex matching origin, substring checks, `.includes()` / `.contains()` on origin
>    - Allowlist arrays/sets used in origin checks
>
> 4. **Wildcard or permissive patterns**:
>    - `origin: '*'`, `origin: true`, `allowedOrigins("*")`, `allowedOriginPatterns("*")`
>    - `null` in allowed origins list
>    - Dynamic reflection: setting Allow-Origin to the request Origin value
>
> **What to skip**:
> - Static asset CORS (fonts, images, CSS) that only serves public content
> - Test/mock configurations clearly scoped to test files
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # CORS Recon: [Project Name]
>
> ## Summary
> Found [N] CORS configuration sites.
>
> ## Configuration Sites
>
> ### 1. [Descriptive name — e.g., "Reflected origin in API middleware"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Framework / method**: [cors middleware / manual header / Spring @CrossOrigin / etc.]
> - **Configuration type**: [reflected origin / wildcard / regex / allowlist / null origin]
> - **Credentials enabled**: [yes / no / unknown]
> - **Affected routes**: [all routes / specific paths]
> - **Code snippet**:
>   ```
>   [the CORS configuration code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Confirm CORS Misconfigurations

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand which endpoints serve sensitive data, require authentication, or handle credentials.
>
> **For each CORS configuration site, verify whether it creates an exploitable misconfiguration**:
>
> 1. **Reflected origin**: Does the configuration set `Access-Control-Allow-Origin` to the request's `Origin` header without validation?
>    - Check if ANY origin check exists (allowlist, regex, domain comparison)
>    - Check if `Access-Control-Allow-Credentials: true` is set
>    - If reflected + credentials on sensitive endpoints → VULNERABLE
>
> 2. **Wildcard with credentials**: Is `origin: '*'` combined with `credentials: true`?
>    - Browsers block this combo, but it signals misconfigured intent
>    - Check if framework silently converts wildcard to reflected origin
>
> 3. **Null origin**: Does the configuration accept `Origin: null`?
>    - `null` origin exploitable via sandboxed iframes, `data:` URIs, file:// protocol
>    - Check if credentials are allowed with null origin
>
> 4. **Regex bypass**: Is origin validated with a regex?
>    - Test for: unanchored start (`/\.example\.com$/` matches `evil-example.com`)
>    - Missing protocol check (matches both http and https)
>    - Missing dot anchor (`/example\.com/` matches `notexample.com`)
>    - Backtracking or overly broad character classes
>
> 5. **Substring/contains check**: Is origin checked with `.includes()`, `.contains()`, `.indexOf()`, or `in` operator?
>    - `origin.includes('example.com')` matches `example.com.evil.com`
>
> 6. **Scope assessment**: What endpoints does the CORS policy cover?
>    - Sensitive endpoints (auth, user data, admin) → higher severity
>    - Public-only endpoints → lower severity or not vulnerable
>
> **Classification**:
> - **Vulnerable**: CORS policy demonstrably allows attacker-controlled origins to access sensitive endpoints with credentials.
> - **Likely Vulnerable**: Weak validation (regex bypass, substring check) or reflected origin without clear allowlist.
> - **Not Vulnerable**: Strict allowlist, properly anchored regex, or only public non-sensitive endpoints affected.
> - **Needs Manual Review**: Cannot determine endpoint sensitivity or full CORS middleware chain.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # CORS Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / scope**: [route or middleware scope]
> - **Issue**: [e.g., "Origin header reflected into Access-Control-Allow-Origin with credentials on /api/user endpoint"]
> - **Misconfiguration type**: [reflected origin / null origin / regex bypass / wildcard+credentials]
> - **Impact**: Attacker website can read authenticated API responses, steal user data, perform CSRF-like actions
> - **Remediation**: Implement strict origin allowlist. Remove `null` from allowed origins. Anchor regex with protocol.
> - **Dynamic test**: `curl -H "Origin: https://evil.com" -v https://target.com/api/user` — check if response includes `Access-Control-Allow-Origin: https://evil.com`
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Reflected origin + credentials on auth/user-data endpoint → CRITICAL
> - Null origin or regex bypass + credentials → HIGH
> - Wildcard on non-credential endpoints with sensitive data → MEDIUM
> - Overly permissive methods/headers on non-sensitive endpoints → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full misconfiguration details and a dynamic test command
   - Separate each field with a blank line; end each entry with a `---` separator
4. Append the completion marker: `<!-- scan:cors completed -->`
5. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all CORS configuration points regardless of whether they are secure. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each configuration site, determine whether it creates an exploitable policy.
- Reflected origin is the most dangerous pattern — it turns CORS into an open door for any website when combined with credentials.
- `null` origin is frequently overlooked. It is exploitable from sandboxed iframes, `data:` URIs, cross-scheme redirects, and file:// protocol.
- Regex-based origin checks are error-prone. Test every regex for anchor issues, protocol omission, and subdomain bypasses.
- Substring/contains checks on origin strings are almost always bypassable by registering a domain containing the target string.
- CORS misconfigurations on public, non-sensitive endpoints are generally low risk. Focus on endpoints that return user-specific or authenticated data.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
