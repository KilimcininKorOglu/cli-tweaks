---
name: rust-mem-layout
description: >
  This skill MUST be invoked when the user says "rust memory", "memory layout",
  "bellek optimizasyonu", "struct boyutu", "struct size", "shrink struct",
  "reduce allocations", "allocation azalt", "cache entry memory", "Box<[T]>",
  "enum size", "large enum variant", "padding", "hot struct", "per-entry memory"
  or any variation asking to reduce the memory footprint or allocation count of
  Rust data structures that are stored in bulk (caches, maps, record lists,
  arenas). Scans the crate for the five layout anti-patterns from Cloudflare's
  1.1.1.1 DNS-cache optimization (growable containers on immutable data,
  parallel lists, derivable fields, oversized enums, per-record heap boxes) and
  fixes them.
argument-hint: "[scan | fix]"
---

# Rust Memory Layout — scan & fix

Find structs that are instantiated in bulk (cache entries, records, nodes, events) and cut their per-instance footprint and allocation count without changing behavior. Based on the five optimizations Cloudflare applied to Big Pineapple's DNS cache (953 B → 420 B per entry, −56%; inserts +43%, lookups −19%): <https://blog.cloudflare.com/dns-cache-memory-optimization-1111/>

**Default behavior is `scan` (dry-run).** Layout changes touch every construction/read site of a type. Fix only after reviewing the scan report.

## Usage

```
/rust-mem-layout          # Scan only — report candidates with estimated savings (DEFAULT)
/rust-mem-layout scan     # Same as default
/rust-mem-layout fix      # Apply fixes from the last scan, one pattern at a time
```

## Scope rule

Only structs that exist in **high cardinality** matter. 8 bytes on a config struct is noise; 8 bytes on a struct held 10M times is 80 MB. Before anything else, identify bulk types:

- Values of `HashMap`/`BTreeMap`/`DashMap`/`moka`/`lru` caches
- Elements of long-lived `Vec<T>` / `Box<[T]>` / slab / arena
- Anything with a comment like "entry", "record", "node", "item", "cell"
- Types whose `size_of` is asserted or benchmarked already

Report non-bulk hits under "low priority" and do not fix them unless asked.

## Phase 1: Measure

Never estimate when you can measure.

```bash
# Exact size/alignment/padding per type (nightly only)
RUSTFLAGS="-Zprint-type-sizes" cargo +nightly build --release 2>&1 \
  | grep -A20 'type: `crate::path::TypeName`'

# Clippy layout lints (stable)
cargo clippy --all-targets -- -W clippy::large_enum_variant -W clippy::box_collection -W clippy::vec_box
```

If nightly is unavailable, add a temporary test:

```rust
#[test]
fn print_sizes() {
    use std::mem::{size_of, align_of};
    macro_rules! p { ($t:ty) => { eprintln!("{:<40} size={:>4} align={}", stringify!($t), size_of::<$t>(), align_of::<$t>()); } }
    p!(CacheEntry); p!(Record); p!(RecordData); p!(CacheKey);
}
```

Run with `cargo test print_sizes -- --nocapture`. Record numbers in the scan report as **before**.

For allocation counts, wrap the global allocator in tests/benches:

```rust
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering::Relaxed};

pub struct Counting;
pub static ALLOCS: AtomicUsize = AtomicUsize::new(0);
pub static BYTES:  AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for Counting {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, Relaxed); BYTES.fetch_add(l.size(), Relaxed);
        System.alloc(l)
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) { System.dealloc(p, l) }
}
#[global_allocator] static A: Counting = Counting;
// Measure: snapshot ALLOCS/BYTES, construct N entries, diff / N.
```

## Phase 2: Scan patterns

Grep each bulk struct for the five patterns. For each hit, compute the estimated saving per instance and multiply by the instance count if known.

### P1 — Growable container on immutable data

`Vec<T>` = ptr + len + cap (24 B). `String` = same. If the field is never mutated after construction, `cap` is dead weight and the heap buffer may be over-allocated.

**Detect:** a `Vec<T>` / `String` field where no code calls `.push`, `.extend`, `.insert`, `.remove`, `.clear`, `.truncate`, `.reserve`, `.drain`, `&mut` borrow, or `std::mem::take` on it after the constructor. Check `impl` blocks, `Default`, `From`, serde `Deserialize`, and builders.

**Fix:** `Vec<T>` → `Box<[T]>`, `String` → `Box<str>`. Saves 8 B per field on the struct plus any unused capacity on the heap.

```rust
// before
pub answers: Vec<Record>,
pub name: String,
// after
pub answers: Box<[Record]>,
pub name: Box<str>,
```

Conversion: `vec.into_boxed_slice()` / `string.into_boxed_str()`. Both call `shrink_to_fit` first, which may reallocate — acceptable at construction, but see P5 for the scratch-buffer approach if this is on a hot insert path.

`Option<Box<str>>` and `Option<Box<[T]>>` are niche-optimized (no extra tag byte) — free to use.

### P2 — Parallel lists of the same element type

Several `Box<[T]>` / `Vec<T>` fields holding the same `T` each cost 16–24 B of header and a separate allocation.

**Detect:** ≥ 2 fields of identical element type in one struct (e.g. `answers`, `authority`, `additional: Vec<Record>`).

**Fix:** one `Box<[T]>` plus small offsets marking section boundaries. Choose the offset width from the real maximum count (`u8`/`u16`). Expose the sections via accessor methods so call sites don't change.

```rust
pub struct Entry {
    records: Box<[Record]>,
    authority_start: u16,
    additional_start: u16,
}
impl Entry {
    pub fn answers(&self)    -> &[Record] { &self.records[..self.authority_start as usize] }
    pub fn authority(&self)  -> &[Record] { &self.records[self.authority_start as usize..self.additional_start as usize] }
    pub fn additional(&self) -> &[Record] { &self.records[self.additional_start as usize..] }
}
```

Three lists → one: saves 2×16 B headers − 2×2 B offsets = 28 B, and two allocations.

**Also in this phase — bool packing:** ≥ 2 `bool` fields → pack into a `u8` bitfield or `bitflags!`. The direct saving is small; the real gain is the padding that disappears around them. Re-measure after — savings are often larger than the sum of the removed fields.

Note: `repr(Rust)` already reorders fields to minimize padding. Do not manually reorder fields unless the struct is `#[repr(C)]`; instead reduce field *count* and *width*.

### P3 — Derivable fields

Data that can be recovered from context at read time (the map key, a parent struct, a global table) is stored redundantly per instance.

**Detect:** a field whose value equals, or is almost always equal to, something available at every access site — typically the key of the map the struct lives in. Examples: record owner name == query name; child `parent_id` when the child is only reached via the parent; a `kind` tag duplicated from the enum variant.

**Fix:** store `Option<T>` (or `Option<Box<T>>` for large `T`) and use `None` for the common "same as context" case. Reconstruct in the accessor from the context that is already in hand.

```rust
pub struct Record {
    owner: Option<Box<Name>>,   // None => same as the CacheKey's qname
    ...
}
impl Record {
    pub fn owner<'a>(&'a self, key: &'a CacheKey) -> &'a Name {
        self.owner.as_deref().unwrap_or(&key.qname)
    }
}
```

Cost: the struct is no longer self-contained. Only apply when every read site already has the context; if it requires threading a new parameter through many layers, report it instead of fixing.

### P4 — Enum sized by its rarest variant

An enum is as large as its largest variant. If the common variants are small and a rare one is big, every common instance pays the difference in padding.

**Detect:** `-Zprint-type-sizes` shows `variant` sizes with one outlier; or `clippy::large_enum_variant` fires. Confirm with the actual distribution — which variants dominate at runtime.

**Fix:** box the large/rare variants, keep small/common ones inline.

```rust
pub enum RecordData {
    A(Ipv4Addr),          // 4 B, inline
    Aaaa(Ipv6Addr),       // 16 B, inline
    Txt(Box<Txt>),        // large → heap
    Naptr(Box<Naptr>),
    Svcb(Box<Svcb>),
}
```

The enum shrinks to `max(inline variants, 8) + tag + padding` (typically 24 B). Boxed variants pay one extra allocation and allocator size-class rounding (jemalloc/glibc round up to bins: a 40 B request costs 48 B). Accept this only when the boxed variants are genuinely rare. If they are common, go to P5 instead.

### P5 — Per-record heap boxes → one packed byte buffer

If a struct holds many small variable-size records (each boxed after P4), the boxes fragment the heap, hurt cache locality, and each carries allocator overhead.

**Detect:** a `Box<[Record]>` where `Record` contains `Box<...>` variants or nested `Box<str>`/`Box<[u8]>`, and the struct already has (or could trivially have) a canonical byte encoding (wire format, protobuf, a fixed header + payload).

**Fix:** store the records as a single `Box<[u8]>` of `[len: u16][bytes]...` frames. Iterate sequentially; random indexing is lost, which is fine for small counts.

```rust
pub struct Entry {
    records: Box<[u8]>,       // u16-length-prefixed frames, section offsets in bytes
    authority_start: u32,
    additional_start: u32,
}

pub struct Frames<'a>(&'a [u8]);
impl<'a> Iterator for Frames<'a> {
    type Item = &'a [u8];
    fn next(&mut self) -> Option<&'a [u8]> {
        if self.0.len() < 2 { return None; }
        let n = u16::from_le_bytes([self.0[0], self.0[1]]) as usize;
        let (frame, rest) = self.0[2..].split_at(n);
        self.0 = rest;
        Some(frame)
    }
}
```

Build the buffer through a **reusable scratch `Vec<u8>`** kept across inserts (thread-local or owned by the writer), then copy into an exactly-sized `Box<[u8]>`:

```rust
scratch.clear();
for r in records { encode(&mut scratch, r); }
let packed: Box<[u8]> = scratch.as_slice().into();   // one exact allocation, no shrink
```

Do not `Vec::with_capacity(guess)` then `into_boxed_slice()` — the shrink may not release the tail. Do not encode straight into a fresh `Vec` per insert — that's the reallocation churn the scratch buffer exists to avoid.

Records that need no interpretation on read (fixed layout, no internal pointers) can be memcpy'd straight out of the buffer; only decode the ones that need transformation. This is where lookup latency improves, not just memory.

## Phase 3: Scan report format

Output exactly this structure. No changes to files in scan mode.

```
## rust-mem-layout scan — <crate>

### Bulk types found
| Type | Where held | Est. instances | size_of (before) | align |
|------|------------|----------------|------------------|-------|

### Findings
#### [P1] src/cache/entry.rs:42 — CacheEntry.answers: Vec<Record>
Never mutated after `CacheEntry::new` (checked: 3 impl blocks, 1 builder).
Fix: Box<[Record]>. Saves 8 B/instance + unused capacity. Touches: 4 sites.

#### [P4] src/dns/record.rs:10 — enum RecordData (144 B, largest variant Naptr 136 B)
A/Aaaa variants observed at ~80% of instances.
Fix: box Txt/Naptr/Svcb/... → ~24 B. Saves ~120 B/instance for A/Aaaa. Touches: 11 match sites.

### Low priority (non-bulk)
- [P1] src/config.rs:8 — Config.paths: Vec<String> (1 instance) — skip

### Summary
Est. per-instance: <before> B → <after> B (−N%), allocations: <before> → <after>
Recommended fix order: P1 → P2 → P3 → P4 → P5 (re-measure after each)
```

## Phase 4: Fix mode

Apply findings **in order P1 → P5, one pattern per commit**, re-measuring after each. Each step:

1. Change the type definition.
2. Update constructors/builders/`From`/serde impls.
3. Add accessor methods so read sites keep compiling where possible; update the rest.
4. Add a size assertion so the gain can't silently regress:
   ```rust
   const _: () = assert!(std::mem::size_of::<CacheEntry>() <= 128);
   ```
5. `cargo build --release && cargo test && cargo clippy --all-targets`
6. Re-run the Phase 1 measurement, append **after** numbers to the report.
7. If a bench exists (criterion/divan), run it. A memory win that costs throughput needs an explicit decision from the user — stop and ask.

Stop and report (do not fix) when:
- A P3 change requires threading context through > 2 call layers.
- A P5 change requires inventing a byte encoding that doesn't already exist in the project.
- The type derives `Serialize`/`Deserialize` and the on-disk/on-wire format would change — layout changes must not alter serialized output unless the user confirms.
- The field is behind `pub` in a library crate (API break).

## Verification

```bash
# Sizes before/after
RUSTFLAGS="-Zprint-type-sizes" cargo +nightly build --release 2>&1 | grep -E 'type: `.*(Entry|Record|Data)`' -A3

# No behavior change
cargo test --all

# Lints clean
cargo clippy --all-targets -- -D warnings

# Allocation count per instance (counting allocator test)
cargo test --release alloc_per_entry -- --nocapture

# Throughput/latency unchanged or better
cargo bench
```

## Rules

- **Default to `scan`.** Never modify files without an explicit `fix`.
- Measure with `-Zprint-type-sizes` or `size_of` before claiming a saving. Padding makes arithmetic on field sizes unreliable in both directions.
- Optimize bulk types only. Report the rest as low priority.
- Follow the order P1 → P5. P5 supersedes P4 for the same field — if P5 applies, skip boxing the variants.
- `Vec` → `Box<[T]>` only when provably immutable after construction. A single `.push` in a rarely-run path still disqualifies it.
- `Option<Box<T>>`, `Option<Box<[T]>>`, `Option<Box<str>>`, `Option<&T>`, `Option<NonZeroU*>` cost zero extra bytes (niche). Prefer them over sentinel values.
- Offsets: size to the real max (`u8`/`u16`/`u32`), never `usize`.
- Do not hand-reorder fields in `repr(Rust)` structs; the compiler already does it. Reorder only `#[repr(C)]`/`#[repr(packed)]` types and only when measurement shows padding.
- Boxing an enum variant adds one allocation and allocator size-class rounding. Box only rare variants; if the large variant is common, pack (P5) instead.
- Scratch buffer for building packed data must be reused across inserts; allocate the final `Box<[u8]>` exactly once per instance.
- Never change serialized formats, public struct fields of a library crate, or `unsafe` layout assumptions without asking.
- Add `const _: () = assert!(size_of::<T>() <= N)` for every type you shrink.
- A memory saving that regresses a benchmark is not a fix. Report it and let the user decide.
