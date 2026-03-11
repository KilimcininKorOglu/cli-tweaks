---
name: task-plan
description: >
  This skill MUST be invoked when the user says "task-plan", "görev planla",
  "break down this PRD", "create tasks from spec", "PRD'yi parçala",
  "görevleri oluştur" or any variation requesting task breakdown from a
  specification document. SHOULD also invoke when user mentions "feature
  breakdown", "sprint planning", "task tracking", or wants to manage a
  structured development workflow with features, tasks, and git branches.
---

# Task Plan - Generate Task Breakdown from PRD

Analyzes PRD/SPEC files and creates/updates comprehensive task breakdown structures.
Supports subcommands: `add`, `status`, `run`.

## Subcommands

| Command                          | Description                          |
|----------------------------------|--------------------------------------|
| `$task-plan`                     | Analyze PRD, generate/update tasks   |
| `$task-plan docs/PRD.md`         | Specify PRD path                     |
| `$task-plan add "description"`   | Add a new feature inline             |
| `$task-plan add @docs/spec.md`   | Add feature from file                |
| `$task-plan status`              | Show task status table               |
| `$task-plan run`                 | Run all tasks autonomously           |

## Operating Mode

On each execution:
1. **PRD Analysis**: Analyze the PRD file from scratch
2. **Check Current State**: Read existing files in `tasks/` directory
3. **Detect Changes**: Identify new features, changed requirements, or removed sections
4. **Incremental Update**: Update only changed parts, preserve existing progress

## Finding PRD File

1. If provided as argument: `$ARGUMENTS`
2. Otherwise search project root: `PRD.md`, `SPEC.md`, `prd.md`, `spec.md`, `docs/PRD.md`, `docs/SPEC.md`

## Core Steps

### Step 1: Find and Read PRD File

Search for PRD/SPEC in project root and docs/, specifications/, specs/ directories.

### Step 2: Analyze Existing Task Structure

If `tasks/` directory exists:
- Read all feature files (tasks/XXX-*.md)
- Read `tasks/tasks-status.md`
- Record status of completed and in-progress tasks
- Track highest Feature ID (FXXX) and Task ID (TXXX) for continuation

When PRD is added to an existing project with manually added features, new features
must continue from the highest existing IDs. Never reset or conflict.

### Step 3: Parse PRD and Compare

Extract: project metadata, feature boundaries, technical stack, user stories,
performance criteria, security requirements.

Compare with existing tasks:
- **New features**: In PRD but not in tasks/
- **Changed features**: Definition changed in PRD
- **Removed features**: In tasks/ but not in PRD (warn, don't delete)

### Step 4: Create/Update Task Structure

For each new feature, create `tasks/XXX-feature-name.md` using the
[feature template](assets/feature.md).

Rules for existing features:
- Preserve completed tasks (don't modify COMPLETED status)
- Preserve in-progress tasks (keep progress)
- Add new tasks for new requirements
- Mark changed requirements with AT_RISK status

Also update:
- [Status tracker](assets/status-tracker.md) at `tasks/tasks-status.md`
- [Execution plan](assets/execution-plan.md) at `tasks/task-execution-plan.md`

### Step 5: Generate Change Summary

Output: added features, updated features, warnings (removed from PRD), statistics.

## Task Properties Standards

Each task must include:
1. **Unique ID**: TXXX format
2. **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED | BLOCKED | AT_RISK | PAUSED
3. **Priority**: P1 (Critical) | P2 (High) | P3 (Medium) | P4 (Low)
4. **Effort**: Developer-days (1 day = 6-8 hours)
5. **Dependencies**: Hard and soft dependencies
6. **Success Criteria**: At least 3-5 measurable criteria
7. **Files to Touch**: File paths (new/update/delete)

Task sizing: Atomic tasks 0.5-5 days, Features 1-6 weeks, Milestones 1-3 months.

## Git Integration

See [references/run.md](references/run.md) for full git workflow.

Branch strategy: one branch per feature, one commit per task.
```
feature/FXXX-short-description
```

Branches are NEVER deleted to preserve history.

## Subcommand Details

- For `$task-plan add`: see [references/add.md](references/add.md)
- For `$task-plan status`: see [references/status.md](references/status.md)
- For `$task-plan run`: see [references/run.md](references/run.md)

## Quality Checklist

- [ ] All tasks have unique IDs
- [ ] Dependencies are not circular
- [ ] Estimates are realistic
- [ ] Success criteria are measurable
- [ ] File paths are correct
- [ ] Critical path is optimized
- [ ] Documentation and test tasks included
- [ ] No mock code or placeholders - all implementations must be production-ready
