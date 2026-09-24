# check-python: Report template

Print the ranked summary in this shape, most severe first:

```
# Python security & quality report — <project name>
Runtime: python<X.Y.Z>   Declared floor: <requires-python X.Y>   Scanned: <source paths>
Context: Dependency source: <--locked . | -r requirements.txt | pip-audit . | none (plain script mode)>
Security  — pip-audit: N vulns (D direct, T transitive)   bandit: P (Q real, R false-pos)   semgrep: S
Quality   — ruff: L violations   C901: C over limit   UP: U suggestions   mypy: <E errors | not configured>

# === SECURITY (fix first) ===

## pip-audit — vulnerabilities
### GHSA-xxxx-xxxx-xxxx — <package> <version>
- Fixed in: <version>   Dependency: direct | transitive (via <parent>)
- Fix: pin <package>>=<version> in <manifest>

## bandit — findings
### B602 (CWE-78) subprocess with shell=True — <file>:<line> [HIGH/HIGH]
- <what is tainted> → fix by passing an argument list instead of a shell string.

## semgrep — findings
### <rule-id> — <file>:<line>
- <taint path source → sink>

# === CODE QUALITY (lower priority) ===

## ruff (config: pyproject.toml [tool.ruff] | ruff.toml | defaults)
- [F401] path/file.py:12 — `os` imported but unused

## ruff C901 — functions over the complexity limit of 10
- <function> (complexity <N>) — <file>:<line> (refactor into smaller functions)

## mypy — type errors
- [arg-type] path/file.py:88 — Argument 1 has incompatible type "str"; expected "int"

## ruff UP (optional idiom upgrades, bounded by requires-python)
- <file>:<line> — <suggested modern idiom>

## Verdict
Security: <🟢 green ONLY if 0 vulns AND bandit 0 AND semgrep 0 | 🔴 red: list fixes>
Quality:  <🟢 green ONLY if ruff 0 AND C901 0 AND UP 0 AND mypy 0-or-not-configured | 🟡 yellow: list>
```
