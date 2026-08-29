---
name: pg-insert-perf
description: >
  This skill MUST be invoked when the user says "insert performance",
  "insert hızlandır", "postgres yavaş yazıyor", "batch insert", "bulk insert",
  "COPY FROM", "pgx CopyFrom", "SendBatch", "toplu yazma", "write throughput",
  "connection pool size", "bağlantı havuzu", "too many connections",
  "flush buffer", "yazma optimizasyonu" or any variation about speeding up
  Postgres INSERT throughput or right-sizing connection usage. Scans the
  project for single-row-in-a-loop inserts, oversized pools, and missing
  batching/COPY; reports expected gains; on request implements buffered
  batch inserts or COPY with backpressure.
argument-hint: "[scan | fix]"
---

# Postgres Insert Performance

Move write paths from row-at-a-time INSERTs to batched INSERT / `COPY FROM` behind a small in-memory buffer, and right-size the connection pool. Measured on a local M3 Max (Hatchet benchmarks, 2025): single connection loop ≈2k rows/s → 20-connection pool ≈16k → single batched query ≈37k → 20 buffered batch writers ≈80k → buffered `COPY` ≈92k rows/s. Above ~20 connections throughput plateaued and then fell.

**Default behavior is `scan` (dry-run).** Batching changes failure semantics (one bad row fails the batch), latency, and `RETURNING` availability. Apply only after review.

## Usage

```
/pg-insert-perf          # Scan only — report findings and estimated gains (DEFAULT)
/pg-insert-perf scan     # Same as default
/pg-insert-perf fix      # Implement the changes from the scan
```

## How It Works

### Phase 1: Project Scan

Run `scripts/pg-insert-perf.scan.sh` from the project root, then read the flagged locations. Detect the driver:

| Language | Driver / pool                                   | Batch API                          | COPY API                         |
|----------|-------------------------------------------------|------------------------------------|----------------------------------|
| Go       | pgx/v5 + pgxpool, database/sql + lib/pq         | `conn.SendBatch(ctx, &pgx.Batch{})`| `conn.CopyFrom(ctx, table, cols, src)` |
| Node.js  | pg, postgres.js, knex, prisma                   | multi-row VALUES / `sql\`...\``    | `pg-copy-streams`                |
| Python   | psycopg3, asyncpg, SQLAlchemy                   | `executemany` / `execute_values`   | `cursor.copy()` / `copy_records_to_table` |
| Rust     | tokio-postgres, sqlx                            | multi-row VALUES / `UNNEST`        | `copy_in`                        |

Identify and classify every write path:

1. **Loop inserts** — `for ... { INSERT ... }` or per-item `exec`/`execute`. Highest-value target.
2. **Per-request single inserts** — one row per HTTP request/event. Candidate for a shared buffer if volume > ~500/s.
3. **Already batched** — multi-row VALUES, `UNNEST`, `SendBatch`, `COPY`. Leave alone; check batch size.
4. **Pool configuration** — `MaxConns`, `max`, `pool_size`, `max_connections`. Flag > 20 per app instance without a documented reason; flag "unbounded".
5. **`RETURNING *` usage** — if the returned row is not consumed, drop it (blocks `COPY`).
6. **Network topology** — DB in another cloud/region adds ms per round-trip; batching matters even more there.

### Phase 2: Report

For each write path output: location, current pattern, rows/s ceiling (from the table above), proposed pattern, and the latency cost (buffered writes add ~flush-interval of latency; ~10 ms at batch ≈25 is the usual sweet spot).

Report pool findings separately with the recommended size (start at `min(20, 2 × CPU cores of the DB)` and measure).

### Phase 3: Implementation (fix)

#### 3.1 Choose the mechanism

| Situation                                                    | Use                          |
|--------------------------------------------------------------|------------------------------|
| Need `RETURNING` (ids, defaults)                             | batched INSERT (`SendBatch` or multi-row VALUES / `UNNEST`) |
| Fire-and-forget rows, ids generated client-side or unused    | `COPY FROM`                  |
| Rows arrive continuously (OLTP)                              | buffer → flush on interval OR size, whichever first |
| One-off bulk load (migration, seed)                          | single `COPY` of everything  |
| Upserts (`ON CONFLICT`)                                      | multi-row INSERT / `UNNEST`; COPY cannot upsert |

#### 3.2 Buffer with backpressure (Go, pgx)

Properties: flushes when the flush interval elapses **or** the buffer is full; when full, `Add` blocks — that is the backpressure. One buffer owns one connection at a time; run N buffers to use N pool connections.

```go
type Row struct{ Args []byte }

type Buffer struct {
    ch       chan Row
    pool     *pgxpool.Pool
    maxSize  int
    interval time.Duration
}

func NewBuffer(pool *pgxpool.Pool, maxSize int, interval time.Duration) *Buffer {
    return &Buffer{ch: make(chan Row, maxSize), pool: pool, maxSize: maxSize, interval: interval}
}

// Add blocks when the buffer is full — intentional backpressure.
func (b *Buffer) Add(ctx context.Context, r Row) error {
    select {
    case b.ch <- r:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (b *Buffer) Run(ctx context.Context) {
    t := time.NewTicker(b.interval)
    defer t.Stop()
    batch := make([]Row, 0, b.maxSize)
    flush := func() {
        if len(batch) == 0 {
            return
        }
        if err := b.write(ctx, batch); err != nil {
            log.Printf("flush failed (%d rows): %v", len(batch), err)
        }
        batch = batch[:0]
    }
    for {
        select {
        case <-ctx.Done():
            flush()
            return
        case r := <-b.ch:
            batch = append(batch, r)
            if len(batch) >= b.maxSize {
                flush()
            }
        case <-t.C:
            flush()
        }
    }
}
```

**COPY writer** (fastest, no RETURNING):

```go
func (b *Buffer) write(ctx context.Context, rows []Row) error {
    _, err := b.pool.CopyFrom(ctx,
        pgx.Identifier{"tasks"},
        []string{"args"},
        pgx.CopyFromSlice(len(rows), func(i int) ([]any, error) {
            return []any{rows[i].Args}, nil
        }),
    )
    return err
}
```

**Batched INSERT writer** (when you need ids back):

```go
func (b *Buffer) write(ctx context.Context, rows []Row) error {
    args := make([][]byte, len(rows))
    for i, r := range rows { args[i] = r.Args }
    // UNNEST: one statement, one round-trip, RETURNING works, arbitrary batch size.
    _, err := b.pool.Exec(ctx,
        `INSERT INTO tasks (args) SELECT * FROM UNNEST($1::jsonb[])`, args)
    return err
}
```

`SendBatch` is the alternative when rows go to different tables or statements differ; it pipelines N statements in one round-trip inside an implicit transaction.

Start N buffers:

```go
for i := 0; i < numBuffers; i++ { // numBuffers ≤ pool MaxConns
    go buffers[i].Run(ctx)
}
```

Route rows to buffers by hash or round-robin. Keep `numBuffers × 1 ≤ MaxConns` so flushes never wait on the pool.

#### 3.3 Pool sizing

```go
cfg.MaxConns = 20 // start here; benchmark 10/20/40, keep the knee
cfg.MinConns = 4
cfg.MaxConnLifetime = 30 * time.Minute
```

Never set the application pool near the server's `max_connections`. Connection storms saturate Postgres' lock manager and write latency explodes. If many app instances share one DB, put PgBouncer (transaction mode) in front and keep per-instance pools small.

#### 3.4 Other languages (patterns, same rules)

- **Node (pg):** `INSERT ... SELECT * FROM UNNEST($1::jsonb[])` or `pg-copy-streams`; pool `max: 10–20`.
- **Python (psycopg3):** `with cursor.copy("COPY tasks (args) FROM STDIN") as cp: cp.write_row(...)`; asyncpg `copy_records_to_table`. Pool 10–20.
- **Rust (sqlx):** bind arrays + `UNNEST`; tokio-postgres `copy_in`.

### Phase 4: Verification

```bash
# 1. Build + tests
<build-cmd> && <test-cmd>

# 2. Throughput/latency at batch sizes 1, 10, 25, 50, 100, 500 — pick the knee.
#    Report rows/s and p50/p99 write latency for each. Expect ~25 to saturate.

# 3. Confirm pool never waits on acquire
#    pgxpool: pool.Stat().EmptyAcquireCount() should stay ~0 under load

# 4. Confirm server-side connection count is bounded
psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 5. Confirm no lock contention regression
psql -c "SELECT wait_event_type, wait_event, count(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL GROUP BY 1,2;"
```

Report before/after rows/s and latency in the same format for both.

## Rules

- **Default to `scan` mode.** Never modify code without explicit `fix`.
- NEVER raise the pool above ~20 per instance as an "optimization". More connections past the knee lowers throughput and raises latency.
- ALWAYS bound the buffer and block on full. An unbounded buffer turns a DB slowdown into an OOM.
- ALWAYS flush on shutdown (`ctx.Done()`); otherwise buffered rows are lost.
- ALWAYS flush on interval even when nearly empty — a 3-row batch after 10 ms is correct; waiting for 100 rows at low traffic is a latency bug.
- Use `COPY` only when `RETURNING` and `ON CONFLICT` are not needed. Otherwise `UNNEST`/multi-row INSERT.
- Prefer `UNNEST` over generated `VALUES ($1),($2),...` — fixed statement text, no parameter-count limit issues (65535 params in pgx), plan cache friendly.
- Batch size: aim for the smallest size that saturates throughput (usually 25–100). Larger batches add latency without throughput.
- One batch = one transaction. If per-row failure isolation matters, validate before buffering or split into smaller batches on error; do not silently drop the batch.
- Do not batch across tables with FK dependencies in one COPY; order table writes within a transaction instead.
- Keep single-row `INSERT ... RETURNING` for genuinely low-volume, latency-sensitive paths (user-facing create with immediate id use). Batching is for volume.
- Measure on the real topology. 2 ms of network latency cuts single-row throughput ~5×; the benefit of batching scales with round-trip cost.
- If the DB is CPU-saturated, batching helps less; report that separately rather than pushing batch sizes up.
