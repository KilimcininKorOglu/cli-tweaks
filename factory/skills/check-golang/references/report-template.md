# check-golang: Report template

Print the ranked summary in this shape, most severe first:

```
# Go security & quality report — <module path>
Runtime: go<X.Y.Z>   Declared floor: go<X.Y.Z>   Scanned: ./...
(when they differ, the floor-pinned govulncheck is authoritative — that is what CI/release build)
Security  — govulncheck: N called, M imported-only   gosec: P (Q real, R false-pos)
Quality   — golangci-lint: L issues   gocyclo: C over limit   modernize: S suggestions

# === SECURITY (fix first) ===

## govulncheck — Called (action required)
### GO-YYYY-NNNN — <title>
- Package: crypto/tls (standard library)
- Found in: go<X.Y.Z> → Fixed in: go<X.Y.Z'>
- Fix: bump Go toolchain to >= go<X.Y.Z'> (go.mod + Dockerfile + CI + goreleaser)

## gosec — findings
### G705 (CWE-79) XSS — <file>:<line> [HIGH/HIGH]
- <what is tainted> → fix with the appropriate stdlib sanitizer.

## govulncheck — Imported-only (informational)
- GO-YYYY-NNNN — <module>@<ver> → fixed in <ver> (not reached by your code)

# === CODE QUALITY (lower priority) ===

## golangci-lint (config: .golangci.yml | defaults)
- [errcheck] path/file.go:42 — Error return value not checked

## gocyclo — functions over the complexity limit of 10
- <complexity> <package>.<Func> — <file>:<line> (refactor into smaller functions)

## modernize (optional idiom upgrades)
- <file>:<line> — <suggested modern idiom>

## Verdict
Security: <green ONLY if 0 called CVEs AND gosec exit 0 | red: list fixes>
Quality:  <green ONLY if lint 0 AND gocyclo 0 AND modernize 0 | yellow: L lint, C over limit, S modernize>
```
