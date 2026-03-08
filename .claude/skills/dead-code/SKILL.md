---
name: dead-code
description: >
  This skill MUST be invoked when the user says "dead code", "ölü kod",
  "kullanılmayan kod", "unused code", "dead code audit", "ölü kod analizi"
  or any variation requesting dead code detection. SHOULD also invoke when
  user mentions "phantom dependencies", "unreachable code", "kullanılmayan
  import", "unused imports", or asks to find code that can be safely deleted.
  Analyzes the entire repository to identify dead code, unused declarations,
  and phantom dependencies. Creates a DEAD-CODE.md report with severity-ranked
  findings, cleanup roadmap, and executive summary.
argument-hint: "[--scope src|all] [--output DEAD-CODE.md]"
---

# Dead Code Audit

Conduct a surgical dead-code audit: detect, triage, and prescribe cleanup actions.

## Usage

```bash
/dead-code                     # Full codebase analysis
/dead-code --scope src         # Limit to src directory
/dead-code --output report.md  # Custom output file
```

## Process

### Phase 1: Discovery (Scan Everything)

Hunt for these waste categories across the ENTIRE codebase:

#### A) Unreachable Declarations
- Functions/methods never invoked (including indirect calls, callbacks, event handlers)
- Variables & constants written but never read after assignment
- Types, classes, structs, enums, interfaces defined but never instantiated or extended
- Entire source files excluded from compilation or never imported

#### B) Dead Control Flow
- Branches that can never be reached (conditions always true/false, code after unconditional return/throw/exit)
- Feature flags hardcoded to one state

#### C) Phantom Dependencies
- Import/require/use statements whose exported symbols go completely untouched
- Package-level dependencies (package.json, go.mod, Cargo.toml, etc.) with zero usage in source

### Phase 2: Verification (Don't Shoot Living Code)

Before marking anything dead, rule out these false-positive sources:

| Exemption                  | Description                                                    |
|----------------------------|----------------------------------------------------------------|
| Dynamic dispatch           | Reflection, runtime type resolution                            |
| Dependency injection       | Wiring via string names or decorators                          |
| Serialization targets      | ORM models, JSON mappers, protobuf                             |
| Metaprogramming            | Macros, annotations, code generators, template engines         |
| Test fixtures              | Test-only utilities and mocks                                  |
| Public API surface         | Library exports consumed externally                            |
| Framework hooks            | beforeEach, onMount, middleware chains                         |
| Config-driven behavior     | Symbol names in config files, env vars, feature registries     |

If any exemption applies, lower the confidence rating and state the reason.

### Phase 3: Triage (Prioritize the Cleanup)

Assign each finding a Risk Level:

| Risk   | Meaning                                                              |
|--------|----------------------------------------------------------------------|
| HIGH   | Safe to delete immediately; zero external callers, no framework magic |
| MEDIUM | Likely dead but indirect usage possible; verify before deleting       |
| LOW    | Probably used via reflection/config/public API; flag for human review |

## Output Format

Generate `DEAD-CODE.md` with three sections:

### Section 1: Findings Table

```markdown
| # | File | Line(s) | Symbol | Category | Risk | Confidence | Action |
|---|------|---------|--------|----------|------|------------|--------|
```

Categories: `UNREACHABLE_DECL` / `DEAD_FLOW` / `PHANTOM_DEP`

Actions: `DELETE` / `RENAME_TO_UNDERSCORE` / `MOVE_TO_ARCHIVE` / `MANUAL_VERIFY` / `SUPPRESS_WITH_COMMENT`

### Section 2: Cleanup Roadmap

Group findings into three sequential batches based on Risk Level.

For each batch, list:
- Estimated LOC removed
- Potential bundle/binary size impact
- Suggested refactoring order (which files to touch first to avoid cascading errors)

### Section 3: Executive Summary

```markdown
| Metric                       | Count |
|------------------------------|-------|
| Total findings               |       |
| High-confidence deletes      |       |
| Estimated LOC removed        |       |
| Estimated dead imports       |       |
| Files safe to delete entirely|       |
| Estimated build time improvement |   |
```

End with a one-paragraph assessment of overall codebase health and the top-3 highest-impact actions.

## Report Template

```markdown
# Dead Code Audit Report - [Repository Name]

Generated: [Current Date]
Scope: [Full codebase | src/ | custom path]

## Executive Summary

| Metric                         | Count |
|--------------------------------|-------|
| Total findings                 | X     |
| High-confidence deletes        | X     |
| Estimated LOC removed          | X     |
| Estimated dead imports         | X     |
| Files safe to delete entirely  | X     |

[One-paragraph codebase health assessment]

## Findings

| # | File | Line(s) | Symbol | Category | Risk | Confidence | Action |
|---|------|---------|--------|----------|------|------------|--------|
| 1 | path/file.ts | 42-50 | unusedFunc | UNREACHABLE_DECL | HIGH | 95% | DELETE |

## Cleanup Roadmap

### Batch 1: High Risk (Safe Deletes)
- Estimated LOC: X
- Files: [list]
- Order: [suggested sequence]

### Batch 2: Medium Risk (Verify First)
- Estimated LOC: X
- Files: [list]
- Verification steps: [what to check]

### Batch 3: Low Risk (Human Review)
- Estimated LOC: X
- Files: [list]
- Why flagged: [exemption reasons]

## Top 3 Recommended Actions

1. [Highest impact action]
2. [Second highest]
3. [Third highest]
```

## Notes

- Be thorough but avoid false positives
- Always check for dynamic usage before marking as dead
- Respect existing code patterns
- Group related findings together
- If previous `DEAD-CODE.md` exists, compare and note changes
