# cli-tweaks

[Türkçe](README.tr.md)

A collection of hooks and skills for Factory Droid, Claude Code, OpenCode, Codex CLI, and Pi Agent that add planning automation, persistent memory, smart commits, and more. Drop them into your home directory and they work out of the box.

## What's Included

### Hooks

| Hook                  | Event                | Description                                                                                    |
|-----------------------|----------------------|------------------------------------------------------------------------------------------------|
| `session-start.py`    | SessionStart/compact | Injects global user files and project memory into context                                      |
| `plan-mode.py`        | UserPromptSubmit     | Detects planning needs via keywords or complexity scoring, injects a 5-phase planning workflow |
| `save-plan.py`        | PostToolUse          | Saves plans to disk (Factory) or sends notification only (Claude Code)                         |
| `memory-save.py`      | Stop                 | Reminds the agent to save learnings before the session ends                                    |
| `compact-reinject.py` | SessionStart:compact | Re-injects instruction files (via argv) after context compaction                               |
| `auto-allow.py`       | PermissionRequest    | Auto-approves tools matching settings.json allow list, notifies on mismatch (Claude Code only) |
| `notify.py`           | (helper module)      | Cross-platform desktop notifications (macOS, Linux, Windows)                                   |

### Skills

| Skill                              | Command                         | Description                                                                      |
|------------------------------------|---------------------------------|----------------------------------------------------------------------------------|
| `commit`                           | `/commit`                       | Conventional commits with repo style mimicry, smart staging, git safety protocol |
| `task-plan`                        | `/task-plan`                    | PRD breakdown into features with autonomous execution and checkpointing          |
| `bug-report`                       | `/bug-report`                   | Systematic bug analysis and structured report generation                         |
| `dead-code`                        | `/dead-code`                    | Dead code audit with 3-phase analysis and cleanup roadmap                        |
| `git-flow`                         | `/git-flow`                     | Structured branch management with strict validation rules                        |
| `initialize` (Claude Code, Codex)  | `/initialize`                   | Creates AGENTS.md by scanning the codebase                                       |
| `init-claude` (Factory, Pi)        | `/init-claude`                  | Creates CLAUDE.md by scanning the codebase                                       |
| `implement-plan`                   | `/implement-plan`               | Interactive planning with mandatory user questions                               |
| `frontend-design`                  | `/frontend-design`              | Distinctive, production-grade frontend interfaces                                |
| `tech-debt`                        | `/tech-debt`                    | Technical debt mapping, measurement, and prioritization                          |
| `test-review`                      | `/test-review`                  | Test suite quality, coverage gaps, and strategy review                           |
| `error-review`                     | `/error-review`                 | Error message quality and information disclosure audit                           |
| `ai-code-audit`                    | `/ai-code-audit`                | AI-generated code detection, security, and quality review                        |
| `api-audit`                        | `/api-audit`                    | API performance, resilience, and contract testing audit                          |
| `cache-audit`                      | `/cache-audit`                  | Caching strategy, consistency, and security analysis                             |
| `disaster-recovery`                | `/disaster-recovery`            | Disaster recovery and business continuity assessment                             |
| `feature-flags-audit`              | `/feature-flags-audit`          | Feature flag hygiene, rollout safety, and experimentation                        |
| `integration-security`             | `/integration-security`         | Third-party integration and webhook security analysis                            |
| `observability-audit`              | `/observability-audit`          | Logging, metrics, health checks, and debugging readiness                         |
| `payment-security`                 | `/payment-security`             | Payment flow and financial transaction security audit                            |
| `queue-audit`                      | `/queue-audit`                  | Queue and async job management resilience analysis                               |
| `release-discipline`               | `/release-discipline`           | Version control, change management, and release process                          |
| `serialization-audit`              | `/serialization-audit`          | Data serialization and transformation security review                            |
| `session-audit`                    | `/session-audit`                | Session management and state persistence security                                |
| `tenant-isolation`                 | `/tenant-isolation`             | Multi-tenant data isolation and leakage audit                                    |
| `upload-security`                  | `/upload-security`              | File upload and media processing security audit                                  |
| `version-update-skill-creator`     | `/version-update-skill-creator` | Scans project and creates a tailored version-update skill                        |

## Directory Structure

```
cli-tweaks/
  factory/           <-- Factory Droid (copy to ~/.factory/)
    hooks/
    skills/
  claude/            <-- Claude Code (copy to ~/.claude/)
    hooks/
    skills/
  opencode/          <-- OpenCode (copy to ~/.config/opencode/)
    plugins/
  codex/             <-- Codex CLI (copy to ~/.codex/)
    skills/
  pi/                <-- Pi Agent (pi install or copy to ~/.pi/agent/)
    extensions/
    skills/
  package.json       <-- Pi Package manifest (at repo root for discovery)
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

# OpenCode
npx degit KilimcininKorOglu/cli-tweaks/opencode/plugins ~/.config/opencode/plugins

# Codex CLI
npx degit KilimcininKorOglu/cli-tweaks/codex/skills ~/.codex/skills

# Pi Agent (package install -- recommended)
pi install git:github.com/KilimcininKorOglu/cli-tweaks
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

# OpenCode
npx degit KilimcininKorOglu/cli-tweaks/opencode/plugins /tmp/cli-tweaks-plugins
mkdir -p ~/.config/opencode/plugins
cp -r /tmp/cli-tweaks-plugins/* ~/.config/opencode/plugins/
rm -rf /tmp/cli-tweaks-plugins

# Codex CLI
npx degit KilimcininKorOglu/cli-tweaks/codex/skills /tmp/cli-tweaks-skills
mkdir -p ~/.codex/skills
cp -r /tmp/cli-tweaks-skills/* ~/.codex/skills/
rm -rf /tmp/cli-tweaks-skills

# Pi Agent (package install is preferred, but manual also works)
npx degit KilimcininKorOglu/cli-tweaks/pi/skills /tmp/cli-tweaks-skills
npx degit KilimcininKorOglu/cli-tweaks/pi/extensions /tmp/cli-tweaks-extensions
mkdir -p ~/.pi/agent/skills ~/.pi/agent/extensions
cp -r /tmp/cli-tweaks-skills/* ~/.pi/agent/skills/
cp -r /tmp/cli-tweaks-extensions/* ~/.pi/agent/extensions/
rm -rf /tmp/cli-tweaks-skills /tmp/cli-tweaks-extensions
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

# OpenCode
mkdir -p ~/.config/opencode/plugins
cp opencode/plugins/* ~/.config/opencode/plugins/

# Codex CLI
mkdir -p ~/.codex/skills
cp -r codex/skills/* ~/.codex/skills/

# Pi Agent
mkdir -p ~/.pi/agent/skills ~/.pi/agent/extensions
cp -r pi/skills/* ~/.pi/agent/skills/
cp pi/extensions/* ~/.pi/agent/extensions/
```

### Hook Registration

After copying the files, register hooks by merging the hook definitions into your `settings.json`:

| Platform      | Source                           | Target                             |
|---------------|----------------------------------|------------------------------------|
| Factory Droid | `factory/settings.json.example`  | `~/.factory/settings.json`         |
| Claude Code   | `claude/settings.json.example`   | `~/.claude/settings.json`          |
| OpenCode      | `opencode/opencode.json.example` | `~/.config/opencode/opencode.json` |
| Codex CLI     | `codex/config.toml.example`      | `~/.codex/config.toml`             |

Copy the `hooks` section from the example file into your existing settings, or use the example as a starting point.

### Selective Install

Pick only what you need. Examples below use `factory/`; replace with `claude/` for Claude Code.

```bash
# Just the planning hooks (notify.py is required by save-plan.py)
cp factory/hooks/plan-mode.py ~/.factory/hooks/
cp factory/hooks/save-plan.py ~/.factory/hooks/
cp factory/hooks/notify.py ~/.factory/hooks/

# Just the memory system
cp factory/hooks/session-start.py ~/.factory/hooks/
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

The memory system gives your agent persistent, project-scoped memory across sessions. Memory is stored in a shared location (`~/.cli-tweaks/memory/`) so Factory Droid, Claude Code, OpenCode, and Pi Agent can all access the same knowledge base:

- On session start, `session-start.py` reads `~/.cli-tweaks/memory/<project>/MEMORY.md` and injects it
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

The `session-start.py` hook injects all listed files at session start and after context compaction. A template is provided in `SOUL.md.template` with an example "tough love" persona -- copy and customize it to your preference.

### Desktop Notifications

Desktop notifications are configured per-feature in your `settings.json`:

```json
{
  "hookNotifyAutoAllow": true,
  "hookNotifyPlanSave": true
}
```

- `hookNotifyAutoAllow`: Notifications for tools not in the allow list (Claude Code only, default: `true`)
- `hookNotifyPlanSave`: Notifications when plans are saved (default: `false`)

## Requirements

- Python 3.8+ (Factory Droid, Claude Code)
- Bun runtime (OpenCode -- auto-installed by OpenCode)
- Node.js (Pi Agent -- installed with Pi Agent)
- Factory Droid, Claude Code, OpenCode, Codex CLI, or Pi Agent

## Platform Differences

| Feature                 | Factory Droid    | Claude Code       | OpenCode              | Codex CLI             | Pi Agent                  |
|-------------------------|------------------|-------------------|-----------------------|-----------------------|---------------------------|
| Global config dir       | `~/.factory/`    | `~/.claude/`      | `~/.config/opencode/` | `~/.codex/`           | `~/.pi/agent/`            |
| Shared data dir         | `~/.cli-tweaks/` | `~/.cli-tweaks/`  | `~/.cli-tweaks/`      | N/A (built-in memory) | `~/.cli-tweaks/`          |
| Hook config file        | `settings.json`  | `settings.json`   | `opencode.json`       | `config.toml`         | `settings.json`           |
| Plan mode exit event    | `ExitSpecMode`   | `ExitPlanMode`    | Built-in (Tab key)    | Built-in (Shift+Tab)  | Extension-based           |
| User question tool      | `AskUser`        | `AskUserQuestion` | N/A                   | `AskUserQuestion`     | Extension-based           |
| Re-injection target     | `AGENTS.md`      | `CLAUDE.md`       | Native rules system   | `AGENTS.md` (native)  | `AGENTS.md` (native)      |
| Subagent terminology    | "worker"         | "Explore"         | N/A                   | N/A                   | Extension-based           |
| Plugin runtime          | Python 3.8+      | Python 3.8+       | JS/TS (Bun)           | N/A (skills only)     | JS/TS (Node.js)           |
| Skill invocation prefix | `/`              | `/`               | `/`                   | `$`                   | `/skill:`                 |
| Memory system           | Hook-based       | Hook-based        | Plugin-based          | Built-in              | Extension-based           |
| `/init-claude` skill    | Yes (CLAUDE.md)  | No (built-in)     | No                    | No                    | Yes (CLAUDE.md)           |
| `/initialize` skill     | No               | Yes (AGENTS.md)   | No                    | Yes (AGENTS.md)       | No                        |
| `auto-allow.py` hook    | No               | Yes (v2.0.45+)    | No                    | No (OS-level sandbox) | No (no permission system) |

## License

MIT
