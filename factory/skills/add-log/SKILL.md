---
name: add-log
description: Implement centralized API request logging, audit logging, and general-purpose application logging (request_logs + audit_logs + app_logs schema) for any language or framework
argument-hint: "[optional: target endpoint or directory]"
disable-model-invocation: true
allowed-tools:
  - read
  - edit
  - grep
  - glob
  - exec
---

Implement centralized logging for the current project: $ARGUMENTS

This skill is language-agnostic. It implements three independent log tables/collections, backed by
`reference/log-schema-sql.sql` (relational) or `reference/log-schema-nosql.md` (document store):

- `request_logs` + `audit_logs`: populated by the middleware chain in
  `reference/framework-middleware-map.md` (Auth -> PermissionCheck -> RequestLoggingMiddleware ->
  Validation -> AuditLogMiddleware -> Handler).
- `app_logs`: populated by a DB sink/handler/transport added to the project's existing logging
  library, per `reference/general-logging-map.md`. Independent of HTTP context; works from
  background jobs, startup code, and any non-HTTP call site.

@reference/log-schema-sql.sql

@reference/log-schema-nosql.md

@reference/framework-middleware-map.md

@reference/general-logging-map.md

## Steps

1. **Detect stack.** Identify the project's language, web framework, and persistence layer by
   reading its manifest file (`go.mod`, `package.json`, `requirements.txt`/`pyproject.toml`,
   `pom.xml`/`build.gradle`, `*.csproj`, `Gemfile`, `composer.json`, `Cargo.toml`) and any existing
   ORM/driver config. Look up the matching row in `reference/framework-middleware-map.md` for the
   correct middleware/interceptor mechanism.

2. **Check for an existing logging setup.** Search the codebase for existing logging/audit code
   (grep for "audit", "log", "middleware", "interceptor") before adding anything. If a centralized
   logger or audit mechanism already exists, extend it instead of creating a parallel one.

3. **Confirm the log storage.** Determine whether the project is relational or document-based from
   its existing persistence layer. Do not introduce a new database technology to satisfy this skill;
   reuse whatever the project already uses. If genuinely no database is configured yet, ask the user
   which one to set up rather than guessing.

4. **Create the schema.** Adapt the DDL in `reference/log-schema-sql.sql` (or the collection shape in
   `reference/log-schema-nosql.md`) to the target database's dialect and add it through the project's
   existing migration mechanism (migration files, ORM schema definitions, etc.); do not hand-edit a
   live database directly. Two tables/collections: `request_logs` and `audit_logs`, exactly as
   specified in the reference files; do not collapse them into one table.

5. **Implement the request logger.** Add a `RequestLoggingMiddleware` (or the idiomatic equivalent
   per `reference/framework-middleware-map.md`) that, for every API request, records: timestamp,
   `requestId` (generate a UUID per request for correlation), `userId`/`username` (from the
   already-authenticated context), `ipAddress`, `userAgent`, `httpMethod`, `endpoint`, `module`,
   `action`, redacted `queryParams`/`requestBody`, and, after the handler completes,
   `responseStatus`, `responseTimeMs`, `errorMessage`. Apply the redaction list in
   `reference/framework-middleware-map.md` before persisting the body.

6. **Implement the audit logger.** Add an `AuditLogMiddleware`/service call that fires only for
   data-mutating operations (Insert/Update/Delete, including bulk variants), recording
   `actionType`, `tableName`, `recordId` (or `affectedCount` for bulk ops), `oldValues`/`newValues`,
   and the correlating `requestId`/`userId`. Write the audit row in the same transaction as the
   business write whenever the persistence layer supports transactions, so they commit or roll back
   together.

7. **Wire the chain.** Insert both middlewares into the existing router/handler chain in the position
   described in `reference/framework-middleware-map.md` (logging after auth/permission, audit log
   after validation, both before/around the handler); do not place logging before authentication.
   Follow the exact registration style already used in the project for other middlewares.

8. **Make writes non-blocking.** Persist log rows asynchronously (background task/queue/goroutine)
   so logging never adds latency to the request path, unless the project has an explicit requirement
   for synchronous audit writes.

9. **Verify the request/audit logging.** Add or run a test that hits a mutating endpoint and
   asserts: a `request_logs` row was created with the correct status/method/endpoint, and a
   corresponding `audit_logs` row was created with the correct `actionType`/`tableName`. If the
   project has no test infrastructure, manually exercise the endpoint and inspect the resulting
   rows instead of asserting success without evidence.

10. **Implement the general application logger.** Per `reference/general-logging-map.md`, detect
    the project's existing logging library (do not introduce a new one if one is already in use)
    and add a custom DB sink/handler/transport/appender that writes to `app_logs`. The sink must:
    buffer and flush in batches rather than writing on every call, default its minimum level to
    `INFO` (file/stdout output can stay at whatever level the project already uses), never crash
    the app if the DB write fails, redact sensitive fields in the structured `context` the same way
    as `requestBody`, and attach the current `requestId` only when one is available from
    request-scoped context (never require it).

11. **Verify the general logger.** Trigger a log call from a non-HTTP code path (e.g. a background
    job, a startup log line, or a deliberately caught exception) and confirm a row appears in
    `app_logs` with the correct `level`/`message`/`loggerName`, independent of any HTTP request.

## Constraints

- Never log raw passwords, tokens, secrets, or other sensitive fields; redact per the list in
  `reference/framework-middleware-map.md` (applies to `request_logs`/`audit_logs`) and
  `reference/general-logging-map.md` (applies to `app_logs`).
- Never block the main request/response cycle, or any calling code, on a log write.
- Never merge `request_logs`, `audit_logs`, and `app_logs` into a single table; keep the three-table
  split.
- Never duplicate `request_logs`/`audit_logs` entries into `app_logs`; they serve different purposes.
- Match the target codebase's existing naming convention (snake_case vs camelCase, etc.) instead of
  copying the casing used in the reference files verbatim.
