---
name: check-js
description: >
  JavaScript or TypeScript security and code-quality scan of the whole project.
  Invoke on "check-js", "check-ts", "npm audit", "eslint", "knip", "js lint",
  "ts lint", "ölü kod tara", or any variation naming JavaScript, TypeScript or
  their tooling.
  ALSO invoke on the language-agnostic requests "cve tara", "cve raporu",
  "güvenlik açığı tara", "zafiyet tara", "güvenlik taraması", "kod kalitesi tara",
  "lint tara", "lint check", "vulnerability scan", "vuln scan", "scan for CVEs",
  "check vulnerabilities", "security scan", "static security analysis" — but ONLY
  when the target project is JavaScript or TypeScript. Those phrases are shared
  verbatim with check-golang, check-php, check-rust and check-swift, so they carry
  no language signal: choose by what the project actually is (`package.json`
  present) and never by the phrase alone. If the repository holds more than one of
  these languages, ask which one the user means instead of guessing.
  Treat "semgrep" the same way: check-swift uses it too, so it names a tool rather
  than a language and selects nothing on its own.
  Runs FOUR tools by default — the package manager's
  audit (CVEs), semgrep (security static analysis), ESLint (lint), and knip
  (dead code and unused dependencies) — installs any that are missing, scans the
  whole project, classifies each finding, and produces a ranked combined report
  with fix guidance.
argument-hint: "[scan | report | fix]"
---

# JavaScript & TypeScript Security & Quality Scanner

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

Scan the entire JavaScript/TypeScript project for security AND code-quality
problems and produce a full report. Runs four complementary tools by default:

Security:
- **package manager audit** (`npm audit` / `pnpm audit` / `yarn npm audit` /
  `bun audit`) — known CVEs from the GitHub Advisory Database, resolved against
  the lockfile.
- **semgrep** (`semgrep --config auto`) — static analysis for insecure code
  patterns (injection, XSS, hardcoded secrets, unsafe deserialization, taint).

Code quality:
- **ESLint** (`eslint`) — the project's configured linter; honors flat config
  (`eslint.config.*`) or legacy `.eslintrc.*`.
- **knip** (`knip`) — dead code, unused exports, unused files, and unused or
  undeclared dependencies; the modernization/hygiene tier.

**Default behavior is `scan`** — run ALL FOUR tools and report every finding.
`fix` additionally proposes and (with confirmation) applies remediation.

## Key facts you must not forget

**The audit resolves the LOCKFILE, not `package.json`.** Detect the package
manager from the lockfile, never guess: `package-lock.json` → npm,
`pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lockb`/`bun.lock` → bun. Using
the wrong one either errors or silently audits a tree the project does not build.
If there is no committed lockfile, do both things: report its absence as a
finding in its own right, and generate a tree so the audit has something to
resolve. Advisories from a generated tree describe what installs today, not what
the project ships, so label them that way and never present them as the shipped
result.

**`npm audit` has NO reachability analysis.** Unlike a call-graph scanner it
cannot tell whether your code reaches the vulnerable function, so every advisory
in the tree looks "affected". Never downgrade a finding to "probably unreachable"
on your own judgement. Report it, and use `npm ls <pkg>` / `pnpm why <pkg>` to
show which dependency pulls it in — the fix usually belongs to the intermediate
package, not yours.

**`npm audit fix --force` is destructive.** It installs semver-major upgrades to
clear advisories and routinely breaks the build. NEVER run it as part of a scan,
and in `fix` mode only run plain `npm audit fix` (semver-compatible); anything
requiring a major bump must be proposed to the user with the breaking change
named, one package at a time.

**A dev-only CVE still matters, but differently.** A vulnerability in a build
tool or test runner does not ship to production users, yet it does execute on
developer machines and in CI with repo credentials, so it is a supply-chain risk,
not a runtime one. Keep the two labelled separately (`dependencies` vs
`devDependencies`) and never quietly drop dev findings.

**Transitive fixes need an override, and overrides are a liability.** When no
parent release fixes the tree, npm `overrides` / pnpm `overrides` / yarn
`resolutions` can force a patched version, but they pin a package against its
parent's declared range and silently go stale. Use one only with the user's
agreement, and record in the report that it must be revisited.

**ESLint config format decides whether it runs at all.** ESLint v9+ defaults to
flat config (`eslint.config.js|mjs|ts`); a project still on `.eslintrc.*` needs
`ESLINT_USE_FLAT_CONFIG=false` or the compatibility layer. Both cases exit `2`,
so classify by cause, never by the exit code alone: no config file anywhere is a
project finding (the project has no agreed lint standard), while a config that
exists but fails to load is a tool error. Report which config actually applied.

**Security vs quality are separate tiers.** Security findings (audit, semgrep)
always rank above code-quality findings (ESLint, knip). A style lint never blocks
the way a CVE does — report both, but never let quality noise bury a real
vulnerability. knip findings are hygiene, not defects; apply them only in `fix`
mode and only when removal is proven safe.

**knip's default confidence is not proof.** Dynamic imports, framework
conventions (route files, config files loaded by name), and plugin entry points
routinely look "unused" to static analysis. NEVER delete a file or export on
knip's word alone — verify each one, and prefer configuring knip's entry points
over deleting something the framework loads reflectively.

## Usage

```
/check-js          # scan whole project with all four tools, report all (default)
/check-js scan     # same as default
/check-js report   # scan + write a markdown report file
/check-js fix      # scan, then propose/apply fixes after confirmation
```

## Step 1: Preconditions

Verify this is a JS/TS project, detect the package manager, and ensure the tools
are available.

1. Confirm a `package.json` exists at the repo root (or find it):
   ```bash
   test -f package.json && head -20 package.json || echo "NO package.json — not a JS project"
   ```
   If there is no `package.json`, STOP and tell the user this is not a
   JavaScript/TypeScript project. Note whether it declares `workspaces` — that
   decides scan scope.

2. Detect the package manager from the lockfile — never guess:
   ```bash
   ls -1 package-lock.json pnpm-lock.yaml yarn.lock bun.lockb bun.lock 2>/dev/null
   grep -E '"packageManager"' package.json 2>/dev/null
   ```
   Exactly one lockfile should be present. If several exist, that is a finding
   (the repo builds differently depending on who installs). If none exists,
   record the absence as a finding, then run the install to generate one and
   label every advisory that follows as coming from a freshly resolved tree
   rather than the committed one.

3. Record the runtime and manager versions — findings hinge on them:
   ```bash
   node --version && npm --version
   ```

4. Inventory EVERY declared Node version and compare them. Drift between these is
   itself a finding. This scans whatever exists without depending on shell glob
   expansion (unmatched globs abort the command under zsh):
   ```bash
   grep -E '"engines"' -A3 package.json 2>/dev/null                   # the floor
   cat .nvmrc 2>/dev/null
   # every other declaration, across whatever config files the repo actually has:
   grep -rniE 'node-version"?:|node:[0-9]|NODE_VERSION' \
     --include='*.yml' --include='*.yaml' --include='Dockerfile*' \
     --include='*.Dockerfile' . 2>/dev/null
   ```
   Flag any source whose Node version differs from the `engines` floor —
   `Dockerfile` base images, `node-version` in EVERY workflow (`ci`, `release`,
   etc., not just one), and container/CI configs. An end-of-life Node major is
   itself a security finding: it stops receiving patches.

   A red CI job is not always visible in the run you are looking at. When the
   inventory finds drift, check the last few runs of the affected workflow
   (`gh run list --workflow=<name>.yml --limit 6 --json headSha,conclusion`),
   because a job broken by an earlier bump keeps failing on every commit after
   it and is easy to read as a new failure or to miss entirely.

5. Ensure all four tools are available; install whichever is missing:
   ```bash
   command -v semgrep >/dev/null 2>&1 || python3 -m pip install --user semgrep
   npx --yes eslint --version >/dev/null 2>&1 || echo "eslint not resolvable — check devDependencies"
   npx --yes knip --version   >/dev/null 2>&1 || echo "knip will be fetched by npx"
   # the audit ships with the package manager; no install needed
   ```
   Prefer the project's own ESLint from `node_modules` over a fetched one, so the
   plugins and config resolve. If the project's CI pins specific tool versions
   (check `.github/workflows/*.y*ml`), use those exact versions instead so local
   results match CI.

## Step 2: Scan the whole project (all four tools)

Run every tool against the whole project. Capture human output plus
machine-readable streams (authoritative for classification). Use the package
manager detected in Step 1.

Write every machine-readable stream into a fresh per-run directory, NEVER a
fixed `/tmp/eslint.json` / `/tmp/semgrep.json`. A shared path is the classic
cross-project trap: if a tool errors and does not overwrite, you silently parse
another repo's stale JSON as this project's findings. A unique dir per run makes
a write failure show up as a missing file instead of stale data.

```bash
RUNDIR="$(mktemp -d /tmp/check-js.XXXXXXXX)"; echo "run dir: $RUNDIR"

# --- Security ---
npm audit ; echo "audit exit: $?"                       # pnpm audit | yarn npm audit | bun audit
npm audit --json > "$RUNDIR/npm-audit.json" 2>/dev/null

semgrep --config auto --error 2>&1 ; echo "semgrep exit: $?"
semgrep --config auto --json -o "$RUNDIR/semgrep.json" --quiet

# --- Code quality ---
npx eslint . ; echo "eslint exit: $?"                   # exit 1 if problems
npx eslint . -f json -o "$RUNDIR/eslint.json" 2>/dev/null

npx knip ; echo "knip exit: $?"                         # exit 1 if issues
npx knip --reporter json > "$RUNDIR/knip.json" 2>/dev/null

# Cyclomatic complexity gate: every function must stay at or below 10.
# Pass the rule explicitly — the project's config usually does not enable it,
# and ESLint's own default for `complexity` is 20, not 10.
npx eslint . --no-inline-config --rule '{"complexity":["error",10]}' \
  -f json -o "$RUNDIR/complexity.json" 2>/dev/null
npx eslint . --no-inline-config --rule '{"complexity":["error",10]}' ; echo "complexity exit: $?"
```

For a monorepo, scan every workspace, not just the root:
```bash
npm audit --workspaces --include-workspace-root
npx eslint .                                  # flat config already covers the tree
npx knip --workspace <name>                   # repeat per workspace if knip is not monorepo-configured
```

Before classifying, confirm the report belongs to THIS project. The scan scope is
the repo root and, in a monorepo, its declared workspaces; every finding's file
path MUST fall under the current repo root. If a path points outside it (a
sibling project, a stale file, a globally linked package), discard that finding
and re-run the tool into a fresh `$RUNDIR` — never report another project's
issues as this one's.

Notes:
- Exit codes: `npm audit` `1` = vulnerabilities found; semgrep `1` = findings
  (with `--error`); ESLint `1` = lint problems, `2` = ESLint could not run; knip
  `1` = issues. `0` = clean for all. Every `1` means "parse the findings". ESLint
  `2` needs its cause read from stderr: no config file anywhere is a project
  finding, a config that exists but fails to load is a real tool error.
- `semgrep --config auto` fetches the community rule packs. Offline, fall back to
  the local packs `--config p/javascript --config p/typescript --config p/react
  --config p/nodejs` and say which ran.
- ESLint only covers the file types its config targets. Confirm TypeScript files
  are actually linted (`--ext` on legacy configs, or the `files` globs on flat
  config); a green ESLint that never opened a `.ts` file is a false negative.
- knip honors `knip.json` / the `knip` key in `package.json`. Note which applied.
- A zero from an absent lockfile is not a clean result. Generate the tree as
  Step 1 directs, rerun, and keep the missing committed lockfile as its own
  finding even when the generated tree audits clean.

## Step 3: Classify every finding

**audit** — for each advisory extract:
- **ID** (e.g. `GHSA-xxxx-xxxx-xxxx`) and its advisory link, plus the CVE alias
  when one exists.
- **Package** and whether it is a direct or transitive dependency. Resolve the
  path with `npm ls <pkg>` (or `pnpm why <pkg>`).
- **Vulnerable range** and **patched version**.
- **Tree**: `dependencies` (ships to production) or `devDependencies`
  (build/CI supply-chain risk only). Label them separately.
- **Severity** as reported (critical / high / moderate / low).
- Whether the fix is semver-compatible or needs a **breaking** major bump.

**semgrep** — for each finding extract:
- **Rule ID** (e.g. `javascript.lang.security.audit.code-string-concat`) and the
  **CWE/OWASP** reference, file:line, code snippet.
- **Severity** (ERROR/WARNING/INFO).
- Judge whether it is a real risk or a **false positive** (e.g. a value that is
  already validated, or an operator-controlled constant semgrep cannot prove
  safe).

**ESLint** — for each finding extract file:line, the **rule name** (e.g.
`no-unused-vars`, `@typescript-eslint/no-explicit-any`) and the message. Note
error vs warning; security-plugin rules (`eslint-plugin-security`,
`no-eval`-class rules) rank with the security tier, not with style.

**knip** — for each finding extract the category (unused file, unused export,
unused dependency, unlisted dependency, unresolved import) and the path. An
**unlisted dependency** is the important one: code imports a package that is not
declared, so the build works only by hoisting accident.

**complexity** — for each `complexity` violation extract file:line, the function
name, and the reported complexity. Every one is a function over the limit of 10.
Unlike a style rule this is NOT optional: the limit is a project rule, and a
function above it must be refactored into smaller single-responsibility
functions, never suppressed and never given a raised threshold.

Rank all findings by severity for action (security tier first, always):
1. **Critical/high CVE in `dependencies`** — highest; ships to production.
2. **Node version drift or an end-of-life major** — a release, container or CI
   path declares a version other than the `engines` floor, or the floor itself is
   EOL. Ranked here because it is how an unpatched runtime reaches production
   while the local scan reads clean.
3. **Critical/high CVE in `devDependencies`** — build/CI compromise risk.
4. **semgrep ERROR real finding** — fix in code.
5. **Moderate/low CVE** — upgrade on the normal cycle.
6. **semgrep WARNING / false positive** — validate if cheap, else annotate.
7. **ESLint security-plugin rule** — treat as a code security finding.
8. **knip unlisted dependency** — build correctness; declare it.
9. **ESLint error** — quality; fix in code.
10. **Function over the complexity limit (`complexity` > 10)** — quality;
    refactor into smaller functions. Ranked above warnings and hygiene because it
    is a limit, not a suggestion.
11. **ESLint warning** — quality; lower.
12. **knip unused file/export/dependency** — lowest; hygiene, verify before
    deleting.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Use this shape:

```
# JS/TS security & quality report — <package name>
Node: <vX.Y.Z>   engines floor: <range>   Manager: npm|pnpm|yarn|bun   Scanned: whole project
(when Node drift exists, name it — an EOL major is itself a security finding)
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

**Verdict rule:** Quality is green ONLY when ESLint, the complexity gate AND knip
all report zero.
Any knip finding (or any lint problem) means quality is NOT clean — mark it
yellow and list the outstanding items. Never call a tier green while it still has
open findings, however minor.

For `report` mode, also write this to `VULN-REPORT.md` (or append to an
existing `BUG-REPORT.md` if the project uses one) in English.

## Step 5: Fix (only in `fix` mode, after confirmation)

Never edit files in `scan`/`report` mode. In `fix` mode:

**Take the batch latch first.** A `fix` run repairs one finding class after
another, so run this before the first fix:

```bash
mkdir -p ~/.cli-tweaks/.batch-locks && touch ~/.cli-tweaks/.batch-locks/$PPID
```

This keeps the `memory-save.py` stop hook silent for the whole run, so a finding
does not cost an extra turn. A finished finding is a checkpoint, not an ending:
continue to the next finding in the same turn. Release the latch at the end of
**Prove the fix**, never earlier. A decision the run genuinely needs from the
user, such as a major-version bump below, still ends the turn; the latch removes
only the hook turn.

### Semver-compatible CVEs
```bash
npm audit fix          # NEVER --force; it installs breaking majors
npm update <pkg>
```

### CVEs needing a major bump
NEVER apply these automatically. Propose them one package at a time, naming the
breaking change and the migration the upgrade requires, and let the user decide:
```bash
npm install <pkg>@<patched-major>
```
Run the project's tests after every such bump, before moving to the next.

### Transitive CVEs with no parent release
Only with the user's agreement, force the resolution:
```jsonc
// package.json — npm / pnpm
"overrides":    { "<vulnerable-pkg>": "<patched-version>" }
// yarn
"resolutions":  { "<vulnerable-pkg>": "<patched-version>" }
```
Then reinstall and re-audit. Record in the report that this override pins a
package against its parent's declared range and must be revisited when the parent
ships a fix.

### Node version drift or an end-of-life major
The fix is a runtime bump, not a code change. Raise the Node version everywhere
the Step 1 inventory found it:
- `package.json` — the `engines.node` range (the floor CI resolves against)
- `.nvmrc` — the local/CI default version
- `Dockerfile` — the base image tag
- CI workflows — `node-version` in EVERY `.github/workflows/*.y*ml` (ci, release,
  and any other), not just one; prefer `node-version-file: .nvmrc` so they track
  the floor automatically and cannot drift

After raising the floor, re-run the Step 1 inventory and confirm no source still
names a version below it. A bump that misses one source is silent in the scan
output but red in CI on every push that follows.

### semgrep findings
- **Real finding**: fix the code. XSS → escape or use a framework's safe binding
  instead of `innerHTML`; injection → parameterize; hardcoded secret → move to
  the environment and rotate the exposed value; unsafe deserialization → validate
  the shape before use.
- **False positive** (proven safe but semgrep cannot follow the validator): add
  `// nosemgrep: <rule-id>` on the flagged line WITH a justification comment
  above it. Never disable a rule globally to hide a real finding.
- Re-run semgrep until it exits 0.

### ESLint problems
```bash
npx eslint . --fix     # auto-fixable rules only; review the diff
```
Fix the rest in code following each rule's guidance. Re-run until 0. Do not
silence a rule unless the finding is a proven false positive, and then scope
`// eslint-disable-next-line <rule>` to the single line with a reason. Never add
a file-wide or config-wide disable to hide a real finding.

### Functions over the complexity limit
Refactor each function the complexity gate reported into smaller
single-responsibility functions: extract the branches of a long `if`/`switch`
chain into named helpers, lift error handling out of the happy path, and split
functions that do two jobs. NEVER raise the threshold, add an
`eslint-disable` for `complexity`, or drop the gate to make the report green.
Re-run the gate until it reports nothing.

### knip findings
- **Unlisted dependency**: declare it in `package.json`. This is a real build
  correctness fix, not hygiene.
- **Unused dependency**: remove it after confirming nothing loads it dynamically.
- **Unused file/export**: VERIFY first. Check for dynamic `import()`, framework
  route/config conventions, and plugin entry points. When the framework loads it
  reflectively, configure knip's `entry` patterns instead of deleting. Never
  delete on knip's word alone.

### Prove the fix
A dependency bump changes runtime behavior, so a green scanner is not enough:
```bash
rm -rf node_modules && npm ci     # prove the lockfile itself resolves clean
npm audit                          # must report 0 vulnerabilities
semgrep --config auto --error      # must exit 0
npx eslint . && npx knip           # both must exit 0
npm test && npm run build          # a security bump must not break behavior
```
Expect `found 0 vulnerabilities`, semgrep/ESLint/knip exit 0, and a passing build
and test run. If the project pins Node in CI, run the proof under that exact
version (`nvm use <floor>`), not just the local one. Then remove any helper tool
this run installed outside the project (`python3 -m pip uninstall -y semgrep`,
and any Node version this run fetched with `nvm uninstall <ver>`) and say so. The
run installed it, so the run removes it; offering to remove it and leaving it
installed does not count.

Release the batch latch last, after the proof and the cleanup:

```bash
rm -f ~/.cli-tweaks/.batch-locks/$PPID
```

The stop hook blocks again from here on, so the turn that ends the run carries
everything the run learned into memory.

## Rules

- Default to `scan`; run ALL FOUR tools (audit, semgrep, ESLint, knip) plus the
  complexity gate every time; never modify files unless invoked as `fix`.
- Enforce a cyclomatic complexity limit of 10 per function by passing
  `--rule '{"complexity":["error",10]}'` explicitly; the project's config rarely
  enables the rule and ESLint's own default is 20. Any violation is a finding.
  NEVER raise the threshold, disable the rule, or drop the gate to make the
  report green; refactor into smaller single-responsibility functions instead.
- Detect the package manager from the lockfile; never guess, and never audit
  with a manager the project does not use.
- NEVER truncate a scan command's output with `head`, `tail`, or a count flag.
  A capped run reports the first few findings and hides the rest, so the next
  run finds work you already called done. Read the whole output; use the
  machine-readable stream in `$RUNDIR` when the human output is long.
- Keep security and code-quality findings in SEPARATE tiers in the report;
  security always ranks first. Never let lint/knip noise bury a real CVE.
- Report EVERY finding from all four tools, including dev-dependency CVEs, low
  severities, ESLint warnings, and knip hygiene items — do not silently drop
  anything.
- Label `dependencies` and `devDependencies` findings separately; a dev CVE is a
  build/CI supply-chain risk, not a production one, and must not be dropped.
- The audit has NO reachability analysis; never downgrade an advisory to
  "probably unreachable" on your own judgement. Say plainly that reachability is
  unproven.
- NEVER run `npm audit fix --force`, in any mode. Major bumps are proposed to the
  user one package at a time, with the breaking change named.
- Overrides/resolutions pin a package against its parent's range; use them only
  with the user's agreement and record that they must be revisited.
- NEVER delete a file, export, or dependency on knip's word alone; verify dynamic
  imports and framework conventions first, and prefer configuring entry points.
- Report which ESLint config actually applied, and confirm TypeScript files were
  really linted; a green run that never opened a `.ts` file is a false negative.
- Report the Node version and the `engines` floor in every report, and flag an
  end-of-life Node major as a security finding.
- Never "fix" an end-of-life runtime by editing project code — it is a version
  bump; raise the Node version in EVERY source that declares it, then re-run the
  inventory and confirm none still names a version below the floor.
- Write every machine-readable stream into a fresh `mktemp -d` run directory,
  never a fixed `/tmp` path, so a failed write shows up as a missing file instead
  of another project's stale JSON.
- Confirm every finding's file path falls under the current repo root before
  classifying it; discard and re-scan anything that points outside.
- Clean up any helper tool this run installed outside the project after proving
  a fix.
- For semgrep false positives, prefer a real validator; use a line-scoped
  `// nosemgrep: <rule-id>` with justification only when the code is proven safe.
  Never disable a rule globally to mask a real finding.
- If the project's CI pins scanner versions, scan with those exact versions so
  local results match CI.
- Reports are written in English; explanations to the user follow the user's
  language.
- Confirm with the user before applying any dependency upgrade, override, or
  code change in `fix` mode.
- Always re-run the project's build and tests after a dependency fix.
