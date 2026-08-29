---
name: pg-payload-offload
description: >
  This skill MUST be invoked when the user says "supertoast", "toast table",
  "toast bloat", "payload offload", "jsonb çok yer kaplıyor", "jsonb too
  large", "offload to S3", "S3'e taşı", "cold payload", "soğuk veri",
  "disk doluyor postgres", "autovacuum toast", "autovacuum çok uzun",
  "wraparound vacuum", "büyük payload postgres", "tiered storage postgres",
  "write-and-swap" or any variation about large jsonb/bytea/text payloads
  bloating Postgres, TOAST autovacuum pressure, or moving cold rows to
  object storage. Audits TOAST usage and access patterns; on request
  implements a partitioned inline/external payload table with a
  write-and-swap offload job and batched S3 objects with byte-range keys.
argument-hint: "[scan | fix]"
---

# Postgres Payload Offload (supertoast)

Keep hot payloads inline in Postgres, move cold ones to object storage, and do the move by **rewriting a partition and swapping it in** rather than updating rows. Reference: Hatchet offloads hundreds of millions of payloads per day this way with no autovacuum pressure and bounded S3 cost.

**Default behavior is `scan`.** Fix introduces partitioning, a nightly job, an object store dependency, and a new read path.

## Usage

```
/pg-payload-offload           # Scan: TOAST size, vacuum pressure, access pattern, fit (DEFAULT)
/pg-payload-offload scan      # Same as default
/pg-payload-offload fix       # Implement schema + offload job + read path
```

## Why This Exists

| Symptom                                                 | Cause                                                            |
|---------------------------------------------------------|------------------------------------------------------------------|
| Payload columns are 50–90% of disk                      | `jsonb`/`bytea` > 2 KB goes to TOAST; TOAST rows never leave     |
| `autovacuum: VACUUM pg_toast.pg_toast_NNN (to prevent wraparound)` running for hours | TOAST tables are expensive to traverse; high-churn workloads generate huge dead-tuple volume |
| Disk fills; resizing local NVMe = provision a new DB     | No elastic disk; large WAL makes provisioning slow                |
| Backups bloated with data nobody reads                   | Access follows a power law: > 1 day old ≈ never read             |

The naive fix — a job that `UPDATE`s each row to point at S3 — is worse: every row becomes a dead tuple, autovacuum reclaims the whole partition, and one S3 PUT per row costs real money ($0.005 / 1000 PUTs; at 10^8 rows/day that is thousands of dollars per day).

## Phase 1: Scan

Run `scripts/pg-payload-offload.scan.sql` against the target database. Then answer:

1. **Which tables/columns are TOAST-heavy?** (section 1–2). Candidates: `jsonb`/`bytea`/`text` columns with `toast_pct` > 40%.
2. **Is autovacuum struggling?** (section 3–4, 6). Long-running TOAST vacuums or `xid_age` climbing toward 200M on a TOAST relation.
3. **Access pattern.** From application logs or `pg_stat_statements`: what fraction of reads hit rows older than N hours? If reads are uniform across age, offloading does not fit.
4. **Latency budget for cold reads.** Object-store range GET is ~20–100 ms. Acceptable for cold rows?
5. **Already partitioned?** (section 5). Time-range partitioning on the insert timestamp is a prerequisite.
6. **Write path.** Does anything `UPDATE` the payload after insert? Updates must rewrite inline (offload is append-only).

Report: candidate tables with sizes, estimated reclaimable space (rows older than cutoff × avg TOAST bytes), estimated S3 cost at the chosen batch size, and a fit verdict. If the access pattern is not age-skewed, recommend autovacuum tuning / `toast.autovacuum_*` overrides instead and stop.

## Phase 2: Fix

### 2.1 Schema

```sql
CREATE TYPE payload_location AS ENUM ('INLINE', 'EXTERNAL');

CREATE TABLE payloads (
    id             BIGINT GENERATED ALWAYS AS IDENTITY,
    inserted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    tenant_id      TEXT NOT NULL,
    location       payload_location NOT NULL DEFAULT 'INLINE',
    external_key   TEXT,
    inline_content JSONB,
    PRIMARY KEY (id, inserted_at),
    CHECK (
        (location = 'INLINE'   AND inline_content IS NOT NULL AND external_key IS NULL) OR
        (location = 'EXTERNAL' AND external_key   IS NOT NULL AND inline_content IS NULL)
    )
) PARTITION BY RANGE (inserted_at);

-- one partition per day; create ahead of time (cron or pg_partman)
CREATE TABLE payloads_2026_03_04 PARTITION OF payloads
    FOR VALUES FROM ('2026-03-04') TO ('2026-03-05');
```

Daily partitions are the unit of offload. The CHECK makes the two states mutually exclusive so the read path can trust `location`.

Optional: on the partition, `ALTER TABLE ... SET (toast.autovacuum_vacuum_scale_factor = 0.05)` to vacuum TOAST more eagerly while the day is hot.

### 2.2 External key format

Pack many payloads into one object; store a key that addresses a byte range:

```
<tenant>/<yyyy>/<mm>/<dd>/<hh>/<batch-uuid>.bin:<offset>:<length>
```

Each payload is compressed individually (zstd or gzip), then concatenated. `offset`/`length` refer to the compressed bytes. Read = one range GET + one decompress. Writes drop from one PUT per row to one PUT per batch (≈ 1000–10000 rows), i.e. 3–4 orders of magnitude fewer requests.

```go
type packed struct {
    Body   []byte            // concatenated compressed payloads
    Ranges map[int64][2]int  // payload id → {offset, length}
}

func pack(rows []Row) packed {
    var buf bytes.Buffer
    p := packed{Ranges: make(map[int64][2]int, len(rows))}
    for _, r := range rows {
        start := buf.Len()
        w := zstd.NewWriter(&buf) // or gzip
        w.Write(r.Content); w.Close()
        p.Ranges[r.ID] = [2]int{start, buf.Len() - start}
    }
    p.Body = buf.Bytes()
    return p
}

func key(tenant string, t time.Time, batchID string, off, ln int) string {
    return fmt.Sprintf("%s/%s/%s.bin:%d:%d", tenant, t.UTC().Format("2006/01/02/15"), batchID, off, ln)
}
```

### 2.3 Write-and-swap offload job

Runs once per day for the previous day's partition, at a time when someone is online (Hatchet uses 07:00 local). Phases:

**a. Create the target copy with the partition's bound as a CHECK**

```sql
CREATE TABLE payloads_copy_2026_03_04
    (LIKE payloads_2026_03_04 INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES);

ALTER TABLE payloads_copy_2026_03_04 ADD CONSTRAINT copy_bound_chk CHECK (
    inserted_at IS NOT NULL
    AND inserted_at >= '2026-03-04 00:00:00+00'
    AND inserted_at <  '2026-03-05 00:00:00+00'
);
```

The CHECK must match the partition bound exactly; it lets `ATTACH PARTITION` skip the validation scan later.

**b. Mirror live writes into the copy**

```sql
CREATE OR REPLACE FUNCTION mirror_to_copy() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO payloads_copy_2026_03_04 VALUES (NEW.*)
        ON CONFLICT (id, inserted_at) DO UPDATE
            SET location = EXCLUDED.location, external_key = EXCLUDED.external_key,
                inline_content = EXCLUDED.inline_content;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE payloads_copy_2026_03_04
           SET location = NEW.location, external_key = NEW.external_key, inline_content = NEW.inline_content
         WHERE id = NEW.id AND inserted_at = NEW.inserted_at;
        RETURN NEW;
    ELSE
        DELETE FROM payloads_copy_2026_03_04 WHERE id = OLD.id AND inserted_at = OLD.inserted_at;
        RETURN OLD;
    END IF;
END $$;

CREATE TRIGGER mirror_writes AFTER INSERT OR UPDATE OR DELETE ON payloads_2026_03_04
    FOR EACH ROW EXECUTE FUNCTION mirror_to_copy();
```

Late writes into yesterday's partition (retries, backfills) are rare but must not be lost.

**c. Paginate, pack, upload, insert into the copy**

Progress table: `offload_progress(partition_day DATE PRIMARY KEY, last_id BIGINT, last_inserted_at TIMESTAMPTZ)`. Loop:

```sql
SELECT id, inserted_at, tenant_id, inline_content
FROM payloads_2026_03_04
WHERE location = 'INLINE'
  AND (id, inserted_at) > ($1, $2)          -- keyset from offload_progress
ORDER BY id, inserted_at
LIMIT 5000;
```

1. Split the batch into chunks (e.g. 500–2000 rows, grouped by tenant).
2. Pack + upload chunks in parallel (goroutine pool sized to S3 concurrency).
3. `INSERT INTO payloads_copy_... (id, inserted_at, tenant_id, location, external_key)` with `location='EXTERNAL'` — use `COPY` or `UNNEST` (see `/pg-insert-perf`). Rows already `EXTERNAL` in the source are copied as-is.
4. `UPDATE offload_progress SET last_id=..., last_inserted_at=...`.
5. Repeat until the SELECT returns 0 rows.

The job is idempotent: restart resumes from `offload_progress`; re-uploaded objects are harmless.

**d. Swap**

```sql
BEGIN;
LOCK TABLE payloads IN ACCESS EXCLUSIVE MODE;

DROP TRIGGER mirror_writes ON payloads_2026_03_04;
DROP FUNCTION mirror_to_copy();

ALTER TABLE payloads DETACH PARTITION payloads_2026_03_04;
DROP TABLE payloads_2026_03_04;

ALTER TABLE payloads_copy_2026_03_04 RENAME TO payloads_2026_03_04;
-- rename indexes/constraints to the canonical names here

ALTER TABLE payloads ATTACH PARTITION payloads_2026_03_04
    FOR VALUES FROM ('2026-03-04') TO ('2026-03-05');   -- instant: CHECK already proves the bound

ALTER TABLE payloads_2026_03_04 DROP CONSTRAINT copy_bound_chk;
COMMIT;
```

`DROP TABLE` frees the old heap and its TOAST relation outright — no dead tuples, nothing for autovacuum to do. The lock is held for milliseconds.

### 2.4 Read path

```go
func (s *Store) Payload(ctx context.Context, id int64, at time.Time) ([]byte, error) {
    row := s.q.GetPayload(ctx, id, at) // location, external_key, inline_content
    if row.Location == "INLINE" {
        return row.InlineContent, nil
    }
    objKey, off, ln := parseKey(row.ExternalKey)        // split on last two ':'
    rc, err := s.s3.GetObject(ctx, &s3.GetObjectInput{
        Bucket: &s.bucket, Key: &objKey,
        Range: aws.String(fmt.Sprintf("bytes=%d-%d", off, off+ln-1)),
    })
    if err != nil { return nil, err }
    defer rc.Body.Close()
    return zstdDecompress(rc.Body)
}
```

Updates after offload: write the new value inline (`location='INLINE'`, `external_key=NULL`); the stale bytes in S3 are ignored. Deletes: delete the row; S3 lifecycle rules expire whole objects after the retention window.

### 2.5 Operations

- Schedule: daily cron, previous day's partition, during staffed hours.
- Alerts: job runtime > N hours; `offload_progress` not advancing; swap failed (copy table left behind).
- S3 lifecycle: expire objects at the retention period; consider a colder storage class after 30 days.
- Pre-create partitions ≥ 2 days ahead; a missing partition fails inserts.
- Metrics: rows offloaded, bytes uploaded, PUT count, p99 cold read latency, DB disk delta after swap.

## Phase 3: Verification

```bash
# 1. Dry run on a staging copy of one partition; compare counts
psql -c "SELECT count(*), location FROM payloads_2026_03_04 GROUP BY 2"

# 2. Read 100 random EXTERNAL rows through the read path; decompressed bytes must equal
#    the original inline content captured before the run
# 3. Late-write test: INSERT into yesterday's partition mid-job; confirm it exists after swap
# 4. Swap timing: measure lock hold; expect < 100 ms
# 5. Disk: pg_total_relation_size(parent) before/after; TOAST relation of old partition gone
# 6. Autovacuum: no new long-running pg_toast vacuum on the swapped partition
# 7. S3: PUT count ≈ rows / chunk_size, not ≈ rows
```

## Rules

- **Default to `scan`.** Fix is a storage-architecture change with an external dependency.
- NEVER offload by `UPDATE`-ing rows in place. Rewrite into a copy and swap the partition; `DROP` is free, `UPDATE` is dead tuples.
- NEVER upload one object per row. Pack, compress per payload, address by `key:offset:length`.
- ALWAYS create the copy with a CHECK matching the partition bound so `ATTACH` skips validation and the swap is instant.
- ALWAYS mirror live writes into the copy with a trigger for the duration of the job.
- ALWAYS enforce `INLINE`/`EXTERNAL` exclusivity with a CHECK so the read path never has to guess.
- ALWAYS paginate by the full primary key (keyset), never `OFFSET`; persist progress so the job resumes.
- ALWAYS take `ACCESS EXCLUSIVE` on the parent only for the swap transaction; keep it to DDL, no data movement inside the lock.
- Compress per payload, not per object; range reads must be independently decompressible.
- Rewrite updates inline; do not try to patch bytes in S3. Let lifecycle policies handle deletes.
- Pick the cutoff from measured access age (default 24 h), not by feel. If reads are not age-skewed, do not apply this; tune `toast.autovacuum_*` instead.
- Run the job when an engineer is available; a stuck job leaves a copy table and a trigger behind that must be cleaned up manually.
- Keep `external_key` opaque to clients. The encoding is internal and may change.
- Object-store latency is a cold-read cost; document it as a product behavior, not a bug.
