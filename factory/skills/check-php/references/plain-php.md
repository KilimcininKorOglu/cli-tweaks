# check-php: Plain PHP mode

Read this file when Step 1 recorded **plain PHP mode** (no `composer.json`).
In Composer mode, read the Tool install section too: its Progpilot download
and `docker pull semgrep/semgrep` apply in both modes.

## Tool install (Step 1, item 5)

The tools ship standalone PHARs, so Composer is not needed. Download them into
the run directory, never into the project:
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

## Scan (Step 2)

Plain PHP mode runs the same scan without Composer. `composer audit` is
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
