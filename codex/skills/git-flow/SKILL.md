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
---

# Git Flow

Manage git branches following a structured workflow with strict validation.

## Usage

```bash
$git-flow feature <name>       # Create feature branch from development
$git-flow bugfix <name>        # Create bugfix branch from development
$git-flow hotfix <name>        # Create hotfix branch from master/main
$git-flow release <version>    # Create release branch from development
$git-flow finish               # Merge current branch to appropriate target
$git-flow status               # Show current branch status and rules
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

Example: `$git-flow feature user-authentication`
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

Example: `$git-flow bugfix fix-login-error`
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

Example: `$git-flow hotfix critical-security-patch`
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

Example: `$git-flow release v1.2.0`
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
| feature/* | Checkout development -> Merge feature -> Delete feature branch |
| bugfix/* | Checkout development -> Merge bugfix -> Delete bugfix branch |
| hotfix/* | Checkout master -> Merge hotfix -> Checkout development -> Merge hotfix -> Delete hotfix branch |
| release/* | Checkout master -> Merge release -> Tag version -> Checkout development -> Merge release -> Delete release branch |

Before merge:
- Ensure working tree is clean
- Pull latest from target branch
- Check for potential conflicts

After merge:
- Verify merge was successful
- Report what was merged where
- For hotfix/release: remind to push both branches

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
- Attempting to create feature/bugfix from master/main (must be from development)
- Attempting to create hotfix from development (must be from master/main)
- Branch with same name already exists
- Working tree has uncommitted changes (for finish command)

## Options

| Option | Description |
|--------|-------------|
| `--no-checkout` | Create branch but stay on current branch |

## Safety Protocol

- NEVER force push
- NEVER delete remote branches automatically
- NEVER skip conflict resolution
- Always pull before creating new branch
- Always verify merge success before deleting source branch

## Notes

- Branch names should be kebab-case (e.g., `user-authentication` not `userAuthentication`)
- Version tags should follow semver (e.g., `v1.2.0`)
- After finish, user should manually push changes
- Conflicts must be resolved manually before finish can complete
- IMPORTANT: Always write output in English only, regardless of conversation language
