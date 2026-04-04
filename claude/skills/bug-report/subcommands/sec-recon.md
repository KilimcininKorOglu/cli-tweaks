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

Write a single entry to `BUG-REPORT.md` using the shared report format from `../SKILL.md`:

- **Severity**: LOW
- **Status**: NEW
- **Component**: Architecture / Security Posture
- **Problem**: Document the security-relevant architecture findings. Include: tech stack, auth mechanism, sensitive data inventory, trust boundaries, high-risk patterns observed (e.g., no auth middleware on admin routes, credentials in source, unsafe deserialization libraries present).
- **Expected**: Comprehensive security posture documented.
- **Root Cause**: N/A — reconnaissance phase.
- **Impact**: Informs all subsequent vulnerability scans.
- **Verification**: Findings based on direct codebase exploration.
- **Suggested Commit**: `chore: document security architecture reconnaissance`

Use title: `BUG-XXX: Security Architecture Reconnaissance` (continue existing ID sequence).

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
