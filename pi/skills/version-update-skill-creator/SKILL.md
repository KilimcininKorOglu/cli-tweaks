---
name: version-update-skill-creator
description: >
  This skill MUST be invoked when the user says "version update skill oluştur",
  "create version update skill", "versiyon skill'i oluştur", "update-version skill",
  "version-update skill yap" or any variation requesting creation of a project-local
  version update skill. SHOULD also invoke when user mentions "versiyon güncelleme
  skill'i kur", "setup version bumping", or asks to automate version management
  for the current project. Scans the project for version files, build commands,
  and changelog, then generates a tailored version-update skill in .pi/skills/.
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

Also detect:
- **Build command**: Check `package.json` scripts (build), `Makefile` (build target), `Cargo.toml` (cargo build), `pyproject.toml` (build system), `go.mod` (go build)
- **Existing CHANGELOG.md**: Note if it exists and its current format
- **Latest git tag**: Run `git describe --tags --abbrev=0 2>/dev/null` to find the current version tag
- **Current version**: Read from the primary version file

If NO version files are found, inform the user and stop. Do not create the skill.

## Phase 2: Generate the Skill

Create `.pi/skills/version-update/SKILL.md` with the following structure. Replace all placeholders with actual values from the scan.

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
- Read current version from [PRIMARY VERSION FILE]
- Apply semver bump (default: patch if no argument given)
- Validate: new version must be greater than current

### Step 2: Update Version Files
[FOR EACH FOUND FILE, list the exact edit instruction]
- Update `[FILE]`: change `[FIELD]` from `[CURRENT]` to new version

### Step 3: Build
- Run: `[DETECTED BUILD COMMAND]`
- If build fails, STOP immediately. Do not proceed. Revert version changes.

### Step 4: Update CHANGELOG.md
- Run `git log [LATEST_TAG]..HEAD --oneline --no-decorate` to get commits since last tag
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
- Stage all modified files: version files + CHANGELOG.md
- Commit with message: `chore: bump version to X.Y.Z`

### Step 6: Git Tag
- Create annotated tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`

### Step 7: Push
- Run: `git push && git push --tags`

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
- **Fill in the latest git tag** if one exists
- If the project has NO build command, omit Step 3 entirely
- If the project uses a non-standard tag prefix (e.g., no `v` prefix), match the existing convention
- If CHANGELOG.md already exists, preserve its existing content and prepend the new section

## Phase 3: Confirm

After creating the skill file, output a summary:

```
Version Update skill created at .pi/skills/version-update/SKILL.md

Detected:
- Version files: [list]
- Current version: X.Y.Z
- Build command: [command or "none"]
- Latest tag: [tag or "none"]
- Changelog: [exists / will be created]

The skill is ready. Run /version-update [major|minor|patch] to use it.
```

## Safety Rules

- Only create `.pi/skills/version-update/SKILL.md` -- never modify other files
- If the skill already exists, read it first and ask before overwriting
- Do not run any version update operations -- only create the skill definition
- Do not modify CLAUDE.md, AGENTS.md, or any other configuration files
