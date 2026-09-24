# check-python: Fix mode

Read this file only in `fix` mode, after the scan and the report are complete.
Never edit files in `scan`/`report` mode.

A `fix` run repairs one finding class after another. A finished finding is a
checkpoint, not an ending: continue to the next finding in the same turn. A
decision the run genuinely needs from the user, such as a major-version bump below, still ends the turn.

## Compatible dependency CVEs
Raise the pin to the fixed version in the manifest the project actually uses
(`pyproject.toml`, `requirements*.txt`, `constraints.txt`), then regenerate the
lock file with the project's own tool (`uv lock`, `poetry lock`,
`pip-compile`). Never hand-edit a lock file. `pip-audit --fix` exists, but it
upgrades the environment rather than the manifest, so it does not fix the repo.

## CVEs needing a major bump
NEVER apply these automatically. Propose them one package at a time, naming the
breaking change and the migration the upgrade requires, and let the user decide.
Run the project's tests after every such bump, before moving to the next.

## Transitive CVEs
The parent package pins the vulnerable version. Bump the parent when a fixed
release exists. When it does not, add a constraint (`constraints.txt`, or the
resolver's own override table) pinning the transitive dependency above the fixed
version, and record why the constraint exists in a comment.

## Unpinned dependency sets
Pin every direct dependency with a lower bound at minimum, and commit a lock
file for an application. A library keeps ranges; an application commits the
resolution it ships.

## End-of-life or drifting Python version
Raise the version everywhere the Step 1 inventory found it: `requires-python`,
`.python-version`, `runtime.txt`, `Dockerfile` base images, `python-version` in
EVERY workflow, and `tox.ini` envlist. Keep every source on the same branch — a
stale `release.yml` ships an end-of-life runtime even when `ci.yml` is green.
After raising the floor, re-run the Step 1 inventory and confirm no source still
names a version below it.

## bandit and Semgrep findings
- **Real finding**: fix the code. `shell=True` → pass an argument list;
  `pickle.loads` on untrusted data → use a data format that does not execute;
  `verify=False` → fix the certificate chain instead of disabling verification;
  weak hash → `hashlib.sha256`, or `hmac.compare_digest` for comparisons.
- **False positive** (proven safe but the tool cannot follow the
  sanitizer/validator): add `# nosec <TEST-ID>` on the flagged line WITH a
  justification comment above it. Never add a blanket `exclude` or disable a test
  globally to hide a real finding.
- Re-run both tools after the fix and confirm the finding is gone.

## ruff violations
Fix in code following each rule's guidance. `ruff check . --fix` applies the
safe automatic fixes; review the diff before keeping it, and never pass
`--unsafe-fixes` without reading every change it makes. Re-run
`ruff check . --no-cache` until 0. Do not silence a rule unless the finding is a
proven false positive, and then scope the `# noqa: <CODE>` to the single line
with a reason.

## Functions over the complexity limit
Refactor each function `C901` reported into smaller single-responsibility
functions: extract the branches of a long `if`/`elif` chain into named helpers,
lift error handling out of the happy path, and split loops that do two jobs.
NEVER raise `max-complexity`, add the file to an ignore list, or drop the gate to
make the report green. Re-run
`ruff check . --no-cache --select C901 --config "lint.mccabe.max-complexity = 10"`
until it reports nothing.

## mypy errors
Fix the annotation or the code, never the config. Do not add
`ignore_errors = true` for a module, and do not widen a type to `Any` to silence
an error. A `# type: ignore[<code>]` needs the specific code and a reason.

## ruff `UP` suggestions
Apply ONLY when behavior-preserving and the user wants the idiom upgrade (`X | Y`
annotations, `dict` over `Dict`, f-strings over `%`-formatting). These are
optional — skip any that the `requires-python` floor cannot parse. Re-run the
`UP` selection to confirm.

## Prove the fix
A dependency bump changes runtime behavior, so a green scanner is not enough:
```bash
"$PY_AUDIT" --locked .                       # must report no known vulnerabilities
"$BANDIT" -r . -x './.venv,./venv,./.git,./build,./dist'   # must exit 0
docker run --rm -v "$PWD":/src:ro semgrep/semgrep semgrep scan --config=p/python /src
"$RUFF" check . --no-cache                   # must exit 0
"$RUFF" check . --no-cache --select C901 --config "lint.mccabe.max-complexity = 10"   # must print nothing
python3 -m pytest                            # a security bump must not break behavior
```
Expect `No known vulnerabilities found`, bandit/semgrep/ruff exit 0, an empty
complexity gate, and a passing test run. If CI pins the Python version, run the
proof under that exact version, not just the local one. Then remove the
throwaway tools virtualenv (`rm -rf "$TOOLDIR"`) and any package this run
installed into the project environment, and say so. The run installed it, so the
run removes it; offering to remove it and leaving it installed does not count.
