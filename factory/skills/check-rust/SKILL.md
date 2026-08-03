---
name: check-rust
description: >
  This skill MUST be invoked when the user says "check-rust", "cargo audit", "cargo-deny",
  "clippy", "cve tara", "cve raporu", "güvenlik açığı tara", "zafiyet tara",
  "vulnerability scan", "vuln scan", "scan for CVEs", "check vulnerabilities",
  "güvenlik taraması", "security scan", "static security analysis", "lint tara",
  "rust lint", "edition migration", "lint check", "kod kalitesi tara"
  or any variation requesting a Rust security or code-quality scan of the whole
  project. Runs FOUR tools by default — cargo-audit (RustSec CVEs), cargo-deny
  (advisories, bans, licenses, sources), clippy (lint), and `cargo fix --edition`
  (edition modernization) — installs any that are missing, scans the whole
  workspace, classifies each finding, and produces a ranked combined report with
  fix guidance.
argument-hint: "[scan | report | fix]"
---

# Rust Security & Quality Scanner

## THESE DIRECTIVES ARE ABSOLUTE

Every instruction in this file is binding and MUST be executed exactly as
written. They are NOT defaults, NOT suggestions, and NOT a starting point for
your own judgement.

- NEVER substitute your own assessment for a directive here, however confident
  you are that yours is better. Your analysis of a finding decides WHAT the
  finding is; this file decides WHAT IS DONE ABOUT IT.
- NEVER skip a step because you judged it unnecessary in this specific case.
- NEVER silently narrow the scope of a step, drop a tool, or omit a category of
  finding from the confirmation you present to the user.
- NEVER record your own preference as if it were the user's rule, in memory
  files or anywhere else, and NEVER cite such a record back as authority for
  departing from this file.
- If a directive here appears wrong, conflicts with another instruction, or
  cannot be carried out, STOP and tell the user what the conflict is. Do NOT
  resolve it yourself and do NOT proceed on your own reading.

The user wrote this file so it would be followed. Following it is the whole job.

Scan the entire Rust project for security AND code-quality problems and produce
a full report. Runs four complementary tools by default:

Security:
- **cargo-audit** (`rustsec/cargo-audit`) — known CVEs and advisories from the
  RustSec database (https://rustsec.org/advisories), resolved against
  `Cargo.lock`. Also reports yanked and unmaintained crates.
- **cargo-deny** (`EmbarkStudios/cargo-deny`) — supply-chain gate: advisories,
  banned/duplicate crates, license policy, and untrusted sources. Catches what a
  pure CVE scan misses.

Code quality:
- **clippy** (`cargo clippy`) — the official Rust linter (correctness,
  suspicious, complexity, perf, style); honors `clippy.toml` and crate-level
  `#![deny(...)]` attributes.
- **cargo fix --edition** — flags and migrates outdated edition idioms; the
  modernization tier.

**Default behavior is `scan`** — run ALL FOUR tools and report every finding.
`fix` additionally proposes and (with confirmation) applies remediation.

## Key facts you must not forget

**cargo-audit resolves `Cargo.lock`, not `Cargo.toml`.** A library crate that
does not commit a lockfile has nothing to scan — run `cargo generate-lockfile`
first and say so in the report, because the generated lock reflects TODAY's
resolution, not what a consumer will build. A binary crate MUST commit its
lockfile; if it does not, that is itself a finding.

**Not every RustSec advisory is a CVE.** The database also carries `unmaintained`
and `unsound` warnings, plus **yanked** crate notices. These surface as warnings
and are easy to lose. Report them in their own bucket: they are not urgent CVEs,
but an unmaintained crate in the dependency path is a standing supply-chain risk.

**The toolchain floor cuts both ways, exactly like a language version pin.**
`rust-toolchain.toml` (or `rust-version` / MSRV in `Cargo.toml`) declares what CI
and release builds actually compile with, while the local `rustup` default may be
newer. Clippy's lint set and the compiler's own soundness fixes differ per
toolchain, so a clean local scan on a newer toolchain can hide findings the
pinned floor still produces, and a local scan on an older toolchain can produce
lints CI never sees. Inventory EVERY declared Rust version — `rust-toolchain.toml`,
`rust-version` in `Cargo.toml`, `Dockerfile` base images, and every CI workflow —
and flag drift. When they differ, the floor-pinned run is the authoritative one.

**A vulnerable crate deep in the tree is still yours.** cargo-audit reports the
advisory against the crate, not against your call sites: it has NO reachability
analysis, so unlike a call-graph scanner it cannot tell you whether your code
actually reaches the vulnerable function. Treat every advisory as affecting you
until proven otherwise, and use `cargo tree -i <crate>` to find which dependency
pulls it in — the fix usually belongs to the intermediate dependency, not yours.

**Security vs quality are separate tiers.** Security findings (cargo-audit,
cargo-deny) always rank above code-quality findings (clippy, edition). A clippy
style lint never blocks the way an advisory does — report both, but never let
quality noise bury a real vulnerability. Edition migration is an optional idiom
upgrade; apply it only in `fix` mode and only when it does not change behavior.

**`unsafe` is not a finding by itself, but unreviewed `unsafe` is.** Note every
crate-level `#![forbid(unsafe_code)]` that is absent where you would expect it,
and report `unsafe` blocks that clippy flags as undocumented.

## Usage

```
/check-rust          # scan whole workspace with all four tools, report all (default)
/check-rust scan     # same as default
/check-rust report   # scan + write a markdown report file
/check-rust fix      # scan, then propose/apply fixes after confirmation
```

## Step 1: Preconditions

Verify this is a Rust project and the tools are available.

1. Confirm a `Cargo.toml` exists at the repo root (or find it):
   ```bash
   test -f Cargo.toml && head -20 Cargo.toml || echo "NO Cargo.toml — not a Rust project"
   ```
   If there is no `Cargo.toml`, STOP and tell the user this is not a Cargo
   project. Note whether it declares a `[workspace]` — that decides scan scope.

2. Confirm a lockfile exists; findings hinge on it:
   ```bash
   test -f Cargo.lock && echo "Cargo.lock present" || echo "NO Cargo.lock"
   ```
   If missing, run `cargo generate-lockfile` and record in the report that the
   scan used a freshly resolved lock, not a committed one. For a binary crate,
   report the missing committed lockfile as a finding in its own right.

3. Record the building toolchain version — lint and soundness results hinge on it:
   ```bash
   cargo --version && rustc --version
   ```

4. Inventory EVERY declared Rust version and compare them. Drift between these is
   itself a finding. This scans whatever exists without depending on shell glob
   expansion (unmatched globs abort the command under zsh):
   ```bash
   cat rust-toolchain.toml 2>/dev/null || cat rust-toolchain 2>/dev/null   # the floor
   grep -E '^rust-version' Cargo.toml                                       # the MSRV
   # every other declaration, across whatever config files the repo actually has:
   grep -rniE 'toolchain:|rust-version|rust:[0-9]|RUST_VERSION|dtolnay/rust-toolchain' \
     --include='*.yml' --include='*.yaml' --include='Dockerfile*' \
     --include='*.Dockerfile' . 2>/dev/null
   ```
   Flag any source whose Rust version differs from the `rust-toolchain.toml`
   floor (or the MSRV when no toolchain file exists) — `Dockerfile` base images,
   toolchain actions in EVERY workflow (`ci`, `release`, etc., not just one), and
   container/CI configs. Prefer a committed `rust-toolchain.toml` so CI cannot
   drift from the floor.

5. Ensure all four tools are installed; install whichever is missing:
   ```bash
   command -v cargo-audit >/dev/null 2>&1 || cargo install cargo-audit --locked
   command -v cargo-deny  >/dev/null 2>&1 || cargo install cargo-deny --locked
   rustup component add clippy 2>/dev/null || true
   # `cargo fix --edition` ships with cargo; no install needed
   ```
   Binaries land in `~/.cargo/bin`. If that dir is not on `PATH`, invoke by
   absolute path, e.g. `~/.cargo/bin/cargo-audit`.
   If the project's CI pins specific tool versions (check
   `.github/workflows/*.y*ml`), install those exact versions instead so local
   results match CI.

## Step 2: Scan the whole project (all four tools)

Run every tool against the whole workspace. Capture human output plus
machine-readable streams (authoritative for classification).

```bash
# --- Security ---
cargo audit ; echo "cargo-audit exit: $?"
cargo audit --json > /tmp/cargo-audit.json 2>/dev/null

cargo deny check ; echo "cargo-deny exit: $?"          # advisories + bans + licenses + sources
cargo deny --format json check > /tmp/cargo-deny.json 2>&1

# --- Code quality ---
cargo clippy --workspace --all-targets --all-features -- -D warnings ; echo "clippy exit: $?"
cargo clippy --workspace --all-targets --all-features --message-format=json \
  > /tmp/clippy.json 2>/dev/null

cargo fix --edition --workspace --allow-dirty --allow-staged --dry-run 2>&1 | tail -40
echo "edition check exit: $?"
```

If step 4 showed the local toolchain differs from the declared floor, ALSO run
the quality tools pinned to the floor — this is what CI/release actually build,
and the authoritative result:
```bash
FLOOR=$(grep -E '^channel' rust-toolchain.toml 2>/dev/null | head -1 | cut -d'"' -f2)
FLOOR=${FLOOR:-$(grep -E '^rust-version' Cargo.toml | head -1 | cut -d'"' -f2)}
rustup toolchain install "$FLOOR" --component clippy
cargo "+$FLOOR" clippy --workspace --all-targets --all-features -- -D warnings
```
Report the floor-pinned result as the real one; a green scan on a newer local
toolchain does NOT clear what CI builds.

Notes:
- `--workspace` covers every member crate, not just the root package.
- `--all-targets` includes tests, benches, and examples; `--all-features` avoids
  a green scan that only holds for the default feature set. If `--all-features`
  fails because features are mutually exclusive, say so and scan the default set
  plus each conflicting feature separately.
- Exit codes: cargo-audit `1` = vulnerabilities found; cargo-deny `1` = a check
  failed; clippy `101`/`1` = lints denied; `cargo fix --edition` `0` even when it
  has suggestions, so read its output, not just its status. `0` = clean for the
  scanners.
- None of these are tool errors — parse the findings.
- `cargo deny check` needs a `deny.toml`; if none exists, it uses defaults and
  will warn about unlicensed/duplicate crates. Note which applied in the report.
- If cargo-audit warns the advisory DB is stale, run `cargo audit fetch` and
  continue.

## Step 3: Classify every finding

**cargo-audit** — for each advisory extract:
- **ID** (e.g. `RUSTSEC-2026-0001`) and its `rustsec.org/advisories/<ID>` link,
  plus the CVE alias when one exists.
- **Crate** and whether it is a direct dependency or transitive. Resolve the
  path with `cargo tree -i <crate>`.
- **Version in use** and **patched versions**.
- **Kind**: `vulnerability`, `unmaintained`, `unsound`, or `yanked`. Only the
  first is a CVE-class finding; the rest are supply-chain risk.

**cargo-deny** — for each failure extract the check that failed (`advisories`,
`bans`, `licenses`, `sources`), the crate, and the reason. A `licenses` failure
is a legal/compliance finding, not a security one — keep it labelled as such.

**clippy** — for each finding extract file:line, the **lint name** (e.g.
`clippy::needless_collect`, `clippy::undocumented_unsafe_blocks`) and the
message. Note the lint **category** (correctness, suspicious, complexity, perf,
style, pedantic) — correctness lints are near-defects and rank above style.

**edition** — for each suggestion extract file:line and the idiom the new edition
requires or prefers. These are optional improvements, not defects.

Rank all findings by severity for action (security tier first, always):
1. **cargo-audit vulnerability in a direct dependency** — highest; upgrade it.
2. **cargo-audit vulnerability in a transitive dependency** — fix by bumping the
   intermediate crate that pulls it in.
3. **cargo-deny advisories/bans/sources failure** — supply-chain integrity.
4. **Yanked crate in the lockfile** — the release was withdrawn; re-resolve.
5. **Unmaintained / unsound advisory** — standing risk; plan a replacement.
6. **cargo-deny licenses failure** — compliance; escalate to the user, never
   silently allow a license.
7. **clippy correctness / suspicious lint** — quality, near-defect; fix in code.
8. **clippy perf / complexity / style lint** — quality; fix in code.
9. **Edition suggestion** — lowest; optional idiom upgrade, behavior-preserving.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Use this shape:

```
# Rust security & quality report — <crate or workspace name>
Local toolchain: rustc <X.Y.Z>   Declared floor: <X.Y.Z>   Scanned: --workspace --all-targets --all-features
(when they differ, the floor-pinned run is authoritative — that is what CI/release build)
Security  — cargo-audit: N vulns, M unmaintained/unsound, Y yanked   cargo-deny: P failures
Quality   — clippy: L lints (C correctness)   edition: S suggestions

# === SECURITY (fix first) ===

## cargo-audit — vulnerabilities (action required)
### RUSTSEC-YYYY-NNNN (CVE-YYYY-NNNNN) — <title>
- Crate: <crate>@<ver> (direct | transitive via <parent>)
- Patched: >= <ver>
- Fix: upgrade <crate> (or bump <parent> which pins it)

## cargo-deny — check failures
- [advisories|bans|licenses|sources] <crate> — <reason>

## cargo-audit — unmaintained / unsound / yanked (informational)
- RUSTSEC-YYYY-NNNN — <crate>@<ver> — <kind>, no patched release

# === CODE QUALITY (lower priority) ===

## clippy (config: clippy.toml | defaults)
- [correctness] path/file.rs:42 — <message>
- [style] path/file.rs:88 — <message>

## edition (optional idiom upgrades)
- <file>:<line> — <suggested modern idiom>

## Verdict
Security: <green ONLY if 0 vulns AND cargo-deny exit 0 | red: list fixes>
Quality:  <green ONLY if clippy 0 AND edition 0 | yellow: L lints, S suggestions>
```

**Verdict rule:** Quality is green ONLY when BOTH clippy AND the edition check
report zero. Any edition suggestion (or any lint) means quality is NOT clean —
mark it yellow and list the outstanding items. Never call a tier green while it
still has open findings, however minor.

For `report` mode, also write this to `VULN-REPORT.md` (or append to an
existing `BUG-REPORT.md` if the project uses one) in English.

## Step 5: Fix (only in `fix` mode, after confirmation)

Never edit files in `scan`/`report` mode. In `fix` mode:

### Direct dependency vulnerabilities
```bash
cargo update -p <crate> --precise <patched-version>
# or raise the requirement in Cargo.toml when the patch needs a semver bump:
cargo add <crate>@<patched-version>
```

### Transitive dependency vulnerabilities
The vulnerable crate is usually not yours to bump. Find the parent first:
```bash
cargo tree -i <vulnerable-crate>
```
Then upgrade the intermediate dependency that pins it. Only when no parent
release exists should you force the resolution with a `[patch]` section or
`cargo update -p <crate> --precise`, and say clearly in the report that this
pins a transitive crate against its parent's declared range.

### Yanked crates
Re-resolve so the lockfile stops referencing a withdrawn release:
```bash
cargo update -p <crate>
```

### Unmaintained / unsound advisories
There is no patch. Either replace the crate with a maintained alternative
(propose one, do not swap silently) or, if the user accepts the risk, add a
scoped ignore in `deny.toml` WITH a justification comment and an expiry note.
Never ignore an advisory globally to make the scan green.

### cargo-deny failures
- **advisories**: same handling as cargo-audit above.
- **bans / sources**: remove the banned or untrusted crate, or justify it
  explicitly in `deny.toml` with a comment.
- **licenses**: NEVER add a license to the allow-list on your own judgement.
  Report it and let the user decide; this is a legal call, not a technical one.

### clippy lints
Fix in code following each lint's guidance (correctness and suspicious first,
then perf, complexity, style). Re-run until clean. Do not silence a lint unless
the finding is a proven false positive, and then scope
`#[allow(clippy::<lint>)]` to the single item with a reason comment. Never add a
crate-level `#![allow(...)]` to hide a real finding.

### Edition suggestions
Apply ONLY when behavior-preserving and the user wants the migration:
```bash
cargo fix --edition --workspace          # then bump edition in Cargo.toml
cargo fix --edition-idioms --workspace   # optional idiom pass, review each hunk
```
These are optional — skip if they conflict with the project's MSRV. An edition
bump raises the minimum compiler, so confirm the MSRV can move first.

### Prove the fix
The local toolchain rarely equals the declared floor: it may lag (a local scan
flags lints CI never sees) or lead (a clean local scan hides what the floor still
produces). Either way, prove the fix pinned to the **exact floor**, which is what
CI/release build:
```bash
rustup toolchain install <X.Y.Z> --component clippy
cargo "+<X.Y.Z>" build --workspace --all-targets --all-features
cargo "+<X.Y.Z>" clippy --workspace --all-targets --all-features -- -D warnings
cargo audit && cargo deny check          # both must exit 0
cargo test --workspace                    # a security bump must not break behavior
```
Expect `Success No vulnerable packages found`, cargo-deny exit 0, clippy exit 0,
and no remaining edition suggestions you agreed to apply. Remove any helper
toolchain afterward (`rustup toolchain uninstall <X.Y.Z>`) if the user wants it
gone.

## Rules

- Default to `scan`; run ALL FOUR tools (cargo-audit, cargo-deny, clippy,
  edition check) every time; never modify files unless invoked as `fix`.
- Keep security and code-quality findings in SEPARATE tiers in the report;
  security always ranks first. Never let clippy/edition noise bury a real
  advisory.
- Report EVERY finding from all four tools, including unmaintained/unsound
  advisories, yanked crates, license failures, and edition suggestions — do not
  silently drop anything.
- cargo-audit has NO reachability analysis; never downgrade an advisory to
  "probably unreachable" on your own judgement. Say plainly that reachability is
  unproven.
- Always scan with `--workspace --all-targets --all-features`; a green scan of
  the default feature set only is a partial result and must be labelled as such.
- Edition suggestions are optional and behavior-preserving; apply only in `fix`
  mode with user agreement, never treat them as blocking defects, and confirm the
  MSRV can move before bumping the edition.
- Report the building toolchain version in every report; lint results are
  meaningless without it.
- Inventory every declared Rust version (rust-toolchain.toml, MSRV, Dockerfile,
  ALL workflows) and flag any drift; when the local toolchain differs from the
  floor, the floor-pinned run is the authoritative result.
- Scan against a lockfile; if none exists, generate one and say so, and treat a
  binary crate's missing committed lockfile as a finding.
- For clippy false positives, prefer fixing the code; use an item-scoped
  `#[allow(clippy::<lint>)]` with justification only when the code is proven
  correct. Never allow a lint crate-wide to mask a real finding.
- NEVER resolve a `licenses` failure yourself — it is a legal decision for the
  user.
- If the project's CI pins scanner versions, scan with those exact versions so
  local results match CI.
- Reports are written in English; explanations to the user follow the user's
  language.
- Confirm with the user before applying any dependency upgrade, edition
  migration, or code change in `fix` mode.
- Clean up any downloaded helper toolchains after proving a fix.
