---
name: commit
description: >
  This skill MUST be invoked when the user says "commit", "commitle",
  "commit at", "commit yap", "push" or any variation
  requesting a git commit. SHOULD also invoke when user mentions "stage",
  "staged", "değişiklikleri commitle", or asks to push code changes.
  Creates well-formatted commits with conventional commit messages.
  Auto-detects git state, stages changes intelligently, and creates
  atomic commits with proper type/scope/description format.
argument-hint: "[--all | --staged | --modified | --amend | --no-verify | --wip | --push]"
---

# Commit

Creates well-formatted commits with conventional commit messages.

## Usage

```bash
/commit                  # Auto-detect and handle changes
/commit --all            # Stage all changes including untracked
/commit --staged         # Only commit currently staged files
/commit --modified       # Stage and commit modified files only
/commit --no-verify      # Skip pre-commit hooks
/commit --amend          # Amend the last commit
/commit --wip            # Quick WIP commit
/commit --push           # Commit, then push (confirms before pushing to a default branch)
```

## Git Safety Protocol

- NEVER update the git config
- NEVER skip hooks (--no-verify) unless the user explicitly passes `--no-verify`
- NEVER use `git commit --amend` unless the user explicitly passes `--amend`
- NEVER commit files that likely contain secrets (.env, .env.local, credentials.json, *.pem, *.key, id_rsa, etc.) -- warn the user if detected
- NEVER create empty commits if there are no changes
- NEVER use git commands with -i flag (git rebase -i, git add -i) -- interactive mode is not supported
- NEVER add signatures like "Created by Claude", "Co-authored-by: AI" or similar
- NEVER push unless the user explicitly asked (the `--push` flag, or said "push" / "commit and push") -- a plain commit NEVER pushes
- NEVER push to the default branch (`main`/`master`) without explicit confirmation -- if on the default branch, offer to create a feature branch first

## Commit Message Format (Default)

Used when repo has no established style or uses conventional commits:

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

For multi-line commit messages, use HEREDOC syntax:

```bash
git commit -m "$(cat <<'EOF'
type(scope): subject line

Body paragraph explaining the why, not the what.
Additional context if needed.

Footer: value
EOF
)"
```

## Types

| Type       | Description                              | Example                                |
|------------|------------------------------------------|----------------------------------------|
| `feat`     | New feature                              | `feat: add user authentication`        |
| `fix`      | Bug fix                                  | `fix: resolve memory leak`             |
| `docs`     | Documentation                            | `docs: update API reference`           |
| `style`    | Formatting                               | `style: format code with prettier`     |
| `refactor` | Code change (no fix/feat)                | `refactor: extract helper functions`   |
| `perf`     | Performance                              | `perf: optimize database queries`      |
| `test`     | Tests                                    | `test: add unit tests for auth`        |
| `chore`    | Maintenance                              | `chore: update dependencies`           |
| `ci`       | CI/CD changes                            | `ci: add GitHub Actions workflow`      |
| `security` | Security fixes                           | `security: patch XSS vulnerability`    |
| `hotfix`   | Critical hotfix                          | `hotfix: fix login crash`              |
| `revert`   | Revert changes                           | `revert: undo payment refactor`        |

### Extended Types

- `lint`, `move`, `arch`, `deps-add`, `deps-remove`, `deps-pin`
- `format`, `patch`, `catch`, `remove`, `typo`, `comments`, `deprecate`
- `init`, `seed`, `ux`, `a11y`, `i18n`, `animation`, `ui`, `responsive`
- `db`, `analytics`, `logs`, `logs-remove`, `backup`, `metrics`, `flags`
- `release`, `wip`, `ci-fix`, `ci-build`, `merge`, `license`, `breaking`
- `experiment`, `mock`, `snapshots`, `experimental`, `dx`
- `docs-api`, `docs-readme`, `types`, `business`, `assets`, `gitignore`
- `dead`, `cleanup`, `validation`, `thread`, `offline`

## Process Flow

1. **Gather Context (MANDATORY FIRST STEP)**: Before anything else, run these in parallel:
   ```bash
   git status                    # Current state of working tree
   git diff HEAD                 # All staged and unstaged changes
   git branch --show-current     # Current branch name
   git log --oneline -10         # Recent commits for style matching
   ```
2. **Security Scan**: Check changed files for secrets (.env, keys, credentials)
3. **Smart Staging Decision**:
   - Staged files exist -> commit only staged
   - No staged but changes exist -> analyze and stage appropriately
   - Untracked files -> ask if they should be included
   - Working tree clean -> if a push was requested, skip to step 8; otherwise report no changes
4. **Review Changes**: `git diff --cached --stat` + `git diff --cached`
5. **Match Repo Style**: Look at the recent `git log` and adopt the repo's existing style:
   - Conventional commits (`feat:`, `fix:`) -> follow that
   - Plain messages ("Add login page") -> follow that
   - Ticket prefixes (`JIRA-123: ...`) -> follow that
   - No clear pattern -> default to the conventional `<type>(<scope>): <subject>` format (see Commit Message Format)
6. **Analyze for Logical Grouping**: Check if changes belong together, suggest splitting if multiple concerns
7. **Create Commit**: Use HEREDOC syntax for multi-line, simple -m for single-line
8. **Push (only if requested)**: Push only when the user explicitly asked (`--push`, or said "push" / "commit and push"). If the tree was already clean (nothing to commit), push the existing commits instead. Before pushing to the default branch (`main`/`master`), confirm first or offer to create a feature branch. A plain commit request never reaches this step.

## Smart Staging Strategy

| Situation            | Action                    |
|----------------------|---------------------------|
| Only staged files    | Commit staged files       |
| Only modified files  | Stage only the files for this logical change (explicit paths), then commit |
| Only untracked files | Prompt for inclusion      |
| Mixed changes        | Stage by logical group; ask which files belong together (never `git add -i`) |
| No changes           | Report clean state        |

## Commit Rules

- Imperative mood: "add" not "added"
- First line: max 72 characters
- Atomic commits: single logical change
- No period at end of subject line
- Capitalize first letter of subject
- Focus on "why" not "what" -- the diff shows what changed
- Stage only the files this change touches (explicit paths); NEVER a blanket `git add .` / `git add -A` / `git add <dir>` -- it can sweep in unrelated changes or another session's work

### When to Split Commits
- Different features or fixes
- Mixed types (feat + fix)
- Unrelated file changes
- Large changes (>100 lines)
- Different modules/packages

## Options

| Option          | Description                | Behavior                  |
|-----------------|----------------------------|---------------------------|
| `--all`         | Stage all changes          | Everything incl. untracked -- use only when all changes belong in one commit |
| `--staged`      | Commit only staged         | Ignores unstaged changes  |
| `--modified`    | Stage modified only        | Excludes untracked files  |
| `--no-verify`   | Skip pre-commit hooks      | Bypass Husky checks       |
| `--amend`       | Modify last commit         | Edit previous commit      |
| `--push`        | Commit, then push          | Confirms before pushing to a default branch |
| `--wip`         | Work in progress           | Quick WIP commit          |
