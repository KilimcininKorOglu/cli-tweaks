---
name: tenant-isolation
description: >
  This skill MUST be invoked when the user says "tenant isolation", "multi-tenant audit",
  "veri sızıntısı", "data leakage", "tenant güvenliği", "multi-tenant security"
  or any variation requesting multi-tenant isolation and data leakage analysis.
  SHOULD also invoke when user mentions "tenant_id filter", "cross-tenant access",
  "IDOR", "noisy neighbor", or asks to audit tenant data separation. Audits all
  layers of tenant isolation including database queries, application context,
  caching, file storage, and admin access for data leakage risks.
argument-hint: "[--focus data-isolation|app-layer|boundary-tests|admin|all]"
---

# Multi-Tenant Isolation & Data Leakage Audit

You are a security architect auditing tenant-to-tenant data isolation in a multi-tenant application. Data leakage between tenants is the most devastating security event for a SaaS company — it instantly destroys customer trust.

## 1. Data Isolation Model

- At which layer is tenant isolation? (shared database + tenant_id column, schema-based separation, database-based separation)
- Does EVERY database query include a tenant_id filter? A single forgotten filter = all tenants' data exposed
- Is there automatic tenant filtering at ORM/query builder level? (middleware, global scope, row-level security)
- Are there raw SQL queries? Is the tenant filter added manually in those? (high risk of forgetting)
- Can JOIN queries cross tenant boundaries?
- Do aggregate queries mix data across tenants? (sum, average calculations)
- Do database indexes include tenant_id? (performance + security)

## 2. Application Layer Isolation

- Is tenant context determined at the start of the request and propagated to all layers?
- Is tenant context preserved in background jobs? (does the queue message contain tenant_id)
- Is there tenant separation in cache? (tenant_id in cache key — otherwise tenant A sees tenant B's cached data)
- Is there tenant separation in file storage? (separate directories/buckets)
- Is there tenant filtering in search indexes? (Elasticsearch, Algolia — tenant_id filter)
- Do log entries contain tenant information? (can you tell which tenant's operation it is)

## 3. Tenant Boundary Tests

- Can tenant A access tenant B's data by changing the ID in the URL? (IDOR)
- Can the tenant_id parameter be manipulated in API requests?
- Does one tenant's excessive usage affect other tenants? (noisy neighbor)
- Are resource limits per-tenant? (CPU, memory, storage, API rate limit)
- When a tenant is deleted, is ALL their data cleaned up? (backups, logs, cache, search indexes included)

## 4. Admin Access

- Can platform administrators access tenant data? Is this access logged?
- Is there per-tenant impersonation capability? Is it secure?
- If cross-tenant reporting exists: is tenant data anonymized?

## Verification

Every finding MUST be verified on the actual code before reporting:
- Read the suspect file and trace the full code path (callers, callees, error handlers)
- Confirm the issue is real -- not a pattern you misread, not handled elsewhere, not a deliberate choice
- Check if existing tests already cover the case (if a test exists and passes, it is likely not a bug)
- If you cannot confirm the issue by reading the code, discard the finding
- NEVER report a finding based on assumptions or pattern matching alone

## Output Format

All findings are written to `BUG-REPORT.md` in the repository root, sharing a single ID sequence across all audit skills.

Check `BUG-REPORT.md` for existing IDs and increment from the highest. If none exists, start from BUG-001.

For each verified finding:

```
BUG-[ID]: [Brief description]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: NEW
File: [path/to/file.ext:line_number]
Component: [affected module/feature]

Problem: [What's wrong - current behavior]
Expected: [What should happen]
Root Cause: [Why it happens - if determinable]
Impact: [User/system/business impact]
Verification: [How you confirmed this - specific code path or logic trace]
Suggested Commit: [Conventional commit message, e.g. "fix: add rate limiting to payment endpoint"]
```

If `BUG-REPORT.md` already exists, append new findings under `## Findings` and update the summary table.
If it does not exist, create it with:

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
- Allowed commit types: fix, feat, refactor, chore, test, docs, perf, ci, build, security, cleanup
- Suggested Commit messages NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
