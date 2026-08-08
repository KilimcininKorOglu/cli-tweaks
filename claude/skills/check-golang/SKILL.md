---
name: check-golang
description: >
  Go security and code-quality scan of the whole project. Invoke on "check-golang",
  "govulncheck", "gosec", "golangci-lint", "modernize", "modernizer", "go lint",
  or any variation naming Go or its tooling.
  ALSO invoke on the language-agnostic requests "cve tara", "cve raporu",
  "güvenlik açığı tara", "zafiyet tara", "güvenlik taraması", "kod kalitesi tara",
  "lint tara", "lint check", "vulnerability scan", "vuln scan", "scan for CVEs",
  "check vulnerabilities", "security scan", "static security analysis" — but ONLY
  when the target project is Go. Those phrases are shared verbatim with
  check-js, check-php, check-rust and check-swift, so they carry no language
  signal: choose by what the project actually is (`go.mod` present) and never by
  the phrase alone. If the repository holds more than one of these languages, ask
  which one the user means instead of guessing.
  Runs FOUR tools by default — govulncheck (CVEs), gosec (security
  static analysis), golangci-lint (lint), and the gopls modernize analyzer —
  installs any that are missing, scans every package with ./..., classifies each
  finding, and produces a ranked combined report with fix guidance.
argument-hint: "[scan | report | fix]"
---

# Go Security & Quality Scanner

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

Scan the entire Go project for security AND code-quality problems and produce a
full report. Runs four complementary tools by default:

Security:
- **govulncheck** (`golang.org/x/vuln/cmd/govulncheck`) — known CVEs from the Go
  vulnerability database (https://pkg.go.dev/vuln), stdlib and dependencies.
- **gosec** (`github.com/securego/gosec/v2/cmd/gosec`) — static analysis for
  insecure code patterns (injection, weak crypto, unhandled errors, taint).

Code quality:
- **golangci-lint** (`github.com/golangci/golangci-lint/v2`) — aggregated linters
  (errcheck, unused, staticcheck, etc.); honors any `.golangci.*` config.
- **modernize** (`golang.org/x/tools/gopls/internal/analysis/modernize`) — flags
  outdated idioms replaceable with modern Go equivalents.

**Default behavior is `scan`** — run ALL FOUR tools and report every finding.
`fix` additionally proposes and (with confirmation) applies remediation.

## Key facts you must not forget

**govulncheck** reports standard-library CVEs against the **Go toolchain version
that builds the code**, NOT the `go` directive in `go.mod`. A stdlib finding
usually means "the toolchain building this project is older than the patched
release." Fix stdlib CVEs by raising the Go line in EVERY place that declares it
— `go.mod`, `Dockerfile`, every CI workflow, and `.goreleaser.y*ml` — never by
editing project code; a stale `release.yml` ships CVE-carrying binaries even when
`ci.yml` is green. Third-party module CVEs are fixed by upgrading the dependency.

**The toolchain mismatch cuts BOTH ways.** If the local toolchain is *older*
than the patched release, a local scan yields false *positives* CI already
fixed. If the local toolchain is *newer* than the `go` directive, a clean local
scan is a false *negative*: CI and release builds run with `GOTOOLCHAIN=auto`,
which downloads and compiles with the **`go.mod` floor**, so the shipped binary
carries every CVE fixed after that floor. `go-version-file: go.mod` resolves to
that floor too, and a pinned `go-version: "1.22"` still auto-upgrades to the
floor. Never trust a green scan whose `go version` differs from the `go.mod`
floor — always scan pinned to the floor as well (see Step 1 and Prove the fix).

**gosec** flags insecure code patterns. It runs taint analysis (v2.28+): G705
(XSS — escape client-controlled data reflected into HTML) and G706 (log
injection — strip CR/LF+control chars from client-controlled values before
logging). gosec recognizes stdlib sanitizers like `html.EscapeString` but NOT
custom sanitizer funcs — for a proven-safe custom-sanitized line, annotate with
`// #nosec <RULE>` plus a justification comment rather than disabling the rule
globally. In CI, pin gosec/govulncheck to fixed versions, never `@latest` — new
rule releases silently break pipelines. For ad-hoc LOCAL scans `@latest` is fine
(and is the only option for modernize, which ships no stable binary); if the
project's CI pins tool versions, match them locally so results agree.

**Security vs quality are separate tiers.** Security findings (govulncheck,
gosec) always rank above code-quality findings (golangci-lint, modernize). A
lint or modernize hit never blocks on its own the way a called CVE does — report
both, but never let quality noise bury a real vulnerability. modernize suggestions
are optional idiom upgrades; apply them only in `fix` mode and only when they do
not change behavior.

## Usage

```
/check-golang          # scan whole project with all four tools, report all (default)
/check-golang scan     # same as default
/check-golang report   # scan + write a markdown report file
/check-golang fix      # scan, then propose/apply fixes after confirmation
```

## Step 1: Preconditions

Verify this is a Go project and the tool is available.

1. Confirm a `go.mod` exists at the repo root (or find it):
   ```bash
   test -f go.mod && head -5 go.mod || echo "NO go.mod — not a Go project"
   ```
   If there is no `go.mod`, STOP and tell the user this is not a Go module.

2. Record the building toolchain version — findings hinge on it:
   ```bash
   go version
   ```

3. Inventory EVERY declared Go version and compare them. Drift between these is
   itself a finding (it caused shipped-binary CVEs in the wild). This scans
   whatever exists without depending on shell glob expansion (unmatched globs
   abort the command under zsh):
   ```bash
   grep -E '^(go|toolchain) ' go.mod                    # the floor
   # every other declaration, across whatever config files the repo actually has:
   grep -rniE 'go-version"?:|golang:[0-9]|GO_VERSION|golang\.org/dl/go' \
     --include='*.yml' --include='*.yaml' --include='Dockerfile*' \
     --include='*.Dockerfile' . 2>/dev/null
   ```
   Flag any source whose Go version differs from the `go.mod` floor —
   `Dockerfile` base images, `go-version` / `go-version-file` in every workflow
   (`ci`, `release`, etc., not just one), `.goreleaser.y*ml`, and container/CI
   configs. If `go version` (step 2) is NEWER than the `go.mod` floor, a plain
   local scan is a false negative — you MUST also scan pinned to the floor
   (Step 2, and Prove the fix). Prefer `go-version-file: go.mod` so CI cannot
   drift from the floor.

4. Ensure all four tools are installed; install whichever is missing:
   ```bash
   command -v govulncheck >/dev/null 2>&1 || go install golang.org/x/vuln/cmd/govulncheck@latest
   command -v gosec >/dev/null 2>&1 || go install github.com/securego/gosec/v2/cmd/gosec@latest
   command -v golangci-lint >/dev/null 2>&1 || go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
   # modernize has no stable binary name; run it via `go run` (see Step 2)
   ```
   Binaries land in `$(go env GOPATH)/bin`. If that dir is not on `PATH`, invoke
   by absolute path, e.g. `$(go env GOPATH)/bin/gosec`.
   If the project's CI pins specific tool versions (check
   `.github/workflows/*.y*ml`), install those exact versions instead so local
   results match CI.

## Step 2: Scan the whole project (all four tools)

Run every tool against every package. Capture human output plus machine-readable
streams (authoritative for classification).

```bash
# --- Security ---
govulncheck ./...
govulncheck -json ./... > /tmp/govuln.json

gosec ./... 2>&1 | tail -40                          # exit 1 if issues
gosec -fmt=json -out=/tmp/gosec.json -quiet ./... ; echo "gosec exit: $?"

# --- Code quality ---
golangci-lint run ./... ; echo "golangci exit: $?"    # exit 1 if issues
go run golang.org/x/tools/gopls/internal/analysis/modernize/cmd/modernize@latest ./... ; echo "modernize exit: $?"
```

If step 3 showed `go version` differs from the `go.mod` floor (typically local
is newer), ALSO run govulncheck pinned to the floor — this is what CI/release
actually build, and the authoritative security result:
```bash
FLOOR=$(awk '/^go /{print $2; exit}' go.mod)
case "$FLOOR" in *.*.*) ;; *) FLOOR="$FLOOR.0" ;; esac  # go 1.26 -> 1.26.0 (dl needs full patch)
go install golang.org/dl/go${FLOOR}@latest && go${FLOOR} download
GOTOOLCHAIN=local go${FLOOR} run golang.org/x/vuln/cmd/govulncheck@latest ./...
```
Report the floor-pinned result as the real one; a green scan on a newer local
toolchain does NOT clear the shipped binary.

Notes:
- `./...` covers all packages, including `cmd/` and `internal/`.
- Exit codes: govulncheck `3` = CVE in **called** code; gosec `1` = issues;
  golangci-lint `1` = issues; modernize `3` = suggestions. `0` = clean for all.
  None of these are tool errors — parse the findings.
- If govulncheck errors because the toolchain is too old for the vuln DB, note
  it and continue — the DB still resolves.
- golangci-lint honors a repo `.golangci.*` config if present; otherwise it uses
  its defaults. Note which applied in the report.

## Step 3: Classify every finding

**govulncheck** — for each CVE extract:
- **ID** (e.g. `GO-2026-5856`) and its `pkg.go.dev/vuln/<ID>` link.
- **Package** and whether it is **Standard library** or a third-party module.
- **Found in** version and **Fixed in** version.
- **Called vs imported-only**: govulncheck separates vulns your code actually
  reaches ("Your code is affected") from ones only present in required modules
  ("found in modules you require, but your code doesn't appear to call these").

**gosec** — for each finding extract:
- **Rule** (e.g. `G404`, `G705`) and **CWE**, file:line, code snippet.
- **Severity** (HIGH/MEDIUM/LOW) and **Confidence** (HIGH/MEDIUM/LOW).
- Judge whether it is a real risk or a **false positive** (e.g. taint that is
  already sanitized, or an operator-controlled value gosec cannot prove safe).

**golangci-lint** — for each finding extract file:line, the **linter name**
(e.g. `errcheck`, `staticcheck`, `unused`) and the message.

**modernize** — for each suggestion extract file:line and the modern idiom it
proposes (e.g. "Ranging over SplitSeq is more efficient"). These are optional
improvements, not defects.

Rank all findings by severity for action (security tier first, always):
1. **Called stdlib CVE** — highest; fix by bumping the Go toolchain.
2. **Go version drift** — a release, container or CI path declares a version
   other than the module floor; fix by raising every declaring location. Ranked
   here because it is how a stdlib CVE reaches production while the local scan
   reads clean.
3. **Called third-party CVE** — fix by upgrading the module.
4. **gosec HIGH/MEDIUM real finding** — fix in code.
5. **gosec LOW / false positive** — sanitize if cheap, else annotate `#nosec`.
6. **Imported-only CVE** (not called) — note but not urgent.
7. **golangci-lint issue** — quality; fix in code (correctness linters first).
8. **modernize suggestion** — lowest; optional idiom upgrade, behavior-preserving.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Use this shape:

```
# Go security & quality report — <module path>
Local toolchain: go<X.Y.Z>   go.mod floor: go<X.Y.Z>   Scanned: ./...
(when they differ, the floor-pinned govulncheck is authoritative — that is what CI/release build)
Security  — govulncheck: N called, M imported-only   gosec: P (Q real, R false-pos)
Quality   — golangci-lint: L issues   modernize: S suggestions

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

## modernize (optional idiom upgrades)
- <file>:<line> — <suggested modern idiom>

## Verdict
Security: <green ONLY if 0 called CVEs AND gosec exit 0 | red: list fixes>
Quality:  <green ONLY if lint 0 AND modernize 0 | yellow: L lint, S modernize>
```

**Verdict rule:** Quality is 🟢 green ONLY when BOTH golangci-lint AND modernize
report zero. Any modernize suggestion (or any lint issue) means quality is NOT
clean — mark it 🟡 yellow and list the outstanding items. Never call a tier green
while it still has open findings, however minor.

For `report` mode, also write this to `VULN-REPORT.md` (or append to an
existing `BUG-REPORT.md` if the project uses one) in English.

## Step 5: Fix (only in `fix` mode, after confirmation)

Never edit files in `scan`/`report` mode. In `fix` mode:

### Standard-library CVEs
The fix is a toolchain bump, not a code change. Find the highest "Fixed in"
across all stdlib findings and raise the Go line everywhere the Step 1 inventory
found it:
- `go.mod` — the `go X.Y.Z` directive (the floor CI/release resolve to)
- `Dockerfile` — `FROM golang:X.Y-alpine@sha256:...` (fetch the new digest)
- CI workflows — `go-version` in EVERY `.github/workflows/*.y*ml` (ci, release,
  and any other), not just one; prefer `go-version-file: go.mod` so they track
  the floor automatically and cannot drift
- `.goreleaser.y*ml` and any other container/CI config with a pinned Go version
Keep every source on the same Go line — a stale `release.yml` ships CVE-carrying
binaries even when `ci.yml` is green.

### Third-party CVEs
```bash
go get <module>@<fixed-version> && go mod tidy
```

### gosec findings
- **Real finding**: fix the code. XSS (G705) → escape with `html.EscapeString`;
  log injection (G706) → strip CR/LF+control chars before logging; weak crypto,
  unhandled errors, etc. → follow the rule's guidance.
- **False positive** (proven safe but gosec cannot follow the sanitizer/validator):
  add `// #nosec <RULE>` on the flagged line WITH a justification comment above
  it. Never disable a rule globally to hide a real finding.
- Re-run `gosec ./...` until it exits 0.

### golangci-lint issues
Fix in code following each linter's guidance (unchecked errors, unused code,
staticcheck simplifications, etc.). Re-run `golangci-lint run ./...` until 0.
Do not silence a linter unless the finding is a proven false positive, and then
scope the `//nolint:<linter>` to the single line with a reason.

### modernize suggestions
Apply ONLY when behavior-preserving and the user wants the idiom upgrade (e.g.
`strings.SplitSeq` for range loops, `min`/`max` builtins, `slices`/`maps`
helpers). These are optional — skip if they conflict with the project's minimum
Go version. Re-run the analyzer to confirm.

### Prove the fix
The local toolchain rarely equals the new floor: it may lag (a local scan flags
CVEs CI already fixes — false positive) or lead (a clean local scan hides CVEs
the floor still ships — false negative). Either way, prove the fix pinned to the
**exact new floor**, which is what CI/release build:
```bash
go install golang.org/dl/go<X.Y.Z>@latest && go<X.Y.Z> download
go<X.Y.Z> build ./... && go<X.Y.Z> vet ./...
GOTOOLCHAIN=local go<X.Y.Z> run golang.org/x/vuln/cmd/govulncheck@latest ./...
gosec ./... && golangci-lint run ./...   # both must exit 0
```
Expect `No vulnerabilities found`, gosec/golangci-lint exit 0, and no remaining
modernize suggestions you agreed to apply. Then remove any helper toolchain this
run downloaded (`rm -rf ~/sdk/go<X.Y.Z> "$(go env GOPATH)/bin/go<X.Y.Z>"`) and say
so. The run installed it, so the run removes it; offering to remove it and
leaving it installed does not count.

## Rules

- Default to `scan`; run ALL FOUR tools (govulncheck, gosec, golangci-lint,
  modernize) every time; never modify files unless invoked as `fix`.
- Keep security and code-quality findings in SEPARATE tiers in the report;
  security always ranks first. Never let lint/modernize noise bury a real CVE.
- Report EVERY finding from all four tools, including imported-only CVEs, gosec
  LOW issues, and modernize suggestions — do not silently drop anything.
- modernize suggestions are optional and behavior-preserving; apply only in
  `fix` mode with user agreement, never treat them as blocking defects.
- Report the building toolchain version in every report; stdlib findings are
  meaningless without it.
- Inventory every declared Go version (go.mod floor, Dockerfile, ALL workflows,
  goreleaser) and flag any drift; when the local toolchain differs from the
  `go.mod` floor, the floor-pinned govulncheck is the authoritative result.
- Never "fix" a stdlib CVE by editing project code — it is always a toolchain
  bump; raise the Go line in EVERY source that declares it, not just go.mod.
- For gosec false positives, prefer a real sanitizer/validator; use a
  line-scoped `// #nosec <RULE>` with justification only when the code is proven
  safe. Never disable a rule globally to mask a real finding.
- If the project's CI pins scanner versions, scan with those exact versions so
  local results match CI.
- Reports are written in English; explanations to the user follow the user's
  language.
- Confirm with the user before applying any dependency upgrade, toolchain bump,
  or code change in `fix` mode.
- Clean up any downloaded helper toolchains after proving a fix.
