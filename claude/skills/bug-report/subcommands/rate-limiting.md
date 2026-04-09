---
name: rate-limiting
description: >-
  Detect missing rate limiting and application-level DoS vectors using a
  three-phase approach: find rate-limit-sensitive endpoints and patterns,
  verify missing protections (auth brute force, ReDoS, unbounded pagination),
  then merge confirmed findings. Use when asked to audit rate limiting or DoS vectors.
---

# Rate Limiting Audit

You are performing a focused security assessment to find missing rate limiting and application-level denial-of-service vectors in a codebase. This skill uses a three-phase approach with subagents: **discovery** (find all rate-limit-sensitive endpoints and patterns) then **verify** (confirm whether protections are missing) then **merge** (write confirmed findings).

---

## What is Missing Rate Limiting

Rate limiting controls how frequently a client can perform an operation. Missing rate limits allow attackers to brute-force credentials, exhaust server resources, or abuse expensive operations without throttling. The core pattern: *a sensitive or resource-intensive endpoint accepts unlimited requests without any frequency control.*

### What Missing Rate Limiting IS

- Authentication endpoints (login, password reset, OTP) without request throttling
- Payment/financial endpoints without rate limits
- API endpoints without per-client request caps
- ReDoS-vulnerable regex patterns that cause exponential backtracking
- Unbounded pagination (`?limit=999999` returning entire database)
- Missing request body size limits (accepting multi-GB JSON payloads)
- Email/SMS sending endpoints without throttling
- File upload endpoints without size or frequency limits
- GraphQL queries without depth/complexity limits

### What Missing Rate Limiting is NOT

Do not flag these:

- **Infrastructure-level rate limiting**: Rate limits at API gateway, CDN, WAF, or load balancer level
- **Internal/admin endpoints**: Internal tools accessible only via VPN with network-level controls
- **Background job queues**: Jobs processed at controlled throughput by design
- **Read-only public endpoints**: Public data endpoints where abuse has minimal impact
- **Webhooks with signature verification**: Incoming webhooks validated by HMAC signature

### Patterns That Prevent Rate Limiting Abuse

When you see these patterns, the code is likely **not vulnerable**:

**1. Rate limit middleware on auth routes**
```javascript
const rateLimit = require('express-rate-limit');
const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 5 });
app.use('/api/auth', authLimiter);
```

**2. Framework-level throttling**
```python
# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': '100/hour'}
}
```

**3. Bounded pagination**
```javascript
const limit = Math.min(parseInt(req.query.limit) || 10, 100);
```

---

## Vulnerable vs. Secure Examples

### Authentication — No Rate Limit

```javascript
// VULNERABLE: Unlimited login attempts
app.post('/api/auth/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findOne({ email });
  if (!user || !await bcrypt.compare(password, user.password)) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  res.json({ token: generateToken(user) });
});

// SECURE: Rate limited
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: 'Too many login attempts'
});
app.post('/api/auth/login', loginLimiter, async (req, res) => {
  // ... same logic
});
```

### ReDoS — Catastrophic Backtracking

```javascript
// VULNERABLE: Exponential backtracking on malicious input
const emailRegex = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;
// Input: "aaaaaaaaaaaaaaaaaaaaaaaa!" causes CPU hang

// SECURE: Use validator library or non-backtracking regex
const { isEmail } = require('validator');
if (!isEmail(req.body.email)) return res.status(400).send('Invalid email');
```

### Pagination — Unbounded Limit

```javascript
// VULNERABLE: No upper bound — client can request all records
app.get('/api/users', async (req, res) => {
  const limit = parseInt(req.query.limit) || 10;
  const users = await User.find().limit(limit);
  res.json(users);
});

// SECURE: Cap the limit
app.get('/api/users', async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit) || 10, 100);
  const users = await User.find().limit(limit);
  res.json(users);
});
```

### Request Body Size — Unbounded

```javascript
// VULNERABLE: Default body limit or none set
app.use(express.json());  // Default 100kb but should be explicit

// SECURE: Explicit limit
app.use(express.json({ limit: '1mb' }));
```

### Python — Django/Flask

```python
# VULNERABLE: No throttle on password reset
@api_view(['POST'])
def password_reset(request):
    email = request.data.get('email')
    send_reset_email(email)
    return Response({'status': 'ok'})

# SECURE: Throttled
@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
def password_reset(request):
    email = request.data.get('email')
    send_reset_email(email)
    return Response({'status': 'ok'})
```

### Go — No Rate Limit on API

```go
// VULNERABLE: No rate limiting
http.HandleFunc("/api/search", func(w http.ResponseWriter, r *http.Request) {
    query := r.URL.Query().Get("q")
    results := expensiveSearch(query)
    json.NewEncoder(w).Encode(results)
})

// SECURE: Rate limited with middleware
limiter := rate.NewLimiter(rate.Every(time.Second), 10)
http.HandleFunc("/api/search", rateLimitMiddleware(limiter, func(w http.ResponseWriter, r *http.Request) {
    query := r.URL.Query().Get("q")
    results := expensiveSearch(query)
    json.NewEncoder(w).Encode(results)
}))
```

---

## Execution

### Phase 1: Find Rate-Limit-Sensitive Endpoints

Launch a subagent with the following instructions:

> **Goal**: Find every rate-limit-sensitive endpoint and DoS-prone pattern in the codebase — authentication routes, payment endpoints, search/query handlers, email senders, file upload handlers, regex usage, and pagination logic. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the web framework, middleware stack, and API layer.
>
> **What to search for — rate-limit-sensitive patterns**:
>
> 1. **Authentication endpoints**:
>    - Login, signup, password reset, OTP/verification, token refresh
>    - Search for: `login`, `signin`, `sign-in`, `authenticate`, `password`, `reset`, `verify`, `otp`, `register`
>
> 2. **Existing rate limit configuration**:
>    - `rateLimit`, `rate_limit`, `throttle`, `RateLimiter`, `express-rate-limit`
>    - `slowapi`, `throttle_classes`, `@Throttle`, `bucket`, `sliding_window`
>    - Note which endpoints are covered and which are not
>
> 3. **Expensive operations without throttling**:
>    - Search/query endpoints, report generation, export endpoints
>    - Email/SMS sending functions
>    - File upload handlers
>    - API key generation or token creation
>
> 4. **ReDoS-prone patterns**:
>    - Regex with nested quantifiers: `(a+)+`, `(a|b)*c`, `(a*)*`
>    - User input passed directly to `new RegExp()`, `re.compile()`, `regexp.Compile()`
>    - Email/URL validation regex with backtracking potential
>
> 5. **Pagination and query controls**:
>    - `limit`, `offset`, `page`, `pageSize`, `per_page` parameters
>    - Whether upper bounds are enforced
>    - GraphQL `first`/`last` arguments without limits
>
> 6. **Request body size configuration**:
>    - `express.json()`, `bodyParser.json()` — check for explicit `limit` option
>    - Framework body size configuration
>
> **What to skip**:
> - Internal health check endpoints
> - Static file serving
> - Test/mock endpoints
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Rate Limiting Recon: [Project Name]
>
> ## Summary
> Found [N] rate-limit-sensitive sites. Existing rate limiting: [description].
>
> ## Sensitive Sites
>
> ### 1. [Descriptive name — e.g., "Login endpoint without rate limiting"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Type**: [auth endpoint / payment / search / email / upload / regex / pagination]
> - **Current rate limiting**: [none / partial / present]
> - **Sensitivity**: [credential brute force / resource exhaustion / ReDoS / data dump]
> - **Code snippet**:
>   ```
>   [the endpoint or pattern code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Confirm Missing Rate Limits

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand which endpoints are public-facing and which are internal.
>
> **For each sensitive site, verify whether rate limiting is missing or insufficient**:
>
> 1. **Auth endpoint without rate limit**: Is there any throttling on login/password reset/OTP?
>    - Trace the full middleware chain — rate limiting might be applied globally or at router level
>    - Check for account lockout mechanisms as alternative protection
>    - If no rate limit AND no lockout on auth endpoint → VULNERABLE
>
> 2. **ReDoS pattern**: Does the regex have catastrophic backtracking potential?
>    - Nested quantifiers: `(a+)+`, `(a*)*`, `(a|b)*`
>    - Overlapping alternatives: `(a|a)*`
>    - User input as regex source: `new RegExp(userInput)`
>    - If exploitable backtracking + user-controlled input → VULNERABLE
>
> 3. **Unbounded pagination**: Can clients request unlimited records?
>    - Check if `limit`/`pageSize` has an upper bound (`Math.min`, `min()`, clamp)
>    - Check if default limit is reasonable
>    - If no upper bound on client-supplied limit → LIKELY VULNERABLE
>
> 4. **Missing body size limit**: Is request body size unconstrained?
>    - Check middleware configuration for explicit body size limits
>    - If no explicit limit on JSON/multipart body → LIKELY VULNERABLE
>
> 5. **Expensive operations**: Are resource-intensive endpoints throttled?
>    - Search, export, report generation, email sending
>    - If no rate limit on expensive public endpoint → LIKELY VULNERABLE
>
> 6. **Infrastructure check**: Is rate limiting handled at a different layer?
>    - Check for nginx rate limiting config, API gateway config, WAF rules
>    - If infrastructure-level rate limiting exists → NOT VULNERABLE (note in findings)
>
> **Classification**:
> - **Vulnerable**: Confirmed missing rate limit on sensitive endpoint with clear exploit path (auth brute force, ReDoS).
> - **Likely Vulnerable**: Missing rate limit on expensive operation or unbounded pagination without infrastructure-level protection.
> - **Not Vulnerable**: Rate limiting present at application or infrastructure level, or endpoint is internal-only.
> - **Needs Manual Review**: Rate limiting may exist at infrastructure level but cannot be confirmed from codebase alone.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Rate Limiting Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / scope**: [route or function]
> - **Issue**: [e.g., "Login endpoint accepts unlimited authentication attempts without rate limiting or account lockout"]
> - **Missing protection**: [rate limit / body size limit / pagination cap / regex safety]
> - **Impact**: Credential brute force, denial of service, resource exhaustion, data exfiltration via unbounded queries
> - **Remediation**: Add rate limiting middleware, cap pagination limits, use validator library for regex, set explicit body size limits
> - **Dynamic test**: [e.g., "Send 100 rapid POST requests to /api/auth/login — all should succeed without throttling"]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - ReDoS causing server hang on user-controlled input → CRITICAL
> - Missing rate limit on auth endpoint allowing brute force → CRITICAL
> - Missing rate limit on payment/financial operations → HIGH
> - Unbounded pagination exposing full database → HIGH
> - Missing rate limit on email/SMS sending → MEDIUM
> - Missing body size limit → MEDIUM
> - Missing rate limit on non-critical public endpoint → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full details and a dynamic test command
   - Separate each field with a blank line; end each entry with a `---` separator
4. Append the completion marker: `<!-- scan:rate-limiting completed -->`
5. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all rate-limit-sensitive endpoints regardless of whether they are protected. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each endpoint, determine whether rate limiting is missing or insufficient.
- Authentication endpoints without rate limiting are the highest priority — they enable credential brute force attacks that can compromise any account.
- ReDoS is often overlooked. A single malicious input string can hang a server process for minutes. Look for nested quantifiers and overlapping alternatives in regex patterns.
- Pagination without upper bounds is a data exfiltration vector. `?limit=999999` can dump an entire database table in a single request.
- Rate limiting at infrastructure level (API gateway, nginx, CDN) counts as protection. If you see evidence of infrastructure-level rate limiting, do not flag application-level absence.
- Missing body size limits allow memory exhaustion attacks. Sending a multi-GB JSON payload can crash a Node.js process.
- Account lockout is an alternative to rate limiting for auth endpoints. If lockout exists after N failed attempts, rate limiting is less critical.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
