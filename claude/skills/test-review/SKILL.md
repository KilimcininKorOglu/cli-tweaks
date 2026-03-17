---
name: test-review
description: >
  This skill MUST be invoked when the user says "test review", "test analizi",
  "test kalitesi", "test strategy", "test suite review", "test coverage analysis"
  or any variation requesting test suite quality evaluation. SHOULD also invoke
  when user mentions "coverage gaps", "test quality check", "testing pyramid",
  or asks to evaluate the strength of the test suite. Analyzes the entire test
  suite for coverage gaps, quality issues, strategy balance, and infrastructure
  problems. Produces a prioritized report with concrete test cases to add.
argument-hint: "[--focus coverage|quality|strategy|infrastructure|all]"
---

# Test Suite Quality & Strategy Review

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

## Output Format

For each finding produce:

1. **What's missing** — the specific gap or issue
2. **Risk** — business impact if this fails in production
3. **Concrete test case** — a specific test to add, with description
