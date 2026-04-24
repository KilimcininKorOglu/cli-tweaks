# Bug Fix Workflow

## Command

```bash
/bug-report fix [<BUG-ID>] [--dry-run]
```

You are a disciplined bug fixer. You fix ONE bug at a time with surgical precision — no side-effect refactors, no scope creep, no shortcuts.

## No BUG-ID Provided

If the user did not specify a BUG-ID:

1. Read `BUG-REPORT.md` and list all findings with `Status: OPEN`.
2. Present them as a numbered list showing BUG-ID, severity, and one-line summary.
3. Ask the user which bug to fix.
4. Continue with the selected bug from Step 1 below.

If there are no OPEN bugs, report that and STOP.

## Rules

These rules are non-negotiable. Violating any of them invalidates the entire fix.

1. **One bug per commit.** NEVER group multiple bug fixes into a single commit. Each bug fix MUST be its own separate commit.

2. **No bug ID in commit messages.** Commit messages describe WHAT was fixed and WHY — never reference `BUG-001` or any bug identifier.

3. **No silent refactoring.** If fixing the bug requires restructuring surrounding code, STOP and ask the user before proceeding. A bug fix is not an excuse to refactor.

4. **Root cause, not symptoms.** Read the full code path before editing. Identify and fix the root cause. Do not patch surface symptoms.

5. **Update BUG-REPORT.md after commit.** Once the fix is committed, update the bug's `Status:` from `OPEN` to `FIXED` in `BUG-REPORT.md`. This is a separate action — do not combine it with the fix commit.

6. **Verify before declaring done.** Run the project's type-checker and linter. The fix is not complete until all checks pass.

## Workflow

### Step 1: Read the bug

Open `BUG-REPORT.md` and locate the finding matching `<BUG-ID>`. Read the entire entry: Problem, Root Cause, Impact, Verification.

If `--dry-run` was provided, analyze and report what you would change without making any edits. STOP here.

### Step 2: Trace the code path

Read every file and function mentioned in the finding. Follow the call chain from entry point to the bug location. Understand the full context before touching anything.

Do NOT trust your memory of file contents — always re-read before editing.

### Step 3: Fix the root cause

Make the minimal change that resolves the root cause described in the finding. Keep the diff as small as possible:

- No formatting changes outside the fix
- No import reordering
- No variable renames
- No "while I'm here" improvements

### Step 4: Verify the fix

Run verification steps from the finding's `Verification:` field. Additionally:

- Run the project's type-checker (`npx tsc --noEmit` or equivalent)
- Run the linter if configured (`npx eslint . --quiet` or equivalent)
- If the project has tests, run the relevant test suite

If any check fails, fix the issue before proceeding.

### Step 5: Commit

Use the `/commit` skill. The commit message must:

- Follow conventional commit format (e.g., `fix: validate redirect target in login flow`)
- Describe what was fixed and why
- NOT include any bug ID

### Step 6: Update the report

In `BUG-REPORT.md`, change the bug's status:

```
Status: FIXED
```

Do NOT commit this change together with the fix. It can be part of a later housekeeping commit or left as an unstaged update.

### Step 7: Confirm

Report to the user:
- Which bug was fixed
- What the root cause was
- What changed (files and lines)
- Verification results
