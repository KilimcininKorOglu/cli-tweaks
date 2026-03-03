# Execution Plan Template

Use this template for `tasks/task-execution-plan.md`.
This file is for human planning and visualization. Updated by `/task-plan`, `/task-plan add`, and `/task-plan run`.

```markdown
# Task Execution Plan

**Generated:** [Date]
**Last Updated:** [Date]
**PRD Version:** [Hash or version]

## Progress Overview

| Feature                          | Status      | Tasks | Completed | Progress |
|----------------------------------|-------------|-------|-----------|----------|
| F001 - User Registration         | IN_PROGRESS | 5     | 2         | 40%      |
| F002 - Password Reset            | NOT_STARTED | 3     | 0         | 0%       |

## Execution Phases

### Phase 1: Foundation
**Goal:** [Phase goal]
**Status:** IN_PROGRESS
**Tasks:** T001-T005

| Task | Name               | Status         | Priority |
|------|--------------------|----------------|----------|
| T001 | Kayit formu UI     | COMPLETED      | P2       |
| T002 | Input validation   | COMPLETED      | P2       |
| T003 | API endpoint       | IN_PROGRESS    | P1       |
| T004 | Database migration | NOT_STARTED    | P1       |
| T005 | Unit tests         | NOT_STARTED    | P2       |

## Critical Path
[Tasks that must be done sequentially]

## Parallel Execution Opportunities
[Tasks that can be done in parallel]

## Completed Tasks Log
| Task | Feature | Completed        | Duration |
|------|---------|------------------|----------|
| T001 | F001    | 2024-01-15 10:45 | 45m      |
```
