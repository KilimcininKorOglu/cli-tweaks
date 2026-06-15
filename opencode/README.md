# OpenCode Support

This directory ports the cli-tweaks Claude Code / Factory Droid mechanisms to
[OpenCode](https://opencode.ai). Skills and rules work natively with zero
porting; the Python hooks are re-authored as TypeScript plugins.

> Status: the plugins are authored against OpenCode's documented hook API and
> are syntactically structured to match it, but they were **not runtime-tested**
> — OpenCode was not installed during authoring. Verify each plugin against your
> installed OpenCode version before relying on it.

## What works natively (no porting)

### Skills

OpenCode loads `SKILL.md` files through its native `skill` tool. Its scan paths
include `~/.claude/skills/<name>/` and `.claude/skills/<name>/`, so any skill
already deployed for Claude Code is visible to OpenCode without copying.

- Format follows the Anthropic Agent Skills spec; cli-tweaks frontmatter is
  compatible.
- Invocation differs: Claude uses `/commit` (slash command); OpenCode exposes
  the same skill as the `skills_commit` tool. Trigger keywords in the skill's
  `description` still drive discovery.
- Restrict skills with `opencode.json` `permission.skill` (allow/ask/deny +
  wildcards).

### Rules / instructions

OpenCode reads `AGENTS.md` (and `CLAUDE.md`) natively as custom instructions.
The `instructions` field in `opencode.json` loads additional files (local globs
and remote URLs) and combines them with `AGENTS.md`.

## What needs plugins

cli-tweaks hooks are Python; OpenCode hooks are TypeScript/JavaScript plugins
built on `@opencode-ai/plugin`. The Python scripts cannot be reused directly —
they are re-authored here.

| Plugin | OpenCode hook | Python origin | Match |
|--------|---------------|---------------|-------|
| `memory-save.ts` | `stop` | `memory-save.py` | Full — blocks the first stop and injects a continuation prompt |
| `compact-reinject.ts` | `experimental.session.compacting` | `compact-reinject.py` | Full — preserves AGENTS.md/CLAUDE.md through compaction |
| `memory-inject.ts` | `experimental.chat.system.transform` | `memory-reinject.py` | Experimental — blocked by issue #17100 (see below) |

`session-start.py`'s static file injection has no plugin: it is covered by
native `AGENTS.md` + the `instructions` field.

### Not ported

- `save-plan.py` — OpenCode's plan/spec model was not verified, so the
  `PostToolUse:ExitPlanMode` capture has no confirmed equivalent.

## Install

1. Deploy the plugins to the global plugin directory (auto-loaded at startup):

   ```bash
   cp opencode/plugins/*.ts ~/.config/opencode/plugins/
   ```

   Project-scoped alternative: copy them into `.opencode/plugins/` inside a
   repository.

2. Merge `opencode.json.example` into your config
   (`~/.config/opencode/opencode.json` for global, or `opencode.json` in a
   project).

3. Skills and rules need no deploy step beyond the existing Claude/Factory
   deployment — OpenCode reads `~/.claude/skills/` and `AGENTS.md` directly.

## How local plugins load

OpenCode auto-loads every `.ts`/`.js` file from these directories at startup:

- `~/.config/opencode/plugins/` — global
- `.opencode/plugins/` — project

Local plugins are **not** listed in the `opencode.json` `plugin` array — that
array is for npm packages. Putting a local file path there is incorrect.

## Permission config

`opencode.json.example` ships `permission.skill` to control which skills agents
can load (allow/ask/deny + wildcards, documented in OpenCode's skill docs). If
you also want to gate tools declaratively, OpenCode exposes `permission.bash` /
`edit` / `webfetch` keys — see `opencode.ai/docs/permissions` for their exact
shape, confirmed against your installed version.

## Memory loading

- Reliable path: add your project's `MEMORY.md` to `opencode.json`
  `instructions` (static, always loaded). Because the memory path is
  project-specific (`~/.cli-tweaks/memory/<project>/MEMORY.md`), the example
  config does not hardcode it — add it per project.
- Dynamic re-injection: `memory-inject.ts` reproduces `memory-reinject.py`'s
  cadence (project rules every 5th message, global file every 15th) via
  `experimental.chat.system.transform`. See the limitation below.

## Known limitations and unverified assumptions

- **Not runtime-tested.** Every plugin is authored against documented hook
  signatures (`input.sessionID`, `client.session.prompt`, `output.context`,
  `output.system`) but none were executed.
- **`memory-inject.ts` may have no effect.** `experimental.chat.system.transform`
  is flagged experimental, and issue #17100 (anomalyco/opencode) reports its
  `output.system` mutations are silently discarded by the runtime. Until that is
  fixed, use the static `instructions` path for memory.
- **`memory-save.ts` stop re-fire.** The per-session toggle assumes exactly one
  follow-up stop after `client.session.prompt`. OpenCode's stop re-fire
  semantics were not verified; the toggle prevents an infinite loop either way.

## Shared state

Plugins read and write the same cross-platform state as the Python hooks, under
`~/.cli-tweaks/`:

- memory: `~/.cli-tweaks/memory/<project>/`
- re-injection counters: `~/.cli-tweaks/.reinject-counter/<sessionId>`
- stop toggles: `~/.cli-tweaks/.stop-fired/<sessionId>`

The Python hooks key this state by parent PID; the plugins key it by OpenCode
`sessionID`, which is a stable per-session identifier. OpenCode's stable
`directory` context also makes the Python session-lock indirection unnecessary,
so the plugins resolve the project name directly from the working directory.
