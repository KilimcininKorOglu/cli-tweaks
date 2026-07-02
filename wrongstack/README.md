# WrongStack Support

This directory ports cli-tweaks hooks to [WrongStack](https://github.com/WrongStack/WrongStack) via **Python shell hooks**. WrongStack's shell-hook transport is Claude-compatible (stdin JSON to stdout JSON, exit code 2 = block) but its field names and outcome shape differ -- the `_compat.py` shim absorbs those differences so the hook logic stays identical to the Claude/Factory ports.

> **Status:** Authored against WrongStack's documented hook API (`docs/hooks.md`, `packages/core/src/types/hooks.ts`, `packages/core/src/hooks/shell-executor.ts`). **Not runtime-tested** -- WrongStack was not installed during authoring. Verify with your installed version before relying on it.

## What's included

| Hook | WrongStack event | Matcher | Status |
|------|-----------------|---------|--------|
| `session-start.py` | `SessionStart` | -- | Ported. Global inject + memory load + stop-marker soft reminder. Memory capped at 150 lines for 64 KiB output safety. |
| `git-protect.py` | `PreToolUse` | `Bash` | Direct port. Blocks `git add -f`/`--force` on global-gitignore files. |
| `memory-reinject.py` | `UserPromptSubmit` | -- | Ported. Critical rules every 5th message, global file every 15th. Counter keyed by `sessionId`. |
| `memory-save.py` | `Stop` | -- | **Redesigned.** WrongStack Stop is side-effects-only -- `decision: "block"` is ignored. Auto-generates/updates MEMORY.md directly from the session logs (JSONL discovery, parse, merge) instead. |
| `save-plan.py` | `PostToolUse` | `*` | **Heuristic matcher v1.** WrongStack's plan-exit tool name is unconfirmed; accepts any PostToolUse whose `toolName` contains `plan`/`spec`/`exitplan`/`exitspec`/`exitspecmode`. Misses are visible (no notification), false positives are harmless (a ping). Plans dir: `~/.wrongstack/plans/`. |
| `compact-reinject.py` | -- | -- | **Not ported.** WrongStack has no compaction event (5 documented events, no `SessionStart:compact` equivalent). Stub kept for layout parity. |
| `notify.py` | -- | -- | Helper module. Cross-platform desktop notifications (macOS, Linux, Windows). |

## Skills

| Skill | Command | Description | Notes |
|-------|---------|-------------|-------|
| `commit` | `/commit` | Conventional commits with repo style mimicry, smart staging, git safety protocol | -- |
| `git-flow` | `/git-flow` | Structured branch management with strict validation | Overrides WrongStack's bundled git-flow with extended Turkish triggers |
| `bug-report` | `/bug-report` | Bug analysis, security auditing, and focused security scans with 40 subcommands | Largest skill. Uses `plan` tool instead of `ExitPlanMode` |
| `task-plan` | `/task-plan` | PRD breakdown into features with autonomous execution and checkpointing | -- |
| `initialize` | `/initialize` | Creates AGENTS.md by scanning the codebase | -- |
| `redate-commits` | `/redate-commits` | Rewrites commit dates across a selected range | -- |
| `frontend-design` | `/frontend-design` | Frontend code generation with 28-site design system catalog | -- |
| `version-update-skill-creator` | *(meta-skill)* | Creates a `/version-update` skill for the current project | Outputs to `.wrongstack/skills/` |
| `add-log` | `/add-log` | Adds centralized request, audit, and application logging | Platform-agnostic |
| `goal-prep` | `/goal-prep` | Converts free-form work into a verifiable `/goal` completion condition | Uses generic ask-user wording |
| `no-ai` | `/no-ai` | Rewrites text to remove common AI-generated writing patterns | WrongStack compatibility metadata |
| `ai-seo` | `/ai-seo` | GEO optimization for AI search engines | -- |
| `draft-to-article` | `/draft-to-article` | Format drafts for X Articles, LinkedIn, or Medium/Substack | -- |
| `http-cache` | `/http-cache` | HTTP caching with ETag and Cache-Control headers | -- |
| `audit-replay` | `/audit-replay` | User action tracking, audit event logging, and rrweb session replay | -- |
| `ios-uikit` | `/ios-uikit` | Programmatic UIKit development with 20 reference documents | -- |
| `ios-simulator` | `/ios-simulator` | iOS simulator automation with 22 Node.js scripts | -- |

The `wrongstack/skills/` directory mirrors `claude/skills/` with platform-specific adjustments:
- `draft-to-article`: generic ask-user phrasing (not `AskUserQuestion`)
- `bug-report/fix.md`: generic plan-mode phrasing (not `ExitPlanMode`)
- `initialize`: includes WrongStack in the agent list
- `version-update-skill-creator`: outputs to `.wrongstack/skills/`
- `git-flow`: override note in description
- `goal-prep`: generic ask-user wording and non-interactive guidance
- `no-ai`: WrongStack compatibility metadata and tool list
- All other skills: identical content (platform-agnostic)

## Architecture: `_compat.py` shim

WrongStack's HookInput uses camelCase (`toolName`, `toolInput`, `sessionId`); our hook logic uses snake_case. The outcome JSON is top-level (`{"decision": "block", "reason": "..."}`) -- not Claude's nested `hookSpecificOutput` wrapper.

`_compat.py` provides a thin public API that every hook calls:

```python
import _compat

data = _compat.readInput()                         # stdin to snake_case dict
data.get("tool_name")                              # "Bash"
_compate.emitBlock("reason")                       # {"decision":"block","reason":"..."}
_compate.emitAdditionalContext("text")             # {"additionalContext":"text"}
_compate.emitAllow()                               # no-op (empty stdout)
_compate.resolveProjectName(cwd, sessionId)        # lock > git root > cwd
_compate.writeStopMarker(sessionId, project)       # side-effect on Stop
_compate.readStopMarker(sessionId)                 # True/False
```

Hooks do NOT import `sys`, `json`, or `pathlib` for stdin/stdout -- the shim owns the wire format.

## Shared state

All hooks share the same cross-platform state as the Claude and Factory ports under `~/.cli-tweaks/`:

- Memory: `~/.cli-tweaks/memory/<project>/`
- Re-injection counters: `~/.cli-tweaks/.reinject-counter/<sessionId>` (WrongStack uses `sessionId`, not PPID)
- Stop markers: `~/.cli-tweaks/.stop-reminded/<sessionId>`
- Logs: `~/.cli-tweaks/logs/`

## Global config

Unlike Claude's `settings.json` or Factory's `settings.json`, WrongStack hooks read a dedicated config file: `~/.cli-tweaks/wrongstack-config.json`. This keeps the hooks out of `~/.wrongstack/config.json` (which WrongStack owns and validates).

Example:

```json
{
  "globalInjectFiles": [
    "~/.wrongstack/AGENTS.md"
  ],
  "globalInstructionFile": "~/.wrongstack/AGENTS.md",
  "hookNotifyPlanSave": true
}
```

- `globalInjectFiles` -- paths injected at `SessionStart` (read by `session-start.py`)
- `globalInstructionFile` -- single file re-injected every 15th message (read by `memory-reinject.py`)
- `hookNotifyPlanSave` -- enables desktop notification on plan save (read by `notify.py` + `save-plan.py`)

If the file is missing, hooks work silently with defaults (no global inject, no notification).

## Install

1. Clone the repo:
   ```bash
   git clone https://github.com/KilimcininKorOglu/cli-tweaks.git
   ```

2. Deploy hooks:
   ```bash
   cp -r cli-tweaks/wrongstack/hooks/* ~/.wrongstack/hooks/
   ```

3. Register hooks in `~/.wrongstack/config.json` by merging the `hooks` block from `wrongstack/config.example.json`. **Replace `/path/to/cli-tweaks` with the actual clone path.**

4. Create `~/.cli-tweaks/wrongstack-config.json` with your `globalInjectFiles` and `globalInstructionFile` entries (optional -- hooks work without it).

5. Deploy skills:
   ```bash
   cp -r cli-tweaks/wrongstack/skills/* ~/.wrongstack/skills/
   ```

   Alternatively, skills need no additional deploy step if you already deploy
   `claude/skills/` -- WrongStack reads skill files natively from the same paths
   Claude Code uses (`~/.claude/skills/`). The `wrongstack/skills/` versions
   include platform-specific adjustments (WrongStack-compatible tool names,
   `.wrongstack/skills/` paths, extended trigger keywords).

## Known limitations

- **Not runtime-tested.** All hooks pass `python3 -m py_compile` but none were executed inside a real WrongStack session.
- **Shell-hook output cap.** WrongStack's shell-executor caps hook output at 64 KiB. `session-start.py` truncates MEMORY.md at 150 lines and limits global files to 2-3 entries. A very large global instruction file + memory could still clip silently.
- **Stop cannot block.** `memory-save.py`'s Claude pattern (block first stop, let second through) is impossible. The redesign reads the session logs and writes/merges MEMORY.md directly, since a Stop hook can only run side effects.
- **Compaction re-injection.** WrongStack has no `SessionStart:compact` event. If a long session compacts mid-flight, CLAUDE.md/AGENTS.md and memory are not re-injected until the next session start.
- **Save-plan tool name unconfirmed.** The heuristic string match (`plan`/`spec`/`exitplan`/`exitspec`) is based on WrongStack's README mentioning SpecParser. The actual PostToolUse tool name may differ. Confirm against your install and tighten the `PLAN_TOOL_HINTS` list if needed.
- **Permission ordering.** WrongStack runs `PreToolUse` *before* the permission (trust) policy, so `git-protect.py` can veto tools that would otherwise auto-allow -- this is correct behavior for a block hook.

## Differences from other platforms

| Aspect | WrongStack | Claude Code | OpenCode |
|--------|-----------|-------------|----------|
| Hook runtime | Python shell (`python3`) | Python shell (`python3`) | TS in-process (`@opencode-ai/plugin`) |
| Input fields | camelCase (`toolName`) | snake_case (`tool_name`) | TS objects |
| Outcome shape | Top-level (`decision`, `additionalContext`) | Nested (`hookSpecificOutput`, `decision.behavior`) | Plugin return |
| Session key | `sessionId` (ULID-like) | PPID (pid) | `sessionID` |
| Config file | `~/.wrongstack/config.json` | `~/.claude/settings.json` | `~/.config/opencode/opencode.json` |
| Extra config | `~/.cli-tweaks/wrongstack-config.json` | `~/.claude/settings.json` `globalInjectFiles` | `opencode.json` `instructions` |
| Compact event | ❌ None | ✅ `SessionStart:compact` | ✅ `experimental.session.compacting` |
| Stop block | ❌ Side-effects only | ✅ `decision: "block"` works | ✅ `client.session.prompt` re-fire |
| Output cap | 64 KiB | None | N/A (in-process) |
