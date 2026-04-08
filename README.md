# cli-tweaks

[Türkçe](README.tr.md)

A collection of hooks and skills for Factory Droid and Claude Code that add planning automation, persistent memory, smart commits, and more. Drop them into your home directory and they work out of the box.

## What's Included

### Hooks

| Hook                  | Event                | Description                                                                                    |
|-----------------------|----------------------|------------------------------------------------------------------------------------------------|
| `session-start.py`    | SessionStart/compact | Injects global user files and project memory into context                                      |
| `plan-mode.py`        | UserPromptSubmit     | Detects planning needs via keywords or complexity scoring, delegates to implement-plan skill   |
| `save-plan.py`        | PostToolUse          | Saves plans to disk (Factory) or sends notification only (Claude Code)                         |
| `memory-save.py`      | Stop                 | Reminds the agent to save learnings before the session ends                                    |
| `compact-reinject.py` | SessionStart:compact | Re-injects instruction files (via argv) after context compaction                               |
| `auto-allow.py`       | PermissionRequest    | Auto-approves tools matching settings.json allow list, notifies on mismatch (Claude Code only) |
| `notify.py`           | (helper module)      | Cross-platform desktop notifications (macOS, Linux, Windows)                                   |

### Skills

| Skill                          | Command                         | Description                                                                      |
|--------------------------------|---------------------------------|----------------------------------------------------------------------------------|
| `commit`                       | `/commit`                       | Conventional commits with repo style mimicry, smart staging, git safety protocol |
| `task-plan`                    | `/task-plan`                    | PRD breakdown into features with autonomous execution and checkpointing           |
| `bug-report`                   | `/bug-report`                   | General bug analysis plus focused audit subcommands writing to BUG-REPORT.md      |
| `git-flow`                     | `/git-flow`                     | Structured branch management with strict validation rules                         |
| `initialize`                   | `/initialize`                   | Creates AGENTS.md by scanning the codebase                                        |
| `init-claude`                  | `/init-claude`                  | Creates CLAUDE.md by scanning the codebase                                        |
| `implement-plan`               | `/implement-plan`               | Structured implementation planning with research, questions, and phased design    |
| `redate-commits`               | `/redate-commits`               | Rewrites commit dates across a selected range with safe workflow warnings         |
| `frontend-design`              | `/frontend-design`              | Distinctive, production-grade frontend interfaces                                 |
| `version-update-skill-creator` | `/version-update-skill-creator` | Scans project and creates a tailored version-update skill                         |
| `ai-seo`                       | `/ai-seo`                       | GEO optimization for AI search engines with 8 analysis subcommands                |
| `draft-to-article`             | `/draft-to-article`             | Format drafts for X Articles, LinkedIn, or Medium/Substack                        |
| `design-ref`                   | `/design-ref`                   | 27-site design system catalog with URL-based generator                            |
| `ios-uikit`                    | `/ios-uikit`                    | Programmatic UIKit development with 20 reference documents                        |
| `ios-simulator`                | `/ios-simulator`                | iOS simulator automation with 33 Node.js scripts for semantic navigation          |

#### `bug-report` audit subcommands

**General audits**

| Subcommand | Command | Description |
|------------|---------|-------------|
| `auditcodex` | `/bug-report auditcodex` | Codex CLI diff audit with validated findings written to BUG-REPORT.md |
| `api-audit` | `/bug-report api-audit` | API performance, resilience, contract, and lifecycle audit |
| `cache-audit` | `/bug-report cache-audit` | Caching strategy, consistency, and Redis/security audit |
| `disaster-recovery` | `/bug-report disaster-recovery` | Disaster recovery and business continuity readiness audit |
| `error-review` | `/bug-report error-review` | Error message quality, disclosure, and fallback-state audit |
| `feature-flags-audit` | `/bug-report feature-flags-audit` | Feature flag hygiene, rollout safety, and experimentation audit |
| `observability-audit` | `/bug-report observability-audit` | Logging, metrics, tracing, and debugging-readiness audit |
| `queue-audit` | `/bug-report queue-audit` | Queue, worker, retry, and DLQ resilience audit |
| `release-discipline` | `/bug-report release-discipline` | Version control, review process, and release-discipline audit |
| `tech-debt` | `/bug-report tech-debt` | Technical debt, dead code detection, and test quality audit |
| `tenant-isolation` | `/bug-report tenant-isolation` | Multi-tenant isolation and cross-tenant leakage audit |
| `ai-code-audit` | `/bug-report ai-code-audit` | AI-generated code detection, security, and quality audit |

**Security audits (checklist-based)**

| Subcommand | Command | Description |
|------------|---------|-------------|
| `integration-security` | `/bug-report integration-security` | Third-party integration, webhook, OAuth, and SSRF audit |
| `serialization-audit` | `/bug-report serialization-audit` | Serialization, parsing, XXE, and data transformation security audit |
| `session-audit` | `/bug-report session-audit` | Session lifecycle, JWT vulnerability detection, cookies, and CSRF audit |
| `upload-security` | `/bug-report upload-security` | File upload validation, storage, media processing, and download security audit |
| `business-logic` | `/bug-report business-logic` | Business logic flaws, workflow bypass, race conditions, and payment security audit |

**Security scans (three-phase: recon, batched verify, merge)**

| Subcommand | Command | Description |
|------------|---------|-------------|
| `security-sweep` | `/bug-report security-sweep` | Run all security scans in parallel via workers |
| `sec-recon` | `/bug-report sec-recon` | Codebase architecture and security posture reconnaissance |
| `access-control` | `/bug-report access-control` | IDOR and missing authentication/authorization detection |
| `sqli` | `/bug-report sqli` | SQL injection detection |
| `xss` | `/bug-report xss` | Cross-site scripting detection |
| `rce` | `/bug-report rce` | Remote code execution and command injection detection |
| `ssrf` | `/bug-report ssrf` | Server-side request forgery detection |
| `ssti` | `/bug-report ssti` | Server-side template injection detection |
| `path-traversal` | `/bug-report path-traversal` | Path traversal and directory traversal detection |
| `graphql` | `/bug-report graphql` | GraphQL injection and abuse detection |
| `hardcoded-secrets` | `/bug-report hardcoded-secrets` | Hardcoded API key, token, and password detection |

> Migration note: standalone audit commands such as `/api-audit`, `/error-review`, and `/auditcodex` are now consolidated under `/bug-report <subcommand>`.

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

| Platform      | Source                          | Target                     |
|---------------|---------------------------------|----------------------------|
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

The memory system gives your agent persistent, project-scoped memory across sessions. Memory is stored in a shared location (`~/.cli-tweaks/memory/`) so Factory Droid and Claude Code can both access the same knowledge base:

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

## Platform Differences

| Feature                 | Factory Droid    | Claude Code       |
|-------------------------|------------------|-------------------|
| Global config dir       | `~/.factory/`    | `~/.claude/`      |
| Shared data dir         | `~/.cli-tweaks/` | `~/.cli-tweaks/`  |
| Hook config file        | `settings.json`  | `settings.json`   |
| Plan mode exit event    | `ExitSpecMode`   | `ExitPlanMode`    |
| User question tool      | `AskUser`        | `AskUserQuestion` |
| Re-injection target     | `AGENTS.md`      | `CLAUDE.md`       |
| Subagent terminology    | "worker"         | "Explore"         |
| Skill invocation prefix | `/`              | `/`               |
| `/init-claude` skill    | Yes (CLAUDE.md)  | No (built-in)     |
| `/initialize` skill     | No               | Yes (AGENTS.md)   |
| `auto-allow.py` hook    | No               | Yes (v2.0.45+)    |

## License

MIT
