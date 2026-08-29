---
name: go-time-int64
description: >
  This skill MUST be invoked when the user says "time.Time to int64",
  "time int64", "timestamp int64", "time.Time bellek", "time.Time memory",
  "reduce struct size", "struct küçült", "GC pointer azalt", "reduce GC
  pressure", "in-memory index memory", "bellek optimizasyonu go", "go memory
  overhead", "fit index in memory", "embedded go", "gömülü go", "tinygo",
  "microcontroller", "RAM kısıtlı", "bellek kısıtlı cihaz", "memory
  constrained", "shrink footprint" or any variation requesting memory or GC
  reduction in a Go project by replacing time.Time fields with int64
  timestamps. Scans Go structs for time.Time fields held in hot in-memory
  collections (slices, maps, indexes, queues) or on memory-constrained
  targets, reports the byte and GC-pointer savings, and on request performs
  the conversion with boundary adapters.
argument-hint: "[scan | fix]"
---

# Go time.Time → int64

Replace `time.Time` fields in hot in-memory data structures with `int64` (Unix nanoseconds by default). `time.Time` is 24 bytes and contains a `*Location` pointer; `int64` is 8 bytes and pointer-free. In large slices/maps this is a 3x reduction per field and removes one pointer per element from every GC scan.

The win does not depend on project size. For an internal timestamp field, `int64` is a strictly smaller, pointer-free representation of the same instant, so this is a representation improvement, not a scale-dependent tradeoff. What scale changes is the **magnitude** of the win, and therefore its **priority** — never whether the change is correct:
- Millions of elements turn 16 bytes/field into gigabytes and a pointer-free struct into a `noscan` GC win.
- A **memory-constrained target** (embedded, TinyGo, small-RAM SBC or microcontroller) makes even a handful of structs matter against a fixed RAM budget.
- A small server project gets a real but small win; the only cost is the diff churn.

The actual decision to convert is a **correctness** question, not a size question. Keep `time.Time` at API/JSON/ORM boundaries and on in-process monotonic timing (`time.Since` on a live value); convert the internal storage type everywhere else. Do not gate the change on element count.

**Default behavior is `scan` (dry-run).** The conversion changes semantics at edges (zero value, timezone, monotonic clock, JSON shape). Apply only after reviewing the scan report.

## Usage

```
/go-time-int64          # Scan only — report candidates and savings (DEFAULT)
/go-time-int64 scan     # Same as default
/go-time-int64 fix      # Apply the conversion from the scan
```

## Why It Works

| Type                | Size     | Pointers | Notes                                          |
|---------------------|----------|----------|------------------------------------------------|
| `time.Time`         | 24 bytes | 1 (`*Location`) | wall uint64 + ext int64 + loc *Location |
| `*time.Time`        | 8 bytes  | 1 + heap object | worse: extra allocation, extra indirection |
| `int64` (UnixNano)  | 8 bytes  | 0        | range 1678–2262                                |
| `int64` (UnixMicro) | 8 bytes  | 0        | range ±292k years                              |
| `int64` (Unix sec)  | 8 bytes  | 0        | loses sub-second precision                     |

Two independent wins:
1. **Size** — 16 bytes saved per field per element. 100M elements × 2 timestamp fields = 3.2 GB saved.
2. **GC** — a struct whose only pointer was `*Location` becomes pointer-free. The GC marks pointer-free spans as `noscan` and skips them entirely. This is often the larger win for GC pause time.

Real-world reference: a queue engine's priority+timestamp index went from a few million entries to hundreds of millions on a 2 GB machine after this change plus a light refactor.

## How It Works

### Phase 1: Project Scan

Run the bundled scanner from the project root:

```bash
go run <skill-dir>/scripts/scan.go ./...
```

It walks the AST and reports:
- Every struct field of type `time.Time` or `*time.Time` (file:line, struct, field)
- Whether that struct appears as an element in a slice, array, map, or channel anywhere in the package (hot-path heuristic)
- Whether the struct has any other pointer-typed fields (if not, conversion makes it fully `noscan`)
- Estimated savings per element (16 bytes for `time.Time`, 8 bytes + 1 heap alloc for `*time.Time`)

Then classify manually using the table below. The scanner cannot know intent.

### Phase 2: Classify Candidates

`convert` versus `skip` is decided by **where the field lives and its semantics**, never by instance count. The `skip` and `review` rows below are correctness rules: a wire type, an ORM expectation, monotonic timing, timezone display, or a zero-value edge. Instance count only sets **priority** among the `convert` rows, so it appears in the Reason column, not the Action column.

| Category                                                    | Action     | Reason                                                           |
|-------------------------------------------------------------|------------|------------------------------------------------------------------|
| Struct held in large slice/map/index/queue/cache/ring       | **convert**| the highest-magnitude win: size + `noscan`                       |
| Internal storage struct, any instance count                 | **convert**| representation win applies regardless of count; count sets priority |
| Struct with `*time.Time` for nullable timestamps            | **convert**| use `0` as null sentinel; removes an allocation per element      |
| Internal DTO between DB layer and in-memory engine          | **convert**| convert `pgtype.Timestamptz` → `int64` directly, skip `time.Time`|
| Exported API struct / JSON / HTTP / gRPC request-response   | **skip**   | wire format change; keep `time.Time`, convert at boundary        |
| Struct implementing `sql.Scanner` / ORM model with tags     | **skip**   | ORM expects `time.Time`; convert on load into the internal type  |
| Field used with `time.Since` / `time.Until` on live values  | **review** | loses monotonic clock; fine for stored timestamps, not for deadlines measured in-process |
| Field formatted with a specific `Location` for display      | **review** | `int64` is an instant; re-attach location at format time         |
| Config structs, singletons, request-scoped structs          | **review** | safe to convert, but on a normal-RAM target the diff churn can outweigh a one-off struct's bytes; on a memory-constrained target, convert |
| Field where zero `time.Time{}` (year 1) is semantically used| **review** | `time.Time{}.UnixNano()` is undefined (overflow); must map to `0`|

**Memory-constrained target (embedded / TinyGo / small-RAM device):** priority stops mattering; the RAM budget is fixed and small, so convert every semantically-safe internal candidate, including the one-off structs. 16 bytes off a struct that exists a handful of times still counts when total RAM is measured in KB. The GC/`noscan` argument is secondary here (TinyGo's GC differs); the size win is the point. The boundary `skip` rows (exported API/JSON/ORM structs) stay `skip` — those are correctness rules, not scale rules.

### Phase 3: Conversion (fix)

#### 3.1 Choose precision once per project

- **`UnixNano`** (default) — matches `time.Time` precision, valid 1678–2262. Fine for timestamps that are created "now-ish".
- **`UnixMicro`** — if you store far-future/far-past dates, or sort against Postgres `timestamptz` (which is microsecond precision anyway).
- **`Unix`** — only if seconds are enough and range matters.

Do not mix. Define a named type so the unit is explicit:

```go
// UnixNano is an instant in nanoseconds since epoch. Zero means "unset".
type UnixNano int64

func Now() UnixNano                     { return UnixNano(time.Now().UnixNano()) }
func FromTime(t time.Time) UnixNano     { if t.IsZero() { return 0 }; return UnixNano(t.UnixNano()) }
func (u UnixNano) Time() time.Time      { if u == 0 { return time.Time{} }; return time.Unix(0, int64(u)).UTC() }
func (u UnixNano) IsZero() bool         { return u == 0 }
func (u UnixNano) Before(o UnixNano) bool { return u < o }
func (u UnixNano) After(o UnixNano) bool  { return u > o }
func (u UnixNano) Add(d time.Duration) UnixNano { return u + UnixNano(d) }
func (u UnixNano) Sub(o UnixNano) time.Duration { return time.Duration(u - o) }
```

A named type keeps `unsafe.Sizeof` at 8, is still pointer-free, and lets the compiler catch `int64` vs `UnixNano` mixups.

#### 3.2 Convert the struct

```go
// Before
type Job struct {
    ID        int64
    Priority  int32
    ScheduledAt time.Time
    CreatedAt   time.Time
    LockedAt    *time.Time
}
// unsafe.Sizeof = 72, pointers = 3

// After
type Job struct {
    ID          int64
    ScheduledAt UnixNano
    CreatedAt   UnixNano
    LockedAt    UnixNano // 0 = not locked
    Priority    int32
}
// unsafe.Sizeof = 40, pointers = 0 → noscan
```

Note the field reorder: after shrinking, run `fieldalignment` to remove padding:

```bash
go run golang.org/x/tools/go/analysis/passes/fieldalignment/cmd/fieldalignment@latest -fix ./...
```

#### 3.3 Rewrite call sites

| Before                          | After                                   |
|---------------------------------|-----------------------------------------|
| `a.T.Before(b.T)`               | `a.T < b.T`                             |
| `a.T.After(b.T)`                | `a.T > b.T`                             |
| `a.T.Equal(b.T)`                | `a.T == b.T`                            |
| `a.T.IsZero()`                  | `a.T == 0`                              |
| `t.Add(d)`                      | `t + UnixNano(d)`                       |
| `t.Sub(u)`                      | `time.Duration(t - u)`                  |
| `time.Since(t)`                 | `time.Duration(Now() - t)`              |
| `time.Now()`                    | `Now()`                                 |
| `*t` (nullable)                 | `t` with `t != 0` check                 |
| `sort.Slice(x, func(i,j) bool { return x[i].T.Before(x[j].T) })` | `... x[i].T < x[j].T` |
| `cmp.Compare(a.T.UnixNano(), b.T.UnixNano())` | `cmp.Compare(a.T, b.T)`   |

Comparisons on `int64` are also faster than `time.Time.Before` (which checks wall/monotonic bits) and are safe to use with `==` (comparing `time.Time` with `==` is a known footgun because of `loc` and monotonic bits).

#### 3.4 Boundary adapters

**Postgres (pgx / pgtype):** skip the `time.Time` intermediate entirely.

```go
// Before
var ts pgtype.Timestamptz
rows.Scan(&ts)
job.ScheduledAt = ts.Time

// After
var ts pgtype.Timestamptz
rows.Scan(&ts)
job.ScheduledAt = FromTime(ts.Time) // ts.Valid==false → ts.Time is zero → 0
```

Or push it to SQL when reading huge backlogs:

```sql
SELECT id, priority,
       (EXTRACT(EPOCH FROM scheduled_at) * 1e9)::bigint AS scheduled_at_ns
FROM jobs ORDER BY priority, scheduled_at
```

and scan directly into `int64` — no `pgtype.Timestamptz` allocation at all.

**JSON / API:** keep the wire type. Add a converter at the edge:

```go
type JobResponse struct {
    ID          int64     `json:"id"`
    ScheduledAt time.Time `json:"scheduled_at"`
}
func toResponse(j Job) JobResponse { return JobResponse{ID: j.ID, ScheduledAt: j.ScheduledAt.Time()} }
```

Or implement `MarshalJSON`/`UnmarshalJSON` on `UnixNano` (RFC 3339) if the struct must stay shared — but prefer separate types.

**Logging:** `slog`/`zap` will print the raw int. Add `LogValue()` or format with `.Time()` in log calls.

### Phase 4: Verification

```bash
# 1. Compiles, vet passes
go build ./... && go vet ./...

# 2. Tests pass
go test ./...

# 3. Struct size and pointer count — add a throwaway test
cat > size_test.go <<'EOF'
package yourpkg
import ("testing"; "unsafe"; "reflect")
func TestJobSize(t *testing.T) {
    t.Logf("Sizeof(Job)=%d", unsafe.Sizeof(Job{}))
    var hasPtr bool
    rt := reflect.TypeOf(Job{})
    for i := 0; i < rt.NumField(); i++ {
        switch rt.Field(i).Type.Kind() {
        case reflect.Ptr, reflect.Slice, reflect.Map, reflect.String, reflect.Interface, reflect.Chan, reflect.Func:
            hasPtr = true
        }
    }
    t.Logf("has pointers=%v (false → noscan)", hasPtr)
}
EOF
go test -run TestJobSize -v .

# 4. Heap before/after on realistic load
go test -bench=BenchmarkIndexLoad -benchmem -memprofile mem.out .
go tool pprof -top mem.out | head -20

# 5. GC behaviour (pointer-free spans skipped)
GODEBUG=gctrace=1 ./yourbinary 2>&1 | head
```

Report to the user: size before/after per struct, pointer count before/after, and measured heap delta if a benchmark exists.

## Rules

- **Default to `scan` mode.** Never modify files without an explicit `fix`.
- ONLY convert Go. This skill is Go-specific; do not apply the pattern to other languages.
- Decide `convert` versus `skip` by field location and semantics, never by project size. `int64` is a strictly smaller, pointer-free representation, so the win is real at any scale; size only sets priority, not the decision. Never tell the user the change is not worth doing because the project or instance count is small.
- On a memory-constrained target (embedded, TinyGo, small-RAM device), convert every semantically-safe internal candidate. The fixed RAM budget, not instance count, is the test.
- NEVER convert exported API/JSON/gRPC/ORM-model structs in place. Keep `time.Time` at the boundary and convert into the internal type.
- ALWAYS define a named type (`UnixNano`, `UnixMicro`) rather than bare `int64` so the unit is unambiguous and the compiler catches mixing.
- ALWAYS map `time.Time{}` (zero) ↔ `0`. `time.Time{}.UnixNano()` overflows and returns garbage; `time.Unix(0,0)` is 1970, not zero. Guard both directions.
- ALWAYS check the date range against the chosen precision. `UnixNano` overflows outside 1678–2262. If the domain has "far future" sentinels (e.g. year 9999), use `UnixMicro` or `Unix`.
- ALWAYS replace `*time.Time` with a non-pointer `int64` using `0` as null. A pointer here costs 8 bytes + a 24-byte heap object + a GC edge.
- ALWAYS convert `pgtype.Timestamptz` → `int64` directly at scan time; do not round-trip through `time.Time` in bulk loads. Prefer computing epoch in SQL for very large reads.
- ALWAYS run `fieldalignment` after shrinking fields; the padding freed is often another 8–16 bytes.
- NEVER convert fields used for in-process elapsed-time measurement (`time.Since` on a value captured with `time.Now()` in the same process where monotonic accuracy matters, e.g. timeouts, rate limiters). Stored/persisted timestamps are fine.
- NEVER assume timezone information is needed. `int64` is an absolute instant; attach a `*time.Location` only when formatting for display.
- Prefer `<`, `>`, `==` over method calls; they are correct on `int64` and faster than `time.Time.Before/After/Equal`.
- Convert one hot struct at a time; build and test between each. The compiler will enumerate every call site that needs updating.
- Measure. Report actual `unsafe.Sizeof` and heap deltas, not theoretical numbers.
- If the struct still has other pointers (strings, slices) after conversion, note that it will not become `noscan`; the size win still applies but the GC win is smaller. Suggest interning strings or using indices into a side table if the user wants the full win.
