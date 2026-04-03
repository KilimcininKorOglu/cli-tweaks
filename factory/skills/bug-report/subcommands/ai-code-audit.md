# AI-Generated & AI-Assisted Code Audit

This subcommand replaces the old standalone `/ai-code-audit` skill.

## Command

```bash
/bug-report ai-code-audit [--focus detection|security|quality|process|all]
```

You are a senior code auditor detecting and reviewing code generated or assisted by AI tools (Copilot, ChatGPT, Claude, Cursor, etc.). AI-generated code APPEARS to work but carries risks of subtle bugs, security vulnerabilities, and false confidence.

## 1. AI-Generated Code Indicators

Detect suspicious patterns:

- Excessive comments: unnecessary comments explaining every line (typical AI output)
- Inconsistent style: suddenly changing naming, spacing, idiom usage within a file
- "Textbook" code: works but doesn't follow the project's existing patterns
- Hallucination signs: non-existent API calls, wrong function signatures, phantom library usage
- Copy-paste traces: code taken from Stack Overflow or documentation examples but not adapted to context
- Missing security checks: AI typically generates "happy path", leaving gaps in error handling and security

## 2. Security Checkpoints

- Does AI-generated code have input validation? (AI often skips input safety)
- Are SQL queries parameterized? (AI sometimes generates queries with string interpolation)
- Is sensitive data management correct? (AI copies example code for token/key management, hardcodes)
- Is error handling sufficient? (AI typically only writes the "happy path")
- Are dependencies trustworthy? (AI can suggest non-existent or outdated libraries)
- Is cryptographic code correct? (AI frequently uses weak algorithms or wrong modes)

## 3. Quality Checkpoints

- Does the code conform to the project's existing architectural patterns? (or does it stand apart like an island)
- Have specific tests been written for AI-generated code? (AI writes its own tests too but they're usually shallow)
- Has the performance impact of generated code been evaluated? (AI can produce inefficient but working code)
- Are edge cases handled? (AI mostly solves the average scenario)
- Does the code follow existing error handling and logging patterns?
- Has license compliance been checked? (risk of AI generating copyrighted code)

## 4. Process and Culture

- Is the review process different for AI-generated code? (should require extra attention)
- Does the developer UNDERSTAND the AI output or accept it as a black box?
- What percentage of the project is AI-generated? (50%+ = high risk — nobody left who understands it)
- Is AI-generated code marked? (commit message, comment, label)

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
