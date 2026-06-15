# Language Reference

Per-language building blocks for the eight supported languages. Detect the project's language/framework in Phase 1, then use the matching row from each table. These are the integration points — wire them into the project's existing session/middleware/admin code; do NOT scaffold a new app.

If the project already has a session or cookie system, add `visitor_id` to it instead of creating a separate cookie (see SKILL.md Phase 2).

## visitor_id generation (crypto-secure, 16 bytes → 32-char hex)

Use the language's cryptographic RNG, not a general-purpose PRNG and not a UUID library.

| Language | Generator                                                                                                                    |
|----------|------------------------------------------------------------------------------------------------------------------------------|
| Go       | `crypto/rand`: `rand.Read(b)` on a `[16]byte`, then `hex.EncodeToString(b[:])`                                               |
| Node.js  | `crypto.randomBytes(16).toString('hex')`                                                                                     |
| Python   | `secrets.token_hex(16)`                                                                                                      |
| PHP      | `bin2hex(random_bytes(16))`                                                                                                  |
| Ruby     | `SecureRandom.hex(16)`                                                                                                       |
| Java     | `new SecureRandom().nextBytes(b)` on a `byte[16]`, then `HexFormat.of().formatHex(b)` (Java 17+; pre-17 hex-encode manually) |
| C#       | `RandomNumberGenerator.GetHexString(32)` (.NET 8+) or `Convert.ToHexString(RandomNumberGenerator.GetBytes(16))` (.NET 5+)    |
| Rust     | `getrandom` crate fills a `[u8; 16]`, then `hex::encode(buf)` (the `hex` crate); or use `rand`                               |

## Cookie set (visitor_id; flags from SKILL.md Phase 2)

All must set: `Path=/`, `Max-Age=1 year`, `HttpOnly`, `SameSite=Lax`, `Secure` in production.

| Framework           | Set-cookie call                                                                                                                                                    |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Go (net/http)       | `http.SetCookie(w, &http.Cookie{Name:"visitor_id", Value:id, Path:"/", MaxAge:31536000, HttpOnly:true, SameSite:http.SameSiteLaxMode, Secure:isProd})`             |
| Express             | `res.cookie('visitor_id', id, {maxAge:31536000000, httpOnly:true, sameSite:'lax', secure:isProd, path:'/'})`                                                       |
| Flask               | `resp.set_cookie('visitor_id', id, max_age=31536000, httponly=True, samesite='Lax', secure=is_prod)`                                                               |
| Django              | `response.set_cookie('visitor_id', id, max_age=31536000, httponly=True, samesite='Lax', secure=is_prod)`                                                           |
| PHP                 | `setcookie('visitor_id', $id, ['expires'=>time()+31536000,'path'=>'/','httponly'=>true,'samesite'=>'Lax','secure'=>$isProd])`                                      |
| Rails               | `cookies[:visitor_id] = { value:id, expires:1.year.from_now, httponly:true, same_site: :lax, secure:Rails.env.production? }`                                       |
| Spring              | `ResponseCookie.from("visitor_id", id).path("/").maxAge(Duration.ofDays(365)).httpOnly(true).sameSite("Lax").secure(isProd).build()` → add as `Set-Cookie` header  |
| ASP.NET Core        | `Response.Cookies.Append("visitor_id", id, new CookieOptions{ MaxAge=TimeSpan.FromDays(365), HttpOnly=true, SameSite=SameSiteMode.Lax, Secure=isProd, Path="/" })` |
| Axum / Actix (Rust) | build a `Set-Cookie` header with the same flags (e.g. the `cookie` crate, or `axum-extra` `CookieJar`)                                                             |

## Fire-and-forget LogEvent (never block the request; discard errors)

Critical: in detached tasks, do NOT reuse the request context/scope — it ends when the handler returns and can kill the insert mid-flight.

| Language       | Pattern                                                                                                                                                    |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Go             | `go func(){ ctx,cancel:=context.WithTimeout(context.Background(),5*time.Second); defer cancel(); pool.Exec(ctx, ...) }()` — fresh ctx, NOT the request ctx |
| Node.js        | `db.query(...).catch(()=>{})`                                                                                                                              |
| Python (async) | `t=asyncio.create_task(db.execute(...)); _bg.add(t); t.add_done_callback(_bg.discard)` (keep a ref; needs a running loop)                                  |
| Python (sync)  | a `ThreadPoolExecutor`: `executor.submit(insert, ...)`                                                                                                     |
| PHP            | request is synchronous — keep the INSERT minimal, or flush the response first with `fastcgi_finish_request()` then insert, or push to a queue              |
| Ruby           | `Thread.new { ActiveRecord::Base.connection_pool.with_connection { insert } }`, or enqueue a background job                                                |
| Java (Spring)  | `@Async` method, or `CompletableFuture.runAsync(() -> repo.insert(...))` (on a dedicated executor)                                                         |
| C#             | `_ = Task.Run(async () => { try { await db.InsertAsync(...); } catch { } })` — discard the Task                                                            |
| Rust           | `tokio::spawn(async move { let _ = sqlx::query(...).execute(&pool).await; })` (clone the pool, not request state)                                          |

## Error-event hook (auto-log `error` events)

Hook the framework's central error handler so every unhandled error becomes an `error` audit event.

| Framework    | Hook                                                                                   |
|--------------|----------------------------------------------------------------------------------------|
| Go / Echo    | custom `HTTPErrorHandler` wrapper                                                      |
| Express      | error middleware `app.use((err, req, res, next) => { ... })`                           |
| Django       | middleware `process_exception`                                                         |
| FastAPI      | `@app.exception_handler(Exception)`                                                    |
| Flask        | `@app.errorhandler(Exception)`                                                         |
| Laravel      | `App\Exceptions\Handler::report()` (or the `withExceptions` hook in bootstrap/app.php) |
| Rails        | `rescue_from StandardError` in `ApplicationController`                                 |
| Spring       | `@ControllerAdvice` class with `@ExceptionHandler`                                     |
| ASP.NET Core | exception middleware: `app.UseExceptionHandler(...)`, or `IExceptionHandler` (.NET 8+) |
| Axum (Rust)  | a `tower` middleware layer that inspects the response, or map errors in handlers       |

## Middleware / injection point (where to read-or-set visitor_id and emit page_view)

| Framework    | Point                                                            |
|--------------|------------------------------------------------------------------|
| Go / Echo    | `e.Use(middleware)`                                              |
| Express      | `app.use(...)` early in the chain                                |
| Django       | custom class in `MIDDLEWARE`                                     |
| FastAPI      | `@app.middleware("http")`                                        |
| Flask        | `@app.before_request`                                            |
| Laravel      | global middleware registered in the HTTP kernel                  |
| Rails        | `before_action` in `ApplicationController`, or a Rack middleware |
| Spring       | `HandlerInterceptor` or a servlet `Filter`                       |
| ASP.NET Core | middleware via `app.Use(...)` (or `IMiddleware`)                 |
| Axum (Rust)  | a `tower` layer or `middleware::from_fn`                         |

## Notes

- **Prefer reusing existing infrastructure.** If the project already has session/auth middleware, an ORM, a migration system, an admin panel, or a background job runner, extend those rather than adding parallel machinery (see SKILL.md "Adapting to Framework").
- **Languages not listed here:** apply the same five integration points — crypto-secure 16-byte hex id, cookie with the Phase 2 flags, fire-and-forget insert on a fresh context, central error hook, and an early request middleware. The pattern is language-agnostic; only the API names change.
- **Async vs sync runtimes:** fire-and-forget assumes a long-lived server process (Go, Node, Java, .NET, Rust, async Python). For request-per-process models (classic PHP-FPM), either flush the response before inserting or route events through a queue/worker.
