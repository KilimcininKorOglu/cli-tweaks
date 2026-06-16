---
name: open-redirect
description: >-
  Detect open redirect vulnerabilities using a two-phase approach:
  first find redirect sites (URL parameters, Location headers, client-side
  redirects), then trace whether user input reaches redirect targets without
  validation. Use when asked to find open redirect or URL redirect bugs.
---

# Open Redirect Detection

You are performing a focused security assessment to find open redirect vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **discovery** (find all redirect sites where a destination URL is determined) then **verify** (confirm whether user-supplied input reaches the redirect target without proper validation).

---

## What is Open Redirect

Open redirect occurs when an application accepts user-controlled input as a redirect destination and performs the redirect without validating the target URL against an allowlist. Attackers exploit this for phishing (trusted domain in URL redirects to evil site), OAuth token theft (redirect_uri manipulation), and SSRF chaining. The core pattern: *user-controlled input determines where the application redirects without validation.*

### What Open Redirect IS

- Redirect destination read from URL parameter: `res.redirect(req.query.url)`
- `Location` header set from user input: `response.headers['Location'] = params[:next]`
- Client-side redirect from URL fragment/param: `window.location = getParam('redirect')`
- OAuth `redirect_uri` or `callback` parameter not validated against registered URIs
- Login `return_url` / `next` parameter used as post-auth redirect without domain check
- Protocol-relative URLs accepted: `//evil.com` bypasses scheme-only checks
- Backslash tricks: `\/evil.com` or `\evil.com` parsed as absolute URL by some browsers

### What Open Redirect is NOT

Do not flag these as open redirect:

- **Relative path redirects**: `/dashboard`, `./profile`, `../settings` — cannot redirect to external domains
- **Hardcoded redirect URLs**: `res.redirect('/login')` with no dynamic component
- **Framework-validated redirects**: Some frameworks (Rails `redirect_back` with `fallback_location`) validate by default
- **Internal route dispatching**: Server-side forwarding between internal routes is not a redirect
- **Static HTML meta refresh**: `<meta http-equiv="refresh" content="0;url=/home">` with hardcoded URL

### Patterns That Prevent Open Redirect

When you see these patterns, the code is likely **not vulnerable**:

**1. Domain allowlist validation**
```javascript
const ALLOWED_HOSTS = ['example.com', 'app.example.com'];
const url = new URL(redirectUrl, 'https://example.com');
if (!ALLOWED_HOSTS.includes(url.hostname)) {
  return res.status(400).send('Invalid redirect');
}
res.redirect(url.toString());
```

**2. Relative-only redirect enforcement**
```python
if redirect_url.startswith('/') and not redirect_url.startswith('//'):
    return redirect(redirect_url)
return redirect('/')
```

**3. Framework safe redirect**
```ruby
# Rails url_for with only_path
redirect_to url_for(params[:return_to], only_path: true)
```

---

## Vulnerable vs. Secure Examples

### Node.js / Express

```javascript
// VULNERABLE: Unvalidated redirect from query param
app.get('/redirect', (req, res) => {
  res.redirect(req.query.url);
});

// VULNERABLE: Protocol-relative bypass possible
app.get('/redirect', (req, res) => {
  const url = req.query.next;
  if (url.startsWith('http://evil.com')) return res.status(400);
  res.redirect(url);  // //evil.com bypasses check
});

// SECURE: Allowlist validation
const ALLOWED = new Set(['example.com', 'app.example.com']);
app.get('/redirect', (req, res) => {
  try {
    const url = new URL(req.query.next, 'https://example.com');
    if (!ALLOWED.has(url.hostname)) return res.status(400).send('Bad redirect');
    res.redirect(url.toString());
  } catch { res.status(400).send('Invalid URL'); }
});
```

### Python — Django

```python
# VULNERABLE: Unvalidated redirect
def login_redirect(request):
    next_url = request.GET.get('next', '/')
    return HttpResponseRedirect(next_url)

# SECURE: Django's url_has_allowed_host_and_scheme
from django.utils.http import url_has_allowed_host_and_scheme
def login_redirect(request):
    next_url = request.GET.get('next', '/')
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={'example.com'}):
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect('/')
```

### Python — Flask

```python
# VULNERABLE: redirect to user-supplied URL
@app.route('/goto')
def goto():
    return redirect(request.args.get('url', '/'))

# SECURE: Validate against allowlist
from urllib.parse import urlparse
ALLOWED_HOSTS = {'example.com', 'app.example.com'}
@app.route('/goto')
def goto():
    url = request.args.get('url', '/')
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in ALLOWED_HOSTS:
        return redirect('/')
    return redirect(url)
```

### Ruby on Rails

```ruby
# VULNERABLE: Unvalidated redirect
def login
  redirect_to params[:return_to]
end

# SECURE: Only allow relative paths
def login
  if params[:return_to]&.start_with?('/') && !params[:return_to].start_with?('//')
    redirect_to params[:return_to]
  else
    redirect_to root_path
  end
end
```

### Java — Spring

```java
// VULNERABLE: Unvalidated redirect
@GetMapping("/redirect")
public String redirect(@RequestParam String url) {
    return "redirect:" + url;
}

// SECURE: Allowlist check
private static final Set<String> ALLOWED = Set.of("example.com", "app.example.com");
@GetMapping("/redirect")
public String redirect(@RequestParam String url) {
    try {
        URI uri = new URI(url);
        if (uri.getHost() != null && !ALLOWED.contains(uri.getHost())) {
            return "redirect:/";
        }
    } catch (URISyntaxException e) { return "redirect:/"; }
    return "redirect:" + url;
}
```

### Go

```go
// VULNERABLE: Unvalidated redirect
func redirectHandler(w http.ResponseWriter, r *http.Request) {
    url := r.URL.Query().Get("url")
    http.Redirect(w, r, url, http.StatusFound)
}

// SECURE: Parse and validate host
func redirectHandler(w http.ResponseWriter, r *http.Request) {
    target := r.URL.Query().Get("url")
    parsed, err := url.Parse(target)
    if err != nil || (parsed.Host != "" && parsed.Host != "example.com") {
        http.Redirect(w, r, "/", http.StatusFound)
        return
    }
    http.Redirect(w, r, target, http.StatusFound)
}
```

### Bypass Techniques

```
# Protocol-relative — bypasses scheme-only checks
//evil.com

# Backslash — some browsers/servers normalize to //
\/evil.com
\evil.com

# URL encoding — bypasses naive string checks
%2f%2fevil.com
%5cevil.com

# @ in URL — confuses URL parsers
https://example.com@evil.com

# Data URI — triggers local code execution in some contexts
data:text/html,<script>location='https://evil.com'</script>

# JavaScript URI — if redirect is client-side
javascript:document.location='https://evil.com'

# CRLF injection into Location header
%0d%0aLocation:%20https://evil.com
```

---

## Execution

### Phase 1: Find Redirect Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where a redirect is performed with any dynamic component — URL from parameters, variables, function returns, or computed values. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the web framework, routing, authentication flow, and common redirect patterns.
>
> **What to search for — redirect patterns**:
>
> 1. **Server-side redirect calls with dynamic URL**:
>    - `res.redirect(variable)`, `response.sendRedirect(variable)`, `http.Redirect(w, r, variable, code)`
>    - `HttpResponseRedirect(variable)`, `redirect(variable)`, `redirect_to variable`
>    - `return "redirect:" + variable` (Spring)
>    - `header("Location: " . $variable)` (PHP)
>
> 2. **URL parameters commonly used for redirects**:
>    - `next`, `url`, `redirect`, `redirect_url`, `return_url`, `return_to`, `callback`, `goto`, `continue`, `dest`, `destination`, `redir`, `redirect_uri`, `target`
>    - Search route handlers that read these params
>
> 3. **Client-side redirects from URL input**:
>    - `window.location = variable`, `window.location.href = variable`
>    - `document.location = variable`, `location.assign(variable)`, `location.replace(variable)`
>    - URL parameter read via `URLSearchParams`, `getParam`, `window.location.search`
>
> 4. **OAuth / SSO redirect flows**:
>    - `redirect_uri` parameter handling
>    - Post-login redirect after authentication
>    - Callback URL validation
>
> **What to skip**:
> - Hardcoded redirect URLs with no dynamic component
> - Internal route forwarding (server-side dispatch, not HTTP redirect)
> - Relative paths that are provably internal-only
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Open Redirect Recon: [Project Name]
>
> ## Summary
> Found [N] redirect sites with dynamic URL components.
>
> ## Redirect Sites
>
> ### 1. [Descriptive name — e.g., "Post-login redirect from 'next' param"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or route]
> - **Redirect method**: [res.redirect / HttpResponseRedirect / Location header / window.location / etc.]
> - **URL source**: [query param name / request body field / cookie / path segment]
> - **Code snippet**:
>   ```
>   [the redirect code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Trace User Input to Redirect Targets

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand auth flows, middleware, and URL validation utilities.
>
> **For each redirect site, verify whether user input reaches the redirect target without effective validation**:
>
> 1. **Direct user input**: Is the redirect URL taken directly from a request parameter, header, or body field?
>
> 2. **Validation check**: Does any validation exist between the input source and the redirect call?
>    - Domain allowlist → safe if correctly implemented
>    - Scheme check only (e.g., `startsWith('http')`) → bypassable with `http://evil.com`
>    - Path-relative check (e.g., `startsWith('/')`) → bypassable with `//evil.com`
>    - URL parsing + host check → safe if using proper URL parser (not regex or substring)
>
> 3. **Bypass analysis**: Can the validation be circumvented?
>    - Protocol-relative: `//evil.com`
>    - Backslash: `\/evil.com`, `\evil.com`
>    - URL encoding: `%2f%2fevil.com`
>    - Auth in URL: `https://example.com@evil.com`
>    - Data/JavaScript URIs: `data:text/html,...`, `javascript:...`
>    - CRLF injection in Location header
>
> 4. **Context assessment**: Where does this redirect occur?
>    - OAuth/SSO flow → CRITICAL (token theft)
>    - Post-login redirect → HIGH (credential phishing)
>    - General navigation → MEDIUM
>    - Authenticated-only, non-sensitive → LOW
>
> **Classification**:
> - **Vulnerable**: User input reaches redirect with no validation, or validation is trivially bypassable.
> - **Likely Vulnerable**: Validation exists but appears weak (scheme-only check, regex-based, substring match).
> - **Not Vulnerable**: Strict allowlist, proper URL parsing with host check, or relative-only enforcement.
> - **Needs Manual Review**: Validation logic is in external middleware or helper function that cannot be fully traced.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Open Redirect Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / function**: [route or function name]
> - **Issue**: [e.g., "Query param 'next' passed directly to res.redirect() with no validation"]
> - **Bypass vector**: [e.g., "//evil.com bypasses startsWith('/') check"]
> - **Impact**: Phishing via trusted domain, OAuth token theft, SSRF chaining
> - **Remediation**: Validate redirect URL against domain allowlist using proper URL parser. Reject protocol-relative URLs.
> - **Dynamic test**: `curl -v "https://target.com/redirect?next=//evil.com"` — check Location header
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - OAuth/SSO redirect_uri manipulation → CRITICAL
> - Post-login redirect with no validation → HIGH
> - General redirect with weak validation → MEDIUM
> - Authenticated-only redirect with some validation → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the bypass vector and a dynamic test command or payload
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all redirect sites with dynamic URL components, regardless of whether validation exists. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each redirect site, trace the URL source and test whether validation can be bypassed.
- Protocol-relative URLs (`//evil.com`) are the most common bypass. A `startsWith('/')` check alone does NOT prevent open redirect.
- Backslash tricks (`\/evil.com`) work in some browsers and server frameworks. Always test this vector.
- URL encoding (`%2f%2fevil.com`) may bypass string-level checks when the framework decodes before redirecting.
- The `@` symbol in URLs (`https://example.com@evil.com`) confuses users and some validation logic — the actual destination is `evil.com`.
- Client-side redirects (`window.location`) are equally dangerous — DOM-based open redirect enables phishing and XSS chaining.
- Post-login redirects are high-value targets because users have just entered credentials and trust the flow.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
