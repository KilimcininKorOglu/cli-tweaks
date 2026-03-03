# cli-tweaks

A collection of hooks and skills for Factory Droid and Claude Code that add planning automation, persistent memory, smart commits, and more. Drop them into your home directory and they work out of the box.

## What's Included

### Hooks

| Hook                 | Event              | Description                                                              |
|----------------------|--------------------|--------------------------------------------------------------------------|
| `plan-mode.py`       | UserPromptSubmit   | Detects planning needs via keywords or complexity scoring, injects a 5-phase planning workflow |
| `save-plan.py`       | PostToolUse        | Saves completed plans to disk with desktop notifications                 |
| `memory-load.py`     | SessionStart       | Loads project-specific memory (MEMORY.md + topic files) into context     |
| `memory-save.py`     | Stop               | Reminds the agent to save learnings before the session ends              |
| `compact-reinject.py`| SessionStart:compact | Re-injects AGENTS.md or CLAUDE.md after context compaction             |
| `notify.py`          | (helper module)    | Cross-platform desktop notifications (macOS, Linux, Windows)             |

### Skills

| Skill                      | Command        | Description                                                        |
|----------------------------|----------------|--------------------------------------------------------------------|
| `commit`                   | `/commit`      | Conventional commits with repo style mimicry, smart staging, git safety protocol |
| `task-plan`                | `/task-plan`   | PRD breakdown into features with autonomous execution and checkpointing |
| `bug-report`               | `/bug-report`  | Systematic bug analysis and structured report generation           |
| `initialize`               | `/initialize`  | Creates AGENTS.md by scanning the codebase                         |
| `init` (Factory Droid only)| `/init`        | Creates CLAUDE.md by scanning the codebase                         |
| `implementation-planning` (Factory Droid only) | `/implementation-planning` | Interactive planning with mandatory AskUser questions |

## Directory Structure

```
cli-tweaks/
  .factory/          <-- Factory Droid (Kiro)
    hooks/
    skills/
    settings.json
  .claude/           <-- Claude Code
    hooks/
    skills/
    settings.json
```

## Installation

### Quick Install (copy everything)

```bash
git clone https://github.com/<your-username>/cli-tweaks.git
cd cli-tweaks

# Factory Droid
cp -r .factory/hooks/* ~/.factory/hooks/
cp -r .factory/skills/* ~/.factory/skills/

# Claude Code
cp -r .claude/hooks/* ~/.claude/hooks/
cp -r .claude/skills/* ~/.claude/skills/
```

### Hook Registration

After copying the files, you need to register the hooks in your settings. You can either merge the provided `settings.json` manually or copy the hooks section directly.

**Factory Droid** -- merge into `~/.factory/settings.json`:

```json
{
  "enableHooks": true,
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.factory/hooks/plan-mode.py" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "ExitSpecMode",
        "hooks": [
          { "type": "command", "command": "python3 ~/.factory/hooks/save-plan.py", "timeout": 15 }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.factory/hooks/memory-load.py", "timeout": 10 }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          { "type": "command", "command": "python3 ~/.factory/hooks/compact-reinject.py AGENTS.md", "timeout": 10 }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.factory/hooks/memory-save.py", "timeout": 10 }
        ]
      }
    ]
  }
}
```

**Claude Code** -- merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/plan-mode.py" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/save-plan.py", "timeout": 15 }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/memory-load.py", "timeout": 10 }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/compact-reinject.py CLAUDE.md", "timeout": 10 }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/memory-save.py", "timeout": 10 }
        ]
      }
    ]
  }
}
```

### Selective Install

Pick only what you need:

```bash
# Just the planning hooks
cp .factory/hooks/plan-mode.py ~/.factory/hooks/
cp .factory/hooks/save-plan.py ~/.factory/hooks/
cp .factory/hooks/notify.py ~/.factory/hooks/

# Just the memory system
cp .factory/hooks/memory-load.py ~/.factory/hooks/
cp .factory/hooks/memory-save.py ~/.factory/hooks/

# Just the commit skill
cp -r .factory/skills/commit ~/.factory/skills/
```

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

The memory system gives your agent persistent, project-scoped memory across sessions:

- On session start, `memory-load.py` reads `~/.factory/memory/<project>/MEMORY.md` and injects it
- On session end, `memory-save.py` reminds the agent to save anything new it learned
- Memory files are organized per project with a main index and topic files

### Compaction Re-injection

When the context window gets compacted, your AGENTS.md or CLAUDE.md instructions are lost. The `compact-reinject.py` hook detects compaction events and re-reads the file from your project directory, keeping your instructions alive.

### Commit Skill

The `/commit` skill gathers full git context before committing (status, diff, branch, recent log), matches your repository's existing commit style, enforces a git safety protocol, and supports flags like `--amend`, `--wip`, `--push`, and `--all`.

## Requirements

- Python 3.8+
- Factory Droid or Claude Code (or both)

## Platform Differences

| Feature                    | Factory Droid       | Claude Code          |
|----------------------------|---------------------|----------------------|
| Plan mode exit event       | `ExitSpecMode`      | `ExitPlanMode`       |
| Re-injection target        | `AGENTS.md`         | `CLAUDE.md`          |
| `/init` skill              | Yes (CLAUDE.md)     | No (built-in)        |
| `/implementation-planning` | Yes                 | No                   |
| Memory paths               | `~/.factory/memory/`| `~/.claude/memory/`  |
| Plan save paths            | `~/.factory/plans/` | `~/.claude/plans/`   |

## License

MIT
