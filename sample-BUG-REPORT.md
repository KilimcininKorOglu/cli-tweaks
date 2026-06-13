# Bug Analysis Report - Project Name

Generated: 2026-03-24
Last Bug ID: BUG-030

## Summary

| Severity  | Count  |
|-----------|--------|
| Critical  | 8      |
| High      | 9      |
| Medium    | 4      |
| Low       | 9      |
| **Total** | **30** |

## System Architecture

[sec-recon output is here]

## Findings

### BUG-001: Open redirect via unvalidated `?next=` parameter
Severity: CRITICAL
Status: FIXED
File: src/Controllers/AuthController.php:17,27
Component: Authentication
Suggested Commit: `security: validate redirect target in login to prevent open redirect`

Problem: `$next = $_GET['next'] ?? '/'` is passed directly to `header("Location: $next")` with zero validation. An attacker can craft `https://mailpanel.example.com/login?next=https://evil.com` to redirect authenticated users to a malicious site.

Expected: Only internal relative paths should be accepted as redirect targets.

Root Cause: No validation of the `$next` parameter before use in HTTP redirect.

Impact: Phishing attacks — users redirected to malicious sites after legitimate login.

Verification: Traced `$_GET['next']` from line 17 through to `header()` on line 27 — no filtering anywhere in the path.

---