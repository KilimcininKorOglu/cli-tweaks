# Middleware/Interceptor Chain Mapping by Language & Framework

The reference chain (from the original Gin-Gonic note) is:

```
AuthMiddleware -> PermissionCheck -> RequestLoggingMiddleware -> ValidationMiddleware -> AuditLogMiddleware -> Handler
```

Position rules (apply regardless of language):
1. Auth and permission checks run first; do not log or audit a request that never authenticates/authorizes.
2. `RequestLoggingMiddleware` runs after auth/permission so the logged `userId`/`username` is known, and
   before the handler so request metadata is captured even if the handler later fails.
3. `AuditLogMiddleware` (or an audit call from inside the handler/service layer) only fires for
   data-mutating operations (Insert/Update/Delete), after validation has confirmed the request is
   well-formed, and ideally inside the same transaction as the actual write so the audit row and the
   business write commit or roll back together.
4. `RequestLoggingMiddleware` should finalize (write `responseStatus`/`responseTimeMs`) after the
   handler returns, not before, since those values are not known until the request completes.

Below is the mechanism name to use per language/framework. Detect the framework from the project's
manifest file (`go.mod`, `package.json`, `requirements.txt`/`pyproject.toml`, `pom.xml`/`build.gradle`,
`*.csproj`, `Gemfile`, `composer.json`, `Cargo.toml`) before writing code, and follow the idiomatic
pattern already used elsewhere in that codebase.

| Language   | Framework             | Mechanism                                         |
|------------|------------------------|----------------------------------------------------|
| Go         | Gin                    | `gin.HandlerFunc` middleware (as in the source note) |
| Go         | net/http, Chi, Echo    | `http.Handler` wrapping / framework-specific middleware |
| Node.js    | Express                | `app.use()` middleware function `(req, res, next)` |
| Node.js    | NestJS                 | `Interceptor` (logging) + `Guard` (auth/permission) |
| Node.js    | Fastify                | `onRequest`/`onResponse` hooks                     |
| Python     | Django                 | `MIDDLEWARE` class with `__call__`                 |
| Python     | FastAPI                | `Depends()` dependency or `BaseHTTPMiddleware`     |
| Python     | Flask                  | `before_request`/`after_request` hooks             |
| Java       | Spring Boot            | `HandlerInterceptor` or `OncePerRequestFilter`     |
| Kotlin     | Spring Boot, Ktor      | Same as Spring Boot, or Ktor `Plugin`/`Interceptor` |
| C#         | ASP.NET Core           | `IMiddleware` / custom middleware delegate         |
| Ruby       | Rails                  | `before_action`/`around_action` filter             |
| PHP        | Laravel                | `Middleware` class registered in `Kernel.php`      |
| PHP        | Symfony                | `EventSubscriber` on `kernel.request`/`kernel.response` |
| Rust       | Axum                   | `tower::Layer` / `from_fn` middleware              |
| Rust       | Actix-web               | `Transform`/middleware service                     |

## Sensitive field redaction

Before writing `requestBody`/`oldValues`/`newValues` to any log table, redact known-sensitive field
names regardless of language: `password`, `passwordConfirmation`, `token`, `accessToken`,
`refreshToken`, `secret`, `apiKey`, `authorization`, `creditCard`, `cardNumber`, `cvv`, `ssn`,
`nationalId`. Replace their values with `"[REDACTED]"` rather than omitting the key, so the shape of
the payload is still visible in the log.

## Non-blocking writes

Centralized logging must not add latency to the request path. Write request/audit log rows
asynchronously (background goroutine/queue/task, fire-and-forget with error logging, or a buffered
batch writer) rather than blocking the response on the log write, unless the project already has a
strict consistency requirement that argues otherwise (e.g. log row must exist before returning 200).
