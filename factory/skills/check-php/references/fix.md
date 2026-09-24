# check-php: Fix mode

Read this file only in `fix` mode, after the scan and the report are complete.
Never edit files in `scan`/`report` mode.

A `fix` run repairs one finding class after another. A finished finding is a
checkpoint, not an ending: continue to the next finding in the same turn. A
decision the run genuinely needs from the user, such as a major-version bump below, still ends the turn.

## Semver-compatible CVEs
```bash
composer update <vendor/pkg> --with-dependencies
```

## CVEs needing a major bump
NEVER apply these automatically. Propose them one package at a time, naming the
breaking change and the migration required, and let the user decide:
```bash
composer require <vendor/pkg>:^<patched-major> --update-with-dependencies
```
Run the project's tests after every such bump, before moving to the next.

## Transitive CVEs with no parent release
The vulnerable package is usually not yours to bump. Find the parent first:
```bash
composer why <vulnerable-package>
```
Then upgrade the intermediate dependency that pins it. Only when no parent
release exists should you force the resolution by requiring the patched version
directly, and say clearly in the report that this pins a transitive package
against its parent's declared constraint.

## End-of-life PHP branch
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

## Taint findings (Progpilot and Semgrep)
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

## PHPStan errors
Fix in code following each message. Re-run until 0. Do not silence an error
unless it is a proven false positive, and then scope
`@phpstan-ignore-next-line` (or `@phpstan-ignore <identifier>`) to the single
line with a reason. Put the comment on the line DIRECTLY above the reported line;
one line higher matches nothing and adds an `ignore.unmatchedIdentifier` finding
beside the original. NEVER regenerate the baseline to make new errors disappear —
that hides regressions. If the user wants a stricter analysis, raise the level
one step at a time and fix what each step surfaces.

## Methods over the complexity limit
Refactor each method PHPMD reported into smaller single-responsibility methods:
extract the branches of a long `if`/`switch` chain into named private methods,
lift error handling out of the happy path, and split methods that do two jobs.
NEVER raise the threshold in a custom ruleset, add a
`@SuppressWarnings(PHPMD.CyclomaticComplexity)` annotation, or drop the gate to
make the report green. Re-run `phpmd <src paths> text codesize` until it reports
nothing.

## Rector suggestions
Apply ONLY when behavior-preserving and the user wants the idiom upgrade:
```bash
vendor/bin/rector process        # without --dry-run; review the full diff
```
These are optional — skip if they conflict with the project's minimum PHP
version, and confirm `rector.php` targets the right PHP version first. Review
every hunk: Rector rewrites real code, and a wrong rule set can change behavior.

## Prove the fix
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
