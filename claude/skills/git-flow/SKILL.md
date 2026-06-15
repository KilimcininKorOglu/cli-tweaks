---
name: git-flow
description: >
  This skill MUST be invoked when the user says "git flow", "git-flow",
  "branch aç", "feature başlat", "feature start", "bugfix", "hotfix",
  "release branch", "branch oluştur", "create branch" or any variation
  requesting git branch workflow management. SHOULD also invoke when user
  mentions "finish branch", "merge feature", "complete hotfix", or asks
  to follow git-flow branching strategy. Manages git branches following
  a structured workflow with automatic base branch detection and strict
  validation rules.
argument-hint: "<command> <name> [--no-checkout]"
---

# Git Flow

Manage git branches following a structured workflow with strict validation.

## Usage

```bash
/git-flow feature <name>       # Create feature branch from development
/git-flow bugfix <name>        # Create bugfix branch from development
/git-flow hotfix <name>        # Create hotfix branch from master/main
/git-flow release <version>    # Create release branch from development
/git-flow finish               # Merge current branch to appropriate target
/git-flow status               # Show current branch status and rules
```

## Branch Rules (STRICT)

| Branch Type | Base Branch | Merge Target | Additional |
|-------------|-------------|--------------|------------|
| feature/*   | development | development  | -          |
| bugfix/*    | development | development  | -          |
| hotfix/*    | master/main | master/main  | Also merge to development |
| release/*   | development | master/main  | Also merge to development + tag |

CRITICAL: If attempting to create a branch from wrong base, STOP and show error. Do NOT proceed.

## Context Gathering (MANDATORY FIRST STEP)

Before any operation, gather repository context:

```bash
git status                     # Current state
git branch -a                  # All branches (local + remote)
git branch --show-current      # Current branch name
git remote -v                  # Remote configuration
```

## Auto-Detection Logic

Detect production and development branches automatically:

1. Production branch (in order of priority):
   - `master` if exists
   - `main` if exists
   - Ask user if neither exists

2. Development branch (in order of priority):
   - `development` if exists
   - `develop` if exists
   - `dev` if exists
   - Ask user if none exists

## Commands

### Create Command Preconditions

These apply to every create command (feature/bugfix/hotfix/release) below:

- **Clean working tree required.** If there are uncommitted changes, STOP and ask the user to commit or stash first -- `git checkout <base>` would otherwise fail or carry the changes onto the new branch.
- **Remote is optional.** If the base branch has no configured remote (`git remote -v` is empty), skip `git pull origin <base>` and create from the local base -- a missing remote must never abort branch creation (local-only repositories are valid).
- **`--no-checkout`.** Do not switch branches at all: skip both the `git checkout <base>` and its on-branch `git pull`. Instead update the base ref without moving HEAD, then create from it: `git fetch origin <base>` followed by `git branch <new-branch> origin/<base>` when a remote exists, or just `git branch <new-branch> <base>` for a local-only base.

### feature <name>

Create a new feature branch from development branch.

```bash
# Validation
1. Check current branches exist
2. Verify development branch exists
3. Ensure not already on a feature branch with same name

# Execution
git checkout <development-branch>
git pull origin <development-branch>
git checkout -b feature/<name>
```

Example: `/git-flow feature user-authentication`
Creates: `feature/user-authentication` from `development`

### bugfix <name>

Create a new bugfix branch from development branch.

```bash
# Validation
1. Check current branches exist
2. Verify development branch exists

# Execution
git checkout <development-branch>
git pull origin <development-branch>
git checkout -b bugfix/<name>
```

Example: `/git-flow bugfix fix-login-error`
Creates: `bugfix/fix-login-error` from `development`

### hotfix <name>

Create a new hotfix branch from production branch (master/main).

```bash
# Validation
1. Check current branches exist
2. Verify production branch exists

# Execution
git checkout <production-branch>
git pull origin <production-branch>
git checkout -b hotfix/<name>
```

Example: `/git-flow hotfix critical-security-patch`
Creates: `hotfix/critical-security-patch` from `master`

### release <version>

Create a new release branch from development branch.

```bash
# Validation
1. Check current branches exist
2. Verify development branch exists
3. Validate version format (should start with v or be semver)

# Execution
git checkout <development-branch>
git pull origin <development-branch>
git checkout -b release/<version>
```

Example: `/git-flow release v1.2.0`
Creates: `release/v1.2.0` from `development`

### finish

Merge current branch to appropriate target(s) based on branch type.

```bash
# Detection
1. Get current branch name
2. Determine branch type (feature/bugfix/hotfix/release)
3. Identify merge target(s)

# Execution varies by type:
```

| Current Branch | Actions |
|----------------|---------|
| feature/* | Checkout development → Merge feature (`--no-ff`) → Delete feature branch |
| bugfix/* | Checkout development → Merge bugfix (`--no-ff`) → Delete bugfix branch |
| hotfix/* | Checkout master → Merge hotfix (`--no-ff`) → Checkout development → Merge hotfix (`--no-ff`) → Delete hotfix branch |
| release/* | Checkout master → Merge release (`--no-ff`) → Tag version → Checkout development → Merge release (`--no-ff`) → Delete release branch |

Before merge:
- Ensure working tree is clean
- Pull latest from target branch (skip if the target has no remote)
- Check for potential conflicts

On conflict or a failed merge:
- STOP -- do NOT delete the source branch (its commits are not yet safely in the target)
- For hotfix/release (two targets): if the SECOND merge (to development) conflicts, the change is now in master but not yet in development -- resolve the conflict and complete the development merge before deleting
- Resolve conflicts manually, then re-run finish

After merge:
- Verify every merge was successful
- Report what was merged where
- Remind the user to push the updated target branch(es): development for feature/bugfix; both master and development for hotfix/release
- For release: also remind to push the tag (`git push origin <tag>`, or `git push --tags`)

### status

Show current branch information and applicable rules.

```bash
git branch --show-current
git log --oneline -5
git status
```

Output includes:
- Current branch name and type
- Base branch it should have come from
- Target branch for finish
- Any pending changes

## Validation Rules

NEVER proceed if:
- The base branch does not match the Branch Rules table above (e.g. creating a hotfix from development, or a feature/bugfix from master/main)
- Branch with same name already exists
- Working tree has uncommitted changes (any create or finish command)

## Options

| Option | Description |
|--------|-------------|
| `--no-checkout` | Create branch but stay on current branch |

## Safety Protocol

- NEVER force push
- NEVER delete remote branches automatically
- NEVER skip conflict resolution
- Always merge with `--no-ff` -- the merge commit preserves the branch's history, which is what makes deleting the source branch safe
- Always pull before creating a new branch when the base branch has a remote (skip the pull on local-only repositories)
- Always verify merge success before deleting source branch

## Notes

- Branch names should be kebab-case (e.g., `user-authentication` not `userAuthentication`)
- Version tags should follow semver (e.g., `v1.2.0`)
- After finish, user should manually push changes
- Conflicts must be resolved manually before finish can complete
- IMPORTANT: Always write output in English only, regardless of conversation language
