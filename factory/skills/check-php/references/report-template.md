# check-php: Report template

Print the ranked summary in this shape, most severe first:

```
# PHP security & quality report — <package name>
Runtime: PHP <X.Y.Z>   Declared floor: <composer.json constraint>   Scanned: <src paths>
(when they differ, the floor-pinned run is authoritative)
Context: platform override: <ver|none>
Security  — composer audit: N prod, M dev   progpilot: P (Q open, R false-pos)   semgrep: S raw / F filtered (G open)
Quality   — phpstan: E errors (level L, baseline: yes/no, B suppressed)   phpmd: C over limit   rector: T suggestions

# === SECURITY (fix first) ===

## composer audit — production dependencies (action required)
### CVE-YYYY-NNNNN — <title>
- Package: <vendor/pkg>@<ver> (direct | transitive via <parent>)
- Patched: >= <ver>   Fix: semver-compatible | BREAKING major bump
- Fix: composer require <vendor/pkg>:^<patched>

## progpilot — taint findings
### sql_injection (CWE-89) — <sink file>:<line>
- Path: <source file>:<source line> (<source name>) → <sink name>
- Guard on the line: <the guard you read, or "none">
- Fix: use a prepared statement / the appropriate escaping for that sink.

## semgrep — pattern findings (S raw, F after the superglobal filter)
### <rule id> — <file>:<line>
- Line: <the source line you read from the file>
- Fix: <the escaping or cast that closes it>

## composer audit — dev dependencies (supply-chain risk)
- CVE-YYYY-NNNNN — <vendor/pkg>@<ver> → fixed in <ver> (does not ship)

# === CODE QUALITY (lower priority) ===

## phpstan (config: phpstan.neon | defaults, level L)
- [argument.type] path/File.php:42 — <message>
BASELINE: phpstan-baseline.neon suppresses B findings — this run is NOT a clean codebase.

## phpmd codesize — methods over the complexity limit of 10
- path/File.php:42 — <Class>::<method> has a Cyclomatic Complexity of <N> (refactor)

## rector (sets: <configured sets>, target PHP <ver>) — optional idiom upgrades
- <file>:<line> — <rule> — <suggested modern idiom>

## Verdict
Security: <green ONLY if 0 advisories AND 0 open taint findings | red: list fixes>
Quality:  <green ONLY if phpstan 0 AND phpmd 0 AND rector 0 AND no baseline | yellow: E errors, C over limit, T suggestions>
```
