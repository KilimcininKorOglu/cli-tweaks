# Feature File Template

Use this template when creating `tasks/XXX-feature-name.md`:

```markdown
# Feature N: Feature Name

**Feature ID:** FXXX
**Priority:** P[1-4] - [CRITICAL/HIGH/MEDIUM/LOW]
**Target Version:** vX.Y.Z
**Estimated Duration:** X-Y weeks
**Status:** NOT_STARTED

## Overview

[2-3 paragraph detailed description of the feature, its purpose, and how it fits into the overall system]

## Goals

- [Specific, measurable goal 1]
- [Specific, measurable goal 2]
- [Specific, measurable goal 3]

## Success Criteria

- [ ] All tasks completed
- [ ] All tests passing
- [ ] [Feature-specific criterion]

## Tasks

### TXXX: Task Name

**Status:** NOT_STARTED
**Priority:** P[1-4]
**Estimated Effort:** X days

#### Description

[Clear, detailed description of what this task accomplishes]

#### Technical Details

[Implementation notes, architecture decisions, code patterns to follow]

#### Files to Touch

- ` + "`path/to/file.go`" + ` (new)
- ` + "`path/to/existing.go`" + ` (update)

#### Dependencies

- TYYY (if depends on another task, use actual task ID like T001, T002)
- None (if no dependencies)

IMPORTANT: Dependencies MUST be valid task IDs (T001, T002, etc.) or "None".
Do NOT use descriptions like "All backend features", "Previous tasks", or any other text.

#### Success Criteria

- [ ] [Specific deliverable 1]
- [ ] [Specific deliverable 2]
- [ ] [Specific deliverable 3]
- [ ] Unit tests passing

---

[Repeat ### TXXX for each task in the feature]

## Performance Targets

- [Response time: < Xms]
- [Throughput: X requests/second]
- [Memory usage: < XMB]

## Risk Assessment

| Risk     | Probability     | Impact          | Mitigation            |
|----------|-----------------|-----------------|-----------------------|
| [Risk 1] | Low/Medium/High | Low/Medium/High | [Mitigation strategy] |

## Notes

[Any additional context, references, or considerations]
```
