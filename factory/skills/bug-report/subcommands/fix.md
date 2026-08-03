# Bug Fix Workflow

## Command

```bash
/bug-report fix                  # batch: every open bug in BUG-REPORT.md
/bug-report fix BUG-042          # single bug, selected by ID
/bug-report fix "<description>"  # single bug, described in your own words
```

Fixes bugs recorded in `BUG-REPORT.md`. With no argument it works through every
open bug one at a time: verify, plan, approve, fix, verify, commit, then move to
the next. Each bug is fully resolved and committed before the next one is
started.

---

## What To Do Right Now

Parse the user's argument and follow exactly ONE of these paths:

| Argument | Path |
|----------|------|
| none | Batch mode |
| matches `BUG-<number>` (case-insensitive) | Single-bug mode |
| any other text | Free-text mode, which resolves to one of the two above |

### No argument, batch mode

1. Read `BUG-REPORT.md`. Collect every finding whose `Status:` is `NEW` or `OPEN`, in the order they appear. The report is severity-sorted, so this is CRITICAL first.
2. If zero NEW/OPEN findings exist, tell the user and STOP.
3. Write the queue down as a numbered ledger before touching any code (see the Batch Continuation Contract below). The ledger is binding for the rest of the run.
4. Work through the collected bugs ONE AT A TIME, in that order. For each bug, run Phase 1 through Phase 7 to completion before starting the next bug. Never batch, parallelize, or reorder them.
5. Phase 2C requires explicit user approval before Phase 3 starts ONLY for architectural fixes (see Phase 2C for the definition). Non-architectural fixes proceed directly without plan-mode approval. In batch mode, when approval is required, get it for each bug separately.
6. After the last bug, print the Final Summary at the end of this file.

### BUG-ID provided, single-bug mode

Run Phase 1 through Phase 7 for that one bug, print its per-bug report, and STOP. Do not touch any other bug.

### Free text provided, resolve then fix

The user described a bug in prose instead of naming an ID. Resolve the text to a
target BEFORE any code change, and say out loud which target you resolved to.

1. If `BUG-REPORT.md` exists, read it and score every `NEW`/`OPEN` finding
   against the user's text, comparing against the title, `Problem:`, `File:`,
   and `Component:` fields.
2. **Exactly one clear match** — announce `Matched BUG-<ID>: <title>` with the
   one-line reason it matched, then run single-bug mode for that ID.
3. **Several plausible matches** — do NOT guess. Use `AskUser` to let the
   user pick the intended finding, then run single-bug mode for the chosen ID.
4. **No match, or no `BUG-REPORT.md`** — run ad-hoc mode below.

#### Ad-hoc mode (the described bug is not in the report)

The user's text IS the bug statement; there is no report entry to read.

1. Replace Phase 1 with a triage step: locate the defect in the codebase from the
   description. Search for the named symptom, surface, file, or component.
2. State what you believe the defect is, in the same shape Phase 2A requires:
   exact current behavior, exact expected behavior, and the files and functions
   that prove it exists.
3. If you cannot locate the defect, or the description matches several unrelated
   code paths, STOP and ask the user for the missing detail. NEVER guess a target
   and NEVER fix something the user did not describe.
4. Then run Phase 2A through Phase 5 unchanged.
5. Phase 6 is conditional in this mode:
   - If `BUG-REPORT.md` exists, append a new finding in the canonical report
     format, allocate the next ID from the report's `Last Bug ID:` field, update
     that field, and set `Status: FIXED`.
   - If `BUG-REPORT.md` does NOT exist, skip Phase 6 entirely. NEVER create the
     report file.
6. Print the per-bug report and STOP. Ad-hoc mode fixes exactly the one described
   defect; it never continues into the rest of the report.

---

## Batch Continuation Contract (batch mode only)

Batch mode has ONE failure worth naming: stopping early. Fixing three bugs and
ending the turn is a failed run, not a partial success. This section is the
contract that prevents it.

**Write the ledger first.** Before Phase 0 of the first bug, print the full queue
and keep it as the run's state:

```
Fix queue (N total)
1. BUG-007 — <title>   [pending]
2. BUG-012 — <title>   [pending]
...
```

**Restate progress after every bug.** At the end of each Phase 7, print one line:
`Progress: i/N complete · next: BUG-<ID>` (or `next: none, printing Final
Summary`). This line is mandatory; it is what keeps the queue alive across a long
run.

**NEVER end your turn while the ledger still has a `[pending]` entry.** A batch
run ends by itself in exactly ONE case: every ledger entry is `[fixed]` or
`[skipped]`, and you print the Final Summary. The user explicitly telling you to
stop also ends it. Ad-hoc and free-text mode are single-bug by definition and
never enter this contract.

**Everything else that prevents progress is a BLOCKER, not an ending.** On a
blocker, ask the user how to proceed with `AskUser` and wait for the
answer. Do NOT end the run, and do NOT silently abandon the remaining queue.
Blockers include:

- Phase 0 found uncommitted changes that this run did not create. Show them and
  ask whether to stash them, leave them and skip the affected bug, or abort.
- The current bug cannot be located, or its plan was rejected with no clear
  alternative. Ask what to do with that one entry, apply the answer, then carry
  on with the rest of the ledger.
- A repository gate or tool fails in a way the report does not cover and you
  cannot resolve from the code.

After the user answers a blocker, resume the ledger from the next `[pending]`
entry. A blocker affects at most the current bug; it never cancels the queue.

Nothing else qualifies. In particular, these are NOT stopping points:

- **A finished per-bug report.** Phase 7 output is a checkpoint, not an ending.
  Continue to the next bug in the SAME turn.
- **A plan approval round-trip.** When Phase 2C approval ends a turn, your VERY
  FIRST action in the next turn is to resume that bug's Phase 3, then continue
  the ledger. Do not re-plan finished work and do not restart the queue.
- **A skipped or failed bug.** A failed verification (Phase 4) or a rejected plan
  affects that bug only. Mark it `[skipped]` with its reason and move to the next
  entry immediately.
- **A long run.** Bug count, elapsed work, or context pressure are never reasons
  to stop. If context is tight, re-read `BUG-REPORT.md` and the ledger rather
  than ending the run.

**NEVER ask whether to continue.** Do not ask "should I keep going?", "want me to
fix the next one?", or any variant. The user already asked for every open bug by
invoking batch mode. Asking is the same failure as stopping.

Keep the two kinds of question apart:

| Question | Rule |
|----------|------|
| Queue progression ("continue?", "next one?") | FORBIDDEN — just continue |
| Blocker resolution ("this tree is dirty, stash or skip?") | REQUIRED — ask and wait |

The ban is on asking for permission to do what was already requested. It is not a
ban on asking for a decision you genuinely cannot make.

If a turn ends for any reason outside your control, treat resuming the next
`[pending]` ledger entry as the first action of the next turn, with no new
confirmation.

---

## Phase 0: Start Clean

Before reading or editing the current bug, inspect the working tree.

Hard constraints:
- Continue only from a clean working tree, or from a tree that contains only explicitly allowed report/status edits from earlier completed bugs.
- If unrelated changed files exist, do not overwrite or stage them. In single-bug and ad-hoc mode, report them and STOP. In batch mode this is a blocker, not an ending: report them and ask the user how to proceed, then resume the ledger with their answer.
- Do not start a new bug while a previous bug has uncommitted code changes.
- The uncommitted `BUG-REPORT.md` status edits produced by earlier bugs in THIS run are expected and allowed. They are never a reason to stop the run; only changes this run did not create qualify.

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

## Phase 2C: Pre-Fix Gate in Droid Spec Mode

Enter Droid spec mode before Phase 3 ONLY when the fix involves an
architectural change. For a localized, non-architectural fix, skip spec mode and
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
directly; do not enter spec mode.

When in doubt about whether a fix is architectural, treat it as architectural
and enter spec mode.

When spec mode is required, follow this exact three-step tool sequence. Do not
use `AskUser` for plan approval.

1. Call the `EnterSpecMode` tool to enter spec mode.
2. Write the full plan to the spec file that spec mode designates. The plan is
   read from that file, not from your chat message, so it MUST be written to the
   file. Do not present the plan only as chat text.
3. Call the `ExitSpecMode` tool to request approval. It reads the plan from the
   spec file and shows it to the user. Only proceed to Phase 3 after the user
   approves.

The plan written to the spec file must include these sections:
- Confirmed current defect.
- Product-context assessment.
- Affected paths.
- Callers and consumers.
- UI, API, storage, and runtime impact.
- Minimal implementation boundary.
- Refactor assessment.
- Validation gates.
- Rollback plan.

Hard pre-edit gate (applies ONLY when spec mode is required):
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

Then mark this bug `[fixed]` or `[skipped]` in the ledger and print the mandatory
progress line:

```
Progress: i/N complete · next: BUG-<ID>
```

In batch mode, immediately begin Phase 0 of that next bug in the SAME turn. Do
not stop, do not summarize the run so far, and do not ask whether to continue.
The per-bug report you just printed is a checkpoint, not an ending. Only when the
ledger has no `[pending]` entry left do you print the Final Summary instead.

In single-bug mode and ad-hoc mode, STOP here.

---

## Final Summary

After the last bug in batch mode, print a summary:
- Total bugs processed.
- Fixed and committed bugs, listed by BUG-ID.
- Skipped bugs, each with its reason.
- Any required project gates that still have known baseline failures.
- A reminder that report status edits may be unstaged or ignored according to report rules, and that skipped bugs are still NEW/OPEN for a later run.
