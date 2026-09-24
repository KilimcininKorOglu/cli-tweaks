# check-swift: Report template

Print the ranked summary in this shape, most severe first:

```
# Swift security & quality report — <product name>
Runtime: Swift <X.Y.Z>, Xcode <X.Y>   Declared floor: swift-tools-version <X.Y>   Scanned: <dirs>
Context: Build: <SwiftPM | xcodegen | xcodeproj>   Dependency manifests: <Package.swift | none>
Security  — dependency-check: N CVEs (D direct, T transitive)   semgrep: P (Q real) [CE|Pro]
Quality   — SwiftLint: L issues   complexity: C over limit   swift-format: S violations

# === SECURITY (fix first) ===

## dependency-check — CVEs
### CVE-YYYY-NNNNN — <package>@<ver> [CVSS 9.8 CRITICAL]
- Fixed in: <ver>   Direct dependency
- Fix: raise the version in Package.swift and re-resolve

## semgrep — findings
### <rule-id> (CWE-NNN) — <file>:<line> [ERROR]
- <what is unsafe> → <fix>

# === CODE QUALITY (lower priority) ===

## SwiftLint (config: .swiftlint.yml | defaults)
- [force_cast] <file>:<line> — Force casts should be avoided

## complexity — functions over the limit of 10
- <file>:<line> — <function> has a cyclomatic complexity of <N> (refactor)
(note when the project's .swiftlint.yml disables the rule or raises its thresholds)

## swift-format lint (config: .swift-format | defaults)
- <file>:<line> — <rule>

## Verdict
Security: <🟢 green ONLY if 0 CVEs AND semgrep 0 | 🔴 red: list fixes — and state what had no coverage>
Quality:  <🟢 green ONLY if SwiftLint 0 AND complexity 0 AND swift-format 0 | 🟡 yellow: L lint, C over limit, S style>
```
