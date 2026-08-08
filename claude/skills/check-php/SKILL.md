---
name: check-php
description: >
  PHP security and code-quality scan of the whole project. Invoke on "check-php",
  "composer audit", "psalm", "phpstan", "rector", "taint analysis", "php lint",
  or any variation naming PHP or its tooling.
  ALSO invoke on the language-agnostic requests "cve tara", "cve raporu",
  "güvenlik açığı tara", "zafiyet tara", "güvenlik taraması", "kod kalitesi tara",
  "lint tara", "lint check", "vulnerability scan", "vuln scan", "scan for CVEs",
  "check vulnerabilities", "security scan", "static security analysis" — but ONLY
  when the target project is PHP. Those phrases are shared verbatim with
  check-golang, check-js, check-rust and check-swift, so they carry no language
  signal: choose by what the project actually is (`composer.json` present) and
  never by the phrase alone. If the repository holds more than one of these
  languages, ask which one the user means instead of guessing.
  Runs FOUR tools by default — composer audit (CVEs), Psalm taint
  analysis (security static analysis), PHPStan (lint), and Rector (modernization)
  — installs any that are missing, scans every source path, classifies each
  finding, and produces a ranked combined report with fix guidance.
argument-hint: "[scan | report | fix]"
---

# PHP Security & Quality Scanner

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

Scan the entire PHP project for security AND code-quality problems and produce a
full report. Runs four complementary tools by default:

Security:
- **composer audit** (`composer audit`) — known CVEs from the PHP Security
  Advisories Database, resolved against `composer.lock`.
- **Psalm taint analysis** (`vimeo/psalm --taint-analysis`) — tracks
  user-controlled input to dangerous sinks (SQL injection, XSS, command
  injection, path traversal, unsafe deserialization).

Code quality:
- **PHPStan** (`phpstan/phpstan`) — static analysis for type errors, dead
  branches, and impossible conditions; honors `phpstan.neon` and its level.
- **Rector** (`rectorphp/rector`) — flags outdated idioms replaceable with
  modern PHP equivalents; the modernization tier.

**Default behavior is `scan`** — run ALL FOUR tools and report every finding.
`fix` additionally proposes and (with confirmation) applies remediation.

## Key facts you must not forget

**composer audit resolves `composer.lock`, not `composer.json`.** Without a
committed lockfile there is nothing authoritative to scan: the constraint ranges
in `composer.json` say what MAY be installed, the lock says what IS. If the lock
is missing, run `composer update --dry-run` to see the resolution, say clearly
that the scan used a fresh resolution, and treat the missing committed lockfile
as a finding for an application.

**The declared PHP version can lie about the runtime.** `require.php` in
`composer.json` is the floor, but `config.platform.php` overrides what Composer
*pretends* the runtime is when resolving. A project can therefore resolve
packages for PHP 8.1 while production actually runs 8.3, or the reverse. Compare
`php -v`, `require.php`, `config.platform.php`, the `Dockerfile` base image, and
every CI workflow, and flag any drift. An end-of-life PHP branch is itself a
security finding: it stops receiving patches even when every package is current.

**Baselines hide real findings.** `phpstan-baseline.neon` and
`psalm-baseline.xml` suppress pre-existing errors so a legacy codebase can adopt
the tool. A green run with a baseline is NOT a clean codebase. Always report
whether a baseline is in effect and how many findings it is suppressing; never
present a baselined green as a genuine zero, and NEVER regenerate a baseline to
make new findings disappear.

**PHPStan's level decides what it even looks for.** Levels run 0 (loosest) to 10
(strictest, formerly `max`). A green run at level 0 says almost nothing. Always
report the level that actually applied, and when it is below 5 say plainly that
the analysis is shallow.

**Psalm taint analysis is opt-in and separate from its normal run.** Plain
`psalm` reports type issues; only `--taint-analysis` traces input to sinks, and
it needs the project's `psalm.xml` to declare the source paths. Psalm recognizes
standard escaping functions but NOT custom sanitizer wrappers — for a
proven-safe custom-sanitized line, annotate with `@psalm-taint-escape <type>`
plus a justification comment rather than disabling the rule globally.

**Rector rewrites code, and its dry run is the only safe default.** `rector
process` edits files in place. In `scan`/`report` mode ALWAYS pass `--dry-run`.
Rector's suggestions depend entirely on the rule sets configured in `rector.php`
and the target PHP version declared there — a suggestion list is meaningless
without naming which sets ran.

**Security vs quality are separate tiers.** Security findings (composer audit,
Psalm taint) always rank above code-quality findings (PHPStan, Rector). A
PHPStan type nit never blocks the way a CVE does — report both, but never let
quality noise bury a real vulnerability. Rector suggestions are optional idiom
upgrades; apply them only in `fix` mode and only when they do not change
behavior.

## Usage

```
/check-php          # scan whole project with all four tools, report all (default)
/check-php scan     # same as default
/check-php report   # scan + write a markdown report file
/check-php fix      # scan, then propose/apply fixes after confirmation
```

## Step 1: Preconditions

Verify this is a PHP project and the tools are available.

1. Confirm a `composer.json` exists at the repo root (or find it):
   ```bash
   test -f composer.json && head -30 composer.json || echo "NO composer.json — not a Composer project"
   ```
   If there is no `composer.json`, STOP and tell the user this is not a Composer
   project. Note the `autoload.psr-4` source paths — they decide scan scope.

2. Confirm a lockfile exists; findings hinge on it:
   ```bash
   test -f composer.lock && echo "composer.lock present" || echo "NO composer.lock"
   ```
   If missing, record in the report that the scan used a fresh resolution, and
   for an application treat the missing committed lockfile as a finding.

3. Record the runtime version — findings hinge on it:
   ```bash
   php -v && composer --version
   ```

4. Inventory EVERY declared PHP version and compare them. Drift between these is
   itself a finding. This scans whatever exists without depending on shell glob
   expansion (unmatched globs abort the command under zsh):
   ```bash
   grep -E '"php"' composer.json                                   # the floor
   grep -E -A3 '"platform"' composer.json 2>/dev/null              # what Composer pretends
   # every other declaration, across whatever config files the repo actually has:
   grep -rniE 'php-version"?:|php:[0-9]|PHP_VERSION' \
     --include='*.yml' --include='*.yaml' --include='Dockerfile*' \
     --include='*.Dockerfile' . 2>/dev/null
   ```
   Flag any source whose PHP version differs from the `require.php` floor —
   `config.platform.php`, `Dockerfile` base images, `php-version` in EVERY
   workflow (`ci`, `release`, etc., not just one), and container/CI configs.
   Check the floor against https://www.php.net/supported-versions.php; an
   end-of-life branch is a security finding on its own.

5. Ensure all four tools are available; install whichever is missing:
   ```bash
   test -f vendor/bin/psalm   || composer require --dev vimeo/psalm --no-interaction
   test -f vendor/bin/phpstan || composer require --dev phpstan/phpstan --no-interaction
   test -f vendor/bin/rector  || composer require --dev rector/rector --no-interaction
   # composer audit ships with Composer 2.4+; upgrade Composer if it is older
   ```
   Prefer the project's own `vendor/bin` binaries over globally installed ones so
   the configured rule sets and extensions resolve. If installing a dev
   dependency would modify `composer.json`, ask the user first — in `scan` mode
   you may run the tools via `composer exec` or a throwaway install instead.
   If the project's CI pins specific tool versions (check
   `.github/workflows/*.y*ml`), install those exact versions instead so local
   results match CI.

## Step 2: Scan the whole project (all four tools)

Run every tool against every source path. Capture human output plus
machine-readable streams (authoritative for classification).

```bash
# --- Security ---
composer audit ; echo "composer audit exit: $?"
composer audit --format=json > /tmp/composer-audit.json 2>/dev/null

vendor/bin/psalm --taint-analysis 2>&1 | tail -40 ; echo "psalm taint exit: $?"
vendor/bin/psalm --taint-analysis --report=/tmp/psalm-taint.json 2>/dev/null

# --- Code quality ---
vendor/bin/phpstan analyse --no-progress ; echo "phpstan exit: $?"
vendor/bin/phpstan analyse --no-progress --error-format=json > /tmp/phpstan.json 2>/dev/null

vendor/bin/rector process --dry-run ; echo "rector exit: $?"    # NEVER without --dry-run in scan mode
```

Also audit what actually ships, not just the whole tree:
```bash
composer audit --no-dev          # production-only advisories; label these separately
```

If step 4 showed the runtime differs from the declared floor, ALSO run the
analysis pinned to the floor — that is what CI/production actually execute:
```bash
FLOOR=$(grep -E '"php"' composer.json | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
vendor/bin/phpstan analyse --no-progress --php-version "${FLOOR/./0}"   # e.g. 8.1 -> 801
```
Report the floor-pinned result as the real one; a green scan on a newer local
runtime does NOT clear what production runs.

Notes:
- Scan the real source paths from `autoload.psr-4` (commonly `src/`, `app/`),
  not just the repo root, and never scan `vendor/`.
- Exit codes: `composer audit` `1` = advisories found; Psalm `1`/`2` = issues;
  PHPStan `1` = errors; Rector `2` = changes proposed (with `--dry-run`). `0` =
  clean for all. None of these are tool errors — parse the findings.
- PHPStan honors `phpstan.neon`/`phpstan.dist.neon` including its `level` and any
  baseline; Psalm honors `psalm.xml`; Rector honors `rector.php`. Note which
  config and which level applied in the report — and whether a baseline is
  suppressing findings:
  ```bash
  ls -1 phpstan-baseline.neon psalm-baseline.xml 2>/dev/null
  grep -c '' phpstan-baseline.neon 2>/dev/null      # rough size of what is hidden
  ```
- If Psalm reports that no config exists, generate one with
  `vendor/bin/psalm --init` and say in the report that the scan used a generated
  config, not the project's own.

## Step 3: Classify every finding

**composer audit** — for each advisory extract:
- **ID** (e.g. `CVE-YYYY-NNNNN` / `GHSA-xxxx-xxxx-xxxx`) and its advisory link.
- **Package** and whether it is a direct requirement or transitive. Resolve the
  path with `composer why <package>`.
- **Version in use** and **patched version**.
- **Tree**: production (`require`) or development (`require-dev`). The `--no-dev`
  run tells you which ship. Label them separately.
- **Severity** as reported, and whether the fix needs a major bump.

**Psalm taint** — for each finding extract:
- **Issue type** (e.g. `TaintedSql`, `TaintedHtml`, `TaintedShell`,
  `TaintedFile`) and the **CWE**, file:line, code snippet.
- The **taint path**: where the input enters and which sink it reaches. Psalm
  prints the trace — keep it, it is the evidence.
- Judge whether it is a real risk or a **false positive** (e.g. input already
  escaped by a custom wrapper Psalm cannot follow, or an operator-controlled
  constant).

**PHPStan** — for each error extract file:line, the message, and the
**identifier** when present (e.g. `argument.type`, `return.missing`). Record the
**level** that produced it — a level 9 finding is not comparable to a level 1
finding.

**Rector** — for each proposed change extract file:line and the rule that fired
(e.g. `AddVoidReturnTypeRector`, `ReadOnlyPropertyRector`). These are optional
improvements, not defects. Record which rule sets are configured in `rector.php`.

Rank all findings by severity for action (security tier first, always):
1. **Production CVE (`require`)** — highest; ships to production.
2. **Psalm `TaintedSql` / `TaintedShell` / `TaintedFile`** — injection reaching a
   dangerous sink; fix in code.
3. **Psalm `TaintedHtml` (XSS)** — fix in code.
4. **Dev-only CVE (`require-dev`)** — build/CI supply-chain risk.
5. **Psalm taint false positive** — sanitize properly if cheap, else annotate.
6. **End-of-life PHP branch or version drift** — standing security exposure.
7. **PHPStan error** — quality; fix in code (higher levels first).
8. **Rector suggestion** — lowest; optional idiom upgrade, behavior-preserving.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Use this shape:

```
# PHP security & quality report — <package name>
Runtime: PHP <X.Y.Z>   composer.json floor: <constraint>   platform override: <ver|none>
Scanned: <src paths>   (when they differ, the floor-pinned run is authoritative)
Security  — composer audit: N prod, M dev   psalm taint: P (Q real, R false-pos)
Quality   — phpstan: E errors (level L, baseline: yes/no, B suppressed)   rector: S suggestions

# === SECURITY (fix first) ===

## composer audit — production dependencies (action required)
### CVE-YYYY-NNNNN — <title>
- Package: <vendor/pkg>@<ver> (direct | transitive via <parent>)
- Patched: >= <ver>   Fix: semver-compatible | BREAKING major bump
- Fix: composer require <vendor/pkg>:^<patched>

## psalm — taint findings
### TaintedSql (CWE-89) — <file>:<line>
- Path: <where input enters> → <sink it reaches>
- Fix: use a prepared statement / the appropriate escaping for that sink.

## composer audit — dev dependencies (supply-chain risk)
- CVE-YYYY-NNNNN — <vendor/pkg>@<ver> → fixed in <ver> (does not ship)

# === CODE QUALITY (lower priority) ===

## phpstan (config: phpstan.neon | defaults, level L)
- [argument.type] path/File.php:42 — <message>
BASELINE: phpstan-baseline.neon suppresses B findings — this run is NOT a clean codebase.

## rector (sets: <configured sets>, target PHP <ver>) — optional idiom upgrades
- <file>:<line> — <rule> — <suggested modern idiom>

## Verdict
Security: <green ONLY if 0 advisories AND 0 open taint findings | red: list fixes>
Quality:  <green ONLY if phpstan 0 AND rector 0 AND no baseline | yellow: E errors, S suggestions>
```

**Verdict rule:** Quality is green ONLY when BOTH PHPStan AND Rector report zero
AND no baseline is suppressing findings. Any Rector suggestion (or any PHPStan
error, or an active baseline) means quality is NOT clean — mark it yellow and
list the outstanding items. Never call a tier green while it still has open
findings, however minor.

Security follows the same bar. Judging a taint finding a false positive does not
close it: it stays open, and keeps security red, until it is actually closed by a
real fix or by the narrow line-scoped `@psalm-taint-escape` of a proven-safe
line. Count open findings, never "real" ones.

For `report` mode, also write this to `VULN-REPORT.md` (or append to an
existing `BUG-REPORT.md` if the project uses one) in English.

## Step 5: Fix (only in `fix` mode, after confirmation)

Never edit files in `scan`/`report` mode. In `fix` mode:

### Semver-compatible CVEs
```bash
composer update <vendor/pkg> --with-dependencies
```

### CVEs needing a major bump
NEVER apply these automatically. Propose them one package at a time, naming the
breaking change and the migration required, and let the user decide:
```bash
composer require <vendor/pkg>:^<patched-major> --update-with-dependencies
```
Run the project's tests after every such bump, before moving to the next.

### Transitive CVEs with no parent release
The vulnerable package is usually not yours to bump. Find the parent first:
```bash
composer why <vulnerable-package>
```
Then upgrade the intermediate dependency that pins it. Only when no parent
release exists should you force the resolution by requiring the patched version
directly, and say clearly in the report that this pins a transitive package
against its parent's declared constraint.

### End-of-life PHP branch
The fix is a runtime bump, not a code change. Raise the PHP version everywhere
the Step 1 inventory found it:
- `composer.json` — `require.php`, and `config.platform.php` if present
- `Dockerfile` — the base image tag
- CI workflows — `php-version` in EVERY `.github/workflows/*.y*ml` (ci, release,
  and any other), not just one
Keep every source on the same PHP branch — a stale release workflow deploys on an
unpatched runtime even when CI is green.

### Psalm taint findings
- **Real finding**: fix the code at the sink. SQL injection → prepared statements
  with bound parameters, never string concatenation; XSS → escape on output with
  the templating engine's escaper (or `htmlspecialchars` with `ENT_QUOTES`);
  command injection → avoid the shell, else `escapeshellarg`; path traversal →
  resolve with `realpath` and verify the prefix; unsafe deserialization → never
  `unserialize` untrusted input, use JSON with a validated shape.
- **False positive** (proven safe but Psalm cannot follow the sanitizer): add
  `@psalm-taint-escape <taint-type>` on the sanitizer function WITH a
  justification comment, so Psalm learns the wrapper is an escaper. Never
  suppress the issue type globally to hide a real finding.
- Re-run `vendor/bin/psalm --taint-analysis` until it exits 0.

### PHPStan errors
Fix in code following each message. Re-run until 0. Do not silence an error
unless it is a proven false positive, and then scope
`@phpstan-ignore-next-line` (or `@phpstan-ignore <identifier>`) to the single
line with a reason. NEVER regenerate the baseline to make new errors disappear —
that hides regressions. If the user wants a stricter analysis, raise the level
one step at a time and fix what each step surfaces.

### Rector suggestions
Apply ONLY when behavior-preserving and the user wants the idiom upgrade:
```bash
vendor/bin/rector process        # without --dry-run; review the full diff
```
These are optional — skip if they conflict with the project's minimum PHP
version, and confirm `rector.php` targets the right PHP version first. Review
every hunk: Rector rewrites real code, and a wrong rule set can change behavior.

### Prove the fix
A dependency bump changes runtime behavior, so a green scanner is not enough:
```bash
composer install                              # prove the lockfile resolves clean
composer audit && composer audit --no-dev     # both must exit 0
vendor/bin/psalm --taint-analysis             # must exit 0
vendor/bin/phpstan analyse --no-progress      # must exit 0
vendor/bin/rector process --dry-run           # no remaining suggestions you agreed to apply
vendor/bin/phpunit                            # a security bump must not break behavior
```
Expect `No security vulnerability advisories found`, Psalm/PHPStan exit 0, and a
passing test run. If CI pins the PHP version, run the proof under that exact
version, not just the local one.

## Rules

- Default to `scan`; run ALL FOUR tools (composer audit, Psalm taint, PHPStan,
  Rector) every time; never modify files unless invoked as `fix`.
- ALWAYS pass `--dry-run` to Rector outside `fix` mode; it rewrites files in
  place.
- Keep security and code-quality findings in SEPARATE tiers in the report;
  security always ranks first. Never let PHPStan/Rector noise bury a real CVE.
- Report EVERY finding from all four tools, including dev-dependency CVEs,
  lower-severity advisories, PHPStan errors, and Rector suggestions — do not
  silently drop anything.
- Run `composer audit` both with and without `--no-dev`, and label production
  and development advisories separately; a dev CVE is a build/CI supply-chain
  risk, not a production one, and must not be dropped.
- ALWAYS report whether a PHPStan or Psalm baseline is active and how much it
  suppresses; a baselined green is NOT a clean codebase. NEVER regenerate a
  baseline to hide new findings.
- ALWAYS report the PHPStan level that applied; a green run below level 5 is a
  shallow result and must be labelled as such.
- Taint analysis is opt-in: plain `psalm` does not do it. Always pass
  `--taint-analysis`, and report the taint path as evidence for each finding.
- Report the runtime version, the `require.php` floor, and any
  `config.platform.php` override in every report; flag drift between them and
  treat an end-of-life PHP branch as a security finding.
- Never "fix" an end-of-life runtime by editing project code — it is a version
  bump; raise the PHP version in EVERY source that declares it, not just
  `composer.json`.
- Scan against a lockfile; if none exists, say the scan used a fresh resolution,
  and treat an application's missing committed lockfile as a finding.
- For Psalm false positives, prefer a real escaper; use
  `@psalm-taint-escape <type>` on the sanitizer with justification only when the
  code is proven safe. Never suppress an issue type globally to mask a real
  finding.
- Rector suggestions are optional and behavior-preserving; apply only in `fix`
  mode with user agreement, review every hunk, and never treat them as blocking
  defects.
- If the project's CI pins scanner versions, scan with those exact versions so
  local results match CI.
- Reports are written in English; explanations to the user follow the user's
  language.
- Confirm with the user before applying any dependency upgrade, runtime bump, or
  code change in `fix` mode.
- Always re-run the project's test suite after a dependency fix.
