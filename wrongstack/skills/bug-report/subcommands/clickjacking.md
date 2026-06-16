---
name: clickjacking
description: >-
  Audit clickjacking protection using a single-phase comprehensive approach:
  check X-Frame-Options headers, CSP frame-ancestors directives, JavaScript
  framebusting code, and whether sensitive operations lack frame protection.
  Use when asked to audit clickjacking or UI redressing defenses.
---

# Clickjacking Protection Audit

You are performing a focused security assessment to find clickjacking vulnerabilities in a codebase. Unlike other scans, this is a **single-phase comprehensive audit** — not the 3-phase recon/verify model — because clickjacking protection is a global configuration concern that requires checking header middleware, CSP policies, and individual page protections holistically.

---

## What is Clickjacking

Clickjacking (UI redressing) tricks users into clicking hidden elements by embedding the target application in an invisible iframe on an attacker-controlled page. The user sees the attacker's page but their clicks land on the hidden iframe — performing unintended actions like transferring money, changing settings, or granting permissions. The core pattern: *the application can be embedded in an iframe by any external site because frame protection headers are missing.*

### What Clickjacking IS

- Missing `X-Frame-Options` header (no `DENY` or `SAMEORIGIN`)
- Missing `Content-Security-Policy: frame-ancestors` directive
- Both headers absent — application can be iframed by any site
- JavaScript-only framebusting that can be bypassed with `sandbox` attribute
- Frame protection missing on pages with sensitive actions (transfers, settings, password change)

### What Clickjacking is NOT

Do not flag these:

- **Embeddable widgets by design**: Applications designed to be embedded (payment forms, maps, analytics widgets)
- **API-only responses**: JSON APIs do not render UI elements — clickjacking is irrelevant
- **Static marketing pages**: Public pages with no interactive elements or forms
- **Proxy-level frame protection**: X-Frame-Options set at nginx/Apache level rather than in application code
- **CSP frame-ancestors already set**: If `frame-ancestors 'self'` or `frame-ancestors 'none'` is present, X-Frame-Options absence is defense-in-depth, not a vulnerability

### Patterns That Prevent Clickjacking

When you see these patterns, the code is likely **not vulnerable**:

**1. Helmet middleware (Node.js)**
```javascript
const helmet = require('helmet');
app.use(helmet.frameguard({ action: 'deny' }));
// Or via CSP
app.use(helmet.contentSecurityPolicy({
  directives: { frameAncestors: ["'self'"] }
}));
```

**2. Django setting**
```python
# settings.py
X_FRAME_OPTIONS = 'DENY'
# Django sets this header automatically on all responses
```

**3. Go middleware**
```go
func securityHeaders(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("X-Frame-Options", "DENY")
        w.Header().Set("Content-Security-Policy", "frame-ancestors 'none'")
        next.ServeHTTP(w, r)
    })
}
```

**4. Spring Security**
```java
http.headers().frameOptions().deny();
// Or
http.headers().contentSecurityPolicy("frame-ancestors 'none'");
```

---

## Vulnerable vs. Secure Examples

### Node.js / Express — No Frame Protection

```javascript
// VULNERABLE: No frame protection headers set
app.get('/transfer', (req, res) => {
  res.send('<html><form action="/api/transfer">...</form></html>');
  // Can be iframed by attacker site!
});

// SECURE: Using helmet
const helmet = require('helmet');
app.use(helmet());  // Includes frameguard with SAMEORIGIN by default
```

### Django — Missing X_FRAME_OPTIONS

```python
# VULNERABLE: X_FRAME_OPTIONS not set or set to ALLOW
# If missing from settings.py, Django defaults to DENY since 3.0
# But older versions or explicit override:
X_FRAME_OPTIONS = 'ALLOW-FROM https://example.com'  # Deprecated, inconsistent browser support

# SECURE:
X_FRAME_OPTIONS = 'DENY'
```

### JavaScript Framebusting — Bypassable

```javascript
// VULNERABLE: Can be defeated by sandbox attribute
if (top !== self) {
  top.location = self.location;
}
// Attacker: <iframe src="target.com" sandbox="allow-scripts"></iframe>
// sandbox prevents top.location assignment!

// BETTER: Use HTTP headers instead of JavaScript framebusting
// X-Frame-Options: DENY
// Content-Security-Policy: frame-ancestors 'none'
```

### CSP frame-ancestors vs X-Frame-Options

```
# X-Frame-Options — older, limited (DENY or SAMEORIGIN only)
X-Frame-Options: DENY

# CSP frame-ancestors — modern, flexible (can specify allowed origins)
Content-Security-Policy: frame-ancestors 'self' https://trusted.example.com

# Best practice: set BOTH for defense in depth
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'none'
```

### Spring Boot — Missing Frame Options

```java
// VULNERABLE: Frame protection disabled
@Override
protected void configure(HttpSecurity http) throws Exception {
    http.headers().frameOptions().disable();
}

// SECURE: Frame protection enabled
@Override
protected void configure(HttpSecurity http) throws Exception {
    http.headers().frameOptions().deny();
}
```

---

## Execution

### Single-Phase Comprehensive Audit

Launch a subagent with the following instructions:

> **Goal**: Perform a full clickjacking protection audit. Check whether the application sets frame protection headers globally, whether CSP frame-ancestors is configured, whether any JavaScript framebusting exists, and whether sensitive pages are protected.
>
> **Context**: You will be given the project's architecture summary. Use it to identify the web framework, middleware configuration, and pages with sensitive actions.
>
> **Step 1: Check Global Frame Protection Headers**
>
> Search for X-Frame-Options and CSP frame-ancestors in:
>
> - **Middleware/security configuration**:
>   - `X-Frame-Options`, `x-frame-options`, `frameguard`, `frameOptions`
>   - `frame-ancestors`, `frameAncestors`
>   - `helmet(`, `helmet.frameguard(`, `helmet.contentSecurityPolicy(`
>   - Django: `X_FRAME_OPTIONS` in settings.py
>   - Spring: `frameOptions().deny()`, `frameOptions().sameOrigin()`
>   - ASP.NET: `AddFrameOptionsDeny`, `AddFrameOptionsSameOrigin`
>
> - **Reverse proxy configuration** (if in repo):
>   - nginx: `add_header X-Frame-Options`, `add_header Content-Security-Policy`
>   - Apache: `Header set X-Frame-Options`
>
> Determine: Is frame protection applied globally to ALL responses, only to some routes, or not at all?
>
> **Step 2: Check CSP Configuration**
>
> - Is `Content-Security-Policy` set with `frame-ancestors` directive?
> - Is it `'none'`, `'self'`, or specific origins?
> - Is it set globally or per-route?
> - Is there a `Content-Security-Policy-Report-Only` variant (does not enforce, only reports)?
>
> **Step 3: Check JavaScript Framebusting**
>
> Search for JavaScript-based frame protection:
> - `if (top !== self)`, `if (window.top !== window.self)`, `if (parent !== self)`
> - `top.location = self.location`, `top.location.href =`
> - These are bypassable via `sandbox` attribute on iframe
>
> **Step 4: Identify Sensitive Pages Without Protection**
>
> Check if the following page types have frame protection:
> - Account settings / profile edit pages
> - Password change / reset pages
> - Payment / transfer / checkout pages
> - Permission / role management pages
> - Delete / deactivate account pages
> - OAuth consent screens
>
> **Classification**:
> - **Vulnerable**: No frame protection (X-Frame-Options or CSP frame-ancestors) on pages with sensitive actions.
> - **Likely Vulnerable**: Only JavaScript framebusting (bypassable), or frame protection missing on some sensitive routes.
> - **Not Vulnerable**: Global X-Frame-Options DENY or CSP frame-ancestors 'none'/'self' applied to all HTML responses.
> - **Needs Manual Review**: Frame protection may be set at infrastructure level (nginx/Apache/CDN) but not visible in application code.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Clickjacking Audit: [Project Name]
>
> ## Summary
> - Global X-Frame-Options: [DENY / SAMEORIGIN / not set]
> - CSP frame-ancestors: ['none' / 'self' / specific origins / not set]
> - JavaScript framebusting: [present / absent]
> - Overall protection: [complete / partial / absent]
>
> ## Findings
>
> ### [VULNERABLE] / [LIKELY VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Scope**: [global / specific route]
> - **Issue**: [e.g., "No X-Frame-Options or CSP frame-ancestors set — application can be iframed by any site"]
> - **Affected pages**: [list of sensitive pages without protection]
> - **Impact**: Users tricked into performing unintended actions (transfers, settings changes, permission grants)
> - **Remediation**: Set `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'none'` globally via middleware
>
> ### [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in reporting):
> - No frame protection on pages with financial/permission actions → CRITICAL
> - No frame protection on authenticated pages with forms → HIGH
> - Only JavaScript framebusting (bypassable) → MEDIUM
> - Missing CSP frame-ancestors when X-Frame-Options is set (defense in depth) → LOW

### Merge & Report

After the audit subagent completes:

1. Collect the audit response.
2. Extract **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the specific missing headers and affected pages
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- This is a **single-phase audit**, not the standard 3-phase recon/verify model. No batching is needed.
- Clickjacking is a **global configuration issue**. If frame protection headers are set globally in middleware, the entire application is protected. Focus on whether global protection exists before checking individual pages.
- `X-Frame-Options` is the older standard with limited options: `DENY` or `SAMEORIGIN`. `ALLOW-FROM` is deprecated and inconsistently supported.
- `CSP frame-ancestors` is the modern replacement — it supports multiple origins and has consistent browser support. Best practice is to set both headers for defense in depth.
- JavaScript framebusting (`if (top !== self)`) is NOT reliable protection. The HTML5 `sandbox` attribute on iframes prevents JavaScript from navigating the top frame, defeating all JS-based framebusting.
- API-only applications (returning JSON, not HTML) are NOT vulnerable to clickjacking. Only flag HTML-rendering endpoints.
- Django 3.0+ defaults `X_FRAME_OPTIONS` to `DENY` if not explicitly set. Check the Django version before flagging.
- Frame protection at the reverse proxy level (nginx `add_header X-Frame-Options DENY`) is valid protection. If proxy config exists in the repo, check it.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
