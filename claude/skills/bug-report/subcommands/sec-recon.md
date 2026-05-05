# Security Reconnaissance

This subcommand maps the codebase architecture and security posture, writing findings directly to `BUG-REPORT.md`. Run this before deeper vulnerability scans for best results.

## Command

```bash
/bug-report sec-recon
```

You are performing the first phase of a security assessment. Your goal is to understand the codebase deeply. You are NOT looking for specific vulnerabilities yet — this is pure reconnaissance.

## What to Explore

**Technology stack**
- Languages, frameworks, template engines, ORMs, task queues
- Package manager manifests (package.json, requirements.txt, go.mod, Gemfile, pom.xml, etc.)
- Infrastructure hints: Dockerfiles, docker-compose, Kubernetes manifests, CI/CD configs

**Databases and storage**
- SQL, NoSQL, cache layers, message brokers
- Connection strings, ORM models, migration files

**Authentication and authorization**
- Auth libraries and middleware
- Session configs, OAuth/OIDC providers, JWT usage, API key patterns
- Role/permission system, admin panel

**Entry points**
- HTTP routes, GraphQL schemas, gRPC definitions
- CLI commands, WebSocket handlers, scheduled jobs, message consumers

**Data flow and trust boundaries**
- How user input enters the system, gets processed, stored, and returned
- Where the system transitions between trusted and untrusted contexts
- PII, credentials, tokens, financial data — where stored and how accessed

**High-risk areas**
- File upload handling
- External API calls and webhook receivers
- Deserialization points
- Dynamic query/command construction

## Output

Write the reconnaissance findings to `BUG-REPORT.md` under a dedicated section — **NOT as a numbered BUG entry**. Reconnaissance is architectural documentation, not a vulnerability finding.

### Format

If `BUG-REPORT.md` does not exist, create it with this header structure. If it exists, insert/replace a `## System Architecture` section between `## Summary` and `## Findings`:

```markdown
# Bug Report

## Summary

(existing summary, or empty)

## System Architecture

_Last updated: YYYY-MM-DD via /bug-report sec-recon_

### Technology Stack
- Languages, frameworks, ORMs, template engines
- Package manifests scanned
- Infrastructure (Docker, Kubernetes, CI/CD)

### Authentication & Authorization
- Auth libraries and middleware
- Session/JWT/OAuth configuration
- Role and permission system

### Data Storage
- Databases, caches, message brokers
- Sensitive data locations (PII, credentials, tokens, financial)

### Entry Points
- HTTP/GraphQL/gRPC routes
- CLI, WebSocket, scheduled jobs, consumers

### Trust Boundaries
- Where untrusted input enters
- Where trust transitions occur

### High-Risk Patterns Observed
- Notable observations relevant to subsequent scans (e.g., no auth middleware on admin routes, dynamic query construction, deserialization libraries in use)

## Findings

(existing BUG entries — sec-recon does NOT add a numbered entry here)
```

### Rules

- **Do not assign a BUG-XXX ID to reconnaissance.**
- **Do not use the standard finding format (Severity/Status/File/Component/Suggested Commit/Problem/Expected/Root Cause/Impact/Verification).**
- **Do not increment the BUG ID counter.**
- If a `## System Architecture` section already exists, replace it in place (do not duplicate).
- If subsequent scan subcommands need to reference architectural context, they read this section directly.

## Shared Audit Rules

For BUG entries written by other subcommands, use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`. The architectural section produced by this subcommand is exempt from those rules.
