---
name: goal-prep
description: Converts a free-form task description into a verifiable Claude Code /goal completion condition — one measurable end state, a stated check, constraints, and an optional turn/time cap — asking clarifying questions via AskUserQuestion only when a required component is missing. Invoked explicitly as /goal-prep.
user-invocable: true
disable-model-invocation: true
argument-hint: "[serbest metin: yapılmasını istediğin iş]"
---

# Goal Prep — free-form intent → verifiable /goal condition

Convert the user's free-form task description into a well-formed Claude Code `/goal` completion **condition**: one measurable end state, a stated check, the constraints that matter, and an optional turn/time cap. Ask focused questions only when a required component is genuinely missing.

The output is a single `/goal <condition>` command the user can run. This skill prepares the condition; it does not run the goal itself (slash commands are user-initiated).

## The contract you are writing against

A `/goal` condition is judged after every turn by a small evaluator model (Haiku by default). This shapes every rewrite decision:

1. **The evaluator cannot run commands or read files.** It only sees what Claude has surfaced in the conversation transcript. So the condition must require Claude to *produce visible proof* — command output, a printed count, a diff, a status line — not just "do the thing."
2. **The condition describes the desired END state, not the current state or the steps.** "Make the auth tests pass" → the end state is "every test in `test/auth` reports pass in the transcript."
3. **Vague success words have no observable output and WILL fail.** "production-ready", "clean", "robust", "optimized", "well-structured", "fixed", "works" — each must be replaced with a check whose output appears in the conversation.
4. **Limit is 4,000 characters.** Conditions are usually one rich sentence or a short structured block, not an essay.

## How it works

### Phase 1 — Parse the intent

Read the user's text (the argument). Extract whatever is already present of the four components:

| Component            | What it is                                                  | Example signal in user text                  |
|----------------------|-------------------------------------------------------------|----------------------------------------------|
| **End state**        | The one measurable thing that means "done"                   | "all tests pass", "queue empty", "≤ 300 LOC" |
| **Stated check**     | The command/output that proves the end state, in transcript | "`npm test`", "`git status`", "`cargo build`" |
| **Constraints**      | What must NOT change on the way there                   | "don't touch the API", "no new deps"         |
| **Cap** (optional)   | Turn or time bound if the condition might not converge  | "stop after 20 turns", "within ~1 hour"      |

Also resolve **scope**: which files, directories, modules, or items are in play. Ambiguous scope is the most common cause of a meandering goal.

### Phase 2 — Find the blocking gaps

A gap is **blocking** only if the condition cannot be made verifiable without it. Classify:

- **End state missing or vague** → blocking. A goal with no observable finish line burns tokens forever.
- **Stated check missing** → blocking *unless* the end state is self-evidently checkable (e.g. "file `X` exists" needs no command). Prefer an explicit check anyway.
- **Scope ambiguous** → blocking if "the tests" / "the module" / "the errors" could reasonably mean different sets.
- **Constraints unknown** → usually NOT blocking; default to a sensible guard ("change only files required for this goal; do not modify unrelated tests or config") and state the assumption. Ask only if the task obviously risks collateral damage (migrations, refactors, deletes, formatting passes).
- **Cap** → never blocking. Add one proactively for open-ended classes of work ("fix all the flaky tests").

Do NOT ask about anything the user already gave or that is clearly inferable from the repo or the task. Asking for what was already said is the failure mode.

### Phase 3 — Ask, only if blocking gaps remain

If and only if Phase 2 found blocking gaps, call **AskUserQuestion** — once, batched (up to ~4 questions), never drip-fed across turns. Each question targets exactly one gap, with 2–4 concrete options plus room for the user's own answer.

Question templates (use the user's language; keep commands verbatim):

- **End state** — "Bu iş 'bitti' sayılması için gözlemlenebilir hangi sonuç olmalı?" → options like "Tüm testler geçiyor", "Build hatasız (`exit 0`)", "Belirli bir dosya/çıktı üretildi", "Bir sayım sıfırlandı (ör. lint uyarısı = 0)".
- **Check** — "Claude bunu konuşmada nasıl kanıtlasın?" → options like "`npm test` çıktısı", "`<build cmd>` exit code", "`git status` temiz", "Bir komutun stdout'u".
- **Scope** — "Hangi kapsam?" → list the candidate dirs/modules you actually see, plus "Tümü".
- **Constraints** — "Yol boyunca neyin değişmemesi gerekiyor?" → options like "Public API imzaları", "Mevcut testler", "Bağımlılıklar (yeni paket yok)", "Hiçbir kısıt".

If no blocking gaps remain, skip straight to Phase 4 — do not ask for permission to proceed.

### Phase 4 — Compose the condition

Assemble the four components into one condition. Default template (single line is fine; the labels are for the evaluator, not decoration):

```
<objective, imperative, one clause>. Done when <measurable end state>, proven by <command(s) whose output is printed in the conversation>. Do not change <constraints>. Stop after <N> turns if not met.
```

Rules while composing:

- Replace every vague word from Phase 1 with its observable check. If you cannot find one, that word is still a blocking gap — return to Phase 3.
- Name the **exact command and its expected result** ("`pytest tests/auth -q` reports 0 failures"), not just the tool ("tests pass").
- For multi-item backlogs, make the end state a count that reaches zero or a queue that empties, and require Claude to print the count each turn.
- Keep it under 4,000 characters. Tighten prose; the evaluator rewards clarity, not length.
- Write prose in the user's language; keep code, paths, and commands verbatim.

### Phase 5 — Emit

Output, in this order:

1. A one-line summary of what changed from the raw intent (so the user can sanity-check the verifiability move).
2. The ready-to-run command in its own block:

   ```
   /goal <composed condition>
   ```

3. If the work is meant to run unattended (overnight, CI, headless), also give the non-interactive form:

   ```bash
   claude -p "/goal <composed condition>"
   ```

Do not run the goal yourself. End by telling the user to paste the command (running `/goal` starts a turn immediately).

## Vague → verifiable (rewrite reference)

| Raw intent (fails)                          | Rewritten end state + check (works)                                                                 |
|---------------------------------------------|-----------------------------------------------------------------------------------------------------|
| "make the app production-ready"             | name the actual gates: "`npm run build` exits 0, `npm test` reports 0 failures, `npm run lint` prints no errors" |
| "fix the failing tests"                     | "every test in `tests/` reports pass when `pytest -q` is run, output shown in the conversation"      |
| "clean up the code"                         | "`ruff check .` prints `All checks passed`; no behavior change — `pytest -q` still 0 failures"       |
| "migrate to the v2 API"                     | "no references to `api/v1` remain (`grep -rn 'api/v1' src/` prints nothing) and `npm test` passes"   |
| "split this big file"                       | "no file in `src/parser/` exceeds 300 lines (`wc -l` output shown) and the build still passes"       |
| "clear the bug backlog"                     | "issues labeled `bug` in the local queue file reach 0; print the remaining count each turn"          |
| "optimize the query"                        | "the benchmark script prints a p95 under 50ms; correctness check `<cmd>` still passes"               |

## Rules

- ALWAYS write the condition as an observable END state that the evaluator can read in the transcript — never as steps or as the current state.
- ALWAYS pair the end state with a **stated check**: the exact command and the expected output that proves it.
- NEVER leave a vague success word ("done", "clean", "fixed", "ready", "robust", "optimized", "works") in the final condition — each one is a blocking gap until replaced with a check.
- ALWAYS require Claude to *surface the proof in the conversation* (print the command output, the count, the diff). The evaluator sees nothing else.
- Call AskUserQuestion ONLY when a blocking gap remains, batch all questions into a single call, and offer concrete options — never interrogate one question per turn.
- NEVER ask for information the user already provided or that is plainly inferable from the task or repo.
- For open-ended or multi-item work, ALWAYS add a turn/time cap (e.g. "stop after 20 turns if not met") so the goal cannot loop indefinitely.
- For multi-item backlogs, make the end state a count→0 or empty-queue and require the count to be printed each turn.
- Default constraints to "change only what this goal requires; do not modify unrelated tests, config, or dependencies" and state the assumption — ask about constraints only when the task risks collateral damage.
- KEEP the condition under 4,000 characters.
- Write surrounding prose in the user's language; keep commands, paths, and code verbatim.
- This skill PREPARES the command; it does NOT run `/goal`. Emit the command and let the user run it. Provide the `claude -p "..."` form only when the work is meant to run unattended.
- If the task has no verifiable finish line at all (pure design judgment, subjective quality), say so plainly and recommend the user keep that part interactive rather than forcing a fake condition.
