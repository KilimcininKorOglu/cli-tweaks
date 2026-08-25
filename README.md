# cli-tweaks

[Türkçe](README.tr.md)

A collection of hooks, skills, and output styles for Factory Droid and Claude Code that add planning automation, persistent memory, smart commits, and more. Drop them into your home directory and they work out of the box. The two platforms share the same behavior, mirrored under `factory/` and `claude/`, diverging only where a platform contract requires it.

## What's Included

### Hooks

| Hook                  | Event                | Description                                                                                    |
|-----------------------|----------------------|------------------------------------------------------------------------------------------------|
| `session-start.py`    | SessionStart/compact | Injects global user files and project memory into context                                      |
| `save-plan.py`        | PreToolUse           | Notifies while a plan waits for approval; also saves the plan to disk on Factory |
| `notify-ask.py`       | PreToolUse           | Notifies while a question waits for an answer, with the first question's header |
| `notify-stop.py`      | Stop/StopFailure     | Notifies when the turn ends, with a one-line excerpt of the final message or the error |
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
| `initialize` / `init-claude`   | `/initialize`, `/init-claude`   | Scans the codebase and writes AGENTS.md (Factory, `initialize`) or CLAUDE.md (Claude Code, `init-claude`) |
| `redate-commits`               | `/redate-commits`               | Rewrites commit dates across a selected range with safe workflow warnings        |
| `frontend-design`              | `/frontend-design`              | Frontend code generation with 28-site design system catalog                      |
| `version-update-skill-creator` | `/version-update-skill-creator` | Scans project and creates a tailored version-update skill                        |
| `ai-seo`                       | `/ai-seo`                       | GEO optimization for AI search engines: 7-analysis sequential sweep, plus audit and fix |
| `draft-to-article`             | `/draft-to-article`             | Format drafts for X Articles, LinkedIn, or Medium/Substack                       |
| `ios-uikit`                    | `/ios-uikit`                    | Programmatic UIKit development with 20 reference documents                       |
| `ios-simulator`                | `/ios-simulator`                | iOS simulator automation with 22 Node.js scripts for semantic navigation         |
| `audit-replay`                 | `/audit-replay`                 | User action tracking, audit event logging, and rrweb session replay              |
| `http-cache`                   | `/http-cache`                   | HTTP caching with ETag and Cache-Control header implementation                   |
| `add-log`                      | `/add-log`                      | Adds centralized request, audit, and application logging                         |
| `goal-prep`                    | `/goal-prep`                    | Converts free-form work into a verifiable `/goal` completion condition           |
| `no-ai`                        | `/no-ai`                        | Rewrites text to remove common AI-generated writing patterns                     |
| `check-golang`                 | `/check-golang`                 | Runs four Go scans (govulncheck, gosec, golangci-lint, modernize) into a ranked report |
| `check-swift`                  | `/check-swift`                  | Runs four Swift scans (dependency-check, semgrep, SwiftLint, swift-format) into a ranked report |
| `check-rust`                   | `/check-rust`                   | Runs four Rust scans (cargo-audit, cargo-deny, clippy, edition check) into a ranked report |
| `check-js`                     | `/check-js`                     | Runs four JS/TS scans (package audit, semgrep, ESLint, knip) into a ranked report |
| `check-php`                    | `/check-php`                    | Runs four PHP scans (composer audit, Psalm taint, PHPStan, Rector) into a ranked report |

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
| `security-sweep`    | `/bug-report security-sweep`    | Run all 24 security scans with a rolling 2-worker pool    |
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

### Output Styles

Claude Code only. Factory Droid has no output-style contract, so this tree is not mirrored under `factory/`.

| Style        | File                                   | Description                                                                  |
|--------------|----------------------------------------|------------------------------------------------------------------------------|
| `ASD-STE100` | `claude/output-styles/ASD-STE100.md`   | Simplified Technical English: short sentences, active voice, one instruction per sentence, no invented metaphors, no hedging, no flattery, conclusion first |

Copy the file to `~/.claude/output-styles/`, then select it with `/output-style`. Claude Code reads an output style at session start, so an edit takes effect in the next session or after you re-select the style.

## Directory Structure

```
cli-tweaks/
  factory/           <-- Factory Droid (copy to ~/.factory/)
    hooks/
    skills/
    settings.json.example
  claude/            <-- Claude Code (copy to ~/.claude/)
    hooks/
    skills/
    output-styles/
    settings.json.example
  SOUL.md.template          <-- Custom persona template
  MEMORY.template.md        <-- Project memory structure template
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
npx degit KilimcininKorOglu/cli-tweaks/claude/output-styles /tmp/cli-tweaks-styles
cp -r /tmp/cli-tweaks-hooks/* ~/.claude/hooks/
cp -r /tmp/cli-tweaks-skills/* ~/.claude/skills/
mkdir -p ~/.claude/output-styles && cp -r /tmp/cli-tweaks-styles/* ~/.claude/output-styles/
rm -rf /tmp/cli-tweaks-hooks /tmp/cli-tweaks-skills /tmp/cli-tweaks-styles
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
mkdir -p ~/.claude/output-styles && cp -r claude/output-styles/* ~/.claude/output-styles/
```

### Hook Registration

After copying the files, register hooks by merging the hook definitions into your `settings.json`:

| Platform      | Source                          | Target                       |
|---------------|---------------------------------|------------------------------|
| Factory Droid | `factory/settings.json.example` | `~/.factory/settings.json`   |
| Claude Code   | `claude/settings.json.example`  | `~/.claude/settings.json`    |

Copy the `hooks` section from the example file into your existing settings, or use the example as a starting point.

### Selective Install

Pick only what you need. Examples below use `factory/`; replace with `claude/` for Claude Code.

```bash
# Just the notification hooks (notify.py is required by both)
cp factory/hooks/save-plan.py ~/.factory/hooks/
cp factory/hooks/notify-ask.py ~/.factory/hooks/
cp factory/hooks/notify-stop.py ~/.factory/hooks/
cp factory/hooks/notify.py ~/.factory/hooks/

# Just the memory system
cp factory/hooks/session-start.py ~/.factory/hooks/
cp factory/hooks/memory-save.py ~/.factory/hooks/

# Just the commit skill
cp -r factory/skills/commit ~/.factory/skills/

# Just the output style (Claude Code only)
mkdir -p ~/.claude/output-styles
cp claude/output-styles/ASD-STE100.md ~/.claude/output-styles/
```

> **Note:** `save-plan.py`, `notify-ask.py`, and `notify-stop.py` import `notify.py` at runtime. Always copy `notify.py` alongside any of them.

Then add the corresponding hook entries to your `settings.json`.

## How It Works

### Plan Saving

When you use the agent's built-in plan mode and exit it (`ExitPlanMode` on Claude Code, `ExitSpecMode` on Factory Droid), the `save-plan.py` hook captures the event.

Both platforms register it on `PreToolUse`, which fires *before* the approval prompt blocks on you. That is the moment a notification is useful: the plan is on screen and waiting for your answer. `PostToolUse` would only fire after you already answered, which is too late to be worth a notification. The notification names the project, so you can tell which session wants you when several are open.

The hook never blocks the tool: it exits 0 and writes nothing to stdout, so the approval prompt proceeds untouched.

On Factory Droid the hook also writes the plan content to `~/.factory/plans/<project>/`. Because it now runs before approval, a plan is archived whether or not you approve it. On Claude Code the tool provides no plan content to the hook, so it only notifies.

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

### Desktop Notifications

Desktop notifications are configured per-feature in your `settings.json`:

```json
{
  "hookNotifyPlanSave": true,
  "hookNotifyAskUser": true,
  "hookNotifyStop": true
}
```

- `hookNotifyPlanSave`: Notifications when a plan waits for approval (default: `false`)
- `hookNotifyAskUser`: Notifications when a question waits for an answer (default: `false`)
- `hookNotifyStop`: Notifications when the turn ends or fails (default: `false`)

Each key must be JSON `true`. Any other value, including the string `"false"`, leaves the feature off and is reported on stderr.

## Requirements

- Python 3.8+ (Factory Droid and Claude Code hooks)

## Platform Differences

| Feature                 | Factory Droid    | Claude Code       |
|-------------------------|------------------|-------------------|
| Global config dir       | `~/.factory/`    | `~/.claude/`      |
| Shared data dir         | `~/.cli-tweaks/` | `~/.cli-tweaks/`  |
| Hook config file        | `settings.json`  | `settings.json`   |
| Hook runtime            | Python shell     | Python shell      |
| Plan mode exit event    | `ExitSpecMode`   | `ExitPlanMode`    |
| User question tool      | `AskUser`        | `AskUserQuestion` |
| Re-injection target     | `AGENTS.md`      | `CLAUDE.md`       |
| Skill invocation prefix | `/`              | `/`               |
| Output styles           | not supported    | `~/.claude/output-styles/` |

## License

MIT
