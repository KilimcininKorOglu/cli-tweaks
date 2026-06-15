# Bug Fix Workflow

## Command

```bash
/bug-report fix [BUG-ID] [--dry-run]
```

Fixes bugs recorded in `BUG-REPORT.md`. With no BUG-ID it works through every
open bug one at a time — plan, approve, fix, verify, commit — then moves to the
next. Each bug is fully resolved and committed before the next one is started.

---

## What To Do Right Now

Parse the user's command and follow exactly ONE of these paths:

### No BUG-ID provided (batch mode — process every open bug)

1. Read `BUG-REPORT.md`. Collect every finding whose `Status:` is `NEW` or `OPEN`, in the order they appear (the report is severity-sorted, so this is CRITICAL first).
2. If zero NEW/OPEN findings exist, tell the user and STOP.
3. Work through the collected bugs ONE AT A TIME, in that order. For each bug, run Phase 1 -> Phase 6 to completion before starting the next bug. Never batch, parallelize, or reorder them.
4. After the last bug, print the **Final Summary** at the end of this file.

### BUG-ID provided (single-bug mode)

Run Phase 1 -> Phase 6 for that one bug, print its per-bug report, and STOP. Do not touch any other bug.

### --dry-run flag

Iterate every NEW/OPEN bug and run **Phase 1 and Phase 2 only** for each — show every fix plan. Do NOT edit any file, commit, or change any status. STOP after the last plan.

---

## Phase 1: Read the Bug

Read `BUG-REPORT.md`. Find the `### BUG-[ID]` entry for the current bug. Read every field: Severity, Status, File, Component, Suggested Commit, Problem, Expected, Root Cause, Impact, Verification.

If this bug's Status is already `FIXED`, skip it: continue to the next bug in batch mode, or STOP in single-bug mode.

---

## Phase 2: Trace the Code and Plan the Fix

Read every file path listed in the `File:` field. Read any file referenced in `Root Cause:` or `Problem:`. Follow the call chain from the entry point to the bug location.

Do NOT trust your memory of file contents. Re-read before editing. Always.

Once you understand the root cause, use the agent's built-in plan mode (`ExitPlanMode`) to present a minimal fix plan for THIS bug: root cause in one sentence, the exact file(s) and line(s) to change, and why it is minimal (no refactoring, no scope creep).

Do NOT proceed to Phase 3 until the user approves this bug's plan. If the user rejects it, skip this bug — nothing has been edited yet — and move to the next one. If the fix would require restructuring other code or touching unrelated files, say so in the plan and let the user decide.

---

## Phase 3: Fix

Make the minimal change that resolves the root cause. One change, one purpose.

**Hard constraints:**
- Do NOT touch any line that is not directly related to the bug
- Do NOT reformat surrounding code
- Do NOT reorder imports
- Do NOT rename variables
- Do NOT add "while I'm here" improvements
- If the fix turns out to require restructuring other code, treat it as a failed fix: revert this bug's edits (Phase 4 skip procedure) and move on

---

## Phase 4: Verify

Run the verification steps described in the finding's `Verification:` field.

Then run the project's build/lint/test commands. Examples:
- Type check: `npx tsc --noEmit` or equivalent
- Lint: `npx eslint . --quiet` or equivalent
- Tests: the project's test runner for affected files

**If every check passes,** continue to Phase 5.

**If any check fails,** do NOT commit a broken fix. Instead:
1. Revert ONLY this bug's edits — restore the exact files you changed in Phase 3 to their pre-fix state (e.g. `git restore <those paths>`; delete any new file this fix created). Do not touch other files or earlier commits.
2. Leave this bug's Status unchanged (still NEW/OPEN).
3. Record it as **skipped**, with the failing check as the reason.
4. Continue to the next bug — it must start from a clean working tree.

In single-bug mode, report the failure and STOP instead of continuing.

---

## Phase 5: Commit

Create a single commit for THIS one bug fix.

- Stage ONLY the files you changed for this bug: `git add <those exact paths>`. NEVER `git add -A`, `git add .`, or `git commit -am` — that would sweep in another bug's leftovers or unrelated changes.
- Commit message uses conventional format: `fix: <what was fixed>`
- Describe WHAT was fixed and WHY
- NEVER include any bug ID (no BUG-001, no BUG-xxx)

One bug = one commit. No exceptions.

---

## Phase 6: Update Report

Open `BUG-REPORT.md`. Change this bug's status line from `Status: NEW` or `Status: OPEN` to:
```
Status: FIXED
```

`BUG-REPORT.md` is gitignored and cannot be committed — this status edit just stays in the working tree and never enters any commit. Do not stage it, and do not let it block the next bug.

---

## Phase 7: Per-Bug Report, Then Continue

After each bug, tell the user:
- Which bug was handled (ID + title)
- Outcome: FIXED (committed) or SKIPPED (reason)
- Root cause (1 sentence)
- What changed (file paths and line numbers), or what was reverted
- Verification result (pass/fail)

Then proceed to the next bug in batch mode. In single-bug mode, STOP here.

---

## Final Summary

After the last bug in batch mode, print a summary:
- Total bugs processed
- **Fixed** (committed): list of BUG-IDs
- **Skipped**: list of BUG-IDs, each with its reason (verification failure, plan rejected, restructuring required, etc.)
- Remind the user that `BUG-REPORT.md` status edits are unstaged (it is gitignored) and that skipped bugs are still NEW/OPEN for a later run.
