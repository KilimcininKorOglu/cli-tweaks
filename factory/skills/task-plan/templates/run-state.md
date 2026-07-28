# Run State Template

Use this template for `tasks/run-state.md` (checkpoint file for `/task-plan run`):

```markdown
# Task Plan Run State

**Started:** 2024-01-15T10:00:00Z
**Last Updated:** 2024-01-15T14:30:00Z
**Status:** IN_PROGRESS

## Current Position
- **Current Feature:** F001
- **Current Task:** T003
- **Next Task:** T004

## Progress
| Task | Feature | Status      | Started | Completed | Duration |
|------|---------|-------------|---------|-----------|----------|
| T001 | F001    | COMPLETED   | 10:00   | 10:45     | 45m      |
| T002 | F001    | COMPLETED   | 10:45   | 11:30     | 45m      |
| T003 | F001    | IN_PROGRESS | 11:30   | -         | -        |

## Execution Queue
Priority-sorted remaining tasks:
1. T004 (P1, F001) - blocked by T003
2. T005 (P2, F001) - blocked by T004
3. T006 (P2, F002) - no deps

## Error Log
| Task | Attempt | Error                     | Timestamp |
|------|---------|---------------------------|-----------|
| T003 | 1       | Build failed: missing dep | 11:35     |

## Summary
- Total Features: 2
- Total Tasks: 10
- Completed: 2
- In Progress: 1
- Remaining: 7
- Blocked: 0
```
