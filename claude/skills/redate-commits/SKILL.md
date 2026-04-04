---
name: redate-commits
description: >
  This skill MUST be invoked when the user says
  "commit tarihlerini değiştir", "redate commits",
  "spread commits", "backdate" or any variation requesting git commit
  date rewriting across a date range. Rewrites both author and committer
  dates using git filter-branch, distributing commits realistically
  across the specified period.
argument-hint: "<start-date> <end-date> [--weekdays-only | --include-weekends | --weighted-weekdays]"
---

# Redate Commits

Rewrites git commit dates to distribute them across a specified date range, making the history appear as if development occurred over that period.

## Usage

```bash
/redate-commits 2026-02-01 2026-03-31              # Default: weighted weekdays
/redate-commits 2026-01-01 2026-06-30 --weekdays-only
/redate-commits 2026-02-01 2026-03-31 --include-weekends
```

## Context Gathering (MANDATORY FIRST STEP)

Before doing anything, gather the commit history:

```bash
git log --oneline --format="%H %ai %s" | head -20   # Recent commits with dates
git log --oneline | wc -l                             # Total commit count
git log --reverse --format="%H %s" | head -5          # Oldest commits
git log --reverse --format="%H %s" | tail -5          # Newest commits
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `start-date` | First date (YYYY-MM-DD) | Required |
| `end-date` | Last date (YYYY-MM-DD) | Required |
| `--weekdays-only` | Mon-Fri only | No |
| `--include-weekends` | All 7 days equally | No |
| `--weighted-weekdays` | Heavy weekdays, light weekends | Yes (default) |

## Distribution Strategy

### Weighted Weekdays (Default)
- Weekdays: 1-3 commits per day, working hours (09:00-18:00)
- Weekends: occasional 1 commit (roughly 1 in 3 weekends)
- Most realistic for a solo developer

### Grouping Logic
Commits should be grouped by feature/topic, not randomly scattered. Related commits (same feature branch, same module) should land on the same day or consecutive days.

Analyze commit messages to identify logical groups:
- `feat(T001-T005)` → same feature, same day or 2 days
- `Merge feature/F001` → day after the feature commits
- `chore:`, `docs:` → standalone, can fill gaps
- `fix:` → day after the related `feat:`

### Time Distribution Within a Day
- First commit: 09:00-10:30
- Second commit: 13:00-15:00
- Third commit: 15:30-17:00
- Vary minutes randomly (not exactly on the hour)

## Implementation

### Step 1: Collect Commits
```bash
git log --reverse --format="%H %s"
```

### Step 2: Generate Date Mapping
Create a Python script that:
1. Lists all commit hashes in chronological order
2. Groups them by feature/topic based on commit messages
3. Assigns dates from the range, respecting grouping
4. Writes a shell filter script

### Step 3: Apply with filter-branch
```bash
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --env-filter "$(cat /tmp/git_date_filter.sh)" \
  -- --all
```

The filter script format:
```bash
if [ "$GIT_COMMIT" = "<hash>" ]; then
  export GIT_AUTHOR_DATE="<date>"
  export GIT_COMMITTER_DATE="<date>"
fi
```

### Step 4: Clean Up
```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Step 5: Force Push (only if user confirms)
```bash
git push --force
```

## Safety Protocol

- **ALWAYS** show the planned date distribution BEFORE applying
- **ALWAYS** warn that this operation rewrites ALL commit hashes
- **ALWAYS** warn that force push will be needed
- **NEVER** automatically force push — ask the user first
- **NEVER** run on a shared branch without explicit user confirmation
- If `filter-branch` fails, the original refs are preserved in `refs/original/`

## Troubleshooting

### macOS: `declare -A` not supported
Use Python for the date mapping script, not bash associative arrays. macOS default shell (zsh) has issues with `declare -A` in heredocs.

### filter-branch snapshot error
If Docker was built from the repo, stale image layers can cause snapshot errors. Run:
```bash
docker compose build --no-cache
```

### Verify Results
```bash
# Check first and last commit dates
git log --format="%ai %s" | tail -1    # Should be start-date
git log --format="%ai %s" | head -1    # Should be end-date

# Check weekend distribution
git log --format="%ad" --date=format:"%u %Y-%m-%d" | sort | uniq -c
# Column 1 = count, Column 2 = day-of-week (1=Mon, 7=Sun)
```
