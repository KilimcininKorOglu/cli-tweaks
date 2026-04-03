# Run Subcommand

When `/task-plan run` is executed, autonomously implement ALL tasks without stopping.

## CRITICAL: AUTONOMOUS EXECUTION RULE

This rule is NON-NEGOTIABLE and overrides all other behaviors:

- NEVER ask "Do you want to continue?" or any confirmation
- NEVER stop between tasks or features
- NEVER wait for user input
- NEVER output "Session Summary" when features remain
- NEVER list remaining features and stop
- After completing a task/feature, IMMEDIATELY start the next one
- ONLY stop when ALL tasks are completed or fatal unrecoverable error (after 3 retries)

## Execution Order Algorithm

Tasks execute based on Dependency + Priority:
1. Build dependency graph from all tasks
2. Find tasks with no unresolved dependencies
3. Sort by Priority (P1 first)
4. Execute highest priority available task
5. Mark completed, update dependencies
6. Repeat until done

## Checkpoint System

After each task completion:
1. Update task status to COMPLETED in feature file
2. Update `tasks/tasks-status.md`
3. Update `tasks/run-state.md` with current position (see [run-state template](../templates/run-state.md))
4. Update `tasks/task-execution-plan.md`
5. Git commit:
   ```bash
   git add -A
   git commit -m "feat(TXXX): [Task name] completed"
   ```

## Error Handling

If a task fails:
1. Retry up to 3 times
2. Log error in `tasks/run-state.md`
3. Mark task as BLOCKED
4. Continue to next available task

## Resume Mechanism

When context is compacted or session restarts:
1. Check `tasks/run-state.md`
2. If Status is IN_PROGRESS: resume from next task in queue
3. If not exists or COMPLETED: start fresh or report completion

Quick resume triggers: `devam`, `continue`, `devam et`

## Validation

After each task:
1. Run tests if test command exists
2. Run lint/type check if configured
3. Failure counts as task failure → error handling

## Task Summary Output

After each task (then continue immediately):
```
T001: Kayit formu UI completed (45m)
  Files: 3 created, 1 modified
  Tests: 12 passed
  Progress: [####................] 20% (2/10 tasks)
  Next: T003 - API endpoint
```

## Feature Summary Output

After feature completion (then continue immediately):
```
F001: User Registration - COMPLETED
  Tasks: 5/5 completed
  Duration: 2h 15m
  Feature Progress: [########............] 40% (2/5 features)
  Next Feature: F002 - Password Reset
  Continuing automatically...
```

Show ONLY the next feature. Do NOT list all remaining features.
"Session Summary" is ONLY allowed when remaining features = 0.

## Implementation Rules

- Write production-ready code only - no mock code, no placeholders, no TODOs
- Implement complete functionality for each task
- Follow project conventions and coding standards
- Handle edge cases properly
- Write meaningful commit messages

## Final Completion Output

When ALL tasks are done:
```
ALL TASKS COMPLETED
  Duration: 4h 30m
  Tasks: 10/10 completed
  Features: 2/2 completed
```
