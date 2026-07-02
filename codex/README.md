# Codex Support

Codex is supported through native user-level skills and Python command hooks.

## What is included

| Path | Purpose |
|------|---------|
| `hooks/` | Codex-specific Python hook ports |
| `hooks.json.example` | Example Codex hook registration file |

The canonical Claude skill tree is reused for Codex skills because Codex reads the same `SKILL.md` directory format. Copy `claude/skills/` to `~/.agents/skills/`; older Codex setups may use `~/.codex/skills/`.

## Hook mapping

| Hook | Codex event | Matcher | Status |
|------|-------------|---------|--------|
| `session-start.py` | `SessionStart` | `startup|resume|clear` | Ported |
| `compact-reinject.py` | `SessionStart` | `compact` | Ported |
| `memory-reinject.py` | `UserPromptSubmit` | not used | Ported |
| `memory-save.py` | `Stop` | not used | Ported with Codex continuation semantics |
| `git-protect.py` | `PreToolUse` | `Bash` | Ported |
| `notify.py` | helper module | not applicable | Available for future notification hooks |

`save-plan.py` is not ported because Codex plan-exit tool names and plan transcript semantics are not verified.

## Install

Copy the hooks into Codex. On a fresh install, copy the example hook config to `~/.codex/hooks.json`. If `~/.codex/hooks.json` already exists, merge only the `hooks` object instead of overwriting the file.

```bash
mkdir -p ~/.codex/hooks
cp codex/hooks/*.py ~/.codex/hooks/
# Fresh install only:
cp codex/hooks.json.example ~/.codex/hooks.json
```

Optional global instruction files are configured in `~/.codex/cli-tweaks.json`:

```json
{
  "globalInjectFiles": [
    "~/.codex/AGENTS.md"
  ]
}
```

Codex requires non-managed command hooks to be reviewed and trusted before they run. After installing or changing hooks, open `/hooks` in Codex, inspect the configured commands, and trust the current definitions. Do not use `--dangerously-bypass-hook-trust` as the normal install path.

## Runtime notes

- Hook state is keyed by Codex `session_id`, not by parent process id.
- `Stop` hooks must emit JSON. `memory-save.py` uses `decision: "block"` only to continue Codex once with a memory-hygiene prompt.
- `stop_hook_active` prevents repeated memory-save continuations in the same turn.
- Project-local `.codex/` hooks run only when Codex trusts the project layer.

## Validation

```bash
python3 -m py_compile codex/hooks/*.py
python3 -m json.tool codex/hooks.json.example >/dev/null
```
