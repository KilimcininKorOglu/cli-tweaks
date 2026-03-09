# Status Subcommand

When `/task-plan status` is executed, display a formatted table of all tasks.

## Usage

```bash
/task-plan status                        # Full status table
/task-plan status --filter=IN_PROGRESS   # Filter by status
/task-plan status --feature=F001         # Filter by feature
/task-plan status --priority=P1          # Filter by priority
```

## Output Format

```
| Task ID | Task Name                 | Status       | Priority | Feature |
|---------|---------------------------|--------------|----------|---------|
| T001    | Kayit formu UI            | COMPLETED    | P2       | F001    |
| T002    | Input validation          | COMPLETED    | P2       | F001    |
| T003    | API endpoint              | IN_PROGRESS  | P1       | F001    |
| T004    | Database migration        | NOT_STARTED  | P1       | F001    |

Summary:
  Total: 7 tasks
  COMPLETED:    2 (29%)
  IN_PROGRESS:  1 (14%)
  NOT_STARTED:  4 (57%)
  BLOCKED:      0 (0%)

Progress: [###...................] 29%
```

## Implementation Steps

1. Read all `tasks/XXX-*.md` files
2. Extract Task ID, Name, Status, Priority, Feature from each task
3. Build formatted table
4. Calculate summary statistics
5. Display progress bar
