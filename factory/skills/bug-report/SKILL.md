---
name: bug-report
description: >
  This skill MUST be invoked for bug analysis, security auditing, or any focused
  audit such as "api audit", "error review", "cache audit", "tech debt", or any
  security scan such as "sql injection", "xss", "rce", "ssrf", "access control",
  "hardcoded secrets", "cors", "open redirect", "nosql injection", "dependency audit",
  "data exposure", "crypto", "ci/cd security", "docker security", "rate limiting",
  "websocket", "header injection", "clickjacking", "mass assignment",
  "güvenlik taraması", "security scan", or "security sweep".
  Use `/bug-report` for full audit, `/bug-report <subcommand>` for focused audits,
  `/bug-report security-sweep` for security-only parallel scans.
argument-hint: "[--severity critical|high|medium|low|all | <subcommand>]"
---

# Bug Analysis & Audit

## What To Do Right Now

Parse the user's command and follow exactly ONE of these three paths:

### Path A: Subcommand provided (`/bug-report <name>`)

If the user provided an argument that matches a subcommand from the reference
table at the bottom of this file:

1. Read the full content of `subcommands/<name>.md` using the Read tool.
2. Execute the instructions in that file as your complete workflow.
3. STOP. Do not continue reading this file. The subcommand file is your workflow.

Exception: `security-sweep` is Path B below, not a subcommand file.

### Path B: Security sweep (`/bug-report security-sweep`)

If the user said `/bug-report security-sweep` OR used natural language like
"güvenlik taraması başlat", "security scan", "run all security scans", or
"security sweep" — jump to the **Security Sweep Orchestration** section below.

### Path C: Full audit (`/bug-report` with no subcommand)

Run ALL audit subcommands in parallel using workers. This is the comprehensive
mode — every general audit and every security scan runs simultaneously.

Jump to the **Full Audit Orchestration** section below.

---

## Full Audit Orchestration

This runs when `/bug-report` is called with no subcommand. Launches ALL
subcommands as parallel workers for comprehensive repository analysis.

**Resume support:** Before launching each worker, read `BUG-REPORT.md` and
check for its completion marker (`<!-- scan:SUBCOMMAND completed -->`). Skip
that worker if the marker exists.

**Execution order:**

1. Run `sec-recon` first (inline, not as a worker) to establish codebase context.
   This writes the reconnaissance entry to `BUG-REPORT.md`.

2. Launch ALL remaining subcommands **in parallel** as workers. Skip any worker
   whose completion marker already exists in `BUG-REPORT.md`:

   **General audit workers:**

   | Worker    | Subcommand file                         | Completion marker                            |
   |-----------|-----------------------------------------|----------------------------------------------|
   | Worker 1  | `subcommands/api-audit.md`              | `<!-- scan:api-audit completed -->`          |
   | Worker 2  | `subcommands/cache-audit.md`            | `<!-- scan:cache-audit completed -->`        |
   | Worker 3  | `subcommands/disaster-recovery.md`      | `<!-- scan:disaster-recovery completed -->`  |
   | Worker 4  | `subcommands/error-review.md`           | `<!-- scan:error-review completed -->`       |
   | Worker 5  | `subcommands/feature-flags-audit.md`    | `<!-- scan:feature-flags-audit completed -->` |
   | Worker 6  | `subcommands/integration-security.md`   | `<!-- scan:integration-security completed -->` |
   | Worker 7  | `subcommands/observability-audit.md`    | `<!-- scan:observability-audit completed -->` |
   | Worker 8  | `subcommands/queue-audit.md`            | `<!-- scan:queue-audit completed -->`        |
   | Worker 9  | `subcommands/release-discipline.md`     | `<!-- scan:release-discipline completed -->` |
   | Worker 10 | `subcommands/serialization-audit.md`    | `<!-- scan:serialization-audit completed -->` |
   | Worker 11 | `subcommands/session-audit.md`          | `<!-- scan:session-audit completed -->`      |
   | Worker 12 | `subcommands/tech-debt.md`              | `<!-- scan:tech-debt completed -->`          |
   | Worker 13 | `subcommands/tenant-isolation.md`       | `<!-- scan:tenant-isolation completed -->`   |
   | Worker 14 | `subcommands/upload-security.md`        | `<!-- scan:upload-security completed -->`    |
   | Worker 15 | `subcommands/ai-code-audit.md`          | `<!-- scan:ai-code-audit completed -->`      |

   **Security scan workers:**

   | Worker    | Subcommand file                         | Completion marker                            |
   |-----------|-----------------------------------------|----------------------------------------------|
   | Worker 16 | `subcommands/access-control.md`         | `<!-- scan:access-control completed -->`     |
   | Worker 17 | `subcommands/sqli.md`                   | `<!-- scan:sqli completed -->`               |
   | Worker 18 | `subcommands/xss.md`                    | `<!-- scan:xss completed -->`                |
   | Worker 19 | `subcommands/rce.md`                    | `<!-- scan:rce completed -->`                |
   | Worker 20 | `subcommands/ssrf.md`                   | `<!-- scan:ssrf completed -->`               |
   | Worker 21 | `subcommands/path-traversal.md`         | `<!-- scan:path-traversal completed -->`     |
   | Worker 22 | `subcommands/ssti.md`                   | `<!-- scan:ssti completed -->`               |
   | Worker 23 | `subcommands/graphql.md`                | `<!-- scan:graphql completed -->`            |
   | Worker 24 | `subcommands/business-logic.md`         | `<!-- scan:business-logic completed -->`     |
   | Worker 25 | `subcommands/hardcoded-secrets.md`      | `<!-- scan:hardcoded-secrets completed -->`  |
   | Worker 26 | `subcommands/cors.md`                   | `<!-- scan:cors completed -->`               |
   | Worker 27 | `subcommands/open-redirect.md`          | `<!-- scan:open-redirect completed -->`      |
   | Worker 28 | `subcommands/nosqli.md`                 | `<!-- scan:nosqli completed -->`             |
   | Worker 29 | `subcommands/data-exposure.md`          | `<!-- scan:data-exposure completed -->`      |
   | Worker 30 | `subcommands/crypto.md`                 | `<!-- scan:crypto completed -->`             |
   | Worker 31 | `subcommands/header-injection.md`       | `<!-- scan:header-injection completed -->`   |
   | Worker 32 | `subcommands/websocket.md`              | `<!-- scan:websocket completed -->`          |
   | Worker 33 | `subcommands/mass-assignment.md`        | `<!-- scan:mass-assignment completed -->`    |
   | Worker 34 | `subcommands/rate-limiting.md`          | `<!-- scan:rate-limiting completed -->`      |
   | Worker 35 | `subcommands/ci-cd.md`                  | `<!-- scan:ci-cd completed -->`              |
   | Worker 36 | `subcommands/docker.md`                 | `<!-- scan:docker completed -->`             |
   | Worker 37 | `subcommands/clickjacking.md`           | `<!-- scan:clickjacking completed -->`       |
   | Worker 38 | `subcommands/dependency-audit.md`       | `<!-- scan:dependency-audit completed -->`   |
   | Worker 39 | `subcommands/ldap.md`                   | `<!-- scan:ldap completed -->`               |

3. Each worker prompt must include:
   - The full content of its subcommand file as instructions
   - The repository path to scan
   - Instruction to write all confirmed findings to `BUG-REPORT.md` using the
     shared format below, continuing the existing ID sequence

4. After all workers complete, read `BUG-REPORT.md` and re-sort all findings by
   severity (CRITICAL -> HIGH -> MEDIUM -> LOW), deduplicating overlapping findings.

If `--severity` flag provided, filter final report to only that severity level.

**Worker prompt template:**

> You are an auditor. Execute the following audit on the repository at `[repo_path]`.
> Read the full content of the subcommand file below and follow its instructions.
> Write all confirmed findings to `BUG-REPORT.md` in the repository root.
>
> Finding format:
> ```
> ### BUG-[ID]: [title]
> Severity: CRITICAL | HIGH | MEDIUM | LOW
> Status: NEW
> File: path/to/file:line
> Component: [module]
> Suggested Commit: `[fix: ...]`
>
> Problem: [what's wrong]
>
> Expected: [what should happen]
>
> Root Cause: [why]
>
> Impact: [impact]
>
> Verification: [how confirmed]
>
> ---
> ```
>
> Read existing `BUG-REPORT.md` to continue the ID sequence.
>
> Subcommand instructions:
> [full content of subcommand file]

---

## Security Sweep Orchestration

Use when the user says `/bug-report security-sweep` or natural language like
"güvenlik taraması başlat", "security scan", "run all security scans".

This runs ONLY the security scan subcommands (not general audits).

**Resume support:** Same as Full Audit — check completion markers before launching.

**Execution order:**

1. Run `sec-recon` first (inline) to establish codebase context.

2. Launch security scan workers **in parallel**:

   | Worker    | Subcommand file                     | Completion marker                          |
   |-----------|--------------------------------------|--------------------------------------------|
   | Worker 1  | `subcommands/sqli.md`               | `<!-- scan:sqli completed -->`             |
   | Worker 2  | `subcommands/xss.md`                | `<!-- scan:xss completed -->`              |
   | Worker 3  | `subcommands/rce.md`                | `<!-- scan:rce completed -->`              |
   | Worker 4  | `subcommands/ssrf.md`               | `<!-- scan:ssrf completed -->`             |
   | Worker 5  | `subcommands/access-control.md`     | `<!-- scan:access-control completed -->`   |
   | Worker 6  | `subcommands/path-traversal.md`     | `<!-- scan:path-traversal completed -->`   |
   | Worker 7  | `subcommands/ssti.md`               | `<!-- scan:ssti completed -->`             |
   | Worker 8  | `subcommands/graphql.md`            | `<!-- scan:graphql completed -->`          |
   | Worker 9  | `subcommands/business-logic.md`     | `<!-- scan:business-logic completed -->`   |
   | Worker 10 | `subcommands/hardcoded-secrets.md`  | `<!-- scan:hardcoded-secrets completed -->` |
   | Worker 11 | `subcommands/cors.md`               | `<!-- scan:cors completed -->`             |
   | Worker 12 | `subcommands/open-redirect.md`      | `<!-- scan:open-redirect completed -->`    |
   | Worker 13 | `subcommands/nosqli.md`             | `<!-- scan:nosqli completed -->`           |
   | Worker 14 | `subcommands/data-exposure.md`      | `<!-- scan:data-exposure completed -->`    |
   | Worker 15 | `subcommands/crypto.md`             | `<!-- scan:crypto completed -->`           |
   | Worker 16 | `subcommands/header-injection.md`   | `<!-- scan:header-injection completed -->`  |
   | Worker 17 | `subcommands/websocket.md`          | `<!-- scan:websocket completed -->`        |
   | Worker 18 | `subcommands/mass-assignment.md`    | `<!-- scan:mass-assignment completed -->`  |
   | Worker 19 | `subcommands/rate-limiting.md`      | `<!-- scan:rate-limiting completed -->`    |
   | Worker 20 | `subcommands/ci-cd.md`              | `<!-- scan:ci-cd completed -->`            |
   | Worker 21 | `subcommands/docker.md`             | `<!-- scan:docker completed -->`           |
   | Worker 22 | `subcommands/clickjacking.md`       | `<!-- scan:clickjacking completed -->`     |
   | Worker 23 | `subcommands/dependency-audit.md`   | `<!-- scan:dependency-audit completed -->`  |
   | Worker 24 | `subcommands/ldap.md`               | `<!-- scan:ldap completed -->`              |

3. Use the same worker prompt template from Full Audit above.

4. After all workers complete, re-sort and deduplicate `BUG-REPORT.md`.

---

## Report Format

Save to `BUG-REPORT.md` in repository root:

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

## System Architecture

[sec-recon output — only if sec-recon was run]

## Findings

[All findings sorted by severity: CRITICAL first, LOW last]
```

## Report Rules

- Zero false positives > completeness — only report verified findings
- ALL findings under single `## Findings` section — no custom grouping headers
- Sorted by severity: CRITICAL, HIGH, MEDIUM, LOW
- Each finding: `### BUG-[ID]` heading, `---` separator between entries
- Suggested Commit BEFORE Problem, wrapped in backticks
- Header fields (Severity, Status, File, Component, Suggested Commit) on consecutive lines — no blank lines between them
- One blank line between Suggested Commit and Problem
- Blank line between each body field (Problem, Expected, Root Cause, Impact, Verification)
- Bug IDs never reset — increment from highest existing ID
- If `bugs.md` or `bug.md` exists, merge and delete old file
- Suggested Commit messages NEVER include bug IDs
- Always write report in English only

---

## Subcommand Reference

| Subcommand             | Description                                                              |
|------------------------|--------------------------------------------------------------------------|
| `api-audit`            | API performance, resilience, contract, and lifecycle audit               |
| `cache-audit`          | Caching strategy, consistency, and Redis/security audit                  |
| `disaster-recovery`    | Disaster recovery and business continuity readiness audit                |
| `error-review`         | Error message quality, disclosure, and fallback-state audit              |
| `feature-flags-audit`  | Feature flag hygiene, rollout safety, and experimentation audit          |
| `integration-security` | Third-party integration, webhook, and OAuth security audit               |
| `observability-audit`  | Logging, metrics, tracing, and debugging-readiness audit                 |
| `queue-audit`          | Queue, worker, retry, and DLQ resilience audit                           |
| `release-discipline`   | Version control, review process, and release-discipline audit            |
| `serialization-audit`  | Serialization, parsing, XXE, and data transformation security audit      |
| `session-audit`        | Session lifecycle, JWT vulnerability, cookies, CSRF audit                |
| `tech-debt`            | Technical debt, dead code, and test quality audit                        |
| `tenant-isolation`     | Multi-tenant isolation and cross-tenant leakage audit                    |
| `access-control`       | IDOR and missing authentication/authorization detection                  |
| `upload-security`      | File upload and media processing security audit                          |
| `ai-code-audit`        | AI-generated code detection, security, and quality audit                 |
| `sec-recon`            | Codebase architecture and security posture reconnaissance                |
| `sqli`                 | SQL injection three-phase detection                                      |
| `xss`                  | Cross-site scripting three-phase detection                               |
| `rce`                  | Remote code execution and command injection detection                    |
| `ssrf`                 | Server-side request forgery detection                                    |
| `path-traversal`       | Path traversal and directory traversal detection                         |
| `ssti`                 | Server-side template injection detection                                 |
| `graphql`              | GraphQL injection and abuse detection                                    |
| `business-logic`       | Business logic flaw and workflow bypass detection                        |
| `hardcoded-secrets`    | Hardcoded API key, token, and password detection                         |
| `cors`                 | CORS misconfiguration and cross-origin attack detection                  |
| `open-redirect`        | Open redirect and URL manipulation detection                             |
| `nosqli`               | NoSQL injection (MongoDB, Redis, Elasticsearch) detection                |
| `dependency-audit`     | Supply chain security, CVE detection, typosquatting audit                |
| `data-exposure`        | Sensitive data exposure in logs, errors, and API responses               |
| `crypto`               | Cryptography weakness detection (weak algorithms, hardcoded keys)        |
| `ci-cd`                | CI/CD pipeline security (GitHub Actions, GitLab CI)                      |
| `docker`               | Container security (Dockerfile, docker-compose)                          |
| `rate-limiting`        | Rate limiting and brute force protection audit                           |
| `websocket`            | WebSocket security (origin validation, auth, message injection)          |
| `header-injection`     | HTTP header injection and CRLF detection                                 |
| `clickjacking`         | Clickjacking protection (X-Frame-Options, CSP frame-ancestors)           |
| `mass-assignment`      | Mass assignment and parameter pollution detection                        |
| `fix`                  | Disciplined single-bug fix workflow with commit and report update        |
| `ldap`                 | LDAP injection in search filters and DN construction                     |
