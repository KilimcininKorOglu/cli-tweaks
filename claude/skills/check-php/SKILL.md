---
name: check-php
description: >
  PHP security and code-quality scan of the whole project. Runs FIVE tools by default — composer audit (CVEs), Progpilot (taint
  analysis), Semgrep (security pattern rules), PHPStan (lint), and Rector
  (modernization) —
  installs any that are missing, scans every source path, classifies each
  finding, and produces a ranked combined report with fix guidance.
  The PHPMD complexity gate runs with them.
  Requires a PHP project (`composer.json` present); check-golang, check-js, check-python, check-rust and check-swift cover the other languages.
metadata:
  author: KilimcininKorOglu
  version: "1.0.0"
  category: code-quality
argument-hint: "[scan | report | fix]"
disable-model-invocation: true
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
full report. Runs five complementary tools by default:

Security:
- **composer audit** (`composer audit`) — known CVEs from the PHP Security
  Advisories Database, resolved against `composer.lock`.
- **Progpilot** (`progpilot.phar`) — taint analysis: tracks user-controlled input
  to dangerous sinks (SQL injection, XSS, file inclusion, path traversal,
  command injection).
- **Semgrep** (`semgrep/semgrep` Docker image, `p/php` + `p/owasp-top-ten`) —
  security pattern rules with cross-file taint; catches the shapes Progpilot's
  interprocedural analysis does not reach.

Code quality:
- **PHPStan** (`phpstan/phpstan`) — static analysis for type errors, dead
  branches, and impossible conditions; honors `phpstan.neon` and its level.
- **Rector** (`rectorphp/rector`) — flags outdated idioms replaceable with
  modern PHP equivalents; the modernization tier.

**Default behavior is `scan`** — run ALL FIVE tools plus the PHPMD complexity
gate and report every finding. `fix` additionally proposes and (with
confirmation) applies remediation.

## Key facts you must not forget

**composer audit resolves `composer.lock`, not `composer.json`.** Without a
committed lockfile there is nothing authoritative to scan: the constraint ranges
in `composer.json` say what MAY be installed, the lock says what IS. If the lock
is missing, run `composer update --dry-run` to see the resolution, say clearly
that the scan used a fresh resolution, and treat the missing committed lockfile
as a finding for an application.

**Composer is required for the CVE tier only, never for the whole scan.** A plain
PHP project — legacy code, a WordPress theme or plugin, hand-included libraries,
a single script — has no `composer.lock`, so `composer audit` has nothing to
resolve and there is no SCA surface at all. That is a finding in its own right,
not a green light, and it is NOT a reason to refuse the project: static analysis
is exactly what such a codebase needs most. Progpilot, Semgrep, PHPStan and PHPMD
all run without Composer. State that the dependency tier did not run, and never
report "0 advisories" without saying that nothing was scanned for them.

**Do NOT use Psalm `--taint-analysis` as the taint tier.** It was the tool this
skill named before and it does not finish on a legacy PHP codebase. Measured on a
354-file, 94k-line plain-PHP project: Psalm re-analyses the file-scope
`include_once` chain in every call context, so one bootstrap file was analysed
1356 times in two minutes and two of 366 files completed in 35 minutes. Eight
threads were killed by the OOM killer because Psalm forks per thread and each
fork holds its own taint graph. Progpilot scanned the same tree in 90 seconds and
Semgrep in about 3 minutes. Psalm remains usable for TYPE analysis; it is not the
taint tier.

**Progpilot does not model control flow that ends the request.** It reports a
page that validates its input and then calls `exit()`, and it does not follow an
`in_array()` whitelist or a `preg_replace()` strip. Read the guard above every
reported line before you accept the finding. A finding whose guard refuses the
input is a false positive, and you must say which guard closed it.

**Semgrep withholds the code snippet.** `extra.lines` in the JSON reads
`requires login`, so the finding carries a rule id, a path and a line but no
evidence. Read that line from the file yourself before classifying it. Its
`echoed-request` and `tainted-sql-string` rules also ignore `(int)` casts,
`intval()`, `json_encode()` output and `htmlspecialchars()`, so the raw count is
dominated by already-guarded lines.

**Filter Semgrep before you triage it.** Keep the findings whose reported line
holds a superglobal (`$_GET`, `$_POST`, `$_REQUEST`, `$_COOKIE`) with no cast and
no escaping function on the same line. On the measured project that filter cut
272 findings to 12 candidates, of which 2 were live reflected XSS. Report the
full count AND the filtered count; never present the filtered set as the total.

**The declared PHP version can lie about the runtime.** `require.php` in
`composer.json` is the floor, but `config.platform.php` overrides what Composer
*pretends* the runtime is when resolving. A project can therefore resolve
packages for PHP 8.1 while production actually runs 8.3, or the reverse. Compare
`php -v`, `require.php`, `config.platform.php`, the `Dockerfile` base image, and
every CI workflow, and flag any drift. An end-of-life PHP branch is itself a
security finding: it stops receiving patches even when every package is current.

**Baselines hide real findings.** `phpstan-baseline.neon` suppresses pre-existing
errors so a legacy codebase can adopt the tool. A green run with a baseline is
NOT a clean codebase. Always report whether a baseline is in effect and how many
findings it is suppressing; never present a baselined green as a genuine zero,
and NEVER regenerate a baseline to make new findings disappear.

**PHPStan's level decides what it even looks for.** Levels run 0 (loosest) to 10
(strictest, formerly `max`). A green run at level 0 says almost nothing. Always
report the level that actually applied, and when it is below 5 say plainly that
the analysis is shallow.

**Rector rewrites code, and its dry run is the only safe default.** `rector
process` edits files in place. In `scan`/`report` mode ALWAYS pass `--dry-run`.
Rector's suggestions depend entirely on the rule sets configured in `rector.php`
and the target PHP version declared there — a suggestion list is meaningless
without naming which sets ran.

**Security vs quality are separate tiers.** Security findings (composer audit,
Progpilot, Semgrep) always rank above code-quality findings (PHPStan, PHPMD,
Rector). A PHPStan type nit never blocks the way a CVE does — report both, but
never let quality noise bury a real vulnerability. Rector suggestions are
optional idiom upgrades; apply them only in `fix` mode and only when they do not
change behavior.

## Usage

```
/check-php          # scan whole project with all five tools, report all (default)
/check-php scan     # same as default
/check-php report   # scan + write a markdown report file
/check-php fix      # scan, then propose/apply fixes after confirmation
```

## Step 1: Preconditions

Verify this is a PHP project and the tools are available.

1. Confirm this is a PHP project and determine its shape. Composer is NOT
   required — a plain PHP project still gets the four static-analysis tools:
   ```bash
   test -f composer.json && head -30 composer.json || echo "NO composer.json — plain PHP mode"
   find . -name '*.php' -not -path './vendor/*' -not -path './.git/*' | head -1 \
     || echo "NO .php files — not a PHP project"
   ```
   STOP only when there are no `.php` files at all. Record the mode:
   - **Composer mode** (`composer.json` present) — all five tools run. Note the
     `autoload.psr-4` source paths; they decide scan scope.
   - **Plain PHP mode** (no `composer.json`) — `composer audit` cannot run, the
     others still do (see Step 5 for the PHAR path). Derive the scan scope from
     the real source directories instead:
     ```bash
     ls -d src app lib includes classes inc wp-content 2>/dev/null || echo "scope: repo root"
     ```

2. Confirm a lockfile exists; findings hinge on it. **Composer mode only:**
   ```bash
   test -f composer.lock && echo "composer.lock present" || echo "NO composer.lock"
   ```
   If missing, record in the report that the scan used a fresh resolution, and
   for an application treat the missing committed lockfile as a finding.
   In plain PHP mode there is no lockfile by definition; record the absent SCA
   surface as a finding of its own (see Key facts) rather than a clean result.

3. Record the runtime version — findings hinge on it:
   ```bash
   php -v && composer --version
   ```
   Progpilot v1.3.0 requires PHP 8.3 or newer. When the host PHP is older, or
   when the project runs in a container, run it inside the container that has a
   matching PHP and say in the report where it ran.

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

   A red CI job is not always visible in the run you are looking at. When the
   inventory finds drift, check the last few runs of the affected workflow
   (`gh run list --workflow=<name>.yml --limit 6 --json headSha,conclusion`),
   because a job broken by an earlier bump keeps failing on every commit after
   it and is easy to read as a new failure or to miss entirely.

5. Ensure the tools are available. **Composer mode:**
   ```bash
   test -f vendor/bin/phpstan || composer require --dev phpstan/phpstan --no-interaction
   test -f vendor/bin/rector  || composer require --dev rector/rector --no-interaction
   test -f vendor/bin/phpmd   || composer require --dev phpmd/phpmd --no-interaction
   # composer audit ships with Composer 2.4+; upgrade Composer if it is older
   ```
   Progpilot and Semgrep are NOT installed as dev dependencies: Progpilot runs
   from its PHAR and Semgrep from its Docker image, so neither touches
   `composer.json`. Prefer the project's own `vendor/bin` binaries over globally
   installed ones so the configured rule sets and extensions resolve. If
   installing a dev dependency would modify `composer.json`, ask the user first —
   in `scan` mode you may run the tools via `composer exec` or a throwaway
   install instead. If the project's CI pins specific tool versions (check
   `.github/workflows/*.y*ml`), install those exact versions instead so local
   results match CI.

   **Plain PHP mode** — the tools ship standalone PHARs, so Composer is not
   needed. Download them into the run directory, never into the project:
   ```bash
   PHARDIR="$(mktemp -d /tmp/check-php-tools.XXXXXXXX)"; echo "phar dir: $PHARDIR"
   curl -sSL -o "$PHARDIR/phpstan.phar" https://github.com/phpstan/phpstan/releases/latest/download/phpstan.phar
   curl -sSL -o "$PHARDIR/phpmd.phar"   https://github.com/phpmd/phpmd/releases/latest/download/phpmd.phar
   # Progpilot's release asset carries the version in its NAME; the plain
   # progpilot.phar URL answers "Not Found". Resolve the asset, never guess it:
   PP_URL=$(curl -sSL https://api.github.com/repos/designsecurity/progpilot/releases/latest \
     | python3 -c 'import sys,json;print([a["browser_download_url"] for a in json.load(sys.stdin)["assets"] if a["name"].endswith(".phar")][0])')
   curl -sSL -o "$PHARDIR/progpilot.phar" "$PP_URL"
   php "$PHARDIR/phpstan.phar" --version && php "$PHARDIR/phpmd.phar" --version
   php "$PHARDIR/progpilot.phar" --version
   docker pull semgrep/semgrep                    # the Semgrep tier needs Docker
   ```
   Rector ships no official PHAR; in plain PHP mode skip Rector and say so in the
   report rather than pretending the modernization tier ran. Delete `$PHARDIR`
   when the run finishes.

## Step 2: Scan the whole project (all five tools)

Run every tool against every source path. Capture human output plus
machine-readable streams (authoritative for classification).

Write every machine-readable stream into a fresh per-run directory, NEVER a
fixed `/tmp/phpstan.json` / `/tmp/progpilot.json`. A shared path is the classic
cross-project trap: if a tool errors and does not overwrite, you silently parse
another repo's stale JSON as this project's findings. A unique dir per run makes
a write failure show up as a missing file instead of stale data.

```bash
RUNDIR="$(mktemp -d /tmp/check-php.XXXXXXXX)"; echo "run dir: $RUNDIR"

# --- Security ---
composer audit ; echo "composer audit exit: $?"
composer audit --format=json > "$RUNDIR/composer-audit.json" 2>/dev/null

# Progpilot takes the files as ARGUMENTS, not a directory. Exit 1 means findings.
find . -name '*.php' -not -path './vendor/*' -not -path './.git/*' > "$RUNDIR/phpfiles.txt"
php -d memory_limit=6G "$PHARDIR/progpilot.phar" $(cat "$RUNDIR/phpfiles.txt" | tr '\n' ' ') \
  > "$RUNDIR/progpilot.json" 2>"$RUNDIR/progpilot.err" ; echo "progpilot exit: $?"

# Semgrep: mount the repo READ-ONLY and write the JSON outside it, so the scan
# cannot dirty the working tree.
mkdir -p "$RUNDIR/semgrep"
docker run --rm -v "$PWD":/src:ro -v "$RUNDIR/semgrep":/out semgrep/semgrep \
  semgrep scan --config=p/php --config=p/owasp-top-ten --metrics=off \
  --json -o /out/semgrep.json /src ; echo "semgrep exit: $?"

# --- Code quality ---
vendor/bin/phpstan analyse --no-progress ; echo "phpstan exit: $?"
vendor/bin/phpstan analyse --no-progress --error-format=json > "$RUNDIR/phpstan.json" 2>/dev/null

vendor/bin/rector process --dry-run ; echo "rector exit: $?"    # NEVER without --dry-run in scan mode

# Cyclomatic complexity gate: every method must stay at or below 10.
# PHPMD's codesize ruleset reports CyclomaticComplexity at a threshold of 10.
vendor/bin/phpmd <src paths> text codesize ; echo "phpmd exit: $?"
vendor/bin/phpmd <src paths> json codesize > "$RUNDIR/phpmd.json" 2>/dev/null
```

Also audit what actually ships, not just the whole tree:
```bash
composer audit --no-dev          # production-only advisories; label these separately
```

**Plain PHP mode** runs the same scan without Composer. `composer audit` is
skipped — say so explicitly — and the analyzers run from the PHARs and the
Docker image against the source scope found in Step 1:
```bash
SCOPE="src app lib includes classes inc"      # whatever Step 1 actually found
php "$PHARDIR/phpstan.phar" analyse --no-progress --level 5 $SCOPE ; echo "phpstan exit: $?"
php "$PHARDIR/phpstan.phar" analyse --no-progress --level 5 --error-format=json $SCOPE \
  > "$RUNDIR/phpstan.json" 2>/dev/null
php "$PHARDIR/phpmd.phar" $SCOPE text codesize ; echo "phpmd exit: $?"
```
With no `phpstan.neon` the level is not declared by the project, so pass one
explicitly and report which level you chose — an undeclared level is not the
project's agreed standard, so label those findings advisory.

If step 4 showed the runtime differs from the declared floor, ALSO run the
analysis pinned to the floor — that is what CI/production actually execute:
```bash
FLOOR=$(grep -E '"php"' composer.json | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
vendor/bin/phpstan analyse --no-progress --php-version "${FLOOR/./0}"   # e.g. 8.1 -> 801
```
Report the floor-pinned result as the real one; a green scan on a newer local
runtime does NOT clear what production runs.

Before classifying, confirm the report belongs to THIS project. The scan scope is
the `autoload.psr-4` source paths; every finding's file path MUST fall under the
current repo root, and none may sit inside `vendor/`. If a path points outside it
(a sibling project, a stale file), discard that finding and re-run the tool into
a fresh `$RUNDIR` — never report another project's issues as this one's.

Notes:
- Scan the real source paths from `autoload.psr-4` (commonly `src/`, `app/`),
  not just the repo root, and never scan `vendor/`.
- Exit codes: `composer audit` `1` = advisories found; Progpilot `1` = findings;
  Semgrep `1` = findings; PHPStan `1` = errors; Rector `2` = changes proposed
  (with `--dry-run`). `0` = clean for all. None of these are tool errors — parse
  the findings.
- Semgrep's `--config=p/...` rule packs are fetched from the registry, so that
  tier needs network access. If the fetch fails, say the pattern tier did not run
  rather than reporting Progpilot's count as the whole security result.
- PHPStan honors `phpstan.neon`/`phpstan.dist.neon` including its `level` and any
  baseline; Rector honors `rector.php`. Note which config and which level applied
  in the report — and whether a baseline is suppressing findings:
  ```bash
  ls -1 phpstan-baseline.neon 2>/dev/null
  grep -c '' phpstan-baseline.neon 2>/dev/null      # rough size of what is hidden
  ```

## Step 3: Classify every finding

**composer audit** — for each advisory extract:
- **ID** (e.g. `CVE-YYYY-NNNNN` / `GHSA-xxxx-xxxx-xxxx`) and its advisory link.
- **Package** and whether it is a direct requirement or transitive. Resolve the
  path with `composer why <package>`.
- **Version in use** and **patched version**.
- **Tree**: production (`require`) or development (`require-dev`). The `--no-dev`
  run tells you which ship. Label them separately.
- **Severity** as reported, and whether the fix needs a major bump.

**Progpilot** — each JSON entry carries `vuln_name` (`sql_injection`, `xss`,
`file_inclusion`, `path_traversal`, …), `vuln_cwe`, `source_name`/`source_file`/
`source_line` and `sink_name`/`sink_file`/`sink_line`. For each one:
- Read the SINK line and the guard above it from the file. Progpilot does not
  model `exit()`, `in_array()` whitelists or `preg_replace()` strips, so a page
  that refuses bad input still appears here.
- Name the guard that closes a false positive, or state that none exists.
- `source_name` and `source_file` can be arrays when several sources reach one
  sink; handle both shapes when you parse the JSON.

**Semgrep** — each result carries `check_id`, `path`, `start.line` and
`extra.message`. `extra.lines` is unusable (`requires login`), so:
- Read the reported line range from the file yourself; that snippet is the
  evidence, not the tool's output.
- Classify each one as: escaped (`htmlspecialchars`/`htmlentities`), cast
  (`(int)`/`intval`), JSON output (`json_encode` with a JSON content type),
  bound parameter, or UNGUARDED.
- Report the raw count AND the count that survives the superglobal filter from
  the Key facts. A finding that echoes a database column rather than a
  superglobal is a stored-XSS candidate and belongs in its own group, not in the
  reflected set.

**PHPStan** — for each error extract file:line, the message, and the
**identifier** when present (e.g. `argument.type`, `return.missing`). Record the
**level** that produced it — a level 9 finding is not comparable to a level 1
finding.

**Rector** — for each proposed change extract file:line and the rule that fired
(e.g. `AddVoidReturnTypeRector`, `ReadOnlyPropertyRector`). These are optional
improvements, not defects. Record which rule sets are configured in `rector.php`.

**PHPMD codesize** — for each `CyclomaticComplexity` violation extract file:line,
the class and method name, and the reported complexity. Every one is a method
over the limit of 10. Unlike a Rector suggestion this is NOT optional: the limit
is a project rule, and a method above it must be refactored into smaller
single-responsibility methods, never suppressed and never given a raised
threshold. The same ruleset also reports `NPathComplexity` and `ExcessiveMethodLength`;
report those alongside it.

Rank all findings by severity for action (security tier first, always):
1. **Production CVE (`require`)** — highest; ships to production.
2. **Injection reaching a dangerous sink** — Progpilot `sql_injection`,
   `command_injection`, `file_inclusion`, `path_traversal`, or the Semgrep
   equivalent, with no guard on the line; fix in code.
3. **XSS** — Progpilot `xss` or an unguarded Semgrep `echoed-request`; fix in
   code.
4. **Dev-only CVE (`require-dev`)** — build/CI supply-chain risk.
5. **Taint false positive** — sanitize properly if cheap, else record the guard
   that closes it.
6. **End-of-life PHP branch or version drift** — standing security exposure.
7. **PHPStan error** — quality; fix in code (higher levels first).
8. **Method over the complexity limit (PHPMD `CyclomaticComplexity` > 10)** —
   quality; refactor into smaller methods. Ranked above Rector because it is a
   limit, not a suggestion.
9. **Rector suggestion** — lowest; optional idiom upgrade, behavior-preserving.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Use this shape:

```
# PHP security & quality report — <package name>
Runtime: PHP <X.Y.Z>   composer.json floor: <constraint>   platform override: <ver|none>
Scanned: <src paths>   (when they differ, the floor-pinned run is authoritative)
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

**Verdict rule:** Quality is green ONLY when PHPStan, PHPMD AND Rector all report
zero AND no baseline is suppressing findings. Any Rector suggestion (or any PHPStan
error, or an active baseline) means quality is NOT clean — mark it yellow and
list the outstanding items. Never call a tier green while it still has open
findings, however minor.

**Coverage rule:** A green security verdict MUST name what was not scanned. In
plain PHP mode that is the whole dependency tier: `composer audit` did not run,
so "0 advisories" means "nothing was scanned for advisories", and reporting it as
safety is a lie. Name the skipped tools (Rector too, when no PHAR exists; Semgrep
when the registry fetch failed) rather than letting the report imply all five ran.

Security follows the same bar. Judging a taint finding a false positive does not
close it until you have named the guard that refuses the input. Count open
findings, never "real" ones. Semgrep findings you filtered out are not closed
either: say how many were filtered and on what rule.

For `report` mode, also write this to `VULN-REPORT.md` (or append to an
existing `BUG-REPORT.md` if the project uses one) in English.

## Step 5: Fix (only in `fix` mode, after confirmation)

Never edit files in `scan`/`report` mode. In `fix` mode:

A `fix` run repairs one finding class after another. A finished finding is a
checkpoint, not an ending: continue to the next finding in the same turn. A
decision the run genuinely needs from the user, such as a major-version bump below, still ends the turn.

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

After raising the floor, re-run the Step 1 inventory and confirm no source still
names a version below it. A bump that misses one source is silent in the scan
output but red in CI on every push that follows.

### Taint findings (Progpilot and Semgrep)
- **Prove it first.** A taint finding is a claim, not a defect. Reproduce it
  against the running application with a payload before you change code, and put
  the response that proves it in the commit message. A finding you cannot
  reproduce is reported as unproven, never fixed silently.
- **Real finding**: fix the code at the sink. SQL injection → prepared statements
  with bound parameters, never string concatenation; XSS → escape on output with
  `htmlspecialchars($v, ENT_QUOTES, 'UTF-8')`, or cast when the value is an id;
  command injection → avoid the shell, else `escapeshellarg`; path traversal →
  resolve with `realpath` and verify the prefix; file inclusion → resolve the
  name against a whitelist; unsafe deserialization → never `unserialize`
  untrusted input, use JSON with a validated shape.
- **Prefer the cast to the escape for an id.** `(int) $_GET['id']` both escapes
  and validates; `htmlspecialchars` only escapes. For a comma list of ids,
  rebuild it with `intval()` per element rather than escaping the string.
- **False positive**: record the guard that closes it in the report. Neither tool
  supports an inline suppression comment worth adding, so do NOT annotate the
  code; the report is where a false positive is closed.
- Re-run both tools after the fix and confirm the finding is gone.

### PHPStan errors
Fix in code following each message. Re-run until 0. Do not silence an error
unless it is a proven false positive, and then scope
`@phpstan-ignore-next-line` (or `@phpstan-ignore <identifier>`) to the single
line with a reason. Put the comment on the line DIRECTLY above the reported line;
one line higher matches nothing and adds an `ignore.unmatchedIdentifier` finding
beside the original. NEVER regenerate the baseline to make new errors disappear —
that hides regressions. If the user wants a stricter analysis, raise the level
one step at a time and fix what each step surfaces.

### Methods over the complexity limit
Refactor each method PHPMD reported into smaller single-responsibility methods:
extract the branches of a long `if`/`switch` chain into named private methods,
lift error handling out of the happy path, and split methods that do two jobs.
NEVER raise the threshold in a custom ruleset, add a
`@SuppressWarnings(PHPMD.CyclomaticComplexity)` annotation, or drop the gate to
make the report green. Re-run `phpmd <src paths> text codesize` until it reports
nothing.

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
php "$PHARDIR/progpilot.phar" $(cat "$RUNDIR/phpfiles.txt" | tr '\n' ' ')   # the fixed finding must be gone
docker run --rm -v "$PWD":/src:ro semgrep/semgrep semgrep scan --config=p/php /src
vendor/bin/phpstan analyse --no-progress      # must exit 0
vendor/bin/rector process --dry-run           # no remaining suggestions you agreed to apply
vendor/bin/phpunit                            # a security bump must not break behavior
```
Re-send the payload that proved each taint finding and show the response that no
longer carries it; a scanner that stopped reporting is not by itself proof. If CI
pins the PHP version, run the proof under that exact version, not just the local
one. Then remove any throwaway tool install this run made — if it added PHPStan,
PHPMD or Rector only to scan, drop them again
(`composer remove --dev <package> --no-interaction`) and restore `composer.json`
and `composer.lock` to their committed state, and say so. The run installed it,
so the run removes it; offering to remove it and leaving it installed does not
count.

## Rules

- Default to `scan`; run ALL FIVE tools (composer audit, Progpilot, Semgrep,
  PHPStan, Rector) plus the PHPMD complexity gate every time; never modify files
  unless invoked as `fix`.
- NEVER use Psalm `--taint-analysis` as the taint tier. It does not finish on a
  legacy PHP codebase; Progpilot and Semgrep are the taint tier.
- Read the reported line, and the guard above it, from the FILE before you
  classify any Progpilot or Semgrep finding. Progpilot does not model `exit()` or
  an `in_array()` whitelist, and Semgrep reports `extra.lines` as
  `requires login`, so neither tool's output is evidence on its own.
- Report the raw Semgrep count AND the filtered count, and name the filter. Never
  present the filtered set as the total.
- Reproduce every taint finding against the running application before you fix
  it, and put the proving response in the commit message. Report a finding you
  cannot reproduce as unproven.
- Enforce a cyclomatic complexity limit of 10 per method with
  `phpmd <src paths> text codesize`. Any violation is a finding. NEVER raise the
  threshold, add a `@SuppressWarnings` annotation, or drop the gate to make the
  report green; refactor into smaller single-responsibility methods instead.
- NEVER refuse a PHP project because it has no `composer.json`. STOP only when
  there are no `.php` files. Without Composer, run Progpilot, Semgrep, PHPStan
  and PHPMD from their PHARs and the Docker image, skip `composer audit` and
  Rector, and name every tool that did not run.
- State the coverage gap in every security verdict: in plain PHP mode nothing was
  scanned for advisories, so "0 advisories" must never be presented as safety.
- ALWAYS pass `--dry-run` to Rector outside `fix` mode; it rewrites files in
  place.
- Mount the repository READ-ONLY for Semgrep and write its JSON outside the
  repository, so a scan cannot dirty the working tree.
- NEVER truncate a scan command's output with `head`, `tail`, or a count flag.
  A capped run reports the first few findings and hides the rest, so the next
  run finds work you already called done. Read the whole output; use the
  machine-readable stream in `$RUNDIR` when the human output is long. A
  config-header display, an existence probe and a single-value extraction may
  still use them, because they read one known field, not a finding list.
- Keep security and code-quality findings in SEPARATE tiers in the report;
  security always ranks first. Never let PHPStan/Rector noise bury a real CVE.
- Report EVERY finding from all five tools, including dev-dependency CVEs,
  lower-severity advisories, PHPStan errors, and Rector suggestions — do not
  silently drop anything.
- Run `composer audit` both with and without `--no-dev`, and label production
  and development advisories separately; a dev CVE is a build/CI supply-chain
  risk, not a production one, and must not be dropped.
- ALWAYS report whether a PHPStan baseline is active and how much it suppresses;
  a baselined green is NOT a clean codebase. NEVER regenerate a baseline to hide
  new findings.
- ALWAYS report the PHPStan level that applied; a green run below level 5 is a
  shallow result and must be labelled as such.
- Run PHPStan over the WHOLE tree, never one file, when the file uses a class
  defined elsewhere; a single-file run reports `class.notFound` for every such
  class and hides the findings that depend on those types.
- Report the runtime version, the `require.php` floor, and any
  `config.platform.php` override in every report; flag drift between them and
  treat an end-of-life PHP branch as a security finding.
- Never "fix" an end-of-life runtime by editing project code — it is a version
  bump; raise the PHP version in EVERY source that declares it, not just
  `composer.json`, then re-run the inventory and confirm none still names a
  version below the floor.
- Write every machine-readable stream into a fresh `mktemp -d` run directory,
  never a fixed `/tmp` path, so a failed write shows up as a missing file instead
  of another project's stale JSON.
- Confirm every finding's file path falls under the current repo root and outside
  `vendor/` before classifying it; discard and re-scan anything that points
  elsewhere.
- Clean up any throwaway tool install this run made, and restore `composer.json`
  and `composer.lock` to their committed state.
- Scan against a lockfile; if none exists, say the scan used a fresh resolution,
  and treat an application's missing committed lockfile as a finding.
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
