---
name: header-injection
description: >-
  Detect HTTP header injection vulnerabilities using a three-phase approach:
  find header manipulation sites where user input reaches response headers,
  trace input flow to verify CRLF injection and Host header poisoning,
  then merge confirmed findings. Use when asked to audit HTTP header security.
---

# HTTP Header Injection Scan

You are performing a focused security assessment to find HTTP header injection vulnerabilities in a codebase. This skill uses a three-phase approach with subagents: **discovery** (find all sites where user input is placed into HTTP response headers) then **verify** (trace input flow and confirm exploitability) then **merge** (write confirmed findings).

---

## What is HTTP Header Injection

HTTP header injection occurs when user-controlled input is placed into HTTP response headers without sanitization. Injecting CRLF characters (`\r\n`) allows an attacker to add arbitrary headers or split the response entirely. The core pattern: *user input reaches a response header value without stripping carriage return and line feed characters.*

### What Header Injection IS

- CRLF injection in response headers: user input containing `%0d%0a` injected into `Set-Cookie`, `Location`, `Content-Disposition`, or custom headers
- Host header poisoning: using the attacker-controlled `Host` header to construct password reset URLs, cache keys, or redirect targets
- Response splitting: injecting a double CRLF (`\r\n\r\n`) to terminate headers and inject arbitrary response body (XSS)
- Content-Disposition filename injection: user-controlled filename in download headers enabling header manipulation

### What Header Injection is NOT

Do not flag these:

- **Static header values**: Headers set from constants or server configuration, not user input
- **Modern framework auto-protection**: Node.js 14+, Go net/http, ASP.NET Core, Tomcat 7+ reject CRLF in header values automatically
- **Framework redirect methods**: `res.redirect()` in Express URL-encodes the Location value
- **Content-Type headers**: Typically set by framework based on response type, not user input
- **Reverse proxy normalization**: nginx/Apache strip malformed headers before they reach the application

### Patterns That Prevent Header Injection

When you see these patterns, the code is likely **not vulnerable**:

**1. CRLF stripping before header insertion**
```javascript
const lang = req.query.lang.replace(/[\r\n]/g, '');
res.setHeader('Set-Cookie', `lang=${encodeURIComponent(lang)}`);
```

**2. Using configured server name instead of Host header**
```python
reset_url = f"https://{settings.ALLOWED_HOSTS[0]}/reset?token={token}"
```

**3. Framework-level encoding on redirect**
```javascript
// Express res.redirect() URL-encodes the Location header value
res.redirect(`/dashboard?lang=${req.query.lang}`);
```

---

## Vulnerable vs. Secure Examples

### CRLF Injection in Set-Cookie

```javascript
// VULNERABLE: User input directly in Set-Cookie header
app.get('/lang', (req, res) => {
  res.setHeader('Set-Cookie', `lang=${req.query.lang}`);
  // Attack: ?lang=en%0d%0aSet-Cookie:%20admin=true
  // Injects additional Set-Cookie header
});

// SECURE: Strip CRLF and encode
app.get('/lang', (req, res) => {
  const lang = req.query.lang.replace(/[\r\n]/g, '');
  res.setHeader('Set-Cookie', `lang=${encodeURIComponent(lang)}`);
});
```

### Host Header Poisoning — Password Reset

```python
# VULNERABLE: Host header used to build password reset URL
def password_reset(request):
    host = request.META['HTTP_HOST']  # Attacker-controlled!
    reset_url = f"https://{host}/reset?token={token}"
    send_email(user.email, f"Reset here: {reset_url}")
    # Attacker sets Host: evil.com → victim clicks link to evil.com with valid token

# SECURE: Use configured server name
def password_reset(request):
    reset_url = f"https://{settings.ALLOWED_HOSTS[0]}/reset?token={token}"
    send_email(user.email, f"Reset here: {reset_url}")
```

```javascript
// VULNERABLE: Host header in email link
app.post('/forgot-password', (req, res) => {
  const host = req.headers.host;
  const resetLink = `https://${host}/reset?token=${token}`;
  sendEmail(user.email, resetLink);
});

// SECURE: Use environment variable
app.post('/forgot-password', (req, res) => {
  const resetLink = `${process.env.APP_URL}/reset?token=${token}`;
  sendEmail(user.email, resetLink);
});
```

### Content-Disposition Filename Injection

```go
// VULNERABLE: User filename in Content-Disposition
func download(w http.ResponseWriter, r *http.Request) {
    filename := r.URL.Query().Get("file")
    w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
    // Attack: ?file=test%0d%0aContent-Type:%20text/html%0d%0a%0d%0a<script>alert(1)</script>
}

// SECURE: Sanitize filename
func download(w http.ResponseWriter, r *http.Request) {
    filename := sanitizeFilename(r.URL.Query().Get("file"))
    w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="%s"`, filename))
}

func sanitizeFilename(s string) string {
    return strings.Map(func(r rune) rune {
        if r == '\r' || r == '\n' || r == '"' { return -1 }
        return r
    }, s)
}
```

### Response Splitting via Location Header

```php
// VULNERABLE: User input in Location header (older PHP versions)
<?php
$redirect = $_GET['url'];
header("Location: $redirect");
// Attack: ?url=http://example.com%0d%0aContent-Type:%20text/html%0d%0a%0d%0a<script>alert(1)</script>

// SECURE: Validate and encode redirect URL
<?php
$redirect = filter_var($_GET['url'], FILTER_VALIDATE_URL);
if ($redirect && parse_url($redirect, PHP_URL_HOST) === 'example.com') {
    header("Location: " . $redirect);
}
```

---

## Execution

### Phase 1: Find Header Manipulation Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where user input could reach HTTP response headers — header setting, redirects, cookie creation, Content-Disposition, and Host header usage. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the web framework and HTTP handling patterns.
>
> **What to search for — header manipulation patterns**:
>
> 1. **Response header setting with potential user input**:
>    - `res.setHeader(`, `res.header(`, `response.addHeader(`, `response.setHeader(`
>    - `w.Header().Set(`, `w.Header().Add(`
>    - `Response.Headers.Add(`, `Response.Cookies.Append(`
>    - `header(` (PHP), `add_header` (nginx config in repo)
>
> 2. **Redirect with user input**:
>    - `res.redirect(`, `response.sendRedirect(`, `redirect(`
>    - `http.Redirect(`, `Response.Redirect(`
>    - `Location` header set manually with user-derived value
>
> 3. **Host header usage**:
>    - `req.headers.host`, `req.Host`, `request.getHeader("Host")`
>    - `request.META['HTTP_HOST']`, `$_SERVER['HTTP_HOST']`
>    - Used in URL construction, email links, cache keys
>
> 4. **Content-Disposition with user input**:
>    - `Content-Disposition` header with user-supplied filename
>    - Download handlers that take filename from request parameter
>
> 5. **Cookie setting with user input**:
>    - `Set-Cookie` header with user-derived values
>    - Cookie libraries where value comes from request parameters
>
> **What to skip**:
> - Headers set from constants or environment variables (no user input path)
> - Test/mock responses
> - Static file serving with framework-managed headers
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Header Injection Recon: [Project Name]
>
> ## Summary
> Found [N] header manipulation sites with potential user input.
>
> ## Manipulation Sites
>
> ### 1. [Descriptive name — e.g., "User input in Set-Cookie via language parameter"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Header type**: [Set-Cookie / Location / Content-Disposition / Host usage / custom header]
> - **User input source**: [query param / path param / request body / Host header]
> - **Framework**: [Express / Django / Go net/http / Spring / etc.]
> - **Framework version**: [if determinable — important for auto-CRLF protection]
> - **Code snippet**:
>   ```
>   [the header manipulation code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Trace User Input to Headers

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand framework version and middleware stack.
>
> **For each header manipulation site, trace user input and verify exploitability**:
>
> 1. **CRLF injection in response headers**: Can the user inject `\r\n` into a header value?
>    - Trace user input from source (query param, body, path) to header set call
>    - Check if ANY sanitization strips `\r` and `\n` characters
>    - Check if encoding (URL encode, HTML encode) is applied
>    - Check framework version — Node.js 14+, Go, ASP.NET Core reject CRLF automatically
>    - If user input → header value with no CRLF sanitization + vulnerable framework → VULNERABLE
>
> 2. **Host header poisoning**: Is the Host header used to construct URLs?
>    - Password reset links built with `req.headers.host` or `request.META['HTTP_HOST']`
>    - Cache key generation using Host header (cache poisoning)
>    - Redirect URLs constructed from Host header
>    - If Host header → password reset URL → VULNERABLE (token theft)
>    - If Host header → cache key → LIKELY VULNERABLE (cache poisoning)
>
> 3. **Content-Disposition filename injection**: Can the user inject CRLF via filename?
>    - User-controlled filename in `Content-Disposition: attachment; filename=...`
>    - Check if filename is sanitized (CRLF stripped, quoted)
>    - If unsanitized filename from user input → LIKELY VULNERABLE
>
> 4. **Response splitting**: Can the user terminate headers and inject body?
>    - Double CRLF (`\r\n\r\n`) in header value terminates headers
>    - If exploitable → enables XSS via injected HTML body
>    - Modern frameworks prevent this, but older PHP, Python CGI, or custom HTTP handling may be vulnerable
>
> 5. **Modern framework protection check**:
>    - Node.js 14+: `http.ServerResponse` throws on CRLF in header values
>    - Go net/http: Rejects headers containing `\r` or `\n`
>    - ASP.NET Core: Rejects CRLF in header values
>    - Java Servlet (Tomcat 7+): Rejects CRLF in response headers
>    - If modern framework with auto-protection → NOT VULNERABLE (but note the code smell)
>
> **Classification**:
> - **Vulnerable**: Confirmed CRLF injection or Host header poisoning with clear exploit path on framework without auto-protection.
> - **Likely Vulnerable**: User input reaches header values without sanitization, but framework may auto-protect (version unclear).
> - **Not Vulnerable**: Framework auto-rejects CRLF, or input is properly sanitized/encoded.
> - **Needs Manual Review**: Complex middleware chain or unclear framework version.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Header Injection Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / scope**: [route or handler]
> - **Issue**: [e.g., "Host header used to construct password reset URL — attacker can steal reset tokens"]
> - **Injection type**: [CRLF / Host poisoning / Content-Disposition / response splitting]
> - **Input source**: [query param / Host header / path param]
> - **Impact**: Response splitting (XSS, cache poisoning), session fixation via injected cookies, password reset token theft
> - **Remediation**: Strip CR/LF from user input before header insertion. Use configured server name instead of Host header. Quote and sanitize Content-Disposition filenames.
> - **Proof of concept**: [e.g., "`curl -H 'Host: evil.com' target.com/forgot-password` — check if email contains evil.com URL"]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Response splitting enabling XSS or cache poisoning → CRITICAL
> - Host header poisoning in password reset (token theft) → HIGH
> - CRLF injection in Set-Cookie (session fixation) → HIGH
> - Content-Disposition filename injection → MEDIUM
> - Header injection in framework with likely auto-protection (version unclear) → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full injection details and a proof of concept
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all header manipulation sites regardless of whether they are secure. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each site, trace user input flow and determine whether injection is possible.
- Most modern web frameworks (Node.js 14+, Go, ASP.NET Core, Tomcat 7+) reject CRLF characters in header values automatically. Always check the framework and version before classifying as vulnerable.
- Host header poisoning is the most practically exploitable header injection — it does not require CRLF injection and works against all frameworks. Password reset flows are the primary target.
- CRLF injection is largely mitigated by modern frameworks, but older versions, custom HTTP handling, or proxy configurations may still be vulnerable.
- Content-Disposition filename injection is often overlooked. Even on modern frameworks, the filename value may not be automatically sanitized.
- Response splitting (double CRLF to inject body) is the most severe form of header injection — it enables XSS without a reflected input in the page body.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
