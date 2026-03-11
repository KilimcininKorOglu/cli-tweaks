# cli-tweaks

[Türkçe](README.tr.md)

A collection of hooks and skills for Factory Droid and Claude Code that add planning automation, persistent memory, smart commits, and more. Drop them into your home directory and they work out of the box.

## What's Included

### Hooks

| Hook                  | Event                | Description                                                                                    |
|-----------------------|----------------------|------------------------------------------------------------------------------------------------|
| `plan-mode.py`        | UserPromptSubmit     | Detects planning needs via keywords or complexity scoring, injects a 5-phase planning workflow |
| `save-plan.py`        | PostToolUse          | Saves plans to disk (Factory) or sends notification only (Claude Code)                         |
| `memory-load.py`      | SessionStart/compact | Loads project-specific memory (MEMORY.md + topic files) into context                           |
| `memory-save.py`      | Stop                 | Reminds the agent to save learnings before the session ends                                    |
| `compact-reinject.py` | SessionStart:compact | Re-injects instruction files (via argv) after context compaction                               |
| `global-inject.py`    | SessionStart/compact | Injects global user files (AGENTS.md, SOUL.md, etc.) from settings.json list                   |
| `auto-allow.py`       | PermissionRequest    | Auto-approves tools matching settings.json allow list, notifies on mismatch (Claude Code only) |
| `notify.py`           | (helper module)      | Cross-platform desktop notifications (macOS, Linux, Windows)                                   |

### Skills

| Skill                              | Command           | Description                                                                      |
|------------------------------------|-------------------|----------------------------------------------------------------------------------|
| `commit`                           | `/commit`         | Conventional commits with repo style mimicry, smart staging, git safety protocol |
| `task-plan`                        | `/task-plan`      | PRD breakdown into features with autonomous execution and checkpointing          |
| `bug-report`                       | `/bug-report`     | Systematic bug analysis and structured report generation                         |
| `dead-code`                        | `/dead-code`      | Dead code audit with 3-phase analysis and cleanup roadmap                        |
| `git-flow`                         | `/git-flow`       | Structured branch management with strict validation rules                        |
| `initialize` (Claude Code only)    | `/initialize`     | Creates AGENTS.md by scanning the codebase                                       |
| `init-claude` (Factory Droid only) | `/init-claude`    | Creates CLAUDE.md by scanning the codebase                                       |
| `implement-plan`                   | `/implement-plan` | Interactive planning with mandatory user questions                               |

## Directory Structure

```
cli-tweaks/
  factory/           <-- Factory Droid (copy to ~/.factory/)
    hooks/
    skills/
  claude/            <-- Claude Code (copy to ~/.claude/)
    hooks/
    skills/
  SOUL.md.template   <-- Custom persona template
```

## Installation

### Quick Install (degit)

No need to clone the entire repo. [degit](https://github.com/Rich-Harris/degit) copies only the files you need.

**Fresh install** (no existing config):

```bash
# Factory Droid
npx degit KilimcininKorOglu/cli-tweaks/factory ~/.factory

# Claude Code
npx degit KilimcininKorOglu/cli-tweaks/claude ~/.claude
```

**Merge with existing setup**:

```bash
# Factory Droid
npx degit KilimcininKorOglu/cli-tweaks/factory/hooks /tmp/cli-tweaks-hooks
npx degit KilimcininKorOglu/cli-tweaks/factory/skills /tmp/cli-tweaks-skills
cp -r /tmp/cli-tweaks-hooks/* ~/.factory/hooks/
cp -r /tmp/cli-tweaks-skills/* ~/.factory/skills/
rm -rf /tmp/cli-tweaks-hooks /tmp/cli-tweaks-skills

# Claude Code
npx degit KilimcininKorOglu/cli-tweaks/claude/hooks /tmp/cli-tweaks-hooks
npx degit KilimcininKorOglu/cli-tweaks/claude/skills /tmp/cli-tweaks-skills
cp -r /tmp/cli-tweaks-hooks/* ~/.claude/hooks/
cp -r /tmp/cli-tweaks-skills/* ~/.claude/skills/
rm -rf /tmp/cli-tweaks-hooks /tmp/cli-tweaks-skills
```

### Alternative: git clone

```bash
git clone https://github.com/KilimcininKorOglu/cli-tweaks.git
cd cli-tweaks

# Factory Droid
cp -r factory/hooks/* ~/.factory/hooks/
cp -r factory/skills/* ~/.factory/skills/

# Claude Code
cp -r claude/hooks/* ~/.claude/hooks/
cp -r claude/skills/* ~/.claude/skills/
```

### Hook Registration

After copying the files, register hooks by merging the hook definitions into your `settings.json`:

| Platform      | Source                        | Target                     |
|---------------|-------------------------------|----------------------------|
| Factory Droid | `factory/settings.json.example` | `~/.factory/settings.json` |
| Claude Code   | `claude/settings.json.example`  | `~/.claude/settings.json`  |

Copy the `hooks` section from the example file into your existing settings, or use the example as a starting point.

### Selective Install

Pick only what you need. Examples below use `factory/`; replace with `claude/` for Claude Code.

```bash
# Just the planning hooks (notify.py is required by save-plan.py)
cp factory/hooks/plan-mode.py ~/.factory/hooks/
cp factory/hooks/save-plan.py ~/.factory/hooks/
cp factory/hooks/notify.py ~/.factory/hooks/

# Just the memory system
cp factory/hooks/memory-load.py ~/.factory/hooks/
cp factory/hooks/memory-save.py ~/.factory/hooks/

# Just the commit skill
cp -r factory/skills/commit ~/.factory/skills/
```

> **Note:** `save-plan.py` imports `notify.py` at runtime. Always copy `notify.py` alongside it.

Then add the corresponding hook entries to your `settings.json`.

## How It Works

### Planning Mode

When you type something like "plan this feature" or submit a complex request (detected via scoring), the hook injects a 5-phase workflow:

1. **Explore** -- Gather codebase context
2. **Ask Questions** -- Clarify requirements with the user (mandatory)
3. **Design** -- Draft the implementation plan
4. **Present** -- Show the plan for approval
5. **Wait** -- Do not start coding until approved

Completed plans are saved to `~/.factory/plans/<project>/` (or `~/.claude/plans/<project>/`) with desktop notifications.

### Auto Memory

The memory system gives your agent persistent, project-scoped memory across sessions. Memory is stored in a shared location (`~/.cli-tweaks/memory/`) so both Factory Droid and Claude Code can access the same knowledge base:

- On session start, `memory-load.py` reads `~/.cli-tweaks/memory/<project>/MEMORY.md` and injects it
- On context compaction, memory is automatically re-injected alongside instruction files
- On session end, `memory-save.py` reminds the agent to save anything new it learned
- Memory files are organized per project with a main index and topic files

### Compaction Re-injection

When the context window gets compacted, your AGENTS.md or CLAUDE.md instructions and project memory are lost. The compact hooks detect compaction events and re-inject both instruction files and memory, keeping your context alive.

### Commit Skill

The `/commit` skill gathers full git context before committing (status, diff, branch, recent log), matches your repository's existing commit style, enforces a git safety protocol, and supports flags like `--amend`, `--wip`, `--push`, and `--all`.

### Custom Persona (SOUL.md)

You can define a custom persona that shapes how the agent communicates with you. Create a `SOUL.md` file in your config directory and add it to `globalInjectFiles` in your `settings.json`:

```json
{
  "globalInjectFiles": [
    "~/.factory/AGENTS.md",
    "~/.factory/SOUL.md"
  ]
}
```

The `global-inject.py` hook injects all listed files at session start and after context compaction. A template is provided in `SOUL.md.template` with an example "tough love" persona -- copy and customize it to your preference.

### Desktop Notifications

Desktop notifications are disabled by default. Enable them per-feature in your `settings.json`:

```json
{
  "hookNotifyAutoAllow": true,
  "hookNotifyPlanSave": true
}
```

- `hookNotifyAutoAllow`: Notifications for tools not in the allow list (Claude Code only, default: `true`)
- `hookNotifyPlanSave`: Notifications when plans are saved (default: `false`)

## Requirements

- Python 3.8+
- Factory Droid or Claude Code (or both)

## Platform Differences

| Feature                  | Factory Droid        | Claude Code          |
|--------------------------|----------------------|----------------------|
| Global config dir        | `~/.factory/`        | `~/.claude/`         |
| Shared data dir          | `~/.cli-tweaks/`     | `~/.cli-tweaks/`     |
| Hook config file         | `settings.json`      | `settings.json`      |
| Plan mode exit event     | `ExitSpecMode`       | `ExitPlanMode`       |
| User question tool       | `AskUser`            | `AskUserQuestion`    |
| Re-injection target      | `AGENTS.md`          | `CLAUDE.md`          |
| Subagent terminology     | "worker"             | "Explore"            |
| `/init-claude` skill     | Yes (CLAUDE.md)      | No (built-in)        |
| `/initialize` skill      | No                   | Yes (AGENTS.md)      |
| `auto-allow.py` hook     | No                   | Yes (v2.0.45+)       |

## License

MIT
