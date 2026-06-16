---
name: version-update-skill-creator
description: >
  This skill MUST be invoked when the user says "version update skill oluştur",
  "create version update skill", "versiyon skill'i oluştur", "update-version skill",
  "version-update skill yap" or any variation requesting creation of a project-local
  version update skill. SHOULD also invoke when user mentions "versiyon güncelleme
  skill'i kur", "setup version bumping", or asks to automate version management
  for the current project. Scans the project for version files, build commands,
  and changelog, then generates a tailored version-update skill in .wrongstack/skills/.
---

# Version Update Skill Creator

Scan the current project and create a project-specific `version-update` skill that automates version bumping, changelog generation, git tagging, and pushing.

## Action

Immediately scan the project and create the skill. Do not wait for further instructions. Start scanning now.

## Phase 1: Project Scan

Scan the project root for version files. For each file found, note the exact version field location:

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
- **Latest git tag**: Run `git describe --tags --abbrev=0 2>/dev/null` to find the current version tag
- **Current version**: Read from the primary version file

If NO version files are found, inform the user and stop. Do not create the skill.

## Phase 2: Generate the Skill

Create `.wrongstack/skills/version-update/SKILL.md` with the following structure. Replace all placeholders with actual values from the scan.

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

[LIST ONLY THE FILES THAT WERE FOUND IN THE PROJECT]

| File | Field | Current Version |
|------|-------|-----------------|
| ... | ... | ... |

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

### Step 3: Build
- Run: `[DETECTED BUILD COMMAND]`
- If build fails, STOP immediately. Revert the version-file edits with `git restore [VERSION FILES]` (they are not committed yet) and do not proceed.

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

## Rules

- NEVER ask questions. Run all steps automatically.
- If build fails, revert all version file changes and stop.
- If no argument is given, default to `patch`.
- The commit message format is always `chore: bump version to X.Y.Z`.
- Tag format is always `vX.Y.Z`.
- CHANGELOG entries must be in English.
```

### Adaptation Rules

When generating the skill:
- **Only include version files that actually exist** in the project
- **Fill in the actual build command** detected from the project
- **Fill in the current version** read from files
- Do NOT hardcode the latest tag into Step 4 -- the generated skill finds it at runtime with `git describe`, so it works for the first release (no tag) and never goes stale across later releases
- If the project has NO build command, omit Step 3 entirely
- If the project uses a non-standard tag prefix (e.g., no `v` prefix), match the existing convention
- If CHANGELOG.md already exists, preserve its existing content and prepend the new section

## Phase 3: Confirm

After creating the skill file, output a summary:

```
Version Update skill created at .wrongstack/skills/version-update/SKILL.md

Detected:
- Version files: [list]
- Current version: X.Y.Z
- Build command: [command or "none"]
- Latest tag: [tag or "none"]
- Changelog: [exists / will be created]

The skill is ready. Run /version-update [major|minor|patch] to use it.
```

## Safety Rules

- Only create `.wrongstack/skills/version-update/SKILL.md` -- never modify other files
- If the skill already exists, read it first and ask before overwriting
- Do not run any version update operations -- only create the skill definition
- Do not modify CLAUDE.md, AGENTS.md, or any other configuration files
