---
name: check-swift
description: >
  This skill MUST be invoked when the user says "check-swift", "swiftlint",
  "swift-format", "semgrep", "cve tara", "cve raporu", "güvenlik açığı tara",
  "zafiyet tara", "vulnerability scan", "vuln scan", "scan for CVEs",
  "check vulnerabilities", "güvenlik taraması", "security scan",
  "static security analysis", "lint tara", "swift lint", "swift format",
  "lint check", "kod kalitesi tara"
  or any variation requesting a Swift security or code-quality scan of the whole
  project. Runs FOUR tools by default — dependency-check (CVEs in dependencies),
  semgrep (security static analysis), SwiftLint (lint), and swift-format lint
  (style/modernization) — installs any that are missing via Homebrew, scans every
  source file, classifies each finding, and produces a ranked combined report
  with fix guidance.
argument-hint: "[scan | report | fix]"
---

# Swift Security & Quality Scanner

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

Scan the entire Swift project for security AND code-quality problems and produce
a full report. Runs four complementary tools by default:

Security:
- **dependency-check** (OWASP, `brew install dependency-check`) — known CVEs in
  declared dependencies. Its Swift Package Manager analyzer reads `Package.swift`
  and is enabled by default; the CocoaPods (`.podspec`) and Carthage
  (`Cartfile.resolved`) analyzers are experimental.
- **semgrep** (`brew install semgrep`) — static analysis for insecure code
  patterns (weak crypto, hardcoded secrets, insecure transport, obsolete APIs).

Code quality:
- **SwiftLint** (`brew install swiftlint`) — aggregated lint rules; honors a repo
  `.swiftlint.yml`.
- **swift-format lint** (`brew install swift-format`) — style and idiom
  violations; honors a repo `.swift-format`.

**Default behavior is `scan`** — run ALL FOUR tools and report every finding.
`fix` additionally proposes and (with confirmation) applies remediation.

## Key facts you must not forget

**dependency-check is the only CVE scanner in this skill.** Its Swift Package
Manager analyzer is what reads `Package.swift`; nothing else here scans
dependencies for known vulnerabilities.

**A zero-dependency project has almost no SCA surface, and that is a finding in
itself, not a green light.** If there is no `Package.swift`, `Podfile`, or
`Cartfile`, dependency-check has nothing to analyze. Say so explicitly. The
remaining risk lives in the Xcode toolchain and Apple system frameworks, which
**no tool in this skill covers** — that surface is patched by updating Xcode and
macOS. Never report "0 CVEs" without stating what was actually scanned.

**dependency-check needs an NVD API key to be usable.** Since 9.0.0 it pulls from
the NVD API instead of the data feed; without a key the update is throttled hard
and the first run can take hours. Pass `--nvdApiKey "$NVD_API_KEY"` when the env
var is set, and if it is not, warn the user before starting a first-ever run that
it will be slow, and point them at https://nvd.nist.gov/developers/request-an-api-key.
The local database is cached between runs, so only the first sync is expensive.
Never commit a key; read it from the environment.

**semgrep Community Edition sees less Swift than the marketing implies.** Swift
parsing is GA, but much of the Swift rule coverage is Pro-only and needs
`semgrep login`. A clean CE run is therefore weak evidence on its own — state
which mode was used in the report. `semgrep scan --config=p/default` works
offline-ish and unauthenticated; `semgrep login && semgrep ci` gives full
coverage.

**SwiftLint has two modes and the useful one needs a build log.** `swiftlint lint`
is syntactic only. `swiftlint analyze --compiler-log-path <log>` enables analyzer
rules (unused imports, unused declarations in some setups) but requires a log
from a **clean** build — incremental builds produce an unusable log.

**Security vs quality are separate tiers.** Security findings (dependency-check,
semgrep) always rank above code-quality findings (SwiftLint, swift-format). A
lint or style hit never blocks on its own the way a reachable CVE does — report
both, but never let quality noise bury a real vulnerability. swift-format
findings are optional style upgrades; apply them only in `fix` mode and only when
they do not change behavior.

## Usage

```
/check-swift          # scan whole project with all four tools, report all (default)
/check-swift scan     # same as default
/check-swift report   # scan + write a markdown report file
/check-swift fix      # scan, then propose/apply fixes after confirmation
```

## Step 1: Preconditions

Verify this is a Swift project and inventory the build surface.

1. Confirm Swift sources and identify the project shape:
   ```bash
   ls Package.swift *.xcodeproj *.xcworkspace project.yml Podfile Cartfile 2>/dev/null
   find . -name '*.swift' -not -path './.build/*' -not -path './.git/*' | head -1 \
     || echo "NO Swift sources — not a Swift project"
   ```
   If there are no `.swift` files, STOP and tell the user this is not a Swift
   project.

2. Record the toolchain — findings hinge on it:
   ```bash
   swift --version
   xcodebuild -version
   ```

3. Determine how the project builds. This decides which commands work later:
   - `Package.swift` present → SwiftPM: `swift build`, `swift test`
   - `project.yml` present → the `.xcodeproj` is **generated by xcodegen and
     usually gitignored**; run `xcodegen generate` first or every Xcode-based
     command fails
   - `.xcworkspace` present → pass `-workspace`, not `-project`
   Record the scheme name; SwiftLint's analyze mode needs it.

4. Inventory every declared Swift/Xcode version and deployment target, then flag
   drift between them:
   ```bash
   grep -nE 'swift-tools-version|platforms:|\.macOS\(|\.iOS\(' Package.swift 2>/dev/null
   grep -nE 'SWIFT_VERSION|DEPLOYMENT_TARGET|xcodeVersion' project.yml *.xcconfig 2>/dev/null
   grep -rniE 'xcode-version|macos-[0-9]+|swift-version|runs-on' \
     --include='*.yml' --include='*.yaml' .github/ 2>/dev/null
   ```
   Flag any CI runner or Xcode version that differs from what the project
   declares. A newer local Xcode than CI hides errors CI will hit, and a stricter
   CI Xcode fails builds that pass locally — both are real findings.

5. Ensure all four tools are installed; install whichever is missing:
   ```bash
   command -v swiftlint       >/dev/null 2>&1 || brew install swiftlint
   command -v swift-format    >/dev/null 2>&1 || brew install swift-format
   command -v semgrep         >/dev/null 2>&1 || brew install semgrep
   command -v dependency-check>/dev/null 2>&1 || brew install dependency-check
   ```
   Install without asking — the skill is expected to self-provision. Do ask
   before the first `dependency-check` run if `NVD_API_KEY` is unset, because
   that run is slow (see Key facts).
   Xcode 16+ also ships `swift format` as a subcommand; prefer the Homebrew
   `swift-format` binary so the version is explicit and matches CI.

## Step 2: Scan the whole project (all four tools)

Run every tool across all sources. Capture human output plus machine-readable
streams (authoritative for classification).

```bash
# --- Security ---
# CVEs in declared dependencies (skip with a stated reason if no manifest exists)
dependency-check --scan . --format JSON --out /tmp/depcheck \
  ${NVD_API_KEY:+--nvdApiKey "$NVD_API_KEY"} ; echo "depcheck exit: $?"

semgrep scan --config=p/default --json --output=/tmp/semgrep.json . ; echo "semgrep exit: $?"
semgrep scan --config=p/default .                  # human-readable

# --- Code quality ---
swiftlint lint --quiet ; echo "swiftlint exit: $?"
swift-format lint --recursive --parallel . ; echo "swift-format exit: $?"
```

For SwiftLint's analyzer rules, and only when the user asked for a deep scan,
produce a clean build log first:
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/<ProductName>-*
xcodebuild -scheme <Scheme> -destination 'platform=macOS' clean build > /tmp/xcodebuild.log
swiftlint analyze --compiler-log-path /tmp/xcodebuild.log
```

Notes:
- Exit codes: SwiftLint `2` = violations found (`3` with `--strict` on warnings);
  swift-format lint `1` = violations; semgrep `1` = findings; dependency-check
  returns non-zero only with `--failOnCVSS`. None of these are tool errors —
  parse the findings.
- SwiftLint honors `.swiftlint.yml` and swift-format honors `.swift-format` if
  present; otherwise both use defaults. Note which applied in the report.
- If neither config exists, say so — the defaults are opinionated and the project
  never agreed to them, so treat those findings as advisory.
- Exclude `.build/`, `Pods/`, `Carthage/`, and `DerivedData/` from every scan.

## Step 3: Classify every finding

**dependency-check** — for each CVE extract:
- **CVE ID** and its NVD link, plus the **CVSS score and severity**.
- **Dependency** name and version, and which analyzer found it (SwiftPM /
  CocoaPods / Carthage).
- **Fixed in** version where the advisory states one.
- Whether the dependency is a **direct** declaration or transitive.
- dependency-check matches by CPE and is prone to **false positives** on name
  collisions — verify the flagged product really is the package in use.

**semgrep** — for each finding extract:
- **Rule ID** and **CWE**, file:line, code snippet.
- **Severity** (ERROR/WARNING/INFO).
- Judge whether it is a real risk or a **false positive**.
- Record whether the run was CE (`p/default`) or authenticated Pro — coverage
  differs and the report must say which.

**SwiftLint** — for each violation extract file:line, the **rule identifier**
(e.g. `force_cast`, `cyclomatic_complexity`), severity, and the message.

**swift-format lint** — for each violation extract file:line and the rule name.
These are optional style improvements, not defects.

Rank all findings by severity for action (security tier first, always):
1. **CVE in a direct dependency** — highest; upgrade the dependency.
2. **CVE in a transitive dependency** — upgrade the parent or pin an override.
3. **semgrep ERROR real finding** — fix in code.
4. **semgrep WARNING/INFO or false positive** — fix if cheap, else annotate
   `nosemgrep`.
5. **SwiftLint violation** — quality; fix in code (correctness rules first).
6. **swift-format violation** — lowest; optional style upgrade,
   behavior-preserving.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Use this shape:

```
# Swift security & quality report — <product name>
Toolchain: Swift <X.Y.Z>, Xcode <X.Y>   Build: <SwiftPM | xcodegen | xcodeproj>
Scanned: <dirs>   Dependency manifests: <Package.swift | none>
Security  — dependency-check: N CVEs (D direct, T transitive)   semgrep: P (Q real) [CE|Pro]
Quality   — SwiftLint: L issues   swift-format: S violations

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

## swift-format lint (config: .swift-format | defaults)
- <file>:<line> — <rule>

## Verdict
Security: <green ONLY if 0 CVEs AND semgrep 0 — and state what had no coverage>
Quality:  <green ONLY if SwiftLint 0 AND swift-format 0 | yellow: L lint, S style>
```

**Verdict rule:** Quality is green ONLY when BOTH SwiftLint AND swift-format
report zero. Any style violation (or any lint issue) means quality is NOT clean —
mark it yellow and list the outstanding items. Never call a tier green while it
still has open findings, however minor.

**Coverage rule:** A green security verdict MUST name what was not scanned — at
minimum the Xcode toolchain and Apple system frameworks, and the dependency
manifests when none exist. "0 CVEs" on a zero-dependency project means "nothing
was scanned", and reporting it as safety is a lie.

For `report` mode, also write this to `VULN-REPORT.md` (or append to an existing
`BUG-REPORT.md` if the project uses one) in English.

## Step 5: Fix (only in `fix` mode, after confirmation)

Never edit files in `scan`/`report` mode. In `fix` mode:

### Dependency CVEs
```bash
# SwiftPM: raise the requirement in Package.swift, then
swift package update <package>
swift package resolve
```
For CocoaPods, edit the `Podfile` and run `pod update <pod>`. Verify the new
version actually resolved by reading `Package.resolved` / `Podfile.lock` — a
version range can silently keep the vulnerable build.

### semgrep findings
- **Real finding**: fix the code — replace weak crypto with CryptoKit, move
  secrets to the Keychain, remove ATS exceptions, drop obsolete APIs.
- **False positive** (proven safe but semgrep cannot follow the sanitizer): add
  `// nosemgrep: <rule-id>` on the flagged line WITH a justification comment
  above it. Never disable a rule globally to mask a real finding.
- Re-run `semgrep scan --config=p/default .` until it reports 0.

### SwiftLint violations
Some are auto-fixable:
```bash
swiftlint lint --fix        # then re-run plain lint to see what remains
```
Fix the rest by hand following each rule's guidance. Re-run `swiftlint lint`
until 0. Do not silence a rule unless the finding is a proven false positive, and
then scope `// swiftlint:disable:next <rule>` to the single line with a reason.

### swift-format violations
Apply ONLY when behavior-preserving and the user wants the style upgrade:
```bash
swift-format format --in-place --recursive --parallel .
```
Review the diff before committing — the formatter reflows code the project may
have laid out deliberately. If the project has no `.swift-format`, ask before
reformatting the whole tree; a repo-wide reformat destroys `git blame`.

### Prove the fix
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/<ProductName>-*
xcodebuild -scheme <Scheme> -destination 'platform=macOS' clean build
xcodebuild -scheme <TestScheme> -destination 'platform=macOS' test
swiftlint lint --quiet && swift-format lint --recursive .   # both must exit 0
semgrep scan --config=p/default .                           # 0 findings
dependency-check --scan . --format JSON --out /tmp/depcheck ${NVD_API_KEY:+--nvdApiKey "$NVD_API_KEY"}
```
Expect a clean build, tests passing, SwiftLint and swift-format exit 0, no
semgrep findings, and no remaining CVEs. A clean build must start from deleted
DerivedData — an incremental build hides warnings cached from an earlier compile.

## Rules

- Default to `scan`; run ALL FOUR tools (dependency-check, semgrep, SwiftLint,
  swift-format) every time; never modify files unless invoked as `fix`.
- Install missing tools with Homebrew automatically, without asking. Only ask
  before the first dependency-check run when `NVD_API_KEY` is unset, because that
  run is slow.
- Keep security and code-quality findings in SEPARATE tiers in the report;
  security always ranks first. Never let lint/style noise bury a real CVE.
- Report EVERY finding from all four tools, including transitive CVEs, semgrep
  INFO findings, and swift-format violations — do not silently drop anything.
- swift-format violations are optional and behavior-preserving; apply only in
  `fix` mode with user agreement, never treat them as blocking defects.
- State the coverage gap in every security verdict: the Xcode toolchain and Apple
  system frameworks are not scanned by any tool here, and a project with no
  dependency manifest has no SCA surface at all.
- Report the Swift and Xcode versions in every report, and flag drift between the
  local toolchain and what CI declares.
- Say which semgrep mode ran (CE or authenticated Pro); a clean CE run is weaker
  evidence and the report must not imply otherwise.
- Note whether `.swiftlint.yml` and `.swift-format` exist; when they do not, mark
  those findings advisory rather than violations of an agreed standard.
- Never commit an NVD API key; read it from the environment.
- Reports are written in English; explanations to the user follow the user's
  language.
- Confirm with the user before applying any dependency upgrade, repo-wide
  reformat, or code change in `fix` mode.
