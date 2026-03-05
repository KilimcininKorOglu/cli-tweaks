---
name: init-claude
description: >
  This skill MUST be invoked when the user says "init", "initialize",
  "başlat", "CLAUDE.md oluştur", "create CLAUDE.md" or any variation
  requesting CLAUDE.md creation. SHOULD also invoke when user mentions
  "setup Claude rules", "configure Claude Code". Analyzes the codebase
  and creates/updates a CLAUDE.md file for Claude Code. Scans project
  files, build configs, and existing AI rules to generate comprehensive
  guidance specific to Claude Code.
argument-hint: ""
---

# Init - Create CLAUDE.md

Analyzes the codebase and creates or updates a CLAUDE.md file for Claude Code (claude.ai/code).

## Target File

CLAUDE.md only. Do NOT create or modify AGENTS.md.

## Required Header

```
# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
```

## Files to Scan

| Priority | Files                                                                | Purpose                    |
|----------|----------------------------------------------------------------------|----------------------------|
| High     | `README.md`, `PROJECT.md`, `CONTRIBUTING.md`                         | Project overview           |
| High     | `package.json`, `Makefile`, `Cargo.toml`, `go.mod`, `pyproject.toml` | Build commands             |
| High     | `AGENTS.md`, `GEMINI.md`                                             | Existing AI rules to merge |
| High     | `.cursor/rules/`, `.cursorrules`                                     | Cursor AI rules            |
| High     | `.github/copilot-instructions.md`                                    | Copilot instructions       |
| High     | `.github/workflows/`                                                 | CI/CD build/test commands  |
| Medium   | `docker-compose.yml`, `Dockerfile`                                   | Container setup            |
| Medium   | `.env.example`, `config/`                                            | Configuration              |
| Medium   | `src/`, `lib/`, `app/` structure                                     | Architecture               |
| Medium   | `.gemini/settings.json`                                              | Gemini CLI config          |
| Low      | Linter/formatter configs                                             | Code style                 |
| Low      | `.aider.conf.yml`                                                    | Aider config               |

## What to Include

- Build/Run Commands (install, build, run, test)
- Single Test Execution (how to run individual tests)
- Architecture Overview (high-level structure)
- Key Patterns (codebase-specific conventions)
- Environment setup requirements (if present)
- Database/migration commands (if present)
- Monorepo workspace structure (if present)
- Security considerations (if present)
- PR/commit message guidelines (if present)
- Deployment steps (if present)

## What to Exclude

- Generic development practices
- Obvious instructions
- Complete file/directory listings
- Information easily found in config files
- Made-up sections like "Tips for Development" or "Support and Documentation"

## Behavior

- If CLAUDE.md does not exist: create it directly
- If CLAUDE.md already exists: show proposed changes and ask for confirmation
- If AGENTS.md or other AI config files exist, incorporate their important parts
- You can ONLY edit or create CLAUDE.md -- never touch AGENTS.md

## Output Guidelines

- Keep under 500 lines
- Focused, actionable, scoped rules
- Write like clear internal documentation
- Use tables for command references
- No fabricated information
- Commands verified against project structure
