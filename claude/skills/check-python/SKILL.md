---
name: check-python
description: >
  Python security and code-quality scan of the whole project. Runs FOUR tools by default — pip-audit (CVEs), bandit plus Semgrep
  (security static analysis), ruff (lint), and ruff's pyupgrade rules
  (modernization) — into a throwaway virtualenv,
  installs any that are missing, scans every source path, classifies each
  finding, and produces a ranked combined report with fix guidance.
  The ruff `C901` complexity gate runs with them, and mypy runs when the
  project configures it.
  Requires a Python project (`.py` files present, usually with `pyproject.toml`,
  `requirements*.txt`, `setup.py` or `setup.cfg`); check-golang, check-js, check-php, check-rust and check-swift cover the other languages.
metadata:
  author: KilimcininKorOglu
  version: "1.0.0"
  category: code-quality
argument-hint: "[scan | report | fix]"
disable-model-invocation: true
---

# Python Security & Quality Scanner

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

Scan the entire Python project for security AND code-quality problems and
produce a full report. Runs four complementary tools by default:

Security:
- **pip-audit** (`pypa/pip-audit`) — known CVEs from the Python Packaging
  Advisory Database and the OSV feed, resolved against the project's declared
  dependencies.
- **bandit** (`PyCQA/bandit`) — Python-specific insecure code patterns (`eval`,
  `exec`, `pickle`, `subprocess` with `shell=True`, weak hashes, hardcoded
  passwords, disabled TLS verification).
- **Semgrep** (`semgrep/semgrep` Docker image, `p/python` + `p/owasp-top-ten`) —
  security pattern rules with cross-file taint; catches the injection and SSRF
  chains bandit's single-file AST pass does not reach.

Code quality:
- **ruff** (`astral-sh/ruff`) — the lint tier; honors any `ruff.toml`,
  `.ruff.toml` or `[tool.ruff]` config.
- **ruff `UP` rules** — the modernization tier; the pyupgrade rule set, run as a
  separate selection so idiom upgrades never hide inside the lint count.
- **ruff `C901`** — the cyclomatic complexity gate; every function must stay at
  or below 10.
- **mypy** (`python/mypy`) — the type tier, and ONLY when the project already
  configures it. An unconfigured repository is not scanned with mypy.

**Default behavior is `scan`** — run ALL FOUR tools plus the complexity gate and
report every finding. `fix` additionally proposes and (with confirmation)
applies remediation.

## Key facts you must not forget

**pip-audit resolves what the project DECLARES, not what the container runs.**
`pip-audit` with no argument audits the environment it runs in, so running it
inside a throwaway tools virtualenv audits the tools, never the project. Always
name the source: `-r requirements.txt` for a requirements project, `--locked .`
for a `pyproject.toml` or `pylock.*.toml` project, and `pip-audit .` when the
project must be built to resolve its dependencies. Say in the report which of
the three ran, because they answer different questions.

**An unpinned dependency set is itself a finding.** A `requirements.txt` with
`requests` and no version, or a `pyproject.toml` with no lock file, means the
scan describes today's resolution and nothing else. Record the absent pin as a
finding rather than reporting a clean result.

**bandit reads one file at a time.** It cannot follow a tainted value across
modules, so a `subprocess.run(cmd)` whose `cmd` is built three files away is
invisible to it. That gap is why the Semgrep tier exists. bandit also flags
patterns that are correct in context (`assert` in a test, `subprocess` with a
literal command); judge each one and mark it a false positive with evidence
rather than deleting it from the report.

**`# nosec` and `# noqa` hide findings, they do not fix them.** Use a
line-scoped `# nosec B602` or `# noqa: E501` with a justification comment only
when the code is proven safe. Never add a blanket `exclude` or a global ignore
to make a report green.

**The Python version decides which findings are real.** `requires-python`,
`.python-version`, the Dockerfile base image and every CI `python-version` must
agree. A repository that tests on 3.12 and ships a `python:3.9` image ships an
end-of-life runtime with its own CVEs, and ruff's `UP` rules will propose
syntax the shipped runtime cannot parse. Check the declared branch against
https://devguide.python.org/versions/; an end-of-life branch is a security
finding on its own.

**Security vs quality are separate tiers.** Security findings (pip-audit,
bandit, Semgrep) always rank above code-quality findings (ruff, `UP`, mypy). A
lint or modernization hit never blocks on its own the way a reachable CVE does —
report both, but never let quality noise bury a real vulnerability.

## Usage

```
/check-python          # scan whole project with all four tools, report all (default)
/check-python scan     # same as default
/check-python report   # scan + write a markdown report file
/check-python fix      # scan, then propose/apply fixes after confirmation
```

## Step 1: Preconditions

Verify this is a Python project, determine its shape, and get the tools.

1. Confirm this is a Python project and record its dependency shape. A manifest
   is NOT required — a plain script tree still gets the three static-analysis
   tiers:
   ```bash
   find . -name '*.py' -not -path './.git/*' -not -path './.venv/*' -not -path './venv/*' | head -1 \
     || echo "NO .py files — not a Python project"
   ls pyproject.toml requirements*.txt setup.py setup.cfg Pipfile poetry.lock uv.lock pylock.*.toml 2>/dev/null \
     || echo "NO manifest — plain script mode"
   ```
   STOP only when there are no `.py` files at all. Record the mode:
   - **Manifest mode** — `pip-audit` runs against the declared dependencies.
     Note the source layout (`src/`, the package directory, `tests/`); it decides
     the scan scope.
   - **Plain script mode** (no manifest) — `pip-audit` has nothing to resolve.
     The other tiers still run. Record the absent SCA surface as a finding of its
     own rather than a clean result.

2. Record the runtime version — findings hinge on it:
   ```bash
   python3 --version && python3 -m pip --version
   ```

3. Inventory EVERY declared Python version and compare them. Drift between these
   is itself a finding. This scans whatever exists without depending on shell
   glob expansion (unmatched globs abort the command under zsh):
   ```bash
   grep -E 'requires-python|python_requires' pyproject.toml setup.cfg setup.py 2>/dev/null   # the floor
   cat .python-version runtime.txt 2>/dev/null
   # every other declaration, across whatever config files the repo actually has:
   grep -rniE 'python-version"?:|python:[0-9]|PYTHON_VERSION|basepython|envlist' \
     --include='*.yml' --include='*.yaml' --include='Dockerfile*' \
     --include='*.Dockerfile' --include='tox.ini' --include='Makefile*' . 2>/dev/null
   ```
   Flag any source whose Python version differs from the `requires-python` floor
   — `Dockerfile` base images, `python-version` in EVERY workflow (`ci`,
   `release`, and any other, not just one), `tox.ini` envlist, `.python-version`,
   `runtime.txt`, and container or CI configs. Check the floor against
   https://devguide.python.org/versions/; an end-of-life branch is a security
   finding on its own.

   A red CI job is not always visible in the run you are looking at. When the
   inventory finds drift, check the last few runs of the affected workflow
   (`gh run list --workflow=<name>.yml --limit 6 --json headSha,conclusion`),
   because a job broken by an earlier bump keeps failing on every commit after
   it and is easy to read as a new failure or to miss entirely.

4. Decide whether mypy runs. It runs ONLY when the project already configures it:
   ```bash
   ls mypy.ini .mypy.ini 2>/dev/null
   grep -lE '^\[mypy\]' setup.cfg 2>/dev/null
   grep -lE '^\[tool\.mypy\]' pyproject.toml 2>/dev/null
   ```
   With no config, skip the type tier and write "mypy: not configured" in the
   report. Never invent a mypy configuration for the project, and never run
   `--strict` against an untyped tree: hundreds of missing-annotation errors bury
   every real finding.

5. Install the tools into a THROWAWAY virtualenv, never into the project
   environment. Installing a scanner into the project's own venv changes the
   dependency set the scan is supposed to describe:
   ```bash
   TOOLDIR="$(mktemp -d /tmp/check-python-tools.XXXXXXXX)"; echo "tool dir: $TOOLDIR"
   python3 -m venv "$TOOLDIR/venv"
   "$TOOLDIR/venv/bin/pip" install --quiet --upgrade pip pip-audit 'bandit[toml]' ruff
   PY_AUDIT="$TOOLDIR/venv/bin/pip-audit"; BANDIT="$TOOLDIR/venv/bin/bandit"; RUFF="$TOOLDIR/venv/bin/ruff"
   "$PY_AUDIT" --version && "$BANDIT" --version && "$RUFF" --version
   docker pull semgrep/semgrep                    # the Semgrep tier needs Docker
   ```
   `bandit[toml]` is required, not optional: plain `bandit` cannot read a
   `[tool.bandit]` table and silently ignores the project's own exclusions.
   When the type tier runs, install mypy into the project's environment instead,
   because mypy needs the project's installed packages and their stubs to resolve
   imports. Ask the user before adding it if that changes a tracked file.
   If the project's CI pins specific tool versions (check
   `.github/workflows/*.y*ml`), install those exact versions instead so local
   results match CI. Delete `$TOOLDIR` when the run finishes.

## Step 2: Scan the whole project (all four tools)

Run every tool against every source path. Capture human output plus
machine-readable streams (authoritative for classification).

Write every machine-readable stream into a fresh per-run directory, NEVER a
fixed `/tmp/bandit.json` / `/tmp/ruff.json`. A shared path is the classic
cross-project trap: if a tool errors and does not overwrite, you silently parse
another repo's stale JSON as this project's findings. A unique dir per run makes
a write failure show up as a missing file instead of stale data.

```bash
RUNDIR="$(mktemp -d /tmp/check-python.XXXXXXXX)"; echo "run dir: $RUNDIR"

# --- Security ---
# Name the dependency source explicitly; see Key facts. Use the one that matches
# the project, and say in the report which one ran.
"$PY_AUDIT" --locked . ; echo "pip-audit exit: $?"                    # pyproject.toml / pylock.*.toml
"$PY_AUDIT" --locked . --format json -o "$RUNDIR/pip-audit.json"
# requirements project instead:
# "$PY_AUDIT" -r requirements.txt --format json -o "$RUNDIR/pip-audit.json"

"$BANDIT" -r . -x './.venv,./venv,./.git,./build,./dist' ; echo "bandit exit: $?"
"$BANDIT" -r . -x './.venv,./venv,./.git,./build,./dist' -f json -o "$RUNDIR/bandit.json"

# Semgrep: mount the repo READ-ONLY and write the JSON outside it, so the scan
# cannot dirty the working tree.
mkdir -p "$RUNDIR/semgrep"
docker run --rm -v "$PWD":/src:ro -v "$RUNDIR/semgrep":/out semgrep/semgrep \
  semgrep scan --config=p/python --config=p/owasp-top-ten --metrics=off \
  --json -o /out/semgrep.json /src ; echo "semgrep exit: $?"

# --- Code quality ---
"$RUFF" check . --no-cache ; echo "ruff exit: $?"
"$RUFF" check . --no-cache --output-format json -o "$RUNDIR/ruff.json"

# Modernization tier, kept separate so an idiom upgrade never hides in the lint count.
"$RUFF" check . --no-cache --select UP --target-version "py<floor>" ; echo "ruff UP exit: $?"
"$RUFF" check . --no-cache --select UP --target-version "py<floor>" --output-format json -o "$RUNDIR/ruff-up.json"

# Cyclomatic complexity gate: every function must stay at or below 10.
# C901 is off by default, so select it explicitly; max-complexity defaults to 10.
"$RUFF" check . --no-cache --select C901 --config "lint.mccabe.max-complexity = 10" \
  | tee "$RUNDIR/complexity.txt" ; echo "complexity exit: $?"

# Type tier, ONLY when Step 1.4 found a config:
# mypy . ; echo "mypy exit: $?"
```

Replace `py<floor>` with the `requires-python` floor from Step 1.3 (`py39`,
`py311`, and so on). Without it ruff assumes a default version and proposes
syntax the shipped runtime cannot parse.

**Plain script mode** runs the same scan without `pip-audit`. Say so explicitly
rather than reporting a clean SCA tier, and scan the real source directories
found in Step 1.

Before classifying, confirm the report belongs to THIS project. Every finding's
file path MUST fall under the current repo root, and none may sit inside
`.venv/`, `venv/`, `site-packages/`, `build/` or `dist/`. If a path points
outside it (a sibling project, a stale file), discard that finding and re-run the
tool into a fresh `$RUNDIR` — never report another project's issues as this
one's.

Notes:
- Exit codes: pip-audit `1` = vulnerabilities found; bandit `1` = issues;
  semgrep `1` = findings; ruff `1` = violations. `0` = clean for all. None of
  these are tool errors — parse the findings.
- NEVER pass `--exit-zero` to bandit or `--exit-zero` to ruff. A suppressed exit
  code turns a failing gate into a green one.
- ruff honors a repo `ruff.toml`, `.ruff.toml` or `[tool.ruff]` config if
  present; otherwise it uses its default rule set (`E4`, `E7`, `E9`, `F`). Note
  which applied in the report, because a default run checks far less than a
  configured one.
- `--no-cache` keeps a stale `.ruff_cache` from answering for code that changed.

## Step 3: Classify every finding

**pip-audit** — for each vulnerability extract:
- **ID** (`GHSA-…`, `PYSEC-…`, `CVE-…`) and its advisory link.
- **Package** and the **installed/resolved version**.
- **Fix versions**, and whether a fix exists at all.
- **Direct vs transitive**: a direct dependency is fixed in the manifest; a
  transitive one may need a constraint or a parent bump.

**bandit** — for each finding extract:
- **Test ID** (e.g. `B602`, `B301`) and **CWE**, file:line, code snippet.
- **Severity** (HIGH/MEDIUM/LOW) and **Confidence** (HIGH/MEDIUM/LOW).
- Judge whether it is a real risk or a **false positive** (a literal command
  passed to `subprocess`, an `assert` inside `tests/`, a hash used for a
  non-security checksum).

**Semgrep** — for each finding extract the rule ID, file:line, the message and
the taint path when the rule reports one. A Semgrep finding that bandit missed is
usually a cross-file flow; keep the whole path in the report, not just the sink.

**ruff** — for each violation extract file:line, the **rule code** (e.g. `F401`,
`E722`, `B008`) and the message.

**ruff `UP`** — for each suggestion extract file:line and the modern idiom it
proposes (e.g. "Use `X | Y` for type annotations"). These are optional
improvements, not defects, and they are bounded by the `requires-python` floor.

**ruff `C901`** — for each line extract the function name, its complexity number
and file:line. Every line is a function over the limit of 10. Unlike the `UP`
tier this is NOT optional: the limit is a project rule, and a function above it
must be refactored into smaller single-responsibility functions, never suppressed
and never given a raised threshold.

**mypy** (when configured) — for each error extract file:line, the error code
(e.g. `[arg-type]`, `[return-value]`) and the message.

Rank all findings by severity for action (security tier first, always):
1. **Reachable CVE in a direct dependency** — highest; fix by bumping the pin.
2. **Python version drift or an end-of-life branch** — a release, container or
   CI path declares a version other than the floor, or the floor itself is out
   of support; fix by raising every declaring location. Ranked here because it
   is how a runtime CVE reaches production while the local scan reads clean.
3. **CVE in a transitive dependency** — fix by bumping the parent or adding a
   constraint.
4. **bandit or Semgrep HIGH/MEDIUM real finding** — fix in code.
5. **bandit LOW / false positive** — sanitize if cheap, else annotate `# nosec`
   with a justification.
6. **Unpinned dependency set** — note as a finding; the SCA result describes one
   resolution only.
7. **ruff lint violation** — quality; fix in code (correctness rules first).
8. **Function over the complexity limit (`C901`)** — quality; refactor into
   smaller functions. Ranked above the modernization tier because it is a limit,
   not a suggestion.
9. **mypy error** (when configured) — quality; fix the annotation or the code.
10. **ruff `UP` suggestion** — lowest; optional idiom upgrade,
    behavior-preserving within the declared floor.

## Step 4: Produce the report

Always print a ranked summary to the user, most severe first. Use this shape:

```
# Python security & quality report — <project name>
Local runtime: python<X.Y.Z>   requires-python floor: <X.Y>   Scanned: <source paths>
Dependency source: <--locked . | -r requirements.txt | pip-audit . | none (plain script mode)>
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
Security: <green ONLY if 0 vulns AND bandit 0 AND semgrep 0 | red: list fixes>
Quality:  <green ONLY if ruff 0 AND C901 0 AND UP 0 AND mypy 0-or-not-configured | yellow: list>
```

**Verdict rule:** Quality is green ONLY when ruff, `C901`, the `UP` tier and mypy
all report zero. Any `UP` suggestion (or any lint violation) means quality is NOT
clean — mark it yellow and list the outstanding items. Never call a tier green
while it still has open findings, however minor. "mypy: not configured" is not a
pass; report it as a gap in the quality surface.

For `report` mode, also write this to `VULN-REPORT.md` (or append to an
existing `BUG-REPORT.md` if the project uses one) in English.

## Step 5: Fix (only in `fix` mode, after confirmation)

Never edit files in `scan`/`report` mode. In `fix` mode, read
[references/fix.md](references/fix.md) in full before you change any file, and
follow every step in it.

## Rules

- Default to `scan`; run ALL FOUR tools (pip-audit, bandit, Semgrep, ruff) plus
  the `UP` tier and the `C901` complexity gate every time; never modify files
  unless invoked as `fix`.
- Run mypy ONLY when the project already configures it, and never invent a
  configuration. Report "mypy: not configured" as a gap, never as a pass.
- Enforce a cyclomatic complexity limit of 10 per function with
  `--select C901 --config "lint.mccabe.max-complexity = 10"`. Any output is a
  finding. NEVER raise the threshold, ignore a file, or drop the gate to make the
  report green; refactor into smaller single-responsibility functions instead.
- Install scanners into a throwaway virtualenv, never into the project
  environment, because a scanner added to the project changes the dependency set
  the scan describes.
- Install `bandit[toml]`, not plain `bandit`, so a `[tool.bandit]` table in
  `pyproject.toml` is read instead of silently ignored.
- Name the pip-audit dependency source explicitly (`--locked .`, `-r <file>` or
  `pip-audit .`) and report which one ran. A bare `pip-audit` audits the
  environment the tool runs in, which in this workflow is the tools virtualenv.
- NEVER pass `--exit-zero` to bandit or ruff, and never suppress a tool's exit
  code; a suppressed gate reads as green while findings stand.
- Pass `--target-version` matching the `requires-python` floor to the `UP` tier,
  so no suggestion proposes syntax the shipped runtime cannot parse.
- NEVER truncate a scan command's output with `head`, `tail`, or a count flag.
  A capped run reports the first few findings and hides the rest, so the next
  run finds work you already called done. Read the whole output; use the
  machine-readable stream in `$RUNDIR` when the human output is long. A
  config-header display, an existence probe and a single-value extraction may
  still use them, because they read one known field, not a finding list.
- Keep security and code-quality findings in SEPARATE tiers in the report;
  security always ranks first. Never let lint or modernization noise bury a real
  CVE.
- Report EVERY finding from all four tools, including transitive-only CVEs,
  bandit LOW issues, and `UP` suggestions — do not silently drop anything.
- `UP` suggestions are optional and behavior-preserving; apply only in `fix` mode
  with user agreement, never treat them as blocking defects.
- Report the runtime version and the `requires-python` floor in every report;
  findings are meaningless without them.
- Inventory every declared Python version (`requires-python`, `.python-version`,
  `runtime.txt`, Dockerfile, ALL workflows, `tox.ini`) and flag any drift; check
  the floor against https://devguide.python.org/versions/ and treat an
  end-of-life branch as a security finding.
- Never hand-edit a lock file; regenerate it with the project's own resolver.
- For a false positive, prefer a real sanitizer or validator; use a line-scoped
  `# nosec <TEST-ID>` or `# noqa: <CODE>` with justification only when the code
  is proven safe. Never disable a rule globally to mask a real finding.
- Scan only the project's own source; never report a finding from `.venv/`,
  `venv/`, `site-packages/`, `build/` or `dist/`.
- If the project's CI pins scanner versions, scan with those exact versions so
  local results match CI.
- Reports are written in English; explanations to the user follow the user's
  language.
- Confirm with the user before applying any dependency upgrade, Python version
  bump, or code change in `fix` mode.
- Delete the throwaway tools virtualenv after proving a fix.
