# Technical Debt Mapping & Prioritization

This subcommand replaces the old standalone `/tech-debt` skill.

## Command

```bash
/bug-report tech-debt [--focus explicit|hidden|dependency|test|architectural|dead-code|all]
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

## Deep Dead Code Scan

Run an automated three-phase scan to precisely locate and triage dead code.

### Phase 1: Discovery

Hunt for these waste categories across the ENTIRE codebase:

**Unreachable Declarations**
- Functions/methods never invoked (including indirect calls, callbacks, event handlers)
- Variables/constants written but never read after assignment
- Types, classes, structs, enums, interfaces never instantiated or extended
- Entire source files never imported or excluded from compilation

**Dead Control Flow**
- Branches that can never be reached (conditions always true/false, code after unconditional return/throw/exit)
- Feature flags hardcoded to one state

**Phantom Dependencies**
- Import/require/use statements whose exported symbols are never used
- Package-level dependencies (package.json, go.mod, Cargo.toml, etc.) with zero usage in source

### Phase 2: Verification (Avoid False Positives)

Before marking anything dead, rule out:

| Exemption              | Description                            |
|------------------------|----------------------------------------|
| Dynamic dispatch       | Reflection, runtime type resolution    |
| Dependency injection   | Wiring via string names or decorators  |
| Serialization targets  | ORM models, JSON mappers, protobuf     |
| Metaprogramming        | Macros, annotations, code generators   |
| Test fixtures          | Test-only utilities and mocks          |
| Public API surface     | Library exports consumed externally    |
| Framework hooks        | beforeEach, onMount, middleware chains |
| Config-driven behavior | Symbol names in config files, env vars |

If any exemption applies, lower confidence and state the reason.

### Phase 3: Triage

| Risk   | Meaning                                                               |
|--------|-----------------------------------------------------------------------|
| HIGH   | Safe to delete immediately; zero external callers, no framework magic |
| MEDIUM | Likely dead but indirect usage possible; verify before deleting       |
| LOW    | Probably used via reflection/config/public API; flag for human review |

Write each HIGH/MEDIUM finding to `BUG-REPORT.md` using the shared format from `../SKILL.md`.
Severity: LOW for dead code (cleanup, not a bug). Suggested Commit: `dead: remove [description]`.

---

## Deep Test Quality Scan

Evaluate the test suite for coverage gaps, quality issues, and structural problems.

### Coverage Gaps

- Which public functions/methods have ZERO tests?
- Which error/exception paths are untested?
- Which edge cases are untested? (empty inputs, boundary values, null/nil, overflow, unicode)
- Which concurrent/async scenarios are untested?
- Which integration points are untested? (DB, HTTP, queue, file system)
- Which critical business rules have no dedicated test?

### Test Quality

For each existing test, check:

- Does it actually assert something meaningful? (not just "no exception thrown")
- Does it test behavior or implementation? (implementation tests break on refactoring)
- Is the test deterministic? (no time-dependency, no random data, no network calls)
- Is the test isolated? (no shared mutable state, no execution order dependency)
- Is mocking excessive? (>3 mocks per test = testing the mocks, not the code)

### Test Strategy

- Is the testing pyramid balanced? (many unit, fewer integration, few E2E)
- Are there contract tests for service boundaries?
- Are there security-focused tests? (injection attempts, auth bypass attempts)
- Is there mutation testing to verify test effectiveness?
- Are tests running in CI on every commit?

### Test Infrastructure

- Is test data management clean? (factories/fixtures, database reset between tests)
- Are slow tests tagged and separable from fast tests?
- Is the test suite fast enough for developer feedback loop? (<5 min for unit tests)

Write findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`. Severity: MEDIUM for missing critical coverage, LOW for quality issues.

---

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
