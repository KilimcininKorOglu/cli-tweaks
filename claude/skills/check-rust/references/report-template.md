# check-rust: Report template

Print the ranked summary in this shape, most severe first:

```
# Rust security & quality report — <crate or workspace name>
Runtime: rustc <X.Y.Z>   Declared floor: <X.Y.Z>   Scanned: --workspace --all-targets --all-features
(when they differ, the floor-pinned run is authoritative — that is what CI/release build)
Security  — cargo-audit: N vulns, M unmaintained/unsound, Y yanked   cargo-deny: P failures
Quality   — clippy: L lints (C correctness)   complexity: X over limit   edition: S suggestions

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

## complexity — functions over the limit of 10 (lizard, cyclomatic)
- path/file.rs:42 — <fn> has a cyclomatic complexity of <N> (refactor into smaller functions)

## edition (optional idiom upgrades)
- <file>:<line> — <suggested modern idiom>

## Verdict
Security: <green ONLY if 0 vulns AND cargo-deny exit 0 | red: list fixes>
Quality:  <green ONLY if clippy 0 AND complexity 0 AND edition 0 | yellow: L lints, X over limit, S suggestions>
```
