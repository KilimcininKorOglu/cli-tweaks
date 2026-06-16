---
name: data-exposure
description: >-
  Detect sensitive data exposure vulnerabilities using a two-phase approach:
  first find data exposure sites (PII in logs, debug mode, stack traces in
  responses, source maps, .env files, verbose errors), then verify actual
  exposure risk. Use when asked to find data leaks or information disclosure bugs.
---

# Sensitive Data Exposure Detection

You are performing a focused security assessment to find sensitive data exposure vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **discovery** (find all places where sensitive data might be exposed) then **verify** (confirm whether the exposure is real, reachable, and impactful).

---

## What is Sensitive Data Exposure

Sensitive data exposure occurs when an application unintentionally reveals confidential information through logs, error messages, API responses, debug modes, or misconfigured file serving. This includes PII (emails, SSNs, credit cards), credentials (passwords, tokens, API keys), internal system details (stack traces, SQL queries, server paths), and source code (source maps, .git directories). The core pattern: *sensitive data crosses an application boundary it should not cross.*

### What Sensitive Data Exposure IS

- PII logged without redaction: `logger.info(f"User login: email={email}, password={password}")`
- Stack traces returned in HTTP responses: `res.status(500).json({ error: err.stack })`
- Debug mode enabled in production config: `DEBUG = True`, `NODE_ENV=development` in production
- Source maps served in production: `//# sourceMappingURL=app.js.map` accessible publicly
- Verbose error messages revealing internals: database queries, file paths, library versions
- `.env` files accessible via web server: `/.env` returning secrets
- API responses with excessive data: full user object including password hash, internal IDs
- Sensitive data in URL query parameters: `?token=abc123&password=secret` (logged in server access logs, browser history, referrer headers)

### What Sensitive Data Exposure is NOT

Do not flag these:

- **Structured logging with redaction**: Logger configured to mask sensitive fields automatically
- **Development-only debug config**: `DEBUG = True` in clearly dev-scoped settings file with production override
- **Error logging to internal systems**: `console.error(err.stack)` to server logs (not to client)
- **Intentional public data**: API returning user's own profile data that is meant to be public
- **Test data in test files**: Fake emails, passwords, and tokens in test fixtures
- **Source maps in dev/staging only**: Build config that strips source maps from production builds

### Patterns That Prevent Data Exposure

When you see these patterns, the code is likely **not vulnerable**:

**1. Environment-aware debug mode**
```python
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
# Production env sets DEBUG=False
```

**2. Error handler with production guard**
```javascript
app.use((err, req, res, next) => {
  console.error(err.stack); // Internal log only
  const message = process.env.NODE_ENV === 'production'
    ? 'Internal server error'
    : err.message;
  res.status(500).json({ error: message });
});
```

**3. Structured logging with field redaction**
```python
class SensitiveFilter(logging.Filter):
    SENSITIVE_FIELDS = {'password', 'token', 'ssn', 'credit_card'}
    def filter(self, record):
        # Redact sensitive fields before logging
        ...
```

**4. API response serialization with field selection**
```javascript
const user = await User.findById(id).select('name email avatar -_id');
res.json(user); // Only selected fields returned
```

---

## Vulnerable vs. Secure Examples

### PII in Logs

```python
# VULNERABLE: Logging raw credentials
logger.info(f"User login: email={email}, password={password}")
logger.debug(f"Payment: card={card_number}, cvv={cvv}")

# SECURE: Redacted logging
logger.info(f"User login: email={mask_email(email)}")
logger.debug(f"Payment: card=****{card_number[-4:]}")
```

```javascript
// VULNERABLE: Logging full request body (may contain passwords)
app.use((req, res, next) => {
  console.log('Request:', JSON.stringify(req.body));
  next();
});

// SECURE: Sanitize before logging
const sanitize = (obj) => {
  const copy = { ...obj };
  ['password', 'token', 'secret'].forEach(k => { if (copy[k]) copy[k] = '***'; });
  return copy;
};
app.use((req, res, next) => {
  console.log('Request:', JSON.stringify(sanitize(req.body)));
  next();
});
```

### Stack Traces in Responses

```javascript
// VULNERABLE: Raw error sent to client
app.use((err, req, res, next) => {
  res.status(500).json({
    error: err.message,
    stack: err.stack,
    query: err.sql  // Exposes SQL query
  });
});

// SECURE: Generic error in production
app.use((err, req, res, next) => {
  console.error(err); // Internal log
  res.status(500).json({ error: 'Internal server error' });
});
```

### Debug Mode in Production

```python
# VULNERABLE: Django debug mode unconditionally on
# settings.py
DEBUG = True  # Exposes stack traces, SQL queries, template context, installed apps

# SECURE: Environment-controlled
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
```

```javascript
// VULNERABLE: Express detailed errors always on
app.use(express.errorHandler({ showStack: true, dumpExceptions: true }));

// SECURE: Only in development
if (app.get('env') === 'development') {
  app.use(express.errorHandler({ showStack: true, dumpExceptions: true }));
}
```

### Excessive API Response Data

```javascript
// VULNERABLE: Full user object including sensitive fields
app.get('/api/users/:id', async (req, res) => {
  const user = await User.findById(req.params.id);
  res.json(user); // Includes passwordHash, resetToken, internalFlags
});

// SECURE: Select only needed fields
app.get('/api/users/:id', async (req, res) => {
  const user = await User.findById(req.params.id)
    .select('name email avatar createdAt');
  res.json(user);
});
```

### Sensitive Data in URLs

```javascript
// VULNERABLE: Token in URL query string
app.get('/verify', (req, res) => {
  const token = req.query.token; // Logged in access logs, visible in referrer
  verifyEmail(token);
});

// SECURE: Token in POST body or header
app.post('/verify', (req, res) => {
  const token = req.body.token; // Not in URL
  verifyEmail(token);
});
```

### Source Maps in Production

```javascript
// VULNERABLE: webpack config serving source maps in production
module.exports = {
  mode: 'production',
  devtool: 'source-map'  // Generates .map files exposing original source
};

// SECURE: No source maps or hidden source maps
module.exports = {
  mode: 'production',
  devtool: false  // No source maps in production
};
```

---

## Execution

### Phase 1: Find Data Exposure Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where sensitive data might be exposed — through logs, error responses, debug config, API responses, URL parameters, or served files. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the web framework, logging setup, error handling, API response patterns, and build configuration.
>
> **What to search for — data exposure patterns**:
>
> 1. **PII in log statements**:
>    - `logger.*password`, `log.*email`, `console.log.*token`, `print.*secret`
>    - Full request body logging: `console.log(req.body)`, `logger.info(request.data)`
>    - PII regex patterns in log strings: credit card (`\d{13,19}`), SSN (`\d{3}-\d{2}-\d{4}`), email patterns
>
> 2. **Stack traces / verbose errors in responses**:
>    - `res.json({ error: err.stack })`, `res.send(err.message)`, `res.status(500).send(err)`
>    - `traceback.format_exc()` returned to client, `e.getMessage()` in response
>    - `e.printStackTrace()` in servlet response, `render json: { error: e.backtrace }`
>
> 3. **Debug mode configuration**:
>    - `DEBUG = True`, `debug: true`, `APP_DEBUG=true`
>    - `NODE_ENV` not set to `production` in startup/config
>    - `FLASK_DEBUG=1`, `RAILS_ENV=development` in non-dev config
>    - `phpinfo()` calls, `server_info` exposure
>
> 4. **Excessive API response data**:
>    - ORM queries without `.select()` / `.only()` returning full objects
>    - User objects returned with password hashes, tokens, internal IDs
>    - Error responses including SQL queries, internal paths
>
> 5. **Sensitive data in URLs**:
>    - Query parameters named `token`, `password`, `secret`, `api_key`, `access_token`, `session`
>    - GET endpoints receiving credentials
>
> 6. **File exposure**:
>    - Source maps in production build config: `devtool: 'source-map'`
>    - `.env` files in static/public directories
>    - `.git` directory accessible via web server
>    - Backup files (`*.bak`, `*.sql`, `*.dump`) in web root
>
> 7. **Missing security headers**:
>    - `X-Powered-By` header revealing framework/version
>    - Missing `X-Content-Type-Options`, `X-Frame-Options` (note: lower severity)
>
> **What to skip**:
> - Logging to internal-only monitoring systems with proper access control
> - Test/development configuration clearly scoped by environment
> - Intentionally public data in API responses
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Data Exposure Recon: [Project Name]
>
> ## Summary
> Found [N] potential data exposure sites.
>
> ## Exposure Sites
>
> ### 1. [Descriptive name — e.g., "Password logged in auth controller"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or route]
> - **Exposure type**: [PII in logs / stack trace in response / debug mode / excessive API data / URL leak / file exposure]
> - **Sensitive data**: [what data is exposed — password, email, stack trace, etc.]
> - **Channel**: [log output / HTTP response / URL / served file]
> - **Code snippet**:
>   ```
>   [the data exposure code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Confirm Actual Exposure

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand deployment environment, logging infrastructure, and production/development separation.
>
> **For each exposure site, verify whether the data actually reaches an unintended recipient**:
>
> 1. **Environment check**: Is this code active in production?
>    - Is there an environment guard (`if NODE_ENV === 'production'`)?
>    - Is the config file scoped to development only?
>    - Is debug mode controlled by environment variable?
>
> 2. **Reachability check**: Can an external party trigger and observe the exposure?
>    - Log exposure: Who has access to logs? (If only internal ops team → lower risk)
>    - Response exposure: Is the endpoint publicly accessible?
>    - File exposure: Is the file in a web-served directory?
>
> 3. **Data sensitivity check**: How sensitive is the exposed data?
>    - Credentials (passwords, tokens, API keys) → CRITICAL
>    - PII (email, SSN, credit card) → HIGH
>    - Internal architecture (stack traces, paths, SQL) → MEDIUM
>    - Framework version, server headers → LOW
>
> 4. **Redaction check**: Is there a redaction/masking layer between the data and the exposure point?
>    - Logging middleware that strips sensitive fields
>    - Serialization layer that excludes fields
>    - Error handler that sanitizes before responding
>
> **Classification**:
> - **Vulnerable**: Sensitive data demonstrably reaches an external-facing channel in production with no redaction.
> - **Likely Vulnerable**: Exposure exists but cannot confirm production reachability, or weak redaction is present.
> - **Not Vulnerable**: Proper environment guards, redaction, or internal-only exposure with access control.
> - **Needs Manual Review**: Cannot determine deployment configuration or log access controls.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Data Exposure Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / function**: [route or function name]
> - **Issue**: [e.g., "Stack trace with SQL query returned in 500 error response with no production guard"]
> - **Data exposed**: [what specific data leaks]
> - **Impact**: Credential theft, PII breach, attack surface mapping
> - **Remediation**: Add production error handler, redact sensitive fields from logs, disable debug mode
> - **Dynamic test**: `curl -v https://target.com/api/nonexistent` — check if response includes stack trace
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Credentials in logs/responses in production → CRITICAL
> - PII exposure, debug mode in production → HIGH
> - Stack traces, verbose errors, source maps → MEDIUM
> - Server version headers, minor info disclosure → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include what data is exposed and through which channel, plus a dynamic test
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all sites where sensitive data might be exposed, regardless of whether protections exist. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each site, check environment guards, reachability, data sensitivity, and redaction.
- The most common data exposure is **stack traces in error responses** — many frameworks send detailed errors by default and developers forget to add production error handlers.
- PII in logs is often overlooked because developers add logging during debugging and forget to remove it. Check all `console.log`, `logger.info`, `print` statements near authentication, payment, and user management code.
- Debug mode in production is a classic misconfiguration. Django `DEBUG = True` exposes full stack traces, SQL queries, template context, and installed apps to any visitor.
- Source maps are frequently deployed to production accidentally. Check webpack/vite/rollup config for production build settings.
- `.env` files in web-accessible directories is a critical finding — it exposes all environment secrets.
- API responses that return full ORM objects often include fields like `passwordHash`, `resetToken`, `internalId` that should never reach the client.
- Sensitive data in URL query parameters is logged in web server access logs, browser history, and sent in `Referer` headers — even over HTTPS.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
