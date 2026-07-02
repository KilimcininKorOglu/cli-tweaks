# cli-tweaks

[Türkçe](README.tr.md)

A collection of hooks and skills for Factory Droid, Claude Code, OpenCode, and WrongStack that add planning automation, persistent memory, smart commits, and more. Drop them into your home directory and they work out of the box. OpenCode is supported through native skills/rules plus TypeScript plugins; WrongStack is supported through Python shell hooks (see [OpenCode Support](#opencode-support) and [WrongStack Support](#wrongstack-support)).

## What's Included

### Hooks

| Hook                  | Event                | Description                                                                                    |
|-----------------------|----------------------|------------------------------------------------------------------------------------------------|
| `session-start.py`    | SessionStart/compact | Injects global user files and project memory into context                                      |
| `save-plan.py`        | PostToolUse          | Saves plans to disk (Factory) or sends notification only (Claude Code)                         |
| `memory-save.py`      | Stop                 | Reminds the agent to update MEMORY.md; offloads old entries to topic files near the line cap and migrates a malformed file to the standard structure |
| `memory-reinject.py`  | UserPromptSubmit     | Re-injects MEMORY.md critical rules (every 5th msg) and the full global instruction file (every 15th) to counter recency bias |
| `compact-reinject.py` | SessionStart:compact | Re-injects instruction files (via argv) after context compaction                               |
| `git-protect.py`      | PreToolUse (Bash)    | Blocks `git add -f/--force` on files listed in the global gitignore                             |
| `notify.py`           | (helper module)      | Cross-platform desktop notifications (macOS, Linux, Windows)                                   |

### Skills

| Skill                          | Command                         | Description                                                                      |
|--------------------------------|---------------------------------|----------------------------------------------------------------------------------|
| `commit`                       | `/commit`                       | Conventional commits with repo style mimicry, smart staging, git safety protocol |
| `task-plan`                    | `/task-plan`                    | PRD breakdown into features with autonomous execution and checkpointing          |
| `bug-report`                   | `/bug-report`                   | General bug analysis plus focused audit subcommands writing to BUG-REPORT.md     |
| `git-flow`                     | `/git-flow`                     | Structured branch management with strict validation rules                        |
| `initialize`                   | `/initialize`                   | Creates AGENTS.md by scanning the codebase                                       |
| `init-claude`                  | `/init-claude`                  | Creates CLAUDE.md by scanning the codebase                                       |
| `redate-commits`               | `/redate-commits`               | Rewrites commit dates across a selected range with safe workflow warnings        |
| `frontend-design`              | `/frontend-design`              | Frontend code generation with 28-site design system catalog                      |
| `version-update-skill-creator` | `/version-update-skill-creator` | Scans project and creates a tailored version-update skill                        |
| `ai-seo`                       | `/ai-seo`                       | GEO optimization for AI search engines with 8 analysis subcommands               |
| `draft-to-article`             | `/draft-to-article`             | Format drafts for X Articles, LinkedIn, or Medium/Substack                       |
| `ios-uikit`                    | `/ios-uikit`                    | Programmatic UIKit development with 20 reference documents                       |
| `ios-simulator`                | `/ios-simulator`                | iOS simulator automation with 22 Node.js scripts for semantic navigation         |
| `goal-prep`                    | `/goal-prep`                    | Converts free-form work into a verifiable `/goal` completion condition           |
| `audit-replay`                 | `/audit-replay`                 | User action tracking, audit event logging, and rrweb session replay              |
| `http-cache`                   | `/http-cache`                   | HTTP caching with ETag and Cache-Control header implementation                   |

#### `bug-report` audit subcommands

**Workflow**

| Subcommand | Command           | Description                                                       |
|------------|-------------------|-------------------------------------------------------------------|
| `fix`      | `/bug-report fix` | Disciplined single-bug fix workflow with commit and report update |

**General audits**

| Subcommand            | Command                           | Description                                                     |
|-----------------------|-----------------------------------|-----------------------------------------------------------------|
| `api-audit`           | `/bug-report api-audit`           | API performance, resilience, contract, and lifecycle audit      |
| `cache-audit`         | `/bug-report cache-audit`         | Caching strategy, consistency, and Redis/security audit         |
| `disaster-recovery`   | `/bug-report disaster-recovery`   | Disaster recovery and business continuity readiness audit       |
| `error-review`        | `/bug-report error-review`        | Error message quality, disclosure, and fallback-state audit     |
| `feature-flags-audit` | `/bug-report feature-flags-audit` | Feature flag hygiene, rollout safety, and experimentation audit |
| `observability-audit` | `/bug-report observability-audit` | Logging, metrics, tracing, and debugging-readiness audit        |
| `queue-audit`         | `/bug-report queue-audit`         | Queue, worker, retry, and DLQ resilience audit                  |
| `release-discipline`  | `/bug-report release-discipline`  | Version control, review process, and release-discipline audit   |
| `tech-debt`           | `/bug-report tech-debt`           | Technical debt, dead code detection, and test quality audit     |
| `tenant-isolation`    | `/bug-report tenant-isolation`    | Multi-tenant isolation and cross-tenant leakage audit           |
| `ai-code-audit`       | `/bug-report ai-code-audit`       | AI-generated code detection, security, and quality audit        |

**Security audits (checklist-based)**

| Subcommand             | Command                            | Description                                                                        |
|------------------------|------------------------------------|------------------------------------------------------------------------------------|
| `integration-security` | `/bug-report integration-security` | Third-party integration, webhook, OAuth, and SSRF audit                            |
| `serialization-audit`  | `/bug-report serialization-audit`  | Serialization, parsing, XXE, and data transformation security audit                |
| `session-audit`        | `/bug-report session-audit`        | Session lifecycle, JWT vulnerability detection, cookies, and CSRF audit            |
| `upload-security`      | `/bug-report upload-security`      | File upload validation, storage, media processing, and download security audit     |
| `business-logic`       | `/bug-report business-logic`       | Business logic flaws, workflow bypass, race conditions, and payment security audit |

**Security scans (three-phase: recon, batched verify, merge)**

| Subcommand          | Command                         | Description                                               |
|---------------------|---------------------------------|-----------------------------------------------------------|
| `security-sweep`    | `/bug-report security-sweep`    | Run all 24 security scans in parallel via workers         |
| `sec-recon`         | `/bug-report sec-recon`         | Codebase architecture and security posture reconnaissance |
| `access-control`    | `/bug-report access-control`    | IDOR and missing authentication/authorization detection   |
| `sqli`              | `/bug-report sqli`              | SQL injection detection                                   |
| `xss`               | `/bug-report xss`               | Cross-site scripting detection                            |
| `rce`               | `/bug-report rce`               | Remote code execution and command injection detection     |
| `ssrf`              | `/bug-report ssrf`              | Server-side request forgery detection                     |
| `ssti`              | `/bug-report ssti`              | Server-side template injection detection                  |
| `path-traversal`    | `/bug-report path-traversal`    | Path traversal and directory traversal detection          |
| `graphql`           | `/bug-report graphql`           | GraphQL injection and abuse detection                     |
| `hardcoded-secrets` | `/bug-report hardcoded-secrets` | Hardcoded API key, token, and password detection          |
| `cors`              | `/bug-report cors`              | CORS misconfiguration and cross-origin attack detection   |
| `open-redirect`     | `/bug-report open-redirect`     | Open redirect and URL manipulation detection              |
| `nosqli`            | `/bug-report nosqli`            | NoSQL injection (MongoDB, Redis, Elasticsearch) detection |
| `dependency-audit`  | `/bug-report dependency-audit`  | Supply chain security, CVE, and typosquatting audit       |
| `data-exposure`     | `/bug-report data-exposure`     | Sensitive data exposure in logs, errors, and APIs         |
| `crypto`            | `/bug-report crypto`            | Cryptography weakness detection (weak algorithms, keys)   |
| `ci-cd`             | `/bug-report ci-cd`             | CI/CD pipeline security (GitHub Actions, GitLab CI)       |
| `docker`            | `/bug-report docker`            | Container security (Dockerfile, docker-compose)           |
| `rate-limiting`     | `/bug-report rate-limiting`     | Rate limiting and brute force protection audit            |
| `websocket`         | `/bug-report websocket`         | WebSocket security (origin, auth, message injection)      |
| `header-injection`  | `/bug-report header-injection`  | HTTP header injection and CRLF detection                  |
| `clickjacking`      | `/bug-report clickjacking`      | Clickjacking protection (X-Frame-Options, CSP)            |
| `mass-assignment`   | `/bug-report mass-assignment`   | Mass assignment and parameter pollution detection         |
| `ldap`              | `/bug-report ldap`              | LDAP injection in search filters and DN construction      |

## Directory Structure

```
cli-tweaks/
  factory/           <-- Factory Droid (copy to ~/.factory/)
    hooks/
    skills/
  claude/            <-- Claude Code (copy to ~/.claude/)
    hooks/
    skills/
  opencode/          <-- OpenCode (TS plugins + config, see opencode/README.md)
    plugins/
    opencode.json.example
  wrongstack/        <-- WrongStack (Python shell hooks + skills, see wrongstack/README.md)
    hooks/
    skills/
  SOUL.md.template          <-- Custom persona template
  GLOBAL-RULES.template.md  <-- Portable global agent-rules template
  sample-BUG-REPORT.md      <-- Finding-format reference for audit skills
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

# WrongStack
npx degit KilimcininKorOglu/cli-tweaks/wrongstack ~/.wrongstack
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

# WrongStack
npx degit KilimcininKorOglu/cli-tweaks/wrongstack/hooks /tmp/cli-tweaks-hooks
npx degit KilimcininKorOglu/cli-tweaks/wrongstack/skills /tmp/cli-tweaks-skills
cp -r /tmp/cli-tweaks-hooks/* ~/.wrongstack/hooks/
cp -r /tmp/cli-tweaks-skills/* ~/.wrongstack/skills/
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

# WrongStack
cp -r wrongstack/hooks/* ~/.wrongstack/hooks/
cp -r wrongstack/skills/* ~/.wrongstack/skills/
```

### Hook Registration

After copying the files, register hooks by merging the hook definitions into your `settings.json`:

| Platform      | Source                          | Target                       |
|---------------|---------------------------------|------------------------------|
| Factory Droid | `factory/settings.json.example` | `~/.factory/settings.json`   |
| Claude Code   | `claude/settings.json.example`  | `~/.claude/settings.json`    |
| WrongStack    | `wrongstack/config.example.json`| `~/.wrongstack/config.json`  |

Copy the `hooks` section from the example file into your existing settings, or use the example as a starting point.

### Selective Install

Pick only what you need. Examples below use `factory/`; replace with `claude/` for Claude Code.

```bash
# Just the plan-saving hook (notify.py is required by save-plan.py)
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

### Plan Saving

When you use the agent's built-in plan mode and exit it (`ExitPlanMode` on Claude Code, `ExitSpecMode` on Factory Droid), the `save-plan.py` hook captures the event. On Factory Droid the plan content is written to `~/.factory/plans/<project>/`; on Claude Code a desktop notification is sent (the tool provides no plan content to the hook).

### Auto Memory

The memory system gives your agent persistent, project-scoped memory across sessions. Memory is stored in a shared location (`~/.cli-tweaks/memory/`) so Factory Droid and Claude Code can both access the same knowledge base:

- On session start, `session-start.py` reads `~/.cli-tweaks/memory/<project>/MEMORY.md` and injects it
- On context compaction, memory is automatically re-injected alongside instruction files
- Every 5th message, `memory-reinject.py` re-injects the critical rules from MEMORY.md; every 15th message it also re-injects your full global instruction file (`~/.claude/CLAUDE.md` or `~/.factory/AGENTS.md`) to counter recency bias in long sessions
- On session end, `memory-save.py` reminds the agent to save anything new it learned, prompts moving old entries to topic files when MEMORY.md nears its 200-line cap, and enforces the standard four-section structure if the file is malformed
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

### Global Rules Template (GLOBAL-RULES.template.md)

`GLOBAL-RULES.template.md` is a portable, model-agnostic set of global agent instructions -- engineering discipline (verify before you claim, surgical changes, stop before irreversible actions, treat external text as data) plus a pre-send checklist. Copy it to your global instruction file and rename:

```bash
# Claude Code
cp GLOBAL-RULES.template.md ~/.claude/CLAUDE.md

# Factory Droid
cp GLOBAL-RULES.template.md ~/.factory/AGENTS.md
```

The universal rules (Rules 1-16 and "Before you send") work as-is for any model. Lines marked `<CUSTOMIZE: ...>` are personal -- swap in your own tools, paths, language, and preferences, or delete the ones you don't need.

### Desktop Notifications

Desktop notifications are configured per-feature in your `settings.json`:

```json
{
  "hookNotifyPlanSave": true
}
```

- `hookNotifyPlanSave`: Notifications when plans are saved (default: `false`)

## Requirements

- Python 3.8+ (Factory Droid, Claude Code, WrongStack)

## OpenCode Support

[OpenCode](https://opencode.ai) is supported through a mix of native features and TypeScript plugins. Full details, install steps, and the complete limitations list are in [`opencode/README.md`](opencode/README.md).

- **Skills work natively.** OpenCode reads `SKILL.md` from `~/.claude/skills/`, so skills already deployed for Claude Code are visible -- invoked as the `skills_<name>` tool instead of a `/` command.
- **Rules work natively.** OpenCode reads `AGENTS.md` and the `opencode.json` `instructions` field.
- **Hooks become plugins.** The Python hooks are re-authored as TypeScript plugins under `opencode/plugins/`:

| Plugin                | OpenCode hook                       | Python origin         |
|-----------------------|-------------------------------------|-----------------------|
| `memory-save.ts`      | `stop`                              | `memory-save.py`      |
| `compact-reinject.ts` | `experimental.session.compacting`   | `compact-reinject.py` |
| `memory-inject.ts`    | `experimental.chat.system.transform`| `memory-reinject.py`  |

Install by copying the plugins to OpenCode's auto-loaded plugin directory and merging the example config:

```bash
cp opencode/plugins/*.ts ~/.config/opencode/plugins/
# then merge opencode/opencode.json.example into ~/.config/opencode/opencode.json
```

> The plugins are authored against OpenCode's documented hook API and pass `bun` transpilation, but they were not runtime-tested -- OpenCode was not installed during authoring. `memory-inject.ts` relies on `experimental.chat.system.transform`, which is blocked by upstream issue #17100; use the static `instructions` path for reliable memory. `save-plan.py` is not ported (OpenCode's plan model was not verified).

## WrongStack Support

[WrongStack](https://github.com/WrongStack/WrongStack) is supported through Python shell hooks and platform-tailored skills. WrongStack's shell-hook transport is Claude-compatible (stdin JSON → stdout JSON, exit code 2 = block) but field names and the outcome shape differ — a `_compat.py` shim absorbs those differences so hook logic stays identical to the Claude/Factory ports. Full details are in [`wrongstack/README.md`](wrongstack/README.md).

- **Hooks are Python shell hooks.** Written under `wrongstack/hooks/`, the same Python source logic is wired through the `_compat.py` shim:

| Hook                  | WrongStack event   | Matcher | Status |
|-----------------------|--------------------|---------|--------|
| `session-start.py`    | `SessionStart`     | —       | Ported (150-line memory cap for 64 KiB output safety) |
| `git-protect.py`      | `PreToolUse`       | `Bash`  | Direct port |
| `memory-reinject.py`  | `UserPromptSubmit` | —       | Ported (counter keyed by `sessionId`) |
| `memory-save.py`      | `Stop`             | —       | Redesigned — Stop is side-effects-only (no block), so it auto-generates/updates MEMORY.md directly from the session logs |
| `save-plan.py`        | `PostToolUse`      | `*`     | Heuristic matcher v1 (plan-exit tool name unconfirmed) |
| `compact-reinject.py` | —                  | —       | Not ported (no compaction event on WrongStack) |
| `notify.py`           | —                  | —       | Helper module |

- **Skills are available under `wrongstack/skills/`.** All 14 claude skills are ported with platform-specific adjustments where needed:

| Skill                          | Command                         | Description                                                                      |
|--------------------------------|---------------------------------|----------------------------------------------------------------------------------|
| `commit`                       | `/commit`                       | Conventional commits with repo style mimicry, smart staging, git safety protocol |
| `git-flow`                     | `/git-flow`                     | Overrides WrongStack's bundled git-flow with extended triggers                   |
| `bug-report`                   | `/bug-report`                   | General bug analysis plus focused audit subcommands                              |
| `task-plan`                    | `/task-plan`                    | PRD breakdown into features with autonomous execution                            |
| `initialize`                   | `/initialize`                   | Creates `AGENTS.md` by scanning the codebase                                     |
| `redate-commits`               | `/redate-commits`               | Rewrites commit dates across a selected range                                    |
| `frontend-design`              | `/frontend-design`              | Frontend code generation with 28-site design catalog                             |
| `version-update-skill-creator` | *(meta-skill)*                  | Creates a `/version-update` skill tailored to the current project                |
| `ai-seo`                       | `/ai-seo`                       | GEO optimization for AI search engines                                           |
| `draft-to-article`             | `/draft-to-article`             | Format drafts for X Articles, LinkedIn, or Medium/Substack                       |
| `http-cache`                   | `/http-cache`                   | HTTP caching with ETag and Cache-Control headers                                 |
| `audit-replay`                 | `/audit-replay`                 | User action tracking, audit event logging, and rrweb session replay              |
| `ios-uikit`                    | `/ios-uikit`                    | Programmatic UIKit development with 20 reference documents                       |
| `ios-simulator`                | `/ios-simulator`                | iOS simulator automation with 22 Node.js scripts                                 |

Platform-specific adjustments in the WrongStack copies:
- `draft-to-article`: generic ask-user phrasing (not `AskUserQuestion`)
- `bug-report/fix.md`: generic plan-mode reference (not `ExitPlanMode`)
- `initialize`: includes WrongStack in the agent list
- `version-update-skill-creator`: outputs to `.wrongstack/skills/`
- `git-flow`: override note in description

Skills can alternatively be deployed from `claude/skills/` — WrongStack also reads `~/.claude/skills/` natively — but the `wrongstack/skills/` versions include the platform-specific fixes above.

Install by registering hooks in `~/.wrongstack/config.json` and copying files:

```bash
# Hooks
cp wrongstack/hooks/* ~/.wrongstack/hooks/
# then merge the hooks block from wrongstack/config.example.json into ~/.wrongstack/config.json

# Skills (optional — WrongStack also reads skills from ~/.claude/skills/)
cp -r wrongstack/skills/* ~/.wrongstack/skills/
```

> The hooks are authored against WrongStack's documented hook API (`docs/hooks.md`, `packages/core/src/types/hooks.ts`, `packages/core/src/hooks/shell-executor.ts`) and pass `python3 -m py_compile`, but they were not runtime-tested — WrongStack was not installed during authoring. `memory-save.py`'s Claude pattern (block first stop, let second through) is impossible on WrongStack because Stop is side-effects-only, so it auto-generates MEMORY.md from the session logs instead. `save-plan.py` uses a heuristic tool-name matcher; the actual plan-exit tool name should be confirmed against your installed version. `compact-reinject.py` has no WrongStack equivalent (no compaction event). Skills are platform-agnostic and tested through their Claude/Factory equivalents.

## Platform Differences

| Feature                 | Factory Droid    | Claude Code       | WrongStack          |
|-------------------------|------------------|-------------------|---------------------|
| Global config dir       | `~/.factory/`    | `~/.claude/`      | `~/.wrongstack/`    |
| Shared data dir         | `~/.cli-tweaks/` | `~/.cli-tweaks/`  | `~/.cli-tweaks/`    |
| Hook config file        | `settings.json`  | `settings.json`   | `config.json`       |
| Hook runtime            | Python shell     | Python shell      | Python shell        |
| Plan mode exit event    | `ExitSpecMode`   | `ExitPlanMode`    | Heuristic match     |
| User question tool      | `AskUser`        | `AskUserQuestion` | (generic)           |
| Re-injection target     | `AGENTS.md`      | `CLAUDE.md`       | config-driven       |
| Skill invocation prefix | `/`              | `/`               | `/`                 |
| Stop block support      | ✅               | ✅                | ❌ Side-effects only|
| Compaction event        | ✅               | ✅                | ❌ None             |
| Hook output cap         | None             | None              | 64 KiB              |

## License

MIT
