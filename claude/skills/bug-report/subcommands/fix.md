# Bug Fix Workflow

## Command

```bash
/bug-report fix [BUG-ID]
```

Fixes bugs recorded in `BUG-REPORT.md`. With no BUG-ID it works through every
open bug one at a time: verify, plan, approve, fix, verify, commit, then move to
the next. Each bug is fully resolved and committed before the next one is
started.

---

## What To Do Right Now

Parse the user's command and follow exactly ONE of these paths:

### No BUG-ID provided, batch mode

1. Read `BUG-REPORT.md`. Collect every finding whose `Status:` is `NEW` or `OPEN`, in the order they appear. The report is severity-sorted, so this is CRITICAL first.
2. If zero NEW/OPEN findings exist, tell the user and STOP.
3. Work through the collected bugs ONE AT A TIME, in that order. For each bug, run Phase 1 through Phase 7 to completion before starting the next bug. Never batch, parallelize, or reorder them.
4. Phase 2C requires explicit user approval before Phase 3 starts ONLY for architectural fixes (see Phase 2C for the definition). Non-architectural fixes proceed directly without plan-mode approval. In batch mode, when approval is required, get it for each bug separately.
5. After the last bug, print the Final Summary at the end of this file.

### BUG-ID provided, single-bug mode

Run Phase 1 through Phase 7 for that one bug, print its per-bug report, and STOP. Do not touch any other bug.

---

## Phase 0: Start Clean

Before reading or editing the current bug, inspect the working tree.

Hard constraints:
- Continue only from a clean working tree, or from a tree that contains only explicitly allowed report/status edits from earlier completed bugs.
- If unrelated changed files exist, STOP and report them. Do not overwrite or stage them.
- Do not start a new bug while a previous bug has uncommitted code changes.

---

## Phase 1: Read the Bug

Read `BUG-REPORT.md`. Find the `### BUG-[ID]` entry for the current bug. Read every field: Severity, Status, File, Component, Suggested Commit, Problem, Expected, Root Cause, Impact, Verification.

If this bug's Status is already `FIXED`, skip it: continue to the next bug in batch mode, or STOP in single-bug mode.

---

## Phase 2A: Verify the Defect Still Exists

Read every file path listed in the `File:` field. Read any file referenced in `Root Cause:`, `Problem:`, `Expected:`, `Impact:`, or `Verification:`. Follow the call chain from the entry point to the bug location.

Do NOT trust your memory of file contents. Re-read before editing. Always.

Before planning a fix, confirm that the reported defect still exists in the current code path.

Write a short defect confirmation that includes:
- The exact current behavior.
- The exact expected behavior from the report.
- The current files and functions that prove the defect still exists.
- Any part of the report that is stale or no longer accurate.

If the defect no longer exists, do not edit code. Update the bug status only if the report rules allow it, record the skip reason, and continue or stop according to mode.

---

## Phase 2B: Trace Product Context and Affected Paths

Before designing the fix, identify the complete product context.

Required trace:
- Entry points.
- Callers and consumers.
- UI or CLI surfaces.
- API contracts.
- Storage or configuration persistence.
- Runtime consumers such as scripts, services, schedulers, workers, and installers.
- Documentation or OpenAPI contracts that must stay in sync.
- Security and authorization boundaries.

Product-facing configuration must be manageable through the product surface that users or operators actually use. Do not implement a script-only, config-only, or backend-only fix when the setting or behavior must be managed through UI, API, CLI, or another product control plane.

If the fix requires a refactor or a scope expansion beyond the report's suggested commit, state that in the plan. Do not start implementation before approval.

---

## Phase 2C: Pre-Fix Gate in Claude Code Plan Mode

Enter Claude Code plan mode before Phase 3 ONLY when the fix involves an
architectural change. For a localized, non-architectural fix, skip plan mode and
proceed directly to Phase 3.

A fix is architectural when it does any of these:
- Adds or changes a database schema or migration.
- Adds a new dependency, new package, or new service.
- Changes an API contract, request/response shape, or route surface.
- Changes an authentication, authorization, or security boundary.
- Introduces a cross-cutting refactor or spans multiple subsystems.
- Changes storage format, configuration model, or a runtime/install contract.
- Expands scope beyond the report's suggested commit.

A fix is NOT architectural when it is localized and behavior-preserving in
shape: a bounded logic correction, a validation or error-handling fix, a
nil/empty guard, an off-by-one, a wrong-constant fix, or a single-surface change
that touches no schema, contract, dependency, or security boundary. Fix these
directly; do not enter plan mode.

When in doubt about whether a fix is architectural, treat it as architectural
and enter plan mode.

When plan mode is required, follow this exact three-step tool sequence. Do not
use `AskUserQuestion` for plan approval.

1. Call the `EnterPlanMode` tool to enter plan mode.
2. Write the full plan to the plan file that plan mode designates. The plan is
   read from that file, not from your chat message, so it MUST be written to the
   file. Do not present the plan only as chat text.
3. Call the `ExitPlanMode` tool to request approval. It reads the plan from the
   plan file and shows it to the user. Only proceed to Phase 3 after the user
   approves.

The plan written to the plan file must include these sections:
- Confirmed current defect.
- Product-context assessment.
- Affected paths.
- Callers and consumers.
- UI, API, storage, and runtime impact.
- Minimal implementation boundary.
- Refactor assessment.
- Validation gates.
- Rollback plan.

Hard pre-edit gate (applies ONLY when plan mode is required):
- Do not call Edit, Write, NotebookEdit, git add, git commit, or any file-mutating shell command before the plan is approved.
- Do not make partial drafts in project files before approval.
- If the user rejects the plan, do not edit code. If the user asks to skip, mark the bug according to the report rules and continue or stop according to mode.

---

## Phase 3: Fix

Make the minimal complete change that resolves the root cause. Minimal means the smallest end-to-end change that makes the product behavior correct, not the smallest number of edited lines.

Hard constraints:
- Do NOT touch any line that is not directly related to the approved fix.
- Do NOT reformat surrounding code.
- Do NOT rename variables unless the approved fix requires it.
- Do NOT add unrelated improvements.
- Do NOT expand beyond the approved implementation boundary.
- If implementation proves the approved plan incomplete, stop, revert this bug's edits, and return to Phase 2C with a corrected plan.
- If the fix requires restructuring that was not approved, treat it as a failed fix: revert this bug's edits using the Phase 4 skip procedure and move on or stop according to mode.

---

## Phase 4: Verify

Run the verification steps described in the finding's `Verification:` field.

Then run the repository's build, lint, typecheck, and test commands. Discover these commands from repository instructions, Makefiles, package scripts, project configuration, and existing documentation. Do not invent project-specific commands.

Verification must cover:
- The changed unit or focused behavior.
- The affected integration path when practical.
- API or UI contracts touched by the fix.
- Linters and typecheckers required by the repository.
- Security-sensitive behavior when the fix touches authorization, secrets, filesystem, subprocesses, network, or user-controlled input.

If every relevant check passes, continue to Phase 5.

If any check fails, do NOT commit a broken fix. Instead:
1. Revert ONLY this bug's edits. Restore the exact files you changed in Phase 3 to their pre-fix state, and delete any new file this fix created. Do not touch other files or earlier commits.
2. Leave this bug's Status unchanged unless the user explicitly approved a skip status.
3. Record it as skipped, with the failing check or product-context failure as the reason.
4. Continue to the next bug in batch mode only when the working tree is clean.

In single-bug mode, report the failure and STOP instead of continuing.

Known baseline failures may be reported separately only when they are verified to predate the current fix and are unrelated to the changed files. Never claim a fully green gate when any required project gate still fails.

---

## Phase 5: Commit

Create a single commit for THIS one bug fix.

Hard constraints:
- Stage ONLY the files changed for this bug: `git add <exact paths>`.
- NEVER use `git add -A`, `git add .`, or `git commit -am`.
- NEVER stage `BUG-REPORT.md` when it is ignored or when report rules say status edits must remain uncommitted.
- Respect repository commit instructions and commit helper skills when available.
- Commit message uses conventional format: `fix: <what was fixed>` unless the repository requires a more specific conventional scope.
- Describe WHAT was fixed and WHY.
- NEVER include any bug ID.

One bug equals one commit. No exceptions.

---

## Phase 6: Update Report

Open `BUG-REPORT.md`. Change this bug's status line from `Status: NEW` or `Status: OPEN` to:

```text
Status: FIXED
```

`BUG-REPORT.md` may be gitignored or otherwise excluded by report rules. This status edit stays in the working tree when the report rules say it must not be committed. Do not stage it, and do not let it block the next bug.

---

## Phase 7: Per-Bug Report, Then Continue

After each bug, tell the user:
- Which bug was handled, with ID and title.
- Outcome: FIXED and committed, or SKIPPED with reason.
- Root cause in one sentence.
- What changed, with file paths and line numbers, or what was reverted.
- Verification result, including any known baseline failures.
- Whether report status was updated and whether it remains unstaged.

Then proceed to the next bug in batch mode. In single-bug mode, STOP here.

---

## Final Summary

After the last bug in batch mode, print a summary:
- Total bugs processed.
- Fixed and committed bugs, listed by BUG-ID.
- Skipped bugs, each with its reason.
- Any required project gates that still have known baseline failures.
- A reminder that report status edits may be unstaged or ignored according to report rules, and that skipped bugs are still NEW/OPEN for a later run.
