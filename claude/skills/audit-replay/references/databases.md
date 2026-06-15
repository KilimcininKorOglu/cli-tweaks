# Database Reference

Full schema and event-store queries for all four supported databases. PostgreSQL is the canonical form; the others are expressed as a small **delta** from it. The append-only `replay_events` table makes the replay write path identical across all SQL databases (`INSERT` a row per batch, `SELECT ... ORDER BY seq` to play back), so there is NO per-database JSON-array-append logic to get wrong.

Detect the project's database in Phase 1, then use the matching schema block plus the canonical queries adjusted by the delta table.

## Schemas (full DDL)

### PostgreSQL

```sql
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

CREATE TABLE IF NOT EXISTS replay_sessions (
    id          BIGSERIAL PRIMARY KEY,
    visitor_id  TEXT NOT NULL,
    page_url    TEXT NOT NULL DEFAULT '',
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
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

### MySQL (8.0+)

```sql
CREATE TABLE IF NOT EXISTS audit_events (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    visitor_id  VARCHAR(64) NOT NULL,
    event_type  VARCHAR(64) NOT NULL,
    event_data  JSON NOT NULL,
    path        TEXT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_visitor (visitor_id, created_at),
    INDEX idx_audit_created (created_at)
);

CREATE TABLE IF NOT EXISTS replay_sessions (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    visitor_id  VARCHAR(64) NOT NULL,
    page_url    TEXT NOT NULL,
    started_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_replay_visitor (visitor_id, started_at)
);
CREATE TABLE IF NOT EXISTS replay_events (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id  BIGINT NOT NULL,
    seq         INT NOT NULL,
    batch       JSON NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_replay_events_session (session_id, seq),
    FOREIGN KEY (session_id) REFERENCES replay_sessions(id)
);
```

### SQLite

```sql
CREATE TABLE IF NOT EXISTS audit_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id  TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    event_data  TEXT NOT NULL DEFAULT '{}',   -- JSON as text
    path        TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_audit_visitor ON audit_events(visitor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC);

CREATE TABLE IF NOT EXISTS replay_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id  TEXT NOT NULL,
    page_url    TEXT NOT NULL DEFAULT '',
    started_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS replay_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES replay_sessions(id),
    seq         INTEGER NOT NULL,
    batch       TEXT NOT NULL,                -- JSON as text
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_replay_visitor ON replay_sessions(visitor_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_replay_events_session ON replay_events(session_id, seq);
```

### MongoDB

No DDL — collections are created on first insert. Use three collections mirroring the SQL tables; create indexes explicitly:

```javascript
db.audit_events.createIndex({ visitor_id: 1, created_at: -1 });
db.audit_events.createIndex({ created_at: -1 });
db.replay_sessions.createIndex({ visitor_id: 1, started_at: -1 });
db.replay_events.createIndex({ session_id: 1, seq: 1 });
```

Document shapes:
- `audit_events`: `{ visitor_id, event_type, event_data: {}, path, created_at: ISODate }`
- `replay_sessions`: `{ _id, visitor_id, page_url, started_at, updated_at }`
- `replay_events`: `{ session_id, seq, batch: [...], created_at }` — one document per batch (append-only, same as the SQL design)

## Canonical event-store queries (PostgreSQL)

Adjust the placeholder and JSON/time syntax per the delta table below.

```sql
-- LogEvent (fire-and-forget)
INSERT INTO audit_events (visitor_id, event_type, path, event_data)
VALUES ($1, $2, $3, $4);

-- GetRecentSessions(limit) — session list for admin
SELECT visitor_id, COUNT(*) AS events,
       MIN(created_at) AS first_seen, MAX(created_at) AS last_seen
FROM audit_events
GROUP BY visitor_id
ORDER BY MAX(created_at) DESC
LIMIT $1;

-- GetVisitorTimeline(visitorID)
SELECT * FROM audit_events
WHERE visitor_id = $1
ORDER BY created_at ASC;

-- SaveReplayEvents — first batch creates the session, then append rows
INSERT INTO replay_sessions (visitor_id, page_url) VALUES ($1, $2) RETURNING id;  -- first batch only
INSERT INTO replay_events (session_id, seq, batch) VALUES ($1, $2, $3);            -- every batch

-- GetReplaySession(id) — read batches in order, concatenate in app code
SELECT batch FROM replay_events WHERE session_id = $1 ORDER BY seq;

-- GetReplaySessions(visitorID)
SELECT id, page_url, started_at FROM replay_sessions
WHERE visitor_id = $1 ORDER BY started_at DESC;

-- CleanupOldEvents(retentionDays)
DELETE FROM audit_events   WHERE created_at < now() - interval '30 days';
DELETE FROM replay_events  WHERE created_at < now() - interval '30 days';
DELETE FROM replay_sessions WHERE started_at < now() - interval '30 days';
```

## Per-database delta

| Concern           | PostgreSQL                                | MySQL                                         | SQLite                                    | MongoDB                                          |
|-------------------|-------------------------------------------|-----------------------------------------------|-------------------------------------------|--------------------------------------------------|
| Param placeholder | `$1, $2, …`                               | `?`                                           | `?`                                       | driver args (objects)                            |
| JSON column type  | `JSONB`                                   | `JSON`                                        | `TEXT` (store/parse JSON)                 | native document/array                            |
| Autoincrement PK  | `BIGSERIAL`                               | `BIGINT AUTO_INCREMENT`                       | `INTEGER PRIMARY KEY AUTOINCREMENT`       | `_id` ObjectId (implicit)                        |
| Timestamp type    | `TIMESTAMPTZ`                             | `DATETIME`                                    | `TEXT` (ISO-8601)                         | `ISODate`                                        |
| "Now"             | `now()`                                   | `CURRENT_TIMESTAMP` / `NOW()`                 | `datetime('now')`                         | `new Date()`                                     |
| Last-insert id    | `RETURNING id`                            | `LAST_INSERT_ID()`                            | `last_insert_rowid()`                     | inserted `_id`                                   |
| Retention cutoff  | `created_at < now() - interval '30 days'` | `created_at < NOW() - INTERVAL 30 DAY`        | `created_at < datetime('now','-30 days')` | `{ created_at: { $lt: cutoff } }` + `deleteMany` |
| Read JSON field   | `event_data->>'key'`                      | `JSON_EXTRACT(event_data,'$.key')` (or `->>`) | `json_extract(event_data,'$.key')`        | `event_data.key`                                 |
| Replay append     | `INSERT replay_events`                    | `INSERT replay_events`                        | `INSERT replay_events`                    | `insertOne` into `replay_events`                 |

## Notes

- **Replay append is append-only on every database.** Never concatenate into one growing JSON array — that forces full-value rewrites (O(n²)) and SQLite has no JSON-array-append operator anyway. One row/document per batch keeps writes O(1) everywhere.
- **MySQL JSON path operator:** `->>` (unquoting extract) works on MySQL 8.0+. On older 5.7 use `JSON_UNQUOTE(JSON_EXTRACT(...))`.
- **SQLite JSON1:** `json_extract` requires the JSON1 extension, bundled in modern SQLite builds. If unavailable, parse the TEXT column in application code.
- **GetRecentSessions at scale:** the `GROUP BY visitor_id` aggregate scans `audit_events`; for very large tables add a summary/rollup table or a materialized view rather than aggregating live.
