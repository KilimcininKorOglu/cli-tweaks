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

All findings are written to `BUG-REPORT.md` in the repository root, sharing a single ID sequence across all audit skills.

Check `BUG-REPORT.md` for existing IDs and increment from the highest. If none exists, start from BUG-001.

For each verified finding:

```
BUG-[ID]: [Brief description]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: NEW
File: [path/to/file.ext:line_number]
Component: [affected module/feature]

Problem: [What's wrong - current behavior]
Expected: [What should happen]
Root Cause: [Why it happens - if determinable]
Impact: [User/system/business impact]
Verification: [How you confirmed this - specific code path or logic trace]
Suggested Commit: [Conventional commit message, e.g. "fix: add rate limiting to payment endpoint"]
```

If `BUG-REPORT.md` already exists, append new findings and update the summary table.
If it does not exist, create it with:

```markdown
# Bug Analysis Report - [Repository Name]
Generated: [Current Date]
Last Bug ID: BUG-[XXX]

## Summary
| Severity     | Count |
|--------------|-------|
| Critical     | X     |
| High         | X     |
| Medium       | X     |
| Low          | X     |
| **Total**    | **X** |

## Findings
[All findings grouped by severity]

## Recommendations
[Suggested fixes and preventive measures]
```

## Notes

- Zero false positives is more important than completeness -- only report verified findings
- Suggested Commit messages follow conventional commits and NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
