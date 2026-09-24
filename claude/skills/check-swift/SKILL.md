---
name: check-swift
description: >
  Swift security and code-quality scan of the whole project. Runs FOUR tools by default — dependency-check (CVEs in dependencies),
  semgrep (security static analysis), SwiftLint (lint), and swift-format lint
  (style and modernization) — through Homebrew,
  installs any that are missing, scans every source path, classifies each
  finding, and produces a ranked combined report with fix guidance.
  Requires a Swift project (`Package.swift` or an Xcode project present); check-golang, check-js, check-php, check-python and check-rust cover the other languages.
metadata:
  author: KilimcininKorOglu
  version: "1.0.0"
  category: code-quality
argument-hint: "[scan | report | fix]"
disable-model-invocation: true
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

   A red CI job is not always visible in the run you are looking at. When the
   inventory finds drift, check the last few runs of the affected workflow
   (`gh run list --workflow=<name>.yml --limit 6 --json headSha,conclusion`),
   because a job broken by an earlier bump keeps failing on every commit after
   it and is easy to read as a new failure or to miss entirely.

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

Write every machine-readable stream into a fresh per-run directory, NEVER a
fixed `/tmp/semgrep.json` / `/tmp/depcheck`. A shared path is the classic
cross-project trap: if a tool errors and does not overwrite, you silently parse
another repo's stale JSON as this project's findings. A unique dir per run makes
a write failure show up as a missing file instead of stale data.

```bash
RUNDIR="$(mktemp -d /tmp/check-swift.XXXXXXXX)"; echo "run dir: $RUNDIR"

# --- Security ---
# CVEs in declared dependencies (skip with a stated reason if no manifest exists)
dependency-check --scan . --format JSON --out "$RUNDIR/depcheck" \
  ${NVD_API_KEY:+--nvdApiKey "$NVD_API_KEY"} ; echo "depcheck exit: $?"

semgrep scan --config=p/default --json --output="$RUNDIR/semgrep.json" . ; echo "semgrep exit: $?"
semgrep scan --config=p/default .                  # human-readable

# --- Code quality ---
swiftlint lint --quiet ; echo "swiftlint exit: $?"
swift-format lint --recursive --parallel . ; echo "swift-format exit: $?"

# Cyclomatic complexity gate: every function must stay at or below 10.
# SwiftLint's cyclomatic_complexity rule is on by default at warning 10 / error
# 20, but a repo .swiftlint.yml may disable it or raise the thresholds. Run the
# gate from its own config so the project's config cannot weaken it.
cat > "$RUNDIR/complexity.swiftlint.yml" <<'YAML'
only_rules: [cyclomatic_complexity]
cyclomatic_complexity:
  warning: 10
  error: 10
excluded: [.build, Pods, Carthage, DerivedData]
YAML
swiftlint lint --config "$RUNDIR/complexity.swiftlint.yml" --quiet
echo "complexity exit: $?"
```

For SwiftLint's analyzer rules, and only when the user asked for a deep scan,
produce a clean build log first:
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/<ProductName>-*
xcodebuild -scheme <Scheme> -destination 'platform=macOS' clean build > "$RUNDIR/xcodebuild.log"
swiftlint analyze --compiler-log-path "$RUNDIR/xcodebuild.log"
```

Before classifying, confirm the report belongs to THIS project. Every finding's
file path MUST fall under the current repo root, and none may sit inside
`.build/`, `Pods/`, `Carthage/` or `DerivedData/`. If a path points outside it
(a sibling project, a stale file), discard that finding and re-run the tool into
a fresh `$RUNDIR` — never report another project's issues as this one's.

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

**complexity** — for each `cyclomatic_complexity` violation extract file:line,
the function name, and the reported complexity. Every one is a function over the
limit of 10. Unlike a style violation this is NOT optional: the limit is a
project rule, and a function above it must be refactored into smaller
single-responsibility functions, never suppressed and never given a raised
threshold. Report separately whether the project's own `.swiftlint.yml` disables
the rule or raises its thresholds — that is a finding of its own.

Rank all findings by severity for action (security tier first, always):
1. **CVE in a direct dependency** — highest; upgrade the dependency.
2. **Swift/Xcode version drift** — a CI runner or workflow declares a version
   other than what the project declares. Ranked here because it is how CI builds
   something the local scan never checked, in either direction.
3. **CVE in a transitive dependency** — upgrade the parent or pin an override.
4. **semgrep ERROR real finding** — fix in code.
5. **semgrep WARNING/INFO or false positive** — fix if cheap, else annotate
   `nosemgrep`.
6. **SwiftLint violation** — quality; fix in code (correctness rules first).
7. **Function over the complexity limit (`cyclomatic_complexity` > 10)** —
   quality; refactor into smaller functions. Ranked above the style tier because
   it is a limit, not a suggestion.
8. **swift-format violation** — lowest; optional style upgrade,
   behavior-preserving.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Read
[references/report-template.md](references/report-template.md) and use its
shape exactly.

**Verdict rule:** Quality is green ONLY when SwiftLint, the complexity gate AND
swift-format all report zero. Any style violation (or any lint issue) means quality is NOT clean —
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

A `fix` run repairs one finding class after another. A finished finding is a
checkpoint, not an ending: continue to the next finding in the same turn. A
decision the run genuinely needs from the user still ends the turn.

### Dependency CVEs
```bash
# SwiftPM: raise the requirement in Package.swift, then
swift package update <package>
swift package resolve
```
For CocoaPods, edit the `Podfile` and run `pod update <pod>`. Verify the new
version actually resolved by reading `Package.resolved` / `Podfile.lock` — a
version range can silently keep the vulnerable build.

### Swift/Xcode version drift
The fix is a version alignment, not a code change. Raise or align the version
everywhere the Step 1 inventory found it:
- `Package.swift` — `swift-tools-version` and the `platforms:` deployment targets
- `project.yml` / `*.xcconfig` — `SWIFT_VERSION`, `*_DEPLOYMENT_TARGET`
- CI workflows — the `runs-on` macOS image and any explicit Xcode selection
  (`xcode-version`, `xcode-select`) in EVERY `.github/workflows/*.y*ml` (ci,
  release, and any other), not just one

After aligning, re-run the Step 1 inventory and confirm no source still names a
version below the project's declared floor. A bump that misses one source is
silent in the scan output but red in CI on every push that follows.

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

### Functions over the complexity limit
Refactor each function the complexity gate reported into smaller
single-responsibility functions: extract the branches of a long `if`/`switch`
chain into named methods, lift error handling out of the happy path, and split
functions that do two jobs. NEVER raise the thresholds in `.swiftlint.yml`, add a
`// swiftlint:disable cyclomatic_complexity`, or drop the gate to make the report
green. Re-run the gate until it reports nothing.

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
dependency-check --scan . --format JSON --out "$RUNDIR/depcheck" ${NVD_API_KEY:+--nvdApiKey "$NVD_API_KEY"}
```
Expect a clean build, tests passing, SwiftLint and swift-format exit 0, no
semgrep findings, and no remaining CVEs. A clean build must start from deleted
DerivedData — an incremental build hides warnings cached from an earlier compile.
Then remove any helper tool this run installed (`brew uninstall <formula>` for
whichever of swiftlint, swift-format, semgrep or dependency-check it added) and
say so. The run installed it, so the run removes it; offering to remove it and
leaving it installed does not count.

## Rules

- Default to `scan`; run ALL FOUR tools (dependency-check, semgrep, SwiftLint,
  swift-format) plus the complexity gate every time; never modify files unless
  invoked as `fix`.
- Enforce a cyclomatic complexity limit of 10 per function by running SwiftLint
  from a gate-only config, so a repo `.swiftlint.yml` that disables the rule or
  raises its thresholds cannot weaken it; report such a config as a finding of
  its own. NEVER raise the thresholds, add a `swiftlint:disable`, or drop the
  gate to make the report green.
- Install missing tools with Homebrew automatically, without asking. Only ask
  before the first dependency-check run when `NVD_API_KEY` is unset, because that
  run is slow.
- NEVER truncate a scan command's output with `head`, `tail`, or a count flag.
  A capped run reports the first few findings and hides the rest, so the next
  run finds work you already called done. Read the whole output; use the
  machine-readable stream in `$RUNDIR` when the human output is long. A
  config-header display, an existence probe and a single-value extraction may
  still use them, because they read one known field, not a finding list.
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
- Never "fix" version drift by editing project code — it is a version alignment;
  raise it in EVERY source that declares it, then re-run the inventory and
  confirm none still names a version below the declared floor.
- Write every machine-readable stream into a fresh `mktemp -d` run directory,
  never a fixed `/tmp` path, so a failed write shows up as a missing file instead
  of another project's stale JSON.
- Confirm every finding's file path falls under the current repo root and outside
  `.build/`, `Pods/`, `Carthage/` and `DerivedData/` before classifying it;
  discard and re-scan anything that points elsewhere.
- Clean up any helper tool this run installed with Homebrew after proving a fix.
- If the project's CI pins scanner versions, scan with those exact versions so
  local results match CI.
- Say which semgrep mode ran (CE or authenticated Pro); a clean CE run is weaker
  evidence and the report must not imply otherwise.
- Note whether `.swiftlint.yml` and `.swift-format` exist; when they do not, mark
  those findings advisory rather than violations of an agreed standard.
- Never commit an NVD API key; read it from the environment.
- Reports are written in English; explanations to the user follow the user's
  language.
- Confirm with the user before applying any dependency upgrade, repo-wide
  reformat, or code change in `fix` mode.
