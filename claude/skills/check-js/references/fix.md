# check-js: Fix mode

Read this file only in `fix` mode, after the scan and the report are complete.
Never edit files in `scan`/`report` mode.

A `fix` run repairs one finding class after another. A finished finding is a
checkpoint, not an ending: continue to the next finding in the same turn. A
decision the run genuinely needs from the user, such as a major-version bump below, still ends the turn.

## Semver-compatible CVEs
```bash
npm audit fix          # NEVER --force; it installs breaking majors
npm update <pkg>
```

## CVEs needing a major bump
NEVER apply these automatically. Propose them one package at a time, naming the
breaking change and the migration the upgrade requires, and let the user decide:
```bash
npm install <pkg>@<patched-major>
```
Run the project's tests after every such bump, before moving to the next.

## Transitive CVEs with no parent release
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

## Node version drift or an end-of-life major
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

## semgrep findings
- **Real finding**: fix the code. XSS → escape or use a framework's safe binding
  instead of `innerHTML`; injection → parameterize; hardcoded secret → move to
  the environment and rotate the exposed value; unsafe deserialization → validate
  the shape before use.
- **False positive** (proven safe but semgrep cannot follow the validator): add
  `// nosemgrep: <rule-id>` on the flagged line WITH a justification comment
  above it. Never disable a rule globally to hide a real finding.
- Re-run semgrep until it exits 0.

## ESLint problems
```bash
npx eslint . --fix     # auto-fixable rules only; review the diff
```
Fix the rest in code following each rule's guidance. Re-run until 0. Do not
silence a rule unless the finding is a proven false positive, and then scope
`// eslint-disable-next-line <rule>` to the single line with a reason. Never add
a file-wide or config-wide disable to hide a real finding.

## Functions over the complexity limit
Refactor each function the complexity gate reported into smaller
single-responsibility functions: extract the branches of a long `if`/`switch`
chain into named helpers, lift error handling out of the happy path, and split
functions that do two jobs. NEVER raise the threshold, add an
`eslint-disable` for `complexity`, or drop the gate to make the report green.
Re-run the gate until it reports nothing.

## knip findings
- **Unlisted dependency**: declare it in `package.json`. This is a real build
  correctness fix, not hygiene.
- **Unused dependency**: remove it after confirming nothing loads it dynamically.
- **Unused file/export**: VERIFY first. Check for dynamic `import()`, framework
  route/config conventions, and plugin entry points. When the framework loads it
  reflectively, configure knip's `entry` patterns instead of deleting. Never
  delete on knip's word alone.

## Prove the fix
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
