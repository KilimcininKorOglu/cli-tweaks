---
name: bug-report
description: >
  Systematic bug analysis and security auditing. Use `/bug-report` for general
  scans, `/bug-report <subcommand>` for focused audits, `/bug-report security-sweep`
  for parallel security scans. All modes write verified findings to BUG-REPORT.md.
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

Jump to the **Security Sweep Orchestration** section below and follow it.

### Path C: General scan (`/bug-report` with no subcommand)

Execute the **Shared Workflow** below from Step 1 through Step 6.
If `--severity` flag provided, filter findings by that severity level.

---

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

Scan broad bug categories:

| Severity | Examples |
|----------|----------|
| CRITICAL | SQL injection, XSS, CSRF, auth bypass, data corruption, crashes, leaks |
| HIGH     | Logic errors, race conditions, missing validation, wrong API contracts |
| MEDIUM   | Swallowed exceptions, edge cases, integration problems |
| LOW      | Deprecated APIs, dead code, N+1 queries, technical debt |

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

---

## Report Rules

- Zero false positives is more important than completeness -- only report verified findings
- ALL findings go under a single `## Findings` section -- no custom grouping headers
- Findings sorted by severity: CRITICAL first, then HIGH, MEDIUM, LOW
- Each finding uses `### BUG-[ID]` heading with `---` separator between entries
- If `bugs.md` or `bug.md` exists, merge into new report and delete old file
- Allowed commit types: fix, feat, refactor, chore, test, docs, perf, ci, build, security, cleanup
- Suggested Commit messages NEVER include bug IDs
- Always write the report in English only, regardless of conversation language

---

## Security Sweep Orchestration

Use when the user says `/bug-report security-sweep`, "guvenlik taramasi baslat", "run all security scans", or "security sweep".

Launch all security scan subcommands **in parallel** using workers. Each worker is fully autonomous -- it reads its subcommand file, executes the three-phase scan (recon, batched verify, merge), and writes confirmed findings directly to `BUG-REPORT.md`.

**Resume support:** Before launching each worker, read `BUG-REPORT.md` and check for its completion marker (`<!-- scan:SUBCOMMAND completed -->`). Skip that worker if the marker exists.

**Execution order:**

1. Run `sec-recon` first (inline, not as a worker) to establish the codebase context. This writes the reconnaissance entry to `BUG-REPORT.md`.

2. Then launch all remaining scans **in parallel** as workers. Skip any worker whose completion marker already exists in `BUG-REPORT.md`:

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

3. Each worker prompt must include:
   - The full content of its subcommand file as instructions
   - The repository path to scan
   - Instruction to write all confirmed findings to `BUG-REPORT.md` using the shared format, continuing the existing ID sequence

4. After all workers complete, read `BUG-REPORT.md` and re-sort all findings by severity (CRITICAL -> HIGH -> MEDIUM -> LOW), deduplicating any overlapping findings across workers.

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

---

## Subcommand Reference

| Subcommand             | Description                                                              |
|------------------------|--------------------------------------------------------------------------|
| `auditcodex`           | Codex CLI diff audit with validated findings                             |
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
