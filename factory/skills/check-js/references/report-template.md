# check-js: Report template

Print the ranked summary in this shape, most severe first:

```
# JS/TS security & quality report — <package name>
Runtime: Node <vX.Y.Z>   Declared floor: <engines range>   Scanned: whole project
(when Node drift exists, name it — an EOL major is itself a security finding)
Context: Manager: npm|pnpm|yarn|bun
Security  — audit: N prod (C critical/high), M dev   semgrep: P (Q real, R false-pos)
Quality   — eslint: E errors, W warnings   complexity: C over limit   knip: U unused, D undeclared

# === SECURITY (fix first) ===

## audit — production dependencies (action required)
### GHSA-xxxx-xxxx-xxxx (CVE-YYYY-NNNNN) — <title> [critical]
- Package: <pkg>@<ver> (direct | transitive via <parent>)
- Patched: >= <ver>   Fix: semver-compatible | BREAKING major bump
- Fix: upgrade <pkg> (or bump <parent> which pins it)

## semgrep — findings
### <rule-id> (CWE-79) — <file>:<line> [ERROR]
- <what is tainted> → fix with the appropriate escape/validation.

## audit — dev dependencies (supply-chain risk)
- GHSA-xxxx — <pkg>@<ver> → fixed in <ver> (build/CI only, does not ship)

# === CODE QUALITY (lower priority) ===

## eslint (config: eslint.config.js | .eslintrc | none)
- [error] [no-unused-vars] path/file.ts:42 — <message>

## complexity — functions over the limit of 10
- path/file.ts:42 — <function> has a complexity of <N> (refactor into smaller functions)

## knip (config: knip.json | defaults)
- [unlisted dependency] <pkg> imported in path/file.ts — declare it in package.json
- [unused export] path/file.ts:12 — <name> (VERIFY before deleting)

## Verdict
Security: <green ONLY if 0 CVEs AND semgrep exit 0 | red: list fixes>
Quality:  <green ONLY if eslint 0 AND complexity 0 AND knip 0 | yellow: E errors, C over limit, U unused>
```
