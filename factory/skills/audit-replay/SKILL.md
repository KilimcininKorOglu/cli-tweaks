# Audit Log + Session Replay

This skill MUST be invoked when the user says "audit log", "audit replay", "session replay", "rrweb", "kullanıcı takip", "kullanıcı izleme", "event sourcing", "user tracking", "visitor tracking", "oturum kaydı", "replay ekle", "audit ekle", "kullanıcı hareketleri", "action log", or any variation requesting user action tracking, audit event logging, or session replay recording. SHOULD also invoke when user mentions "what did the user do", "debug user session", "replay user actions", or wants to add observability for user behavior.

Add user action tracking and visual session replay to any web project. Two systems working together:

1. **Audit Event Log** — Backend event sourcing. Every user action (search, page view, form submit, preference change) recorded as a timestamped event in the database. Admin panel shows per-visitor timeline.
2. **Session Replay** — Frontend DOM recording via rrweb. Mouse movements, clicks, scrolls, and page mutations captured and replayed as video in admin panel.

Both systems share a `visitor_id` cookie for correlation.

## Usage

```
/audit-replay                # Full setup: scan project, add both systems
/audit-replay scan           # Scan only — show what would change
/audit-replay events-only    # Add only audit event log (no rrweb)
/audit-replay replay-only    # Add only session replay (assumes events exist)
```

## How It Works

### Phase 1: Project Detection

Detect the project's language, framework, database, and admin panel:

| Language | Frameworks                    | Database            |
|----------|-------------------------------|---------------------|
| Go       | Echo, Gin, Chi, Fiber, net/http | PostgreSQL, MySQL, SQLite |
| Node.js  | Express, Fastify, Koa, Next.js | PostgreSQL, MongoDB, SQLite |
| Python   | Flask, Django, FastAPI         | PostgreSQL, SQLite  |
| PHP      | Laravel, Symfony, plain        | MySQL, PostgreSQL   |
| Ruby     | Rails, Sinatra                 | PostgreSQL, SQLite  |

Identify:
1. **Session/cookie mechanism** — existing session middleware, cookie library, auth system
2. **Database layer** — ORM, query builder, raw SQL, migration system
3. **Admin panel** — existing admin routes, templates, authentication
4. **Template engine** — where to inject rrweb scripts
5. **Static file serving** — where to place rrweb JS files

### Phase 2: Visitor ID

Every visitor gets a persistent anonymous ID via cookie. Implementation depends on framework:

**Cookie specification:**

| Property   | Value                                 |
|------------|---------------------------------------|
| Name       | `visitor_id`                          |
| Value      | 32-char hex string (crypto/rand)      |
| Path       | `/`                                   |
| Max-Age    | 1 year (365 * 24 * 3600)             |
| HttpOnly   | true                                  |
| SameSite   | Lax                                   |
| Secure     | true (production) / false (localhost) |

**ID generation** — use the language's crypto-secure random, not UUIDs (avoids external dependency):

| Language | Generator                                                |
|----------|----------------------------------------------------------|
| Go       | `crypto/rand` → `hex.EncodeToString(16 bytes)`           |
| Node.js  | `crypto.randomBytes(16).toString('hex')`                 |
| Python   | `secrets.token_hex(16)`                                  |
| PHP      | `bin2hex(random_bytes(16))`                              |
| Ruby     | `SecureRandom.hex(16)`                                   |

**Injection point** — add to existing session/preference/auth middleware. If none exists, create a minimal middleware that reads/writes the cookie on every request.

### Phase 3: Database Schema

Create two tables. Use the project's migration system if one exists; otherwise create a standalone SQL file.

```sql
-- Audit events: one row per user action
CREATE TABLE IF NOT EXISTS audit_events (
    id          BIGSERIAL PRIMARY KEY,
    visitor_id  TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    event_data  JSONB NOT NULL DEFAULT '{}',
    path        TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_visitor ON audit_events(visitor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC);

-- Replay sessions: rrweb event batches per visitor
CREATE TABLE IF NOT EXISTS replay_sessions (
    id          BIGSERIAL PRIMARY KEY,
    visitor_id  TEXT NOT NULL,
    events      JSONB NOT NULL DEFAULT '[]',
    page_url    TEXT NOT NULL DEFAULT '',
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_replay_visitor ON replay_sessions(visitor_id, started_at DESC);
```

**Database adapter notes:**
- MySQL: Use `JSON` instead of `JSONB`, `BIGINT AUTO_INCREMENT` instead of `BIGSERIAL`, `DATETIME` instead of `TIMESTAMPTZ`
- SQLite: Use `TEXT` for JSON columns, `INTEGER PRIMARY KEY AUTOINCREMENT`
- MongoDB: Use two collections with the same field names

### Phase 4: Event Store Layer

Create a data access layer with these operations:

| Operation | SQL | Description |
|-----------|-----|-------------|
| `LogEvent(visitorID, eventType, path, data)` | `INSERT INTO audit_events ...` | Fire-and-forget, errors discarded |
| `GetRecentSessions(limit)` | `SELECT visitor_id, COUNT(*), MIN(created_at), MAX(created_at) FROM audit_events GROUP BY visitor_id ORDER BY MAX(created_at) DESC LIMIT $1` | Session list for admin |
| `GetVisitorTimeline(visitorID)` | `SELECT * FROM audit_events WHERE visitor_id=$1 ORDER BY created_at ASC` | Full event timeline |
| `SaveReplayEvents(visitorID, sessionID, events, url)` | `INSERT` or `UPDATE` replay_sessions | Append rrweb event batches (see note below) |
| `GetReplaySession(id)` | `SELECT * FROM replay_sessions WHERE id=$1` | Single replay for playback |
| `GetReplaySessions(visitorID)` | `SELECT id, page_url, started_at FROM replay_sessions WHERE visitor_id=$1` | List replays for a visitor |
| `CleanupOldEvents(retentionDays)` | `DELETE FROM audit_events WHERE created_at < now() - interval ...` | Retention cleanup |

**SaveReplayEvents — JSONB array append:**
PostgreSQL `||` on two JSONB arrays concatenates them (`[1,2] || [3,4]` = `[1,2,3,4]`). This is the correct operator for appending rrweb event batches. For MySQL, use `JSON_MERGE_PRESERVE()`. For MongoDB, use `$push` with `$each`.

**Orphan session handling:** If `sendBeacon` fires before the first batch response (sessionId is null), a new session is created. This may produce duplicate sessions for the same page visit. Acceptable trade-off — replay player can show both.

**LogEvent pattern** — fire-and-forget. Never block the request. Discard errors:

```go
// Go
go func() { s.pool.Exec(ctx, "INSERT INTO ...", args...) }()

// Node.js
db.query("INSERT INTO ...", args).catch(() => {});

// Python
asyncio.create_task(db.execute("INSERT INTO ...", args))
```

### Phase 5: Event Recording Points

Identify user-facing handlers and add `LogEvent` calls. Common event types:

| Event Type      | When                          | Data to Record                         |
|-----------------|-------------------------------|----------------------------------------|
| `page_view`     | Any page render               | `{path, referrer}`                     |
| `search`        | Search form submitted         | `{query, results_count}`               |
| `view_item`     | Detail/product page opened    | `{item_id, item_name}`                 |
| `change_prefs`  | User changes settings         | `{setting_name, old_value, new_value}` |
| `form_submit`   | Any form submission           | `{form_name, success}`                 |
| `error`         | Error page shown              | `{error_code, error_message}`          |
| `login`         | User logs in                  | `{method}`                             |
| `click_action`  | Significant button clicks     | `{action, target}`                     |

**Error event capture:** Hook into the framework's error handler to log `error` events automatically:

| Framework | Hook |
|-----------|------|
| Go/Echo | `e.HTTPErrorHandler` custom wrapper |
| Express | `app.use((err, req, res, next) => ...)` |
| Django | Custom middleware `process_exception` |
| FastAPI | `@app.exception_handler(Exception)` |
| Laravel | `App\Exceptions\Handler::report()` |

**Rules:**
- Never log sensitive data (passwords, tokens, PII)
- Keep event_data small (< 1KB per event)
- Use consistent event_type naming (snake_case)
- Always include the request path

### Phase 6: rrweb Recording (Frontend)

Download rrweb and create a recorder script:

**Files to add:**

| File | Source | Size |
|------|--------|------|
| `rrweb.min.js` | `https://cdn.jsdelivr.net/npm/rrweb@2.0.0-alpha.13/dist/rrweb-all.min.js` | ~170KB |

**rrweb version note:** 2.0.0-alpha.13 is the most widely used version with good stability despite the alpha tag. The 1.x stable branch lacks TypeScript support and modern features. If alpha is a concern, pin to this exact version — do not use `@latest`.
| `recorder.js` | Custom (see below) | ~1KB |

**recorder.js template:**

```javascript
(function () {
    if (typeof rrweb === 'undefined') return;

    var events = [];
    var sessionId = null;

    rrweb.record({
        emit: function (event) { events.push(event); },
        maskAllInputs: true  // GDPR: mask form inputs
    });

    // Batch send every 10 seconds
    setInterval(function () {
        if (events.length === 0) return;
        var batch = events.splice(0);
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/replay');  // ADJUST endpoint path
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify({ sessionId: sessionId, events: batch, url: location.href }));
        xhr.onload = function () {
            if (xhr.status === 200) {
                try { sessionId = JSON.parse(xhr.responseText).sessionId; } catch (e) {}
            }
        };
    }, 10000);

    // Send remaining events on page close
    window.addEventListener('beforeunload', function () {
        if (events.length === 0) return;
        navigator.sendBeacon('/api/replay', JSON.stringify({
            sessionId: sessionId, events: events, url: location.href
        }));
    });
})();
```

**Injection:** Add `<script>` tags at the end of `<body>` in the main layout template. Do NOT inject in admin pages.

**Replay ingest endpoint:** POST route that receives batches and calls `SaveReplayEvents`. Returns `{sessionId}` for subsequent batches.

**Server-side safeguards:**
- Limit request body size to 1MB (framework-level or handler-level)
- Reject requests without a valid `visitor_id` cookie
- Rate limit: max 10 requests per minute per visitor_id

**SPA support:** For single-page apps (Next.js, Nuxt, React Router), wrap the recorder in a route-change listener to send the current `location.href` on each navigation, not just initial page load:

```javascript
// For SPA: detect route changes
var lastUrl = location.href;
new MutationObserver(function () {
    if (location.href !== lastUrl) {
        lastUrl = location.href;
        // flush current batch with old URL, start new session
        // ... (send events, reset sessionId to null)
    }
}).observe(document.body, { childList: true, subtree: true });
```

### Phase 7: Admin Panel — Audit Log

Create admin pages for viewing audit data. Two views:

**1. Session List** (`/admin/audit`):

| Column | Content |
|--------|---------|
| Visitor ID | First 8 chars + `...` |
| Events | Count of events |
| First Seen | Timestamp |
| Last Seen | Timestamp |
| Action | `[view]` link → timeline |

**2. Visitor Timeline** (`/admin/audit/:visitorId`):

| Column | Content |
|--------|---------|
| Time | `HH:MM:SS` |
| Event | Badge with event_type |
| Path | Request path |
| Data | Key=value pairs from event_data |

Plus a **Replay** section showing available replay sessions with `[play]` buttons.

### Phase 8: Admin Panel — Replay Player

Download rrweb-player and add playback UI:

**Files to add:**

| File | Source | Size |
|------|--------|------|
| `rrweb-player.min.js` | `https://cdn.jsdelivr.net/npm/rrweb-player@2.0.0-alpha.13/dist/index.js` | ~115KB |
| `rrweb-player.min.css` | `https://cdn.jsdelivr.net/npm/rrweb-player@2.0.0-alpha.13/dist/style.css` | ~5KB |

**Player initialization:**

```javascript
function playReplay(sessionId) {
    fetch('/admin/replay/' + sessionId)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var container = document.getElementById('replay-container');
            container.innerHTML = '';
            new rrwebPlayer({
                target: container,
                props: { events: data.events, width: 1024, height: 600 }
            });
        });
}
```

### Phase 9: Retention Cleanup

Add automatic cleanup to an existing background job or cron. Default: **30 days**.

```sql
DELETE FROM audit_events WHERE created_at < now() - interval '30 days';
DELETE FROM replay_sessions WHERE started_at < now() - interval '30 days';
```

If no background job exists, create a simple scheduled task or suggest adding one.

## Privacy & Security

- `visitor_id` is anonymous — no PII, no IP address stored
- `maskAllInputs: true` in rrweb — form values are replaced with `*`
- Event data should never contain passwords, tokens, or personal data
- Replay recordings should only be accessible to authenticated admins
- Add `Cache-Control: no-store` to replay data endpoints
- Consider GDPR cookie consent if operating in EU jurisdictions

## Adapting to Framework

When scanning the project, look for these patterns to determine the best integration approach:

| Pattern | How to Detect | Integration Strategy |
|---------|---------------|---------------------|
| Existing middleware chain | Framework-specific middleware registration | Add visitor_id to existing chain |
| Existing session system | Session cookie, session store | Add visitor_id to session data instead of separate cookie |
| Existing admin panel | `/admin` routes, auth middleware | Add audit pages to existing admin |
| No admin panel | No admin routes | Create minimal standalone admin with basic auth |
| Existing migration system | Migration directory, migration tool config | Add migration file in existing format |
| No migration system | Raw SQL, no migration tool | Create standalone SQL file + manual instructions |
| Existing background job | Cron, scheduler, worker | Add cleanup to existing job |
| No background job | No scheduler | Create simple goroutine/setInterval/cron entry |

## Scan Output Format (`/audit-replay scan`)

When running in scan mode, report without making changes:

```markdown
## Audit Replay Scan: [Project Name]

| Component          | Status   | Detail                                  |
|--------------------|----------|-----------------------------------------|
| Language/Framework | detected | Go / Echo v4                            |
| Database           | detected | PostgreSQL (pgx)                        |
| Session/Cookie     | missing  | No visitor_id — will add to prefs middleware |
| Migration System   | detected | internal/db/migrate.go (hardcoded list) |
| Admin Panel        | detected | /admin/* with JWT auth                  |
| Template Engine    | detected | Go html/template, layout.html           |
| Static Files       | detected | /static/ served by Echo group           |
| Background Job     | detected | internal/refresh/ (24h ticker)          |

### Files to Create
- migrations/0XX_audit.sql
- internal/store/audit.go
- internal/handler/replay.go
- templates/admin/audit.html + audit-detail.html
- static/rrweb.min.js + recorder.js + rrweb-player.min.js + rrweb-player.min.css

### Files to Modify
- internal/prefs/prefs.go — add VisitorID
- internal/handler/search.go — add LogEvent
- ...
```

## Output

After implementation, provide:

1. List of all created/modified files
2. Verification commands (check tables, check cookies, check events)
3. Post-deploy checklist for the admin to verify

## Rules

- NEVER log sensitive data (passwords, tokens, credit cards, PII)
- NEVER inject rrweb in admin/authenticated pages
- ALWAYS use crypto-secure random for visitor_id generation
- ALWAYS use fire-and-forget for event logging (never block requests)
- ALWAYS mask form inputs in rrweb (`maskAllInputs: true`)
- ALWAYS add retention cleanup (default 30 days)
- ALWAYS protect admin audit/replay endpoints with authentication
- ALWAYS use `no-store` cache control on replay data endpoints
- PREFER appending to existing middleware over creating new ones
- PREFER the project's existing migration system over standalone SQL
- PREFER the project's existing admin panel patterns over new UI
- Download rrweb/player locally — do NOT use CDN links in production
