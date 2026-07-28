# General-Purpose Application Logging (`app_logs`) by Language

This covers the third log table, `app_logs`: free-form `TRACE`/`DEBUG`/`INFO`/`WARN`/`ERROR`/`FATAL`
logging that any part of the codebase can call (services, background jobs, startup code, error
handlers), not tied to an HTTP request like `request_logs`/`audit_logs` are.

## Core principle: add a sink, don't replace the logger

If the project already uses a logging library, do not write a new logger from scratch. Add a
custom sink/handler/transport/appender to the existing library that also writes to `app_logs`,
in addition to its existing stdout/file output. Detect the existing library from the manifest file
before choosing an approach.

| Language    | Common library                          | DB sink mechanism                                                                             |
|-------------|-----------------------------------------|-----------------------------------------------------------------------------------------------|
| Go          | `log/slog` (stdlib), `zap`, `zerolog`   | custom `slog.Handler` / `zapcore.Core` / `zerolog.Hook` that also inserts into `app_logs`     |
| Node.js     | `winston`, `pino`                       | custom `winston.Transport` subclass / `pino` transport stream                                 |
| Python      | `logging` (stdlib)                      | custom `logging.Handler` subclass implementing `emit()`                                       |
| Java/Kotlin | SLF4J + Logback or Log4j2               | custom Logback `Appender` / Log4j2 `Appender`, wrapped in an async appender                   |
| C#          | `Microsoft.Extensions.Logging`, Serilog | custom `ILoggerProvider`/`ILogger` / Serilog sink (model on `Serilog.Sinks.PeriodicBatching`) |
| Ruby        | `Logger` (stdlib), `semantic_logger`    | custom `Logger` device (`def write(msg)`) / `semantic_logger` appender                        |
| PHP         | Monolog                                 | custom handler extending `Monolog\Handler\AbstractProcessingHandler`                          |
| Rust        | `log` + `env_logger`, or `tracing`      | custom `log::Log` implementation / `tracing_subscriber::Layer`                                |

If no logging library exists yet, introduce the most idiomatic stdlib-adjacent one for that
language/ecosystem (e.g. `slog` for Go, `logging` for Python) rather than a heavyweight new
dependency, unless the project's conventions already point to something else.

## Required behavior of the DB sink

1. **Never block the calling code on the DB write.** Buffer log entries in memory and flush them
   in batches on a timer or size threshold (e.g. every 100 entries or every 2 seconds, whichever
   first); most libraries listed above have a built-in async/buffered appender pattern, so use it
   instead of inventing one.
2. **Never raise/crash the application if the DB write fails.** Catch the error, fall back to the
   library's normal stdout/file output (which keeps running independently of the DB sink), and do
   not retry indefinitely.
3. **Filter by level before hitting the DB.** Sending every `TRACE`/`DEBUG` line to the database is
   rarely desirable. Default the DB sink's minimum level to `INFO`, and leave file/stdout output at
   whatever level the project already uses; these can run at different verbosity independently.
4. **Capture structured context, not just the message string.** Pass through whatever
   key/value fields the call site attaches (e.g. `logger.Error("failed", "userId", id, "err", err)`
   in Go, or `logger.error("failed", extra={"userId": id})` in Python) into the `context` JSON
   column, after applying the same sensitive-field redaction list used for `request_logs`/`audit_logs`
   (`password`, `token`, `secret`, `apiKey`, `authorization`, `creditCard`, etc.).
5. **Attach `requestId` opportunistically, never require it.** When a log call happens inside an
   HTTP request (i.e. the request-scoped context/goroutine-local/thread-local is available), include
   the current `requestId` so the entry can be correlated with `request_logs`. When it does not
   (startup code, a cron job, a CLI command), leave it `NULL`/`null`; `app_logs` must work standalone.

## What NOT to log here

- Do not duplicate `request_logs`/`audit_logs` entries into `app_logs`; they serve different
  purposes and already have their own tables. `app_logs` is for everything else: caught exceptions,
  startup/shutdown events, background job progress, third-party API call failures, etc.
- Do not log full request/response bodies through the general logger; that is `request_logs`'s job.
