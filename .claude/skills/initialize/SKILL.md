---
name: initialize
description: >
  This skill MUST be invoked when the user says "initialize", "init",
  "başlat", "AGENTS.md oluştur", "create AGENTS.md" or any variation
  requesting project initialization for AI agents. SHOULD also invoke
  when user mentions "setup AI rules", "configure agents", "agent
  kurallarını ayarla". Analyzes the codebase and creates/updates an
  AGENTS.md file for AI coding agents. Scans project files, build configs,
  and existing AI rules to generate comprehensive guidance for all AI agents
  (Cursor, Codex, Gemini CLI, Copilot, etc.).
argument-hint: ""
---

# Initialize - Create AGENTS.md

## Action

Immediately scan the codebase using the files listed below and create or update AGENTS.md. Do not wait for further instructions. Start scanning now.

## Target File

AGENTS.md only. Do NOT create or modify CLAUDE.md.

## Required Header

```
# AGENTS.md
This file provides guidance to AI coding agents (Claude Code, Cursor, Codex, Gemini CLI, GitHub Copilot, Devin, Windsurf, Amp, Jules, Aider, VS Code, Zed, goose, RooCode, etc.) when working with code in this repository.
```

## Files to Scan

| Priority | Files                                                                | Purpose                    |
|----------|----------------------------------------------------------------------|----------------------------|
| High     | `README.md`, `PROJECT.md`, `CONTRIBUTING.md`                         | Project overview           |
| High     | `package.json`, `Makefile`, `Cargo.toml`, `go.mod`, `pyproject.toml` | Build commands             |
| High     | `CLAUDE.md`, `GEMINI.md`                                             | Existing AI rules to merge |
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

- If AGENTS.md does not exist: create it directly
- If AGENTS.md already exists: analyze current content and update it directly
- If CLAUDE.md or other AI config files exist, incorporate their important parts
- If a monorepo is detected, suggest creating nested AGENTS.md files for each subproject
- You can ONLY edit or create AGENTS.md -- never touch CLAUDE.md

## Output Guidelines

- Keep under 500 lines
- Focused, actionable, scoped rules
- Write like clear internal documentation
- Use tables for command references
- No fabricated information
- Commands verified against project structure
- IMPORTANT: Always write in English only, regardless of conversation language
