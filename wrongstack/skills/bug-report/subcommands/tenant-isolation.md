# Multi-Tenant Isolation & Data Leakage Audit

This subcommand replaces the old standalone `/tenant-isolation` skill.

## Command

```bash
/bug-report tenant-isolation [--focus data-isolation|app-layer|boundary-tests|admin|all]
```

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

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
