---
name: bug-report
description: >
  This skill MUST be invoked when the user asks for systematic bug analysis, or any focused audit such as "api audit", "auditcodex", "cache audit", "disaster recovery", "error review", "feature flags audit", "integration security", "observability audit", "queue audit", "release discipline", "serialization audit", "session audit", "tech debt", "tenant isolation", "test review", "upload security", "ai code audit", "dead code", any security vulnerability scan such as "sql injection", "xss", "rce", "ssrf", "xxe", "idor", "jwt", "path traversal", "file upload", "ssti", "graphql injection", "business logic", "missing auth", or "security recon", or a FULL security sweep such as "güvenlik taraması", "security scan", "full security scan", "run all security scans", or "security sweep". Use `/bug-report` for general scans, `/bug-report <subcommand>` for domain-specific audits, and `/bug-report security-sweep` to run all security scans in parallel. All modes write verified findings to BUG-REPORT.md using the shared report contract.
argument-hint: "[--severity critical|high|medium|low|all | <subcommand> [subcommand-options]]"
---

# Bug Analysis & Audit Router

Analyze the repository either broadly (`/bug-report`) or through a focused audit subcommand (`/bug-report <subcommand>`).

## Usage

```bash
/bug-report                              # Full repository bug analysis
/bug-report --severity high              # General scan filtered by severity
/bug-report auditcodex                   # Codex-backed diff audit
/bug-report api-audit                    # Focused API audit
/bug-report error-review                 # Focused error handling audit
/bug-report dead-code                    # Focused dead-code audit
/bug-report security-sweep               # Run ALL security scans in parallel via workers

# Security vulnerability scans (two-phase, subagent-based)
/bug-report sec-recon                    # Codebase architecture map — run before deeper scans
/bug-report sqli                         # SQL injection scan
/bug-report xss                          # Cross-site scripting scan
/bug-report rce                          # Remote code execution scan
/bug-report ssrf                         # Server-side request forgery scan
/bug-report xxe                          # XML external entity scan
/bug-report idor                         # Insecure direct object reference scan
/bug-report jwt                          # JWT weakness scan
/bug-report path-traversal               # Path traversal scan
/bug-report ssti                         # Server-side template injection scan
/bug-report graphql                      # GraphQL injection scan
/bug-report business-logic               # Business logic flaw scan
/bug-report missing-auth                 # Missing authentication/authorization scan
```

## Subcommands

| Subcommand | Command | Description |
|------------|---------|-------------|
| `auditcodex` | `/bug-report auditcodex` | Codex CLI diff audit with validated findings written to BUG-REPORT.md |
| `api-audit` | `/bug-report api-audit` | API performance, resilience, contract, and lifecycle audit |
| `cache-audit` | `/bug-report cache-audit` | Caching strategy, consistency, and Redis/security audit |
| `disaster-recovery` | `/bug-report disaster-recovery` | Disaster recovery and business continuity readiness audit |
| `error-review` | `/bug-report error-review` | Error message quality, disclosure, and fallback-state audit |
| `feature-flags-audit` | `/bug-report feature-flags-audit` | Feature flag hygiene, rollout safety, and experimentation audit |
| `integration-security` | `/bug-report integration-security` | Third-party integration, webhook, and OAuth security audit |
| `observability-audit` | `/bug-report observability-audit` | Logging, metrics, tracing, and debugging-readiness audit |

| `queue-audit` | `/bug-report queue-audit` | Queue, worker, retry, and DLQ resilience audit |
| `release-discipline` | `/bug-report release-discipline` | Version control, review process, and release-discipline audit |
| `serialization-audit` | `/bug-report serialization-audit` | Serialization, parsing, and data transformation security audit |
| `session-audit` | `/bug-report session-audit` | Session lifecycle, cookies, CSRF, and state-management audit |
| `tech-debt` | `/bug-report tech-debt` | Technical debt mapping and prioritization audit |
| `tenant-isolation` | `/bug-report tenant-isolation` | Multi-tenant isolation and cross-tenant leakage audit |
| `test-review` | `/bug-report test-review` | Test suite quality, coverage gaps, and strategy audit |
| `upload-security` | `/bug-report upload-security` | File upload and media processing security audit |
| `ai-code-audit` | `/bug-report ai-code-audit` | AI-generated code detection, security, and quality audit |
| `dead-code`      | `/bug-report dead-code`      | Dead code, unused declarations, and cleanup audit |
| `security-sweep` | `/bug-report security-sweep` | Run all security scans in parallel via workers |
| `sec-recon`      | `/bug-report sec-recon`      | Codebase architecture map — run before deeper security scans |
| `sqli`           | `/bug-report sqli`           | SQL injection two-phase detection |
| `xss`            | `/bug-report xss`            | Cross-site scripting two-phase detection |
| `rce`            | `/bug-report rce`            | Remote code execution and command injection detection |
| `ssrf`           | `/bug-report ssrf`           | Server-side request forgery detection |
| `xxe`            | `/bug-report xxe`            | XML external entity injection detection |
| `idor`           | `/bug-report idor`           | Insecure direct object reference detection |
| `jwt`            | `/bug-report jwt`            | JWT weakness and signature bypass detection |
| `path-traversal` | `/bug-report path-traversal` | Path traversal and directory traversal detection |
| `ssti`           | `/bug-report ssti`           | Server-side template injection detection |
| `graphql`        | `/bug-report graphql`        | GraphQL injection and abuse detection |
| `business-logic` | `/bug-report business-logic` | Business logic flaw and workflow bypass detection |
| `missing-auth`   | `/bug-report missing-auth`   | Missing authentication and privilege escalation detection |

## Operating Modes

### General Mode
Use `/bug-report` when the user wants a broad repository scan for bugs, logic flaws, correctness issues, and high-confidence findings.

### Full Security Sweep Mode

Use `/bug-report security-sweep` (or when the user says "güvenlik taraması başlat", "run all security scans", "security sweep", etc.).

Launch all security scan subcommands **in parallel** using workers. Each worker is fully autonomous — it reads its subcommand file, executes the two-phase scan, and writes confirmed findings directly to `BUG-REPORT.md`.

**Execution order:**

1. Run `sec-recon` first (inline, not as a worker) to establish the codebase context. This writes the reconnaissance entry to `BUG-REPORT.md`.

2. Then launch all remaining scans **in parallel** as workers — one worker per subcommand:

   | Worker | Subcommand file |
   |--------|----------------|
   | Worker 1 | `subcommands/sqli.md` |
   | Worker 2 | `subcommands/xss.md` |
   | Worker 3 | `subcommands/rce.md` |
   | Worker 4 | `subcommands/ssrf.md` |
   | Worker 5 | `subcommands/xxe.md` |
   | Worker 6 | `subcommands/idor.md` |
   | Worker 7 | `subcommands/jwt.md` |
   | Worker 8 | `subcommands/path-traversal.md` |
   | Worker 9 | `subcommands/ssti.md` |
   | Worker 10 | `subcommands/graphql.md` |
   | Worker 11 | `subcommands/business-logic.md` |
   | Worker 12 | `subcommands/missing-auth.md` |

3. Each worker prompt must include:
   - The full content of its subcommand file as instructions
   - The repository path to scan
   - Instruction to write all confirmed findings to `BUG-REPORT.md` using the shared format, continuing the existing ID sequence

4. After all workers complete, read `BUG-REPORT.md` and re-sort all findings by severity (CRITICAL → HIGH → MEDIUM → LOW), deduplicating any overlapping findings across workers.

**Worker prompt template:**

> You are a security scanner. Execute the following security scan on the repository at `[repo_path]`.
> Write all confirmed [VULNERABLE] and [LIKELY VULNERABLE] findings to `BUG-REPORT.md` in the repository root using this format:
>
> ```
> ### BUG-[ID]: [title]
> Severity: CRITICAL | HIGH | MEDIUM | LOW
> Status: NEW
> File: path/to/file:line
> Component: [module]
>
> Problem: [what's wrong]
> Expected: [what should happen]
> Root Cause: [why]
> Impact: [impact]
> Verification: [taint trace + test command]
> Suggested Commit: [fix: ...]
> ---
> ```
>
> Read existing `BUG-REPORT.md` to continue the ID sequence. Do not write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries.
>
> Scan instructions:
> [full content of subcommand file]

### Focused Audit Mode
Use `/bug-report <subcommand>` when the user asks for a specific audit domain. The domain-specific checklist lives in the matching file under `subcommands/`.

- For `/bug-report auditcodex`: see [subcommands/auditcodex.md](subcommands/auditcodex.md)
- For `/bug-report api-audit`: see [subcommands/api-audit.md](subcommands/api-audit.md)
- For `/bug-report cache-audit`: see [subcommands/cache-audit.md](subcommands/cache-audit.md)
- For `/bug-report disaster-recovery`: see [subcommands/disaster-recovery.md](subcommands/disaster-recovery.md)
- For `/bug-report error-review`: see [subcommands/error-review.md](subcommands/error-review.md)
- For `/bug-report feature-flags-audit`: see [subcommands/feature-flags-audit.md](subcommands/feature-flags-audit.md)
- For `/bug-report integration-security`: see [subcommands/integration-security.md](subcommands/integration-security.md)
- For `/bug-report observability-audit`: see [subcommands/observability-audit.md](subcommands/observability-audit.md)
- For `/bug-report queue-audit`: see [subcommands/queue-audit.md](subcommands/queue-audit.md)
- For `/bug-report release-discipline`: see [subcommands/release-discipline.md](subcommands/release-discipline.md)
- For `/bug-report serialization-audit`: see [subcommands/serialization-audit.md](subcommands/serialization-audit.md)
- For `/bug-report session-audit`: see [subcommands/session-audit.md](subcommands/session-audit.md)
- For `/bug-report tech-debt`: see [subcommands/tech-debt.md](subcommands/tech-debt.md)
- For `/bug-report tenant-isolation`: see [subcommands/tenant-isolation.md](subcommands/tenant-isolation.md)
- For `/bug-report test-review`: see [subcommands/test-review.md](subcommands/test-review.md)
- For `/bug-report upload-security`: see [subcommands/upload-security.md](subcommands/upload-security.md)
- For `/bug-report ai-code-audit`: see [subcommands/ai-code-audit.md](subcommands/ai-code-audit.md)
- For `/bug-report dead-code`: see [subcommands/dead-code.md](subcommands/dead-code.md)
- For `/bug-report security-sweep`: see Full Security Sweep Mode section above
- For `/bug-report sec-recon`: see [subcommands/sec-recon.md](subcommands/sec-recon.md)
- For `/bug-report sqli`: see [subcommands/sqli.md](subcommands/sqli.md)
- For `/bug-report xss`: see [subcommands/xss.md](subcommands/xss.md)
- For `/bug-report rce`: see [subcommands/rce.md](subcommands/rce.md)
- For `/bug-report ssrf`: see [subcommands/ssrf.md](subcommands/ssrf.md)
- For `/bug-report xxe`: see [subcommands/xxe.md](subcommands/xxe.md)
- For `/bug-report idor`: see [subcommands/idor.md](subcommands/idor.md)
- For `/bug-report jwt`: see [subcommands/jwt.md](subcommands/jwt.md)
- For `/bug-report path-traversal`: see [subcommands/path-traversal.md](subcommands/path-traversal.md)
- For `/bug-report ssti`: see [subcommands/ssti.md](subcommands/ssti.md)
- For `/bug-report graphql`: see [subcommands/graphql.md](subcommands/graphql.md)
- For `/bug-report business-logic`: see [subcommands/business-logic.md](subcommands/business-logic.md)
- For `/bug-report missing-auth`: see [subcommands/missing-auth.md](subcommands/missing-auth.md)

## Shared Workflow

### Step 1: Repository Assessment

Map the project structure:
- Identify technology stack and dependencies
- Find main entry points and critical paths
- Check for existing tests and linting configurations
- Look for existing `BUG-REPORT.md` to continue ID sequence
- Scan for `TODO`, `FIXME`, `HACK`, `XXX`, `BUG` comments

### Scanning Scope

Always skip non-source directories and generated files:
- `node_modules/`, `vendor/`, `dist/`, `build/`, `.next/`, `__pycache__/`, `.venv/`
- Lock files (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Gemfile.lock`, `poetry.lock`)
- Minified files (`*.min.js`, `*.min.css`), source maps, compiled output
- Third-party code, vendored dependencies, and auto-generated files
- Focus exclusively on project-authored source code

### Step 2: Discovery

For large repositories (50+ source files), scan in parallel:
- Spawn up to 3 sub-agents to scan different areas simultaneously
- Split by category (security, logic, code quality) or by directory (frontend, backend, shared)
- Merge findings and deduplicate before generating the report

For general `/bug-report`, scan broad bug categories:

| Severity | Examples |
|----------|----------|
| CRITICAL | SQL injection, XSS, CSRF, auth bypass, data corruption, crashes, leaks |
| HIGH | Logic errors, race conditions, missing validation, wrong API contracts |
| MEDIUM | Swallowed exceptions, edge cases, integration problems |
| LOW | Deprecated APIs, dead code, N+1 queries, technical debt |

For `/bug-report <subcommand>`, follow the domain-specific checklist in the matching subcommand file. `auditcodex` is the exception to the repository-wide scan pattern: it audits the current diff (or last commit fallback) through Codex CLI and then writes only verified findings to `BUG-REPORT.md`.

### Step 3: Verify Each Finding

Every potential finding MUST be verified on the actual code before reporting:
- Read the suspect file and trace the full code path (callers, callees, error handlers)
- Confirm the issue is real -- not a pattern you misread, not handled elsewhere, not a deliberate choice
- Check if existing tests already cover the case (if a test exists and passes, it is likely not a bug)
- If you cannot reproduce or confirm the logic flaw by reading the code, discard the finding
- NEVER report a finding based on assumptions or pattern matching alone

Only verified findings proceed to documentation.

### Step 4: Document Each Finding

```
BUG-[ID]: [Brief description]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: NEW | CONFIRMED | IN_PROGRESS | FIXED | WONT_FIX
File: [path/to/file.ext:line_number]
Component: [affected module/feature]

Problem: [What's wrong - current behavior]
Expected: [What should happen]
Root Cause: [Why it happens - if determinable]
Impact: [User/system/business impact]
Verification: [How you confirmed this finding - specific code path or logic trace]
Suggested Commit: [Conventional commit message for the fix, e.g. "fix: prevent XSS in user input sanitizer"]
```

### Step 5: ID Management

Bug IDs must never reset. Always increment from the highest existing ID.
Check `BUG-REPORT.md`, `bugs.md`, `bug.md` for existing IDs.
If no existing bugs, start from BUG-001.

### Step 6: Generate Report

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

## Findings

[All findings sorted by severity: CRITICAL first, LOW last]
```

## Notes

- Zero false positives is more important than completeness -- only report verified findings
- ALL findings go under a single `## Findings` section -- no custom grouping headers (no "Technical Debt", "Architecture", etc.)
- Findings must be sorted by severity: CRITICAL first, then HIGH, MEDIUM, LOW
- Each finding uses `### BUG-[ID]` heading with `---` separator between entries
- If `bugs.md` or `bug.md` exists, merge into new report and delete old file
- Allowed commit types: fix, feat, refactor, chore, test, docs, perf, ci, build, security, cleanup
- Suggested Commit messages NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
