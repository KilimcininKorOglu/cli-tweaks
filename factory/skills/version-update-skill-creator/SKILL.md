---
name: version-update-skill-creator
description: >
  This skill MUST be invoked when the user says "version update skill oluştur",
  "create version update skill", "versiyon skill'i oluştur", "update-version skill",
  "version-update skill yap" or any variation requesting creation of a project-local
  version update skill. SHOULD also invoke when user mentions "versiyon güncelleme
  skill'i kur", "setup version bumping", or asks to automate version management
  for the current project. Scans the project for version files, build commands,
  and changelog, then generates a tailored version-update skill in .claude/skills/.
---

# Version Update Skill Creator

Scan the current project and create a project-specific `version-update` skill that automates version bumping, changelog generation, git tagging, and pushing.

## Action

Immediately scan the project and create the skill. Do not wait for further instructions. Start scanning now.

## Phase 1: Project Scan

Scan the project for every place the version is written. The table below lists common starting points, but it is NOT exhaustive -- always finish with the content sweep in the next section. For each file found, note the exact version field location:

| File                    | Version Field                                           | Example                        |
|-------------------------|---------------------------------------------------------|--------------------------------|
| `package.json`          | `"version": "X.Y.Z"`                                   | `"version": "1.2.0"`          |
| `pyproject.toml`        | `[project].version` or `[tool.poetry].version`          | `version = "1.2.0"`           |
| `Cargo.toml`            | `[package].version`                                     | `version = "1.2.0"`           |
| `pubspec.yaml`          | `version:`                                              | `version: 1.2.0`              |
| `build.gradle`          | `version =` or `version '...'`                          | `version = '1.2.0'`           |
| `build.gradle.kts`      | `version =`                                             | `version = "1.2.0"`           |
| `pom.xml`               | Top-level `<version>`                                   | `<version>1.2.0</version>`    |
| `setup.py`              | `version=` in setup() call                              | `version="1.2.0"`             |
| `setup.cfg`             | `[metadata].version`                                    | `version = 1.2.0`             |
| `VERSION` / `VERSION.txt` | Entire file content                                   | `1.2.0`                       |
| `*.gemspec`             | `.version =`                                            | `spec.version = "1.2.0"`      |
| `mix.exs`               | `version:`                                              | `version: "1.2.0"`            |
| `Chart.yaml`            | `version:` and `appVersion:`                            | `version: 1.2.0`              |
| `*.csproj`              | `<Version>` (or `<VersionPrefix>`)                      | `<Version>1.2.0</Version>`    |
| `__init__.py` / `_version.py` | `__version__`                                     | `__version__ = "1.2.0"`       |

Also detect:
- **Build command**: Check `package.json` scripts (build), `Makefile` (build target), `Cargo.toml` (cargo build), `pyproject.toml` (build system), `go.mod` (go build)
- **Existing CHANGELOG.md**: Note if it exists and its current format
- **GitHub Actions**: List `.github/workflows/*.yml` and note which trigger on `push`/tags (e.g. `ci`, `release`). Check `gh` is installed and authenticated (`gh auth status`). If workflows exist AND `gh` works, the generated skill gets a post-push Step 8 that tracks them; otherwise it omits that step.
- **Release mechanism** (language-agnostic — applies to every ecosystem, not just Go): determine whether pushing a tag produces a GitHub Release, and who writes its body. Classify into one of three cases:
  - **CI generates a release with an auto body** — a tag-triggered workflow runs a releaser that builds the body from git commits, NOT from CHANGELOG.md. Examples across ecosystems: `goreleaser` (Go, `.goreleaser.y*ml` + `goreleaser-action`), `softprops/action-gh-release` / `gh release create` (any lang), `cargo-dist` (Rust), electron-builder publish (JS). Step 9 must OVERWRITE that body after CI with the CHANGELOG section via `gh release edit`.
  - **A release tool already owns the CHANGELOG and the release notes** — `semantic-release`, `release-please`, `changesets`, `standard-version`. These generate the CHANGELOG and the release body themselves; do NOT add Step 9 (and usually this whole skill overlaps them — warn the user instead of fighting the tool).
  - **No release is produced** (or the skill itself will create it) — if nothing produces a release, omit Step 9; if the skill will create the release, it passes the notes at creation time.
- **Latest git tag**: Run `git describe --tags --abbrev=0 2>/dev/null` to find the current version tag
- **Current version**: Read from the primary version file

### Content sweep (MANDATORY -- the table is not enough)

Manifest tables miss version strings embedded in non-manifest files: `openapi.json`/`swagger.json` `info.version`, HTML `<meta>` tags, README/badge URLs (shields.io), Docker `LABEL version`, `manifest.json` (browser extension), `app.json`/`app.config.js` (Expo), `Chart.yaml` `appVersion`, sitemaps, embedded constants. Do NOT rely on the table alone.

After reading the current version, grep the WHOLE repo for that literal to find every occurrence regardless of filename:

```
git grep -n --fixed-strings "<CURRENT_VERSION>" -- . ':!CHANGELOG.md' ':!*.lock' ':!go.sum' ':!*.mod'
```

If there is no version file yet, derive the current version from `git describe --tags --abbrev=0` (strip any `v` prefix) and sweep for that. Classify EVERY hit into one of two buckets:

- **Hardcoded** -- the literal version is stored here and must be bumped on release. Add it to the generated skill's Step 2.
- **Dynamic reader** -- the file reads the version at runtime (from a version file, an env var, a build flag, or an HTTP endpoint like `/healthz`) and only happens to contain the literal as a fallback/comment/test fixture. These MUST NOT be edited by the skill. Record them in a "DO NOT edit" list.

When unsure whether a hit is hardcoded or dynamic, open the file and read the surrounding code before deciding. A version bump that overwrites a dynamic reader is worse than one that misses a file.

If NO version files AND no version literals are found, inform the user and stop. Do not create the skill.

## Phase 2: Generate the Skill

Create `.claude/skills/version-update/SKILL.md` with the following structure. Replace all placeholders with actual values from the scan.

The generated skill MUST include:

### Frontmatter

```yaml
---
name: version-update
description: >
  This skill MUST be invoked when the user says "version update",
  "versiyon güncelle", "bump version", "release", "tag ekle",
  "versiyon yükselt", "yeni versiyon" or any variation requesting
  a version bump. Bumps the project version, updates changelog,
  creates a git tag, and pushes. Runs fully automatically.
argument-hint: "[major | minor | patch]"
---
```

### Body Template

The generated skill body must follow this exact structure:

```markdown
# Version Update

Bump the project version, update changelog, create git tag, commit, and push.
Runs fully automatically with no user interaction.

## Usage

/version-update patch    # 1.2.0 → 1.2.1 (default)
/version-update minor    # 1.2.0 → 1.3.0
/version-update major    # 1.2.0 → 2.0.0

## Version Files

Every place the version is hardcoded. ALL must be bumped together and hold identical values.

[LIST ONLY THE HARDCODED FILES THAT WERE FOUND IN THE PROJECT]

| File | Field | Current Version |
|------|-------|-----------------|
| ... | ... | ... |

### Dynamic (DO NOT edit -- they read the version at runtime)

[LIST ANY DYNAMIC-READER FILES FOUND; OMIT THIS SUBSECTION IF NONE]

- `[FILE]`: [how it resolves the version, e.g. reads the embedded VERSION file / fetches /healthz]

Never hardcode a version in these files.

## Steps (execute ALL automatically, no questions)

### Step 1: Determine New Version
- FIRST resume any unpushed release: if HEAD is already on a version tag (`git describe --exact-match --tags HEAD 2>/dev/null` returns a tag) that is not yet on the remote (`git ls-remote --tags origin <tag>` is empty, or no remote exists), SKIP the bump and jump straight to Step 7 to push that existing commit and tag -- a prior run committed and tagged but failed to push, and re-bumping would silently skip that version
- Verify the current branch is the intended release branch (typically `main`/`master`); if on a feature/topic branch, STOP -- a release must not be tagged from a feature branch
- Read current version from [PRIMARY VERSION FILE]
- If multiple version files exist, read them all and verify they currently agree; if they disagree, STOP and report the mismatch instead of silently overwriting them to the primary's value
- Apply semver bump (default: patch if no argument given)
- Validate: new version must be greater than current

### Step 2: Update Version Files
[FOR EACH FOUND FILE, list the exact edit instruction]
- Update `[FILE]`: change `[FIELD]` from `[CURRENT]` to new version
- For `Chart.yaml`, bump `version` (the chart version); leave `appVersion` unless it tracks the same app release -- the two are semantically distinct

### Step 3: Build and Verify
- Run: `[DETECTED BUILD COMMAND]`
- If build fails, STOP immediately. Revert the version-file edits with `git restore [VERSION FILES]` (they are not committed yet) and do not proceed.
- Verify completeness with a content sweep -- the OLD version must survive ONLY in expected places (CHANGELOG history, dynamic-reader fallbacks): `git grep -n --fixed-strings "[OLD_VERSION]" -- . ':!CHANGELOG.md'`. If it appears in any hardcoded file that was supposed to be bumped, that file was missed -- bump it now before continuing.
- If any version file is a structured format (JSON/YAML/TOML), confirm it still parses after the edit.

### Step 4: Update CHANGELOG.md
- Find the last release tag at runtime: `git describe --tags --abbrev=0 2>/dev/null`
- Get commits since then: if a tag was found, `git log <tag>..HEAD --oneline --no-decorate`; otherwise `git log HEAD --oneline --no-decorate` (first release -- use full history)
- Get today's real date from `date +%Y-%m-%d` (never guess the date)
- If CHANGELOG.md does not exist, create it
- Prepend a new section at the top (below the header) in Keep a Changelog format:

## [X.Y.Z] - YYYY-MM-DD

### Added
- [new features from commits]

### Changed
- [changes from commits]

### Fixed
- [bug fixes from commits]

Categorize commits by their conventional commit prefix:
- feat: → Added
- fix: → Fixed
- everything else → Changed
- Skip: chore(deps), merge commits, version bump commits

### Step 5: Git Commit
- Stage ONLY the bumped files by explicit path: the version files listed above + CHANGELOG.md. NEVER `git add -A` / `git add .` -- the Step 3 build may have produced artifacts that must not enter the release commit
- Commit with message: `chore: bump version to X.Y.Z`

### Step 6: Git Tag
- If `vX.Y.Z` already exists (`git rev-parse vX.Y.Z 2>/dev/null`), STOP -- this version was already tagged
- Create annotated tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`

### Step 7: Push
- Verify an upstream exists: `git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null`. If none, STOP after the local tag and tell the user to push manually -- a missing upstream must not abort mid-release
- Push the branch and ONLY the new tag: `git push && git push origin vX.Y.Z` (or `git push --follow-tags`). NEVER `git push --tags` -- it pushes every local tag, not just this release
- If the push fails after the tag was created, report the exact state (commit + tag exist locally, nothing pushed yet); re-running the skill resumes at the push because Step 1 detects the unpushed tag and skips the bump

[INCLUDE STEP 8 ONLY IF THE PROJECT HAS `.github/workflows/*.yml` AND the `gh` CLI is available; otherwise omit it entirely]

### Step 8: Track GitHub Actions
- The push in Step 7 triggers any workflow bound to `push` on this branch or to the new tag (e.g. `ci`, `release`). Watch them to completion and report the result -- a release is not "done" until CI is green.
- Give Actions a moment to register the runs, then find the runs for the pushed commit:
  - `SHA=$(git rev-parse HEAD)`
  - `gh run list --commit "$SHA" --json databaseId,name,event,status,conclusion` (retry a few times if empty -- runs take a few seconds to appear)
  - Also check tag-triggered runs if a release workflow exists (they share the same commit SHA, so `--commit` catches them too)
- Watch each run to completion: `gh run watch <databaseId> --exit-status` (exits non-zero if the run fails)
- Report a compact table: workflow name, event, final conclusion (success/failure), and the run URL (`gh run view <databaseId> --json url`)
- If any run FAILS: report the failing job and a short log tail (`gh run view <databaseId> --log-failed | tail -50`). Do NOT roll back the release -- the tag is already public; surface the failure so the user can decide.
- If `gh` is not authenticated or the repo has no Actions, note that runs could not be tracked and stop cleanly (the release itself already succeeded).

[INCLUDE STEP 9 ONLY IF a release with an AUTO-GENERATED body is produced (CI releaser like goreleaser/action-gh-release/cargo-dist, or the skill creates the release) AND `gh` is available. OMIT it if a release tool already owns the CHANGELOG+notes (semantic-release, release-please, changesets) or if no release is produced. The extraction and `gh` commands below are language-agnostic — they read CHANGELOG.md, not any build tool.]

### Step 9: Set release notes from CHANGELOG
The release body must be the human-written CHANGELOG section, not auto-generated commit noise. Extract the section for this version and apply it.
- Extract just this version's section (from `## [X.Y.Z]` to the next `## [`):
  ```bash
  awk -v v="X.Y.Z" '$0 ~ "^## \\["v"\\]"{f=1;next} f&&/^## \[/{exit} f{print}' CHANGELOG.md > /tmp/relnotes.md
  ```
  If `/tmp/relnotes.md` is empty, STOP this step and report it -- do not push blank notes over a good body.
- [IF THE RELEASE IS PRODUCED BY CI (goreleaser / release workflow)]: the body already exists once CI finished in Step 8. OVERWRITE it (CI generated its own from commits): `gh release edit vX.Y.Z --notes-file /tmp/relnotes.md`. Wait until the release exists first (`gh release view vX.Y.Z` succeeds); if CI failed in Step 8, skip -- there is no release to edit.
- [IF THE SKILL ITSELF CREATES THE RELEASE (no CI release step)]: create it with the notes directly: `gh release create vX.Y.Z --title vX.Y.Z --notes-file /tmp/relnotes.md`.
- Confirm: `gh release view vX.Y.Z` shows the CHANGELOG content as the body.

## Rules

- NEVER ask questions. Run all steps automatically.
- If build fails, revert all version file changes and stop.
- If no argument is given, default to `patch`.
- The commit message format is always `chore: bump version to X.Y.Z`.
- Tag format is always `vX.Y.Z`.
- CHANGELOG entries must be in English.
- After pushing, track any triggered GitHub Actions to completion and report pass/fail; never roll back a pushed tag on CI failure -- report it instead.
- If a release is produced, its body must be the CHANGELOG section for this version, never auto-generated commit notes; set it via `gh release edit`/`create --notes-file`.
```

### Adaptation Rules

When generating the skill:
- **The content sweep is authoritative, not the table.** List every hardcoded hit the grep found -- including non-manifest files like `openapi.json` `info.version`, HTML meta tags, or Docker labels -- not just the ones that matched a known filename.
- **Separate hardcoded files from dynamic readers.** Put runtime-resolving files in the "DO NOT edit" list, never in Step 2.
- **Only include version files that actually exist** in the project
- **Fill in the actual build command** detected from the project
- **Fill in the current version** read from files
- Do NOT hardcode the latest tag into Step 4 -- the generated skill finds it at runtime with `git describe`, so it works for the first release (no tag) and never goes stale across later releases
- If the project has NO build command, drop only the build line from Step 3; KEEP the content-sweep verification and rename the step to just "Verify"
- If the project uses a non-standard tag prefix (e.g., no `v` prefix), match the existing convention
- If CHANGELOG.md already exists, preserve its existing content and prepend the new section
- **Match Step 9 to the detected release mechanism (this is language-agnostic).** If CI produces a release with an auto body (goreleaser, action-gh-release, cargo-dist, etc.), generate the `gh release edit` variant that overwrites the CI body AFTER Step 8. If the skill creates the release itself, generate the `gh release create --notes-file` variant. If a tool already owns the CHANGELOG+notes (semantic-release, release-please, changesets) or no release is produced, omit Step 9. Never generate more than one variant.

## Phase 3: Confirm

After creating the skill file, output a summary:

```
Version Update skill created at .claude/skills/version-update/SKILL.md

Detected:
- Hardcoded version files: [list]
- Dynamic readers (not edited): [list or "none"]
- Current version: X.Y.Z
- Build command: [command or "none"]
- Latest tag: [tag or "none"]
- Changelog: [exists / will be created]
- GitHub Actions tracking: [enabled (workflows: ci, release) / disabled (no workflows or no gh)]
- Release notes from CHANGELOG: [enabled via gh release edit (CI auto-body: <tool>) / enabled via gh release create / disabled (tool owns changelog: <tool>) / disabled (no release mechanism)]

The skill is ready. Run /version-update [major|minor|patch] to use it.
```

## Safety Rules

- Only create `.claude/skills/version-update/SKILL.md` -- never modify other files
- If the skill already exists, read it first and ask before overwriting
- Do not run any version update operations -- only create the skill definition
- Do not modify CLAUDE.md, AGENTS.md, or any other configuration files
