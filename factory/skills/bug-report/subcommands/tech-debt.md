# Technical Debt Mapping & Prioritization

This subcommand replaces the old standalone `/tech-debt` skill.

## Command

```bash
/bug-report tech-debt [--focus explicit|hidden|dependency|test|architectural|all]
```

You are a senior software engineer systematically mapping, measuring, and prioritizing all technical debt in the codebase. Technical debt is like credit card debt — if you don't pay it, interest accumulates and eventually crashes the system.

## 1. Explicit Debt

Find issues already marked in code:

- Collect ALL TODO, FIXME, HACK, XXX, WORKAROUND, TEMPORARY, KLUDGE comments
- For each, determine the date (via git blame), author, and why it's still unresolved
- How many are older than 6 months? 1 year? 2 years?
- Which of these carry security or data integrity risk?
- Identify code written as a temporary solution that became permanent

## 2. Hidden Debt

Find problems that nobody marked but exist:

- Excessive complexity: functions with cyclomatic complexity >15, files >500 lines, functions with >5 parameters
- Duplicated code: code blocks with >80% similarity (copy-paste debt)
- Outdated patterns: old design approaches not used in the rest of the project
- Dead code: functions called from nowhere, unreachable endpoints, unused dependencies
- Missing abstraction: same logic manually repeated in 3+ places
- Wrong layer: business logic in controllers, database queries in views
- Undocumented behavior: critical code sections with no answer to "why does this work this way"

## 3. Dependency Debt

- How many dependencies are outdated? (minor, major, critical security updates)
- Are there deprecated API or function calls?
- Is there code stuck on an old version of the language/framework?
- Are there library changes that need migration but have been deferred?

## 4. Test Debt

- Which critical modules have test coverage below 80%?
- Are there broken (disabled/skipped) tests?
- Which flows require manual testing but have no automation?
- Is the test infrastructure itself technical debt? (slow, fragile, hard to maintain)

## 5. Architectural Debt

- Are there structures that were appropriate in the initial design but no longer fit scale/requirements?
- Are there modules that should be separated from the monolith but remain coupled?
- Are there database schema structures that no longer meet business requirements?
- Are there architectural shortcuts made during emergencies that were never fixed?

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
