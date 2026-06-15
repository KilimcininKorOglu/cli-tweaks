# Bug Fix Workflow

## Command

```bash
/bug-report fix [BUG-ID] [--dry-run]
```

---

## What To Do Right Now

Parse the user's command and follow exactly ONE of these paths:

### No BUG-ID provided

1. Read `BUG-REPORT.md`. Find every finding where `Status: NEW` or `Status: OPEN`.
2. If zero NEW/OPEN findings exist, tell the user and STOP.
3. Present a numbered list: `BUG-ID | Severity | First line of Problem`.
4. Ask the user which one to fix. Wait for answer.
5. Once the user picks one, continue to **Phase 1** below with that BUG-ID.

### BUG-ID provided

Continue to **Phase 1** below with the given BUG-ID.

### --dry-run flag

Run Phase 1 and Phase 2 only. Report what you would change. Do NOT edit any file. STOP after Phase 2.

---

## Phase 1: Read the Bug

Read `BUG-REPORT.md`. Find the `### BUG-[ID]` entry. Read every field: Severity, Status, File, Component, Suggested Commit, Problem, Expected, Root Cause, Impact, Verification.

If Status is already FIXED, tell the user and STOP.

---

## Phase 2: Trace the Code and Plan the Fix

Read every file path listed in the `File:` field. Read any file referenced in `Root Cause:` or `Problem:`. Follow the call chain from the entry point to the bug location.

Do NOT trust your memory of file contents. Re-read before editing. Always.

Once you understand the root cause, present a short fix plan to the user and wait for approval:

> Root cause: [one sentence]. Proposed change: [file(s) and line(s), what edit]. Minimal because: [no refactoring, no scope creep].

Do NOT proceed to Phase 3 until the user approves the plan. If the fix would require restructuring other code or touching unrelated files, STOP and ask the user first.

---

## Phase 3: Fix

Make the minimal change that resolves the root cause. One change, one purpose.

**Hard constraints:**
- Do NOT touch any line that is not directly related to the bug
- Do NOT reformat surrounding code
- Do NOT reorder imports
- Do NOT rename variables
- Do NOT add "while I'm here" improvements
- If the fix requires restructuring other code, STOP and ask the user first

---

## Phase 4: Verify

Run the verification steps described in the finding's `Verification:` field.

Then run the project's build/lint/test commands. Examples:
- Type check: `npx tsc --noEmit` or equivalent
- Lint: `npx eslint . --quiet` or equivalent
- Tests: the project's test runner for affected files

If any check fails, fix the issue before proceeding. Do NOT skip verification.

---

## Phase 5: Commit

Create a single commit for this one bug fix. The commit message:
- Uses conventional commit format: `fix: <what was fixed>`
- Describes WHAT was fixed and WHY
- NEVER includes any bug ID (no BUG-001, no BUG-xxx)

One bug = one commit. No exceptions.

---

## Phase 6: Update Report

Open `BUG-REPORT.md`. Change the bug's status line from `Status: NEW` or `Status: OPEN` to:
```
Status: FIXED
```

Do NOT commit this change together with the fix. Leave it as an unstaged change.

---

## Phase 7: Report

Tell the user exactly:
- Which bug was fixed (ID + title)
- What the root cause was (1 sentence)
- What changed (file paths and line numbers)
- Verification result (pass/fail)

STOP. Do not proceed to the next bug unless the user explicitly asks.
