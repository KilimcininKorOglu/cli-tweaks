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

-- Replay sessions: one row per recording session (metadata only)
CREATE TABLE IF NOT EXISTS replay_sessions (
    id          BIGSERIAL PRIMARY KEY,
    visitor_id  TEXT NOT NULL,
    page_url    TEXT NOT NULL DEFAULT '',
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Replay events: append-only batches (never rewrite one growing JSONB array)
CREATE TABLE IF NOT EXISTS replay_events (
    id          BIGSERIAL PRIMARY KEY,
    session_id  BIGINT NOT NULL REFERENCES replay_sessions(id),
    seq         INTEGER NOT NULL,
    batch       JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_replay_visitor ON replay_sessions(visitor_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_replay_events_session ON replay_events(session_id, seq);
```

**Database adapter notes:**
- MySQL: Use `JSON` instead of `JSONB`, `BIGINT AUTO_INCREMENT` instead of `BIGSERIAL`, `DATETIME` instead of `TIMESTAMPTZ`
- SQLite: Use `TEXT` for JSON columns, `INTEGER PRIMARY KEY AUTOINCREMENT`. The append-only `replay_events` table sidesteps SQLite's lack of a JSON-array append operator (`||` is string concatenation in SQLite, not JSON merge)
- MongoDB: Use three collections (`audit_events`, `replay_sessions`, `replay_events`) with the same field names

### Phase 4: Event Store Layer

Create a data access layer with these operations:

| Operation | SQL | Description |
|-----------|-----|-------------|
| `LogEvent(visitorID, eventType, path, data)` | `INSERT INTO audit_events ...` | Fire-and-forget, errors discarded |
| `GetRecentSessions(limit)` | `SELECT visitor_id, COUNT(*), MIN(created_at), MAX(created_at) FROM audit_events GROUP BY visitor_id ORDER BY MAX(created_at) DESC LIMIT $1` | Session list for admin |
| `GetVisitorTimeline(visitorID)` | `SELECT * FROM audit_events WHERE visitor_id=$1 ORDER BY created_at ASC` | Full event timeline |
| `SaveReplayEvents(visitorID, sessionID, seq, events, url)` | `INSERT INTO replay_events` (create the `replay_sessions` row on the first batch) | Append one batch — see note below |
| `GetReplaySession(id)` | `SELECT batch FROM replay_events WHERE session_id=$1 ORDER BY seq` | Fetch and concatenate batches in order for playback |
| `GetReplaySessions(visitorID)` | `SELECT id, page_url, started_at FROM replay_sessions WHERE visitor_id=$1` | List replays for a visitor |
| `CleanupOldEvents(retentionDays)` | `DELETE FROM audit_events WHERE created_at < now() - interval ...` | Retention cleanup |

**SaveReplayEvents — append-only batches:**
Each batch is a NEW row in `replay_events` (`INSERT (session_id, seq, batch)`), never an append into one growing array. A single appended JSONB array forces every write to rewrite the whole TOAST-ed value (≈O(n²) writes, rows ballooning to MBs); separate rows keep each write O(1) and behave identically on PostgreSQL, MySQL, and SQLite — no DB-specific JSON-merge operator required. For MongoDB, insert each batch as its own document. On playback, read batches ordered by `seq` and concatenate them.

**Orphan session handling:** If `sendBeacon` fires before the first batch response (sessionId is null), a new session is created. This may produce duplicate sessions for the same page visit. Acceptable trade-off — replay player can show both.

**LogEvent pattern** — fire-and-forget. Never block the request. Discard errors. Do NOT reuse the request context in the detached task — it is cancelled when the handler returns and can kill the insert mid-flight (silent event loss):

```go
// Go — fresh context, NOT the request ctx (which is cancelled on handler return)
go func() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    s.pool.Exec(ctx, "INSERT INTO ...", args...)
}()

// Node.js — rejection intentionally swallowed
db.query("INSERT INTO ...", args).catch(() => {});

// Python — keep a reference so the task isn't garbage-collected; needs a running loop
task = asyncio.create_task(db.execute("INSERT INTO ...", args))
_bg_tasks.add(task); task.add_done_callback(_bg_tasks.discard)
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

**SPA note:** In single-page apps, server-side handlers only see the initial document load — all in-app navigation happens client-side. Emit `page_view` from the client on each route change (reuse the History API hook from Phase 6) and POST it to a lightweight `/api/event` endpoint, or the audit log misses every in-app navigation.

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
| `rrweb.min.js` | bundled UMD build of the current stable `rrweb` 2.0.x — exposes the global `rrweb` | ~170KB |
| `recorder.js` | Custom (see below) | ~1KB |

**rrweb version note:** Pin the **current stable** `rrweb` 2.0.x — the main `rrweb` package still ships a bundled build that exposes the global `rrweb`. Do NOT use `@latest`, and do NOT switch to the scoped `@rrweb/all` / `@rrweb/record` packages here — those are still on `2.0.0-alpha` releases. Vendor the bundled/UMD file locally; the ES-module (`.js`) builds do not expose a global via a plain `<script>` tag.

**recorder.js template:**

```javascript
(function () {
    if (typeof rrweb === 'undefined') return;

    var events = [];
    var sessionId = null;
    var seq = 0;

    rrweb.record({
        emit: function (event) { events.push(event); },
        maskAllInputs: true,             // masks <input> values only
        maskTextSelector: '.pii',        // masks VISIBLE text inside PII-bearing elements
        blockSelector: '.rr-block',      // elements not recorded at all (rendered as placeholders)
        checkoutEveryNms: 5 * 60 * 1000  // periodic full snapshot so a replay can start mid-session
    });

    function send(payload, useBeacon) {
        var body = JSON.stringify(payload);
        if (useBeacon) {
            // Blob preserves Content-Type application/json (a raw string would send text/plain)
            navigator.sendBeacon('/api/replay', new Blob([body], { type: 'application/json' }));
            return;
        }
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/replay');  // ADJUST endpoint path
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            if (xhr.status === 200) {
                try { sessionId = JSON.parse(xhr.responseText).sessionId; } catch (e) {}
            }
        };
        xhr.send(body);
    }

    // Batch send every 10 seconds
    setInterval(function () {
        if (events.length === 0) return;
        send({ sessionId: sessionId, seq: seq++, events: events.splice(0), url: location.href }, false);
    }, 10000);

    // Send remaining events on page close (Blob keeps the JSON content type)
    window.addEventListener('beforeunload', function () {
        if (events.length === 0) return;
        send({ sessionId: sessionId, seq: seq++, events: events, url: location.href }, true);
    });
})();
```

**Injection:** Add `<script>` tags at the end of `<body>` in the main layout template. Do NOT inject in admin pages.

**Replay ingest endpoint:** POST route that receives batches and calls `SaveReplayEvents`. Returns `{sessionId}` for subsequent batches.

**Server-side safeguards:**
- Limit request body size, but leave headroom for the initial full-DOM snapshot, which can exceed 1MB on complex pages — use ~4-8MB (or accept the first snapshot batch separately). A hard 1MB cap silently rejects the first batch and leaves the replay unplayable.
- Reject requests without a valid `visitor_id` cookie
- Rate limit: max 10 requests per minute per visitor_id

**SPA support:** rrweb's single `record()` call already captures SPA route changes as DOM mutations — you do NOT need to restart recording per route. Only add the hook below if you want per-route segmentation (a separate replay per view). Detect real navigation by patching the History API — NOT a `MutationObserver`, which fires on every DOM change, not just navigation:

```javascript
// For SPA: detect real route changes via the History API
(function () {
    function onRouteChange() {
        // flush the current batch with the old URL, then start a new session
        // (reuse recorder's send(); reset sessionId = null and seq = 0)
    }
    ['pushState', 'replaceState'].forEach(function (m) {
        var orig = history[m];
        history[m] = function () {
            var r = orig.apply(this, arguments);
            onRouteChange();
            return r;
        };
    });
    window.addEventListener('popstate', onRouteChange);
})();
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
| `rrweb-player.min.js` | UMD build of `rrweb-player` (`umd/rrweb-player.min.js` or `dist/index.umd.cjs`) — exposes the global `rrwebPlayer` | ~115KB |
| `rrweb-player.min.css` | `rrweb-player`'s `dist/style.css` | ~5KB |

**Critical — load the UMD build, not the ES module.** The player's `.js` build (`dist/index.js`) is an ES module and will NOT define the global `rrwebPlayer` when loaded via a plain `<script>` tag — `new rrwebPlayer(...)` below would throw `ReferenceError`. Use the UMD build (`umd/rrweb-player.min.js` or `dist/index.umd.cjs`).

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
- **rrweb records ALL visible page text, not just inputs.** `maskAllInputs: true` masks only `<input>` values; names, emails, addresses, and order details rendered as page text are captured verbatim unless excluded. Mark every PII-bearing element with `.rr-block` (not recorded) or `.pii` (`maskTextSelector`, text masked). Do NOT treat `maskAllInputs` alone as GDPR compliance.
- Event data should never contain passwords, tokens, or personal data
- Replay recordings should only be accessible to authenticated admins
- Add `Cache-Control: no-store` to replay data endpoints
- GDPR: obtain cookie/recording consent before recording in EU jurisdictions — session replay of PII-bearing pages is personal-data processing

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
- ALWAYS mask inputs AND block/mask PII-bearing visible text in rrweb (`maskAllInputs: true` plus `.rr-block` / `maskTextSelector` on PII elements) — inputs alone do not cover rendered personal data
- ALWAYS add retention cleanup (default 30 days)
- ALWAYS protect admin audit/replay endpoints with authentication
- ALWAYS use `no-store` cache control on replay data endpoints
- PREFER appending to existing middleware over creating new ones
- PREFER the project's existing migration system over standalone SQL
- PREFER the project's existing admin panel patterns over new UI
- Download rrweb/player locally — do NOT use CDN links in production
