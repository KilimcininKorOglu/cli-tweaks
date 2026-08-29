---
name: pg-fair-queue
description: >
  This skill MUST be invoked when the user says "fair queue", "adil kuyruk",
  "multi-tenant queue", "tenant isolation queue", "round-robin queue",
  "noisy neighbor", "bir kullanıcı kuyruğu tıkıyor", "SKIP LOCKED",
  "postgres task queue", "postgres job queue", "kuyruk starvation",
  "per-tenant concurrency", "group concurrency limit" or any variation about
  designing or auditing a Postgres-backed task queue where one tenant's
  backlog must not starve others. Audits an existing queue (schema + pop
  query) for fairness and O(n) traps, and on request applies a
  write-time block-ID round-robin design with per-group concurrency limits.
argument-hint: "[scan | fix]"
---

# Postgres Fair Queue

Deterministic round-robin across tenants/groups in a Postgres task queue, with constant-time pop and optional per-group concurrency limits. The trick: encode the round-robin rank into the task ID **at write time** so the pop query stays a plain `ORDER BY id ... FOR UPDATE SKIP LOCKED` index scan.

**Default behavior is `scan`.** Applying changes the ID scheme and adds tables; it is a migration, not a patch.

## Usage

```
/pg-fair-queue            # Scan existing queue: fairness, scaling traps, concurrency (DEFAULT)
/pg-fair-queue scan       # Same as default
/pg-fair-queue fix        # Implement the block-ID design (schema + queries + worker changes)
```

## The Problem

One FIFO queue: tenant Bob enqueues 10,000 tasks, tenant Alice enqueues 1. Alice waits behind all 10,000. Adding workers does not fix this; it only speeds up Bob.

## Why Not `PARTITION BY`

The obvious fix — `row_number() OVER (PARTITION BY group_key ORDER BY id)` then `ORDER BY rn, id` — fails three ways:

1. `FOR UPDATE` is not allowed with window functions. Splitting into two CTEs "works" but the first CTE selects rows already locked by other workers, and the second CTE's `SKIP LOCKED` then discards them — concurrent workers pop 0 rows.
2. The window aggregate scans **every** `QUEUED` row. At ~25k queued rows the pop query exceeds the polling interval, workers stall, backlog grows, and the system cannot recover by adding workers.
3. `JOIN LATERAL` per group scales with group count; decrementing ranks after reads scales with group size. Neither is constant-time.

## The Design: Block-Addressed IDs

Partition the BIGINT ID space into blocks of `BLOCK_LEN` (e.g. 2^20 = 1,048,576). Each group has a small integer `gid` (< `BLOCK_LEN`) and a pointer `block_addr` to the last block it wrote into. A global pointer `max_assigned_block` tracks the block of the highest non-QUEUED task.

Task ID = `gid + BLOCK_LEN × block_addr`.

Enqueue for group j:
- new group → `block_addr(j) = max_assigned_block`
- existing group → `block_addr(j) = max(block_addr(j) + 1, max_assigned_block)`

Consequences:
- Within one block, at most one task per group → `ORDER BY id` is round-robin across groups.
- A group with a deep backlog spreads across many future blocks; a new task from an idle group lands in the **current** block, i.e. near the head.
- Pop is `WHERE status='QUEUED' ORDER BY id LIMIT n FOR UPDATE SKIP LOCKED` — pure index scan, ~constant time (measured ~20 ms for 100 rows at 1M queued / 1k groups).
- Per-group concurrency `c`: only consider `id < min_queued_id + c × BLOCK_LEN`. A group can appear at most `c` times in that window.

Constraints:
- Group count must stay < `BLOCK_LEN`. Changing `BLOCK_LEN` later requires offsetting new IDs past the current max.
- Capacity ≈ `BIGINT_MAX / BLOCK_LEN` blocks ≈ 8.8×10^12 blocks at 2^20; blocks are consumed roughly once per enqueue wave, so practical ceiling is high but finite. Plan an ID re-basing path.
- Writes become ~500–1k/s because every enqueue updates the group pointer row. Fine for most queues; if ingest rate matters more than strict fairness, use an `OVERFLOW` gate plus approximate fairness instead.

## Phase 1: Scan

Read the schema and the pop query. Check:

| Check                                                        | Finding if present                                   |
|--------------------------------------------------------------|------------------------------------------------------|
| Single global `ORDER BY id/created_at` with no group notion  | No fairness; one tenant can starve all others        |
| `row_number() OVER (PARTITION BY ...)` in pop path           | O(queued rows) per pop; worker stall above ~25k rows |
| Window function + `FOR UPDATE` split across CTEs             | Concurrent workers pop 0 rows (locked rows pre-selected) |
| `ORDER BY random()`                                          | Non-deterministic; no ordering guarantees            |
| No `FOR UPDATE SKIP LOCKED`                                  | Duplicate dispatch under concurrent workers          |
| Workers start simultaneously with fixed poll interval        | Thundering herd on the pop query                     |
| No upper bound on QUEUED rows                                | Unrecoverable degradation under backlog              |
| Per-group concurrency enforced in application memory         | Not consistent across workers; races                 |
| Watermark/pointer maintained by `... WHERE status <> 'QUEUED' ORDER BY id DESC LIMIT 1` | O(queued) per pop; scans every queued row above the frontier |
| Pop query lacks index on `(status, id)` or partial index     | Seq scan under load                                  |

Report each finding with the `EXPLAIN ANALYZE` of the current pop query at a representative backlog (seed 25k and 1M rows if a test DB is available). Then recommend: block-ID design (strict fairness), or `OVERFLOW` gate + simpler queue (approximate fairness, higher write rate).

## Phase 2: Fix

### 2.1 Schema

```sql
CREATE TYPE task_status AS ENUM ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED','OVERFLOW');

CREATE TABLE task_groups (
    gid        BIGINT PRIMARY KEY,           -- dense small integer, < BLOCK_LEN
    group_key  TEXT NOT NULL UNIQUE,
    block_addr BIGINT NOT NULL
);

CREATE TABLE task_ptrs (                      -- single row
    singleton  BOOL PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    max_assigned_block BIGINT NOT NULL DEFAULT 0
);
INSERT INTO task_ptrs DEFAULT VALUES;

CREATE TABLE tasks (
    id         BIGINT PRIMARY KEY,            -- assigned, NOT serial
    group_key  TEXT NOT NULL REFERENCES task_groups(group_key),
    status     task_status NOT NULL DEFAULT 'QUEUED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    args       JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX tasks_queued_idx ON tasks (id) WHERE status = 'QUEUED';
```

`BLOCK_LEN` is a constant in the application and in SQL (`1048576`). Put it in one place.

### 2.2 Enqueue

```sql
-- $1 group_key, $2 args
WITH g AS (
    INSERT INTO task_groups (gid, group_key, block_addr)
    VALUES (
        COALESCE((SELECT max(gid) FROM task_groups), -1) + 1,
        $1,
        (SELECT max_assigned_block FROM task_ptrs)
    )
    ON CONFLICT (group_key) DO UPDATE SET
        block_addr = GREATEST(task_groups.block_addr + 1,
                              (SELECT max_assigned_block FROM task_ptrs))
    RETURNING gid, block_addr
)
INSERT INTO tasks (id, group_key, args)
SELECT gid + 1048576 * block_addr, $1, $2 FROM g
RETURNING id;
```

The `max(gid)+1` is racy under concurrent *new* groups; serialize new-group creation with an advisory lock (`pg_advisory_xact_lock(hashtext('task_groups'))`) or pre-register groups.

### 2.3 Pop (unchanged shape, with per-group concurrency)

```sql
-- $1 limit, $2 concurrency per group
WITH lo AS (
    SELECT COALESCE(min(id), 0) AS min_id FROM tasks WHERE status = 'QUEUED'
),
picked AS (
    SELECT id FROM tasks
    WHERE status = 'QUEUED'
      AND id >= (SELECT min_id FROM lo)
      AND id <  (SELECT min_id FROM lo) + $2::bigint * 1048576
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT $1
)
UPDATE tasks t SET status = 'RUNNING'
FROM picked WHERE t.id = picked.id
RETURNING t.*;
```

Drop the `id <` bound for no per-group limit.

The `id <` window bounds a group to at most `c` tasks in a **single pop's** candidate set (a group has one task per block, so `c` blocks hold at most `c`). It is not a hard cap on tasks `RUNNING` per group across workers over time. For a strict global limit, also track a running count per group and skip a group at its cap.

### 2.4 Advance the global pointer — same transaction as pop

`max_assigned_block` is the block of the dispatch frontier: the highest block whose tasks have left `QUEUED`. Advance it from the rows this pop just dispatched, not by scanning for the highest non-`QUEUED` task.

```sql
-- $1 = max(id) among the rows this pop returned (0 if it returned none)
UPDATE task_ptrs
SET max_assigned_block = GREATEST(max_assigned_block, $1::bigint / 1048576);
```

Pop takes the lowest `QUEUED` ids, so `max(id)` of the popped rows is the new frontier. This is O(popped) and keeps the pop transaction constant-time.

NEVER advance the pointer with `SELECT ... WHERE status <> 'QUEUED' ORDER BY id DESC LIMIT 1`. Under a backlog the highest ids are all `QUEUED` future blocks, so that scan skips every queued row above the frontier — O(queued) per pop, the exact trap this design exists to avoid.

Without this advance, idle groups keep landing in old blocks and fairness degrades.

### 2.5 Worker hygiene

- Stagger worker start: `sleep(workerIndex × pollInterval / numWorkers)`.
- Poll interval must exceed pop query duration; alert if `p99(pop) > interval / numWorkers`.
- Overflow gate: cap `QUEUED` rows (e.g. 100k). Enqueue as `OVERFLOW` above the cap; a periodic job promotes `OVERFLOW → QUEUED` while under cap. Keeps pop latency bounded regardless of ingest.
- Optional `LISTEN/NOTIFY` on enqueue to cut idle polling; keep polling as fallback.

## Phase 3: Verification

```bash
# 1. Seed: 1000 groups, skewed (one group 90% of tasks), 1M rows
# 2. EXPLAIN ANALYZE the pop query — expect Index Scan on tasks_queued_idx, no WindowAgg, no Seq Scan
# 3. Run 10 workers simultaneously — each must pop `limit` rows on the first poll, none 0
# 4. Fairness: enqueue 1 task for a fresh group behind a 100k backlog; it must be dispatched within ~1 poll
# 5. Concurrency: with c=5, count RUNNING per group — never > 5 from a single pop window
# 6. Pointer: after draining, task_ptrs.max_assigned_block == max block of any group
```

## Rules

- **Default to `scan`.** Fix is a migration with an ID-scheme change; require explicit `fix`.
- NEVER use window functions in the pop path. Rank at write time, not read time.
- ALWAYS use `FOR UPDATE SKIP LOCKED` on the *same* SELECT that filters and orders — never pre-select in a CTE then lock in a second one.
- ALWAYS update `task_ptrs` in the pop transaction; it is what keeps the round-robin honest.
- ALWAYS advance `max_assigned_block` from the `max(id)` of the popped rows, never by scanning `status <> 'QUEUED' ORDER BY id DESC`; the scan is O(queued) per pop.
- ALWAYS define `BLOCK_LEN` once and assert `count(task_groups) < BLOCK_LEN` in a health check.
- ALWAYS serialize new-group creation (advisory lock) to avoid `gid` collisions.
- ALWAYS bound `QUEUED` with an overflow status. This is independent of the fairness design and prevents unrecoverable states.
- Use a partial index `(id) WHERE status='QUEUED'`; the pop query must be an index scan.
- Do not add `created_at` to `ORDER BY`; the block-ID already encodes arrival order within a group.
- If strict determinism is not required and write throughput is, prefer approximate fairness (overflow gate + shuffle sharding) over this design; note the tradeoff in the scan report.
- Keep task IDs opaque to clients; they are not sequential and will have gaps by design.
- Plan ID re-basing before the ID space or the 1-task-per-group-per-block assumption is exhausted; document the runbook alongside the migration.
