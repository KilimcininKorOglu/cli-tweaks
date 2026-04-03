# Codex Diff Audit

This subcommand replaces the old standalone `/auditcodex` skill.

## Command

```bash
/bug-report auditcodex
```

## Gather Context

Collect the recent changes for review:

- Git diff (staged + unstaged): `git diff HEAD`
- Recent commits on this branch: `git log --oneline -10`
- Git status: `git status --short`

If `git diff HEAD` is empty, review the last commit instead with `git diff HEAD~1 HEAD`.

## Workflow

1. Prepare a concise summary of what changed by reviewing the diff, recent commits, and status.
2. Run Codex CLI with the full diff piped through stdin:

   ```bash
   git diff HEAD | codex exec --full-auto -m "gpt-5.4" -c 'model_reasoning_effort="xhigh"' -c 'service_tier="fast"' -s danger-full-access -C "$(pwd)" "You are a code reviewer. The following diff is piped to your stdin. Review it for: bugs, security issues, performance problems, logic errors, and style concerns. Be specific about file names and line numbers. You can read files, run tests, search the web for relevant docs, or do whatever you need for a thorough review. If everything looks good, say so. Do a deep audit and think from first principles. Leave no question unanswered. Here is context about what changed: <DIFF_SUMMARY>"
   ```

3. If there are no uncommitted changes, use the last-commit fallback:

   ```bash
   git diff HEAD~1 HEAD | codex exec --full-auto -m "gpt-5.4" -c 'model_reasoning_effort="xhigh"' -c 'service_tier="fast"' -s danger-full-access -C "$(pwd)" "You are a code reviewer. The following diff is piped to your stdin. Review it for: bugs, security issues, performance problems, logic errors, and style concerns. Be specific about file names and line numbers. You can read files, run tests, search the web for relevant docs, or do whatever you need for a thorough review. If everything looks good, say so. Here is context about what changed: <DIFF_SUMMARY>"
   ```

4. Validate every Codex finding before keeping it:
   - Check the actual source code to confirm the issue is real, not a hallucination or misread.
   - Check local project context (`AGENTS.md`, `README.md`, `CLAUDE.md`, planning notes, or similar files) to see whether Codex misunderstood an intentional decision.
   - Discard findings that are not both real and meaningful.

5. Write only the validated findings to `BUG-REPORT.md` using the shared report contract from `../SKILL.md`.
   - Continue the existing BUG ID sequence.
   - Do not create placeholder entries if Codex reports all-clear or if every finding fails validation.

## Output Rules

- `BUG-REPORT.md` is the primary artifact for validated findings.
- Do not produce a second full findings report in chat unless the user explicitly asks for one.
- If no validated findings remain after review, report that no entries were added to `BUG-REPORT.md`.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
