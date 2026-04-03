# Test Suite Quality & Strategy Review

This subcommand replaces the old standalone `/test-review` skill.

## Command

```bash
/bug-report test-review [--focus coverage|quality|strategy|infrastructure|all]
```

You are a test engineering lead evaluating the test suite of this project. Tests are the safety net — how strong is it?

## 1. Coverage Gaps

Identify the following:

- Which public functions/methods have ZERO tests?
- Which error/exception paths are untested?
- Which edge cases are untested? (empty inputs, boundary values, null/nil, overflow, unicode)
- Which concurrent/async scenarios are untested?
- Which integration points are untested? (DB, HTTP, queue, file system)
- Which critical business rules have no dedicated test?

Prioritize by risk: what's the business impact if this untested path fails?

## 2. Test Quality

For each existing test, check:

- Does it actually assert something meaningful? (not just "no exception thrown")
- Does it test behavior or implementation? (implementation tests break on refactoring)
- Is the test deterministic? (no time-dependency, no random data, no network calls, no file system race)
- Is the test isolated? (no shared mutable state with other tests, no execution order dependency)
- Is the test readable? (arrange-act-assert structure, descriptive name, clear intent)
- Is mocking excessive? (>3 mocks per test = testing the mocks, not the code)
- Are assertions specific enough? (asserting entire objects vs just the relevant fields)

## 3. Test Strategy

- Is the testing pyramid balanced? (many unit, fewer integration, few E2E)
- Are there contract tests for service boundaries?
- Are there performance/load tests for critical paths?
- Are there security-focused tests? (injection attempts, auth bypass attempts)
- Is there mutation testing to verify test effectiveness?
- Are tests running in CI on every commit?

## 4. Test Infrastructure

- Are test utilities and factories DRY and well-organized?
- Is test data management clean? (factories/fixtures, database reset between tests)
- Are slow tests tagged and separable from fast tests?
- Is the test suite fast enough for developer feedback loop? (<5 min for unit tests)

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
